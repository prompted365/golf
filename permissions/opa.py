"""OPA-based permission engine for evaluating access requests."""

import json
import httpx
import uuid
from typing import List, Optional, Dict, Any

from .base import PermissionEngine
from .models import AccessRequest, AccessResult, RegoPolicy

class OPAPermissionEngine(PermissionEngine):
    """Implements the PermissionEngine interface using Open Policy Agent."""
    
    def __init__(self, opa_url: str = "http://localhost:8181"):
        """
        Initialize the OPA permission engine.
        
        Args:
            opa_url: URL of the OPA server
        """
        self.opa_url = opa_url.rstrip("/")  # Remove trailing slash if present
        self.http_client = httpx.AsyncClient()
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
        
        # Query OPA for the decision
        try:
            response = await self.http_client.post(
                f"{self.opa_url}/v1/data/authed/permissions/allow",
                json=input_data
            )
            response.raise_for_status()
            
            result = response.json()
            allowed = result.get("result", False)
            
            return AccessResult(
                allowed=allowed,
                reason="Policy evaluation successful" if allowed else "Access denied by policy"
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
        policy_id = str(uuid.uuid4())
        
        # Add policy to OPA
        try:
            response = await self.http_client.put(
                f"{self.opa_url}/v1/policies/{policy.package_name}",
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
        
        try:
            response = await self.http_client.delete(
                f"{self.opa_url}/v1/policies/{policy.package_name}"
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