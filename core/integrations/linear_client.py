"""Linear API client for interacting with Linear's GraphQL API."""

import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime

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
                          status: Optional[str] = None,
                          priority: Optional[int] = None,
                          first: int = 100) -> Tuple[List[Dict[str, Any]], bool]:
        """
        Fetch issues from Linear based on criteria.
        
        Args:
            assignee: Filter by assignee name
            labels: Filter by issue labels
            status: Filter by issue state name
            priority: Filter by issue priority (1-4)
            first: Maximum number of issues to fetch
            
        Returns:
            Tuple[List[Dict[str, Any]], bool]: Tuple of (issues list, has_next_page)
        """
        # Build filter variables
        variables = {
            "first": first
        }
        
        # Build filter conditions for the filter object
        filter_parts = []
        
        if assignee:
            filter_parts.append("assignee: { name: { eq: $assigneeName } }")
            variables["assigneeName"] = assignee
            
        if labels and len(labels) > 0:
            filter_parts.append("labels: { name: { in: $labelNames } }")
            variables["labelNames"] = labels
            
        if status:
            filter_parts.append("state: { name: { eq: $stateName } }")
            variables["stateName"] = status
            
        if priority is not None:
            filter_parts.append("priority: { eq: $priority }")
            variables["priority"] = priority
        
        # Construct filter clause
        filter_clause = ""
        if filter_parts:
            filter_string = ", ".join(filter_parts)
            filter_clause = f"(filter: {{ {filter_string} }}, first: $first)"
        else:
            filter_clause = "(first: $first)"

        # GraphQL query with pagination
        query = """
        query IssueSearch(
            $first: Int!,
            $assigneeName: String,
            $labelNames: [String!],
            $stateName: String,
            $priority: Int
        ) {
            issues""" + filter_clause + """ {
                nodes {
                    id
                    identifier
                    title
                    description
                    priority
                    estimate
                    dueDate
                    createdAt
                    updatedAt
                    assignee {
                        id
                        name
                        email
                    }
                    state {
                        id
                        name
                        color
                        type
                    }
                    labels {
                        nodes {
                            id
                            name
                            color
                        }
                    }
                    team {
                        id
                        name
                        key
                    }
                    project {
                        id
                        name
                    }
                }
                pageInfo {
                    hasNextPage
                    endCursor
                }
            }
        }
        """
        
        # Execute the query
        result = await self.execute_query(query, variables)
        
        # Process and return the issues
        issues_data = []
        has_next_page = False
        
        if "issues" in result:
            if "nodes" in result["issues"]:
                issues = result["issues"]["nodes"]
                
                # Transform issues to match our internal format
                for issue in issues:
                    # Extract labels
                    label_list = []
                    if issue.get("labels") and "nodes" in issue["labels"]:
                        label_list = [label["name"] for label in issue["labels"]["nodes"]]
                    
                    # Extract assignee
                    assignee_name = None
                    if issue.get("assignee"):
                        assignee_name = issue["assignee"].get("name")
                    
                    # Extract state/status
                    state_name = None
                    if issue.get("state"):
                        state_name = issue["state"].get("name")
                    
                    # Extract team
                    team_name = None
                    if issue.get("team"):
                        team_name = issue["team"].get("name")
                    
                    # Format dates 
                    created_date = issue.get("createdAt")
                    updated_date = issue.get("updatedAt")
                    due_date = issue.get("dueDate")
                    
                    issues_data.append({
                        "id": issue.get("id"),
                        "identifier": issue.get("identifier"),
                        "title": issue.get("title"),
                        "description": issue.get("description"),
                        "priority": issue.get("priority"),
                        "estimate": issue.get("estimate"),
                        "assignee": assignee_name,
                        "labels": label_list,
                        "status": state_name,
                        "team": team_name,
                        "project": issue.get("project", {}).get("name"),
                        "created_date": created_date,
                        "updated_date": updated_date,
                        "due_date": due_date
                    })
            
            # Check for pagination info
            if "pageInfo" in result["issues"]:
                has_next_page = result["issues"]["pageInfo"].get("hasNextPage", False)
        
        return issues_data, has_next_page
    
    async def fetch_teams(self, 
                         owner: Optional[str] = None,
                         first: int = 50) -> Tuple[List[Dict[str, Any]], bool]:
        """
        Fetch teams from Linear.
        
        Args:
            owner: Filter by team owner name
            first: Maximum number of teams to fetch
            
        Returns:
            Tuple[List[Dict[str, Any]], bool]: Tuple of (teams list, has_next_page)
        """
        # Build filter variables
        variables = {
            "first": first
        }
        
        # Build filter conditions
        filter_parts = []
        
        if owner:
            filter_parts.append("members: { user: { name: { eq: $ownerName } }, isAdmin: true }")
            variables["ownerName"] = owner
        
        # Construct filter clause
        filter_clause = ""
        if filter_parts:
            filter_string = ", ".join(filter_parts)
            filter_clause = f"(filter: {{ {filter_string} }}, first: $first)"
        else:
            filter_clause = "(first: $first)"
        
        # GraphQL query with pagination
        query = """
        query TeamSearch(
            $first: Int!,
            $ownerName: String
        ) {
            teams""" + filter_clause + """ {
                nodes {
                    id
                    name
                    key
                    description
                    color
                    states {
                        nodes {
                            id
                            name
                            color
                            type
                        }
                    }
                    members {
                        nodes {
                            user {
                                id
                                name
                                email
                            }
                            isAdmin
                        }
                    }
                    createdAt
                    updatedAt
                }
                pageInfo {
                    hasNextPage
                    endCursor
                }
            }
        }
        """
        
        # Execute the query
        result = await self.execute_query(query, variables)
        
        # Process and return the teams
        teams_data = []
        has_next_page = False
        
        if "teams" in result:
            if "nodes" in result["teams"]:
                teams = result["teams"]["nodes"]
                
                for team in teams:
                    # Extract members and identify owner/admin
                    members = []
                    owner_name = None
                    
                    if team.get("members") and "nodes" in team["members"]:
                        for member in team["members"]["nodes"]:
                            if member.get("user"):
                                user = member["user"]
                                members.append(user.get("name"))
                                
                                # Admin member is considered an owner
                                if member.get("isAdmin"):
                                    if not owner_name:  # First admin found becomes owner
                                        owner_name = user.get("name")
                    
                    # Extract states
                    states = []
                    if team.get("states") and "nodes" in team["states"]:
                        states = [state["name"] for state in team["states"]["nodes"]]
                    
                    teams_data.append({
                        "id": team.get("id"),
                        "name": team.get("name"),
                        "key": team.get("key"),
                        "description": team.get("description"),
                        "color": team.get("color"),
                        "owner": owner_name,
                        "members": members,
                        "states": states,
                        "created_date": team.get("createdAt"),
                        "updated_date": team.get("updatedAt")
                    })
            
            # Check for pagination info
            if "pageInfo" in result["teams"]:
                has_next_page = result["teams"]["pageInfo"].get("hasNextPage", False)
        
        return teams_data, has_next_page
        
    async def fetch_projects(self, 
                           team_id: Optional[str] = None,
                           first: int = 50) -> Tuple[List[Dict[str, Any]], bool]:
        """
        Fetch projects from Linear.
        
        Args:
            team_id: Filter by team ID
            first: Maximum number of projects to fetch
            
        Returns:
            Tuple[List[Dict[str, Any]], bool]: Tuple of (projects list, has_next_page)
        """
        # Build filter variables
        variables = {
            "first": first
        }
        
        # Build filter conditions
        filter_parts = []
        
        if team_id:
            filter_parts.append("team: { id: { eq: $teamId } }")
            variables["teamId"] = team_id
        
        # Construct filter clause
        filter_clause = ""
        if filter_parts:
            filter_string = ", ".join(filter_parts)
            filter_clause = f"(filter: {{ {filter_string} }}, first: $first)"
        else:
            filter_clause = "(first: $first)"
        
        # GraphQL query with pagination
        query = """
        query ProjectSearch(
            $first: Int!,
            $teamId: String
        ) {
            projects""" + filter_clause + """ {
                nodes {
                    id
                    name
                    description
                    state
                    progress
                    startDate
                    targetDate
                    team {
                        id
                        name
                        key
                    }
                    members {
                        nodes {
                            user {
                                id
                                name
                            }
                        }
                    }
                    leadId
                    createdAt
                    updatedAt
                }
                pageInfo {
                    hasNextPage
                    endCursor
                }
            }
        }
        """
        
        # Execute the query
        result = await self.execute_query(query, variables)
        
        # Process and return the projects
        projects_data = []
        has_next_page = False
        
        if "projects" in result:
            if "nodes" in result["projects"]:
                projects = result["projects"]["nodes"]
                
                for project in projects:
                    # Extract members
                    members = []
                    if project.get("members") and "nodes" in project["members"]:
                        for member in project["members"]["nodes"]:
                            if member.get("user") and member["user"].get("name"):
                                members.append(member["user"]["name"])
                    
                    # Extract team info
                    team_name = None
                    team_key = None
                    if project.get("team"):
                        team_name = project["team"].get("name")
                        team_key = project["team"].get("key")
                    
                    projects_data.append({
                        "id": project.get("id"),
                        "name": project.get("name"),
                        "description": project.get("description"),
                        "state": project.get("state"),
                        "progress": project.get("progress"),
                        "start_date": project.get("startDate"),
                        "target_date": project.get("targetDate"),
                        "team_name": team_name,
                        "team_key": team_key,
                        "members": members,
                        "lead_id": project.get("leadId"),
                        "created_date": project.get("createdAt"),
                        "updated_date": project.get("updatedAt")
                    })
            
            # Check for pagination info
            if "pageInfo" in result["projects"]:
                has_next_page = result["projects"]["pageInfo"].get("hasNextPage", False)
        
        return projects_data, has_next_page 