"""Linear API client for interacting with Linear's GraphQL API."""

import logging
from typing import Dict, List, Optional, Any

import httpx

# Set up logging
logger = logging.getLogger(__name__)

class LinearClient:
    """Client for interacting with Linear's GraphQL API."""
    
    def __init__(self, api_key: str):
        """
        Initialize the Linear client.
        
        Args:
            api_key: The Linear API key
        """
        self.api_url = "https://api.linear.app/graphql"
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
        self.http_client = httpx.AsyncClient(timeout=10.0)
    
    async def __aenter__(self) -> "LinearClient":
        """Async context manager entry."""
        return self
    
    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Async context manager exit."""
        await self.close()
    
    async def close(self) -> None:
        """Close the HTTP client and release resources."""
        await self.http_client.aclose()
    
    async def execute_query(self, query: str, variables: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Execute a GraphQL query against the Linear API.
        
        Args:
            query: The GraphQL query to execute
            variables: Variables for the query
            
        Returns:
            Dict[str, Any]: The query result
        """
        try:
            response = await self.http_client.post(
                self.api_url,
                headers=self.headers,
                json={"query": query, "variables": variables or {}}
            )
            response.raise_for_status()
            
            result = response.json()
            
            if "errors" in result:
                error_msg = result["errors"][0].get("message", "Unknown GraphQL error")
                logger.error(f"GraphQL error: {error_msg}")
                raise ValueError(f"GraphQL error: {error_msg}")
            
            return result.get("data", {})
        except httpx.HTTPStatusError as e:
            error_msg = f"HTTP error {e.response.status_code} querying Linear API: {str(e)}"
            logger.error(error_msg)
            raise RuntimeError(error_msg)
        except httpx.RequestError as e:
            error_msg = f"Request error querying Linear API: {str(e)}"
            logger.error(error_msg)
            raise RuntimeError(error_msg)
    
    async def fetch_issues(self, 
                          assignee: Optional[str] = None, 
                          labels: Optional[List[str]] = None, 
                          status: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Fetch issues from Linear based on criteria.
        
        Args:
            assignee: Filter by assignee name/ID
            labels: Filter by issue labels
            status: Filter by issue status
            
        Returns:
            List[Dict[str, Any]]: List of matching issues
        """
        # Build filter conditions
        filter_conditions = []
        variables = {}
        
        if assignee:
            filter_conditions.append("assignee: { name: { eq: $assignee } }")
            variables["assignee"] = assignee
        
        if labels and len(labels) > 0:
            filter_conditions.append("labels: { name: { in: $labels } }")
            variables["labels"] = labels
        
        if status:
            filter_conditions.append("state: { name: { eq: $status } }")
            variables["status"] = status
        
        # Create filter string
        filter_string = ", ".join(filter_conditions)
        filter_clause = f"filter: {{ {filter_string} }}" if filter_string else ""
        
        query = f"""
        query Issues($assignee: String, $labels: [String!], $status: String) {{
            issues({filter_clause}) {{
                nodes {{
                    id
                    title
                    description
                    assignee {{ 
                        id
                        name
                    }}
                    state {{
                        id
                        name
                    }}
                    labels {{
                        nodes {{
                            id
                            name
                        }}
                    }}
                    createdAt
                    updatedAt
                }}
            }}
        }}
        """
        
        # Execute the query
        result = await self.execute_query(query, variables)
        
        # Process and return the issues
        if "issues" in result and "nodes" in result["issues"]:
            issues = result["issues"]["nodes"]
            
            # Transform the issues to match our internal format
            transformed_issues = []
            for issue in issues:
                # Extract label names
                labels = []
                if "labels" in issue and "nodes" in issue["labels"]:
                    labels = [label["name"] for label in issue["labels"]["nodes"]]
                
                # Extract assignee
                assignee_name = None
                if issue.get("assignee"):
                    assignee_name = issue["assignee"].get("name")
                
                # Extract status
                status = None
                if issue.get("state"):
                    status = issue["state"].get("name")
                
                transformed_issues.append({
                    "id": issue.get("id"),
                    "title": issue.get("title"),
                    "description": issue.get("description"),
                    "assignee": assignee_name,
                    "labels": labels,
                    "status": status,
                    "created_date": issue.get("createdAt"),
                    "updated_date": issue.get("updatedAt")
                })
            
            return transformed_issues
        
        return []
    
    async def fetch_teams(self, owner: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Fetch teams from Linear.
        
        Args:
            owner: Filter by team owner name/ID
            
        Returns:
            List[Dict[str, Any]]: List of matching teams
        """
        # Build filter conditions
        filter_conditions = []
        variables = {}
        
        if owner:
            filter_conditions.append("owner: { name: { eq: $owner } }")
            variables["owner"] = owner
        
        # Create filter string
        filter_string = ", ".join(filter_conditions)
        filter_clause = f"filter: {{ {filter_string} }}" if filter_string else ""
        
        query = f"""
        query Teams($owner: String) {{
            teams({filter_clause}) {{
                nodes {{
                    id
                    name
                    key
                    description
                    owner {{
                        id
                        name
                    }}
                }}
            }}
        }}
        """
        
        # Execute the query
        result = await self.execute_query(query, variables)
        
        # Process and return the teams
        if "teams" in result and "nodes" in result["teams"]:
            teams = result["teams"]["nodes"]
            
            # Transform the teams to match our internal format
            transformed_teams = []
            for team in teams:
                # Extract owner
                owner_name = None
                if team.get("owner"):
                    owner_name = team["owner"].get("name")
                
                transformed_teams.append({
                    "id": team.get("id"),
                    "name": team.get("name"),
                    "key": team.get("key"),
                    "description": team.get("description"),
                    "owner": owner_name
                })
            
            return transformed_teams
        
        return [] 