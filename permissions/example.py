"""Example usage of the permission system."""

import asyncio
import json
import os
import sys
import logging

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Add the parent directory to sys.path
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# Import integrations first to ensure they're registered
from permissions.integrations import get_integration_mappings
from permissions.integrations import gmail_integration, linear_integration

# Now we can import from permissions directly
from permissions.engine.opa_client import OPAClient
from permissions.engine.policy_generator import RegoGenerator
from permissions.parser.parser import PermissionParser
from permissions.mapper import SimpleSchemaMapper

from permissions.models import (
    ResourceType,
    SchemaMapping,
    FieldPath
)

async def main():
    """Example of permission system usage."""
    # Get integration mappings
    integration_mappings = get_integration_mappings()
    print(f"Loaded {len(integration_mappings)} integrations: {', '.join(integration_mappings.keys())}")

    # Create instances directly with integration mappings
    async with OPAClient() as engine:
        parser = PermissionParser(integration_mappings=integration_mappings)
        mapper = SimpleSchemaMapper()
        policy_generator = RegoGenerator()
        
        # Register integrations with the mapper
        await mapper.register_integration(gmail_integration)
        await mapper.register_integration(linear_integration)
        
        # First check OPA health
        print("Checking OPA health...")
        is_healthy, error_msg = await engine.check_health()
        if is_healthy:
            print("OPA is healthy and ready to accept policies.")
        else:
            print(f"OPA health check failed: {error_msg}")
            print("Continuing with examples, but OPA operations may fail.")
        
        # Example 1: Creating a permission statement and converting to Rego policy
        statement_text = "GIVE READ ACCESS TO EMAILS WITH TAGS = WORK"
        print(f"\nPermission statement: {statement_text}")
        
        # Parse the statement
        statement = parser.parse_statement(statement_text)
        print(f"Parsed statement: {statement}")
        
        # Generate a Rego policy using the policy generator
        policy = await policy_generator.generate_policy(statement)
        print(f"Generated Rego policy for OPA:")
        print(policy.policy_content)
        
        # Add policy to the engine
        try:
            policy_id = await engine.add_policy(policy)
            print(f"Added policy with ID: {policy_id}")
        except RuntimeError as e:
            print(f"Failed to add policy: {e}")
            
        # Example 2: Schema mapping for Gmail API with nested field paths
        gmail_mapping = SchemaMapping(
            source_api="gmail",
            resource_type=ResourceType.EMAILS,
            property_mappings={
                "tags": FieldPath("labelIds"),
                "sender": FieldPath("payload.headers.from"),
                "recipient": FieldPath("payload.headers.to"),
                "subject": FieldPath("payload.headers.subject"),
                "sender_domain": FieldPath("payload.headers.from_domain"),
                "has_attachments": FieldPath("payload.hasAttachments")
            },
            transformation_rules={
                "tags": "to_list",  # Convert comma-separated string to list
                "sender_domain": "format:{sender.split('@')[1]}"  # Extract domain part
            }
        )
        
        # Add mapping
        mapping_id = await mapper.add_mapping(gmail_mapping)
        print(f"Added mapping with ID: {mapping_id}")
        
        # Example 3: Transform a nested Gmail email request to internal format
        gmail_request = {
            "action": "read",
            "resource_type": "emails",
            "id": "msg123",
            "threadId": "thread456",
            "payload": {
                "headers": {
                    "from": "john@example.com",
                    "to": "mary@example.com",
                    "subject": "Weekly Meeting"
                },
                "body": {
                    "data": "Hello, let's discuss the project progress."
                },
                "hasAttachments": True
            },
            "labelIds": "WORK,IMPORTANT"
        }
        
        # Pretty print the Gmail request
        print("\nGmail API request (with nested fields):")
        print(json.dumps(gmail_request, indent=2))
        
        # Transform request
        internal_request = await mapper.transform_request("gmail", gmail_request)
        print("\nTransformed request:")
        print(json.dumps(internal_request.model_dump(), indent=2))
        
        # Check access using transformed request
        result = await engine.check_access(internal_request)
        print(f"\nAccess result: {result}")
        
        # Example 4: Another request that should be denied (personal email)
        personal_email_request = {
            "action": "read",
            "resource_type": "emails",
            "id": "msg789",
            "threadId": "thread999",
            "payload": {
                "headers": {
                    "from": "friend@personal.com",
                    "to": "mary@example.com",
                    "subject": "Dinner tonight?"
                },
                "body": {
                    "data": "Hey, are you free for dinner tonight?"
                },
                "hasAttachments": False
            },
            "labelIds": "PERSONAL"
        }
        
        # Transform and check
        internal_request = await mapper.transform_request("gmail", personal_email_request)
        result = await engine.check_access(internal_request)
        print(f"\nAccess result for personal email: {result}")
        
        # Example 5: Accessing the specification version
        try:
            from permissions.spec import get_version
            print(f"\nSpecification version: {get_version()}")
        except ImportError:
            print("\nSpecification version module not available")
        
        # Example 6: List all policies and display them
        print("\nListing all policies:")
        policies = await engine.list_policies()
        for i, policy in enumerate(policies):
            print(f"Policy {i+1}: {policy.package_name}")
        
        # The engine's HTTP client will be automatically closed when exiting the async with block

if __name__ == "__main__":
    asyncio.run(main()) 