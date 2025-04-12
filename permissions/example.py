"""Example usage of the permission system."""

import asyncio
from .default import get_default_engine, get_default_translator, get_default_mapper
from .models import (
    ResourceType,
    SchemaMapping
)

async def main():
    """Example of permission system usage."""
    # Get default instances
    engine = get_default_engine()
    translator = get_default_translator()
    mapper = get_default_mapper()
    
    # Example 1: Creating a permission statement and converting to Rego policy
    statement_text = "GIVE READ ACCESS TO EMAILS WITH TAGS = WORK"
    print(f"Permission statement: {statement_text}")
    
    # Parse the statement
    statement = await translator.parse_statement(statement_text)
    print(f"Parsed statement: {statement}")
    
    # Translate to a Rego policy
    policy = await translator.translate(statement)
    print(f"Generated Rego policy for OPA:")
    print(policy.policy_content)
    
    # Add policy to the engine
    policy_id = await engine.add_policy(policy)
    print(f"Added policy with ID: {policy_id}")
    
    # Example 2: Schema mapping for Gmail API
    gmail_mapping = SchemaMapping(
        source_api="gmail",
        resource_type=ResourceType.EMAILS,
        property_mappings={
            "tags": "labels",
            "sender": "from",
            "recipient": "to",
            "subject": "subject"
        },
        transformation_rules={
            "tags": "to_list"  # Convert comma-separated string to list
        }
    )
    
    # Add mapping
    mapping_id = await mapper.add_mapping(gmail_mapping)
    print(f"Added mapping with ID: {mapping_id}")
    
    # Example 3: Transform an external request to internal format
    gmail_request = {
        "action": "read",
        "resource_type": "emails",
        "from": "john@example.com",
        "to": "mary@example.com",
        "subject": "Weekly Meeting",
        "labels": "WORK,IMPORTANT"
    }
    
    # Transform request
    internal_request = await mapper.transform_request("gmail", gmail_request)
    print(f"Transformed request: {internal_request}")
    
    # Check access
    result = await engine.check_access(internal_request)
    print(f"Access result: {result}")
    
    # Example 4: Another request that should be denied
    personal_email_request = {
        "action": "read",
        "resource_type": "emails",
        "from": "friend@example.com",
        "to": "mary@example.com",
        "subject": "Dinner tonight?",
        "labels": "PERSONAL"
    }
    
    # Transform and check
    internal_request = await mapper.transform_request("gmail", personal_email_request)
    result = await engine.check_access(internal_request)
    print(f"Access result for personal email: {result}")

if __name__ == "__main__":
    asyncio.run(main()) 