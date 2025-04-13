"""Example of applying permission middleware to Linear API client."""

import asyncio
import os
from pathlib import Path

# Ensure we're loading the .env from the core/integrations directory
current_dir = Path(__file__).parent
dotenv_path = current_dir / '.env'

from dotenv import load_dotenv
# Load environment variables from .env file using the correct path
load_dotenv(dotenv_path=dotenv_path)

from core.engine.opa_client import OPAClient
from core.mapper import SimpleSchemaMapper
from core.middleware import PermissionMiddleware
from core.models import ResourceType, AccessType
from core.integrations.linear_client import LinearClient
from core.integrations import linear_integration, get_integration_mappings
from core.parser.parser import PermissionParser
from core.engine.policy_generator import RegoGenerator

async def main():
    """Demonstrate how to apply middleware to Linear client."""
    # Linear API configuration
    linear_api_key = os.environ.get("LINEAR_API_KEY")
    if not linear_api_key:
        print("ERROR: LINEAR_API_KEY environment variable is not set.")
        print("Please set this environment variable to your Linear API key before running this example.")
        return
    
    # Initialize OPA client, schema mapper, and register integration
    async with OPAClient() as engine:
        # Set up schema mapper and register Linear integration
        mapper = SimpleSchemaMapper()
        await mapper.register_integration(linear_integration)
        
        # Create and add some permission statements for testing
        parser = PermissionParser(integration_mappings=get_integration_mappings())
        generator = RegoGenerator()
        
        # Define test permission statements
        permission_statements = [
            "GIVE READ ACCESS TO ISSUES WITH PRIORITY = 1",
            "GIVE READ ACCESS TO TEAMS",
            "DENY READ ACCESS TO ISSUES WITH PRIORITY GREATER_THAN 3"
        ]
        
        # Add permissions to OPA
        for statement_text in permission_statements:
            print(f"Adding permission: {statement_text}")
            statement = parser.parse_statement(statement_text)
            policy = await generator.generate_policy(statement)
            policy_id = await engine.add_policy(policy)
            print(f"Added policy with ID: {policy_id}")
        
        # Configure middleware for Linear integration
        middleware_config = {
            "log_level": "debug",
            "endpoint_configs": {
                # Configuration for specific endpoints
                "issues.fetch_issues": {
                    "type": "collection",
                    "item_key": "id",
                    "response_format": "tuple"
                },
                "issues.get_issue": {
                    "type": "resource"
                },
                "teams.fetch_teams": {
                    "type": "collection",
                    "item_key": "id"
                }
            }
        }
        
        # Create middleware specifically for Linear integration
        middleware = PermissionMiddleware(
            engine=engine,
            schema_mapper=mapper,
            integration_name="linear",
            config=middleware_config
        )
        
        # Define method configs for Linear client methods
        linear_method_configs = {
            "fetch_issues": {
                "resource_type": ResourceType.ISSUES,
                "action": AccessType.READ,
                "options": {
                    "format_hint": "tuple",
                    "empty_result": ([], False)
                }
            },
            "fetch_teams": {
                "resource_type": ResourceType.TEAMS,
                "action": AccessType.READ,
                "options": {
                    "format_hint": "tuple",
                    "empty_result": ([], False)
                }
            },
            "fetch_projects": {
                "resource_type": ResourceType.PROJECTS,
                "action": AccessType.READ,
                "options": {
                    "format_hint": "tuple",
                    "empty_result": ([], False)
                }
            }
        }
        
        # Create a middleware-wrapped Linear client class
        LinearClientWithPermissions = middleware.apply_to(
            client_class=LinearClient,
            method_configs=linear_method_configs
        )
        
        # Create an instance of the wrapped client
        async with LinearClientWithPermissions(api_key=linear_api_key) as client:
            # The wrapped client methods now have permission checks
            print("Fetching issues with permission checks...")
            issues, has_more = await client.fetch_issues(priority=1)
            print(f"Retrieved {len(issues)} issues with priority 1")
            
            print("\nFetching teams with permission checks...")
            teams, has_more = await client.fetch_teams()
            print(f"Retrieved {len(teams)} teams")
            
            # Methods not in method_configs are passed through unchanged
            # You can still access the underlying client methods directly
            print("\nAccessing original client...")
            await client._client.close()
            
if __name__ == "__main__":
    asyncio.run(main()) 