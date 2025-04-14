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
        async with LinearClientWithPermissions(api_key=linear_api_key) as client:
            # The wrapped client methods now have permission checks
            print("\nTrying to fetch issues with priority 3 (should be DENIED)...")
            try:
                result = await client.fetch_issues(priority=3)
                
                # Safely unpack result with None checks
                if isinstance(result, tuple) and len(result) >= 1:
                    issues = result[0] if result[0] is not None else []
                    has_more = result[1] if len(result) > 1 else False
                else:
                    issues = []
                    has_more = False
                
                # Debug output for permission enforcement
                print(f"Retrieved {len(issues)} issues with priority 3 after permission filtering")
                print(f"Expected: 0 issues (should be denied by permission rule)")
                
                if issues and len(issues) > 0:
                    print("ERROR: Priority 3 issues were allowed despite DENY rule!")
                    for issue in issues:
                        if issue is None:
                            print("  Warning: None issue found in results, skipping")
                            continue
                        print(f"  Issue {issue.get('identifier', 'unknown')}: Priority {issue.get('priority', 'unknown')}")
                else:
                    print("PASS: No priority 3 issues returned - permission policy correctly blocked them")
                    
            except Exception as e:
                print(f"Error fetching priority 3 issues: {str(e)}")
            
            # Also try to fetch priority 1 issues which should be allowed
            print("\nTrying to fetch priority 1 issues (should be ALLOWED)...")
            try:
                result1 = await client.fetch_issues(priority=1)
                
                # Safely unpack result with None checks
                if isinstance(result1, tuple) and len(result1) >= 1:
                    priority1_issues = result1[0] if result1[0] is not None else []
                else:
                    priority1_issues = []
                    
                print(f"Retrieved {len(priority1_issues)} priority 1 issues")
                print(f"Expected: >0 issues (should be allowed by permission rule)")
                
                if priority1_issues and len(priority1_issues) > 0:
                    print("PASS: Priority 1 issues were allowed as expected")
                else:
                    print("NOTE: No priority 1 issues found (might be OK if there are none in Linear)")
            except Exception as e:
                print(f"Error fetching priority 1 issues: {str(e)}")
            
            # Check for priority 2 issues which should be allowed by default
            print("\nTrying to fetch priority 2 issues (should be ALLOWED)...")
            try: 
                result2 = await client.fetch_issues(priority=2)
                
                # Safely unpack result with None checks
                if isinstance(result2, tuple) and len(result2) >= 1:
                    priority2_issues = result2[0] if result2[0] is not None else []
                else:
                    priority2_issues = []
                    
                print(f"Retrieved {len(priority2_issues)} priority 2 issues")
                print(f"Expected: Any number of issues (no specific rule for priority 2)")
                
            except Exception as e:
                print(f"Error fetching priority 2 issues: {str(e)}")
            
            print("\nFetching teams with permission checks...")
            teams, has_more = await client.fetch_teams()
            print(f"Retrieved {len(teams)} teams")
            
            # Methods not in method_configs are passed through unchanged
            # You can still access the underlying client methods directly
            print("\nAccessing original client...")
            await client._client.close()
            
if __name__ == "__main__":
    asyncio.run(main()) 