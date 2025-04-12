"""Example usage of the permission system."""

import asyncio
import json

# Import the actual implementation classes directly
from .engine.opa_client import OPAClient
from .engine.policy_generator import RegoGenerator
from .parser.parser import PermissionParser
from .mapper import SimpleSchemaMapper  # Assuming this wasn't renamed yet

from .models import (
    ResourceType,
    SchemaMapping,
    FieldPath
)

async def main():
    """Example of permission system usage."""
    # Create instances directly instead of using defaults
    engine = OPAClient()
    parser = PermissionParser()
    mapper = SimpleSchemaMapper()
    policy_generator = RegoGenerator()
    
    # Example 1: Creating a permission statement and converting to Rego policy
    statement_text = "GIVE READ ACCESS TO EMAILS WITH TAGS = WORK"
    print(f"Permission statement: {statement_text}")
    
    # Parse the statement
    statement = await parser.parse_statement(statement_text)
    print(f"Parsed statement: {statement}")
    
    # Generate a Rego policy using the policy generator
    policy = await policy_generator.generate_policy(statement)
    print(f"Generated Rego policy for OPA:")
    print(policy.policy_content)
    
    # Add policy to the engine
    policy_id = await engine.add_policy(policy)
    print(f"Added policy with ID: {policy_id}")
    
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
    print(json.dumps(internal_request.dict(), indent=2))
    
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
        from .spec import get_version
        print(f"\nSpecification version: {get_version()}")
    except ImportError:
        print("\nSpecification version module not available")

if __name__ == "__main__":
    asyncio.run(main()) 