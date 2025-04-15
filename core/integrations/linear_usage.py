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
    
    # Print masked API key for debugging (only show first few characters)
    if len(linear_api_key) > 10:
        print(f"Using Linear API key: {linear_api_key[:4]}...{linear_api_key[-4:]}")
    else:
        print("API key seems to be too short or malformed")
        
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
            "DENY READ ACCESS TO ISSUES WITH PRIORITY = 3"
        ]
        
        # Add permissions to OPA
        for statement_text in permission_statements:
            print(f"Adding permission: {statement_text}")
            statement = parser.parse_statement(statement_text)
            policy = await generator.generate_policy(statement)
            
            # Debug output to see the actual Rego policy being generated
            print(f"\nGenerated Rego policy for: {statement_text}")
            print(f"Package: {policy.package_name}")
            print(f"Policy content:\n{policy.policy_content}")
            
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
                    "empty_result": ([], False),
                    "debug": True  # Enable debug mode for this method
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
        print("\nCreating client with permission middleware...")
        try:
            async with LinearClientWithPermissions(api_key=linear_api_key) as client:
                print("Linear client created successfully.")
                
                # SIMPLIFIED TEST - Test one priority at a time to isolate the issue
                for priority in [1, 2, 3]:
                    print(f"\nTrying priority {priority}...")
                    try:
                        # IMPORTANT: Properly handle the result which might be None
                        result = await client.fetch_issues(priority=priority)
                        
                        if result is None:
                            print(f"Got None result for priority={priority}")
                            continue
                            
                        # Safe unpacking
                        if isinstance(result, tuple) and len(result) >= 1:
                            issues = result[0] if result[0] is not None else []
                            has_more = result[1] if len(result) > 1 else False
                            print(f"Got tuple result: ({len(issues)} issues, has_more={has_more})")
                        else:
                            print(f"Got unexpected result type: {type(result)}")
                            issues = []
                            has_more = False
                            
                        print(f"Retrieved {len(issues)} issues with priority {priority}")
                    except Exception as e:
                        print(f"Error testing priority {priority}: {str(e)}")
                        import traceback
                        traceback.print_exc()
                
                print("\nTesting teams API...")
                try:
                    # Test teams API which should be allowed
                    teams_result = await client.fetch_teams()
                    if teams_result is None:
                        print("Got None result for teams")
                    else:
                        teams = teams_result[0] if isinstance(teams_result, tuple) and len(teams_result) > 0 else []
                        print(f"Retrieved {len(teams)} teams")
                except Exception as e:
                    print(f"Error fetching teams: {str(e)}")
        except Exception as e:
            print(f"Error creating Linear client: {str(e)}")
            
if __name__ == "__main__":
    asyncio.run(main()) 