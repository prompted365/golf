"""OPA client for interacting with the Open Policy Agent."""

import json
import uuid
import httpx
from typing import Dict, Any, List, Optional

from ..base import PermissionEngine
from ..models import AccessRequest, AccessResult, RegoPolicy

class OPAClient(PermissionEngine):
    """Client for interacting with the Open Policy Agent."""
    
    def __init__(self, opa_url: str = "http://localhost:8181"):
        """
        Initialize the OPA client.
        
        Args:
            opa_url: URL of the OPA server
        """
        self.opa_url = opa_url.rstrip("/")  # Remove trailing slash if present
        self.http_client = httpx.AsyncClient(timeout=10.0)
        self.policies: Dict[str, RegoPolicy] = {}
    
    async def check_access(self, request: AccessRequest) -> AccessResult:
        """
        Check if a requested access is allowed based on OPA policies.
        
        Args:
            request: The access request to check
            
        Returns:
            AccessResult: Result indicating whether access is allowed
        """
        # Convert request to OPA input format
        input_data = {
            "input": {
                "action": request.action,
                "resource": {
                    "type": request.resource.type,
                    **request.resource.properties
                },
                "context": request.context
            }
        }
        
        # Determine query path based on resource type and effect
        resource_type = request.resource.type.value.lower()
        effect = request.effect.lower() if request.effect else "allow"
        
        query_path = f"/v1/data/authed/permissions/{resource_type}/{effect}"
        
        # Query OPA for the decision
        try:
            response = await self.http_client.post(
                f"{self.opa_url}{query_path}",
                json=input_data
            )
            response.raise_for_status()
            
            result = response.json()
            
            # Check if the decision exists and is true
            decision = result.get("result", False)
            
            # If effect is "DENY" and decision is true, access is denied
            # If effect is "ALLOW" and decision is true, access is allowed
            allowed = (effect == "allow" and decision) or (effect == "deny" and not decision)
            
            return AccessResult(
                allowed=allowed,
                reason=f"Policy evaluation: {effect}={decision}"
            )
        except httpx.HTTPStatusError as e:
            return AccessResult(
                allowed=False,
                reason=f"Error querying OPA: {str(e)}"
            )
    
    async def add_policy(self, policy: RegoPolicy) -> str:
        """
        Add a new Rego policy to OPA.
        
        Args:
            policy: The Rego policy to add
            
        Returns:
            str: The policy ID
        """
        # Generate a policy ID if not present
        policy_id = policy.metadata.get("id")
        if not policy_id:
            policy_id = str(uuid.uuid4())
            policy.metadata["id"] = policy_id
        
        # Extract package name for the API path
        package_parts = policy.package_name.split(".")
        policy_path = "/".join(package_parts)
        
        # Add policy to OPA
        try:
            response = await self.http_client.put(
                f"{self.opa_url}/v1/policies/{policy_path}",
                content=policy.policy_content
            )
            response.raise_for_status()
            
            # Store policy locally
            self.policies[policy_id] = policy
            
            return policy_id
        except httpx.HTTPStatusError as e:
            raise RuntimeError(f"Error adding policy to OPA: {str(e)}")
    
    async def remove_policy(self, policy_id: str) -> bool:
        """
        Remove a policy from OPA.
        
        Args:
            policy_id: The ID of the policy to remove
            
        Returns:
            bool: True if successfully removed, False otherwise
        """
        if policy_id not in self.policies:
            return False
        
        policy = self.policies[policy_id]
        
        # Extract package name for the API path
        package_parts = policy.package_name.split(".")
        policy_path = "/".join(package_parts)
        
        try:
            response = await self.http_client.delete(
                f"{self.opa_url}/v1/policies/{policy_path}"
            )
            response.raise_for_status()
            
            # Remove from local storage
            del self.policies[policy_id]
            
            return True
        except httpx.HTTPStatusError:
            return False
    
    async def list_policies(self) -> List[RegoPolicy]:
        """
        List all policies in OPA.
        
        Returns:
            List[RegoPolicy]: All policies
        """
        return list(self.policies.values())
    
    async def get_policy(self, policy_id: str) -> Optional[RegoPolicy]:
        """
        Get a policy by its ID.
        
        Args:
            policy_id: The ID of the policy to get
            
        Returns:
            Optional[RegoPolicy]: The policy if found, None otherwise
        """
        return self.policies.get(policy_id)
    
    async def check_health(self) -> bool:
        """
        Check if OPA is healthy.
        
        Returns:
            bool: True if OPA is healthy, False otherwise
        """
        try:
            response = await self.http_client.get(f"{self.opa_url}/health")
            return response.status_code == 200
        except Exception:
            return False 