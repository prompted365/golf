"""OPA client for interacting with the Open Policy Agent."""

import uuid
import logging
import httpx
from typing import Dict, List, Optional, Any, Tuple

from ..base import PermissionEngine
from ..models import AccessRequest, AccessResult, RegoPolicy

# Set up logging
logger = logging.getLogger(__name__)

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
    
    async def __aenter__(self) -> "OPAClient":
        """Async context manager entry."""
        return self
    
    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Async context manager exit."""
        await self.close()
    
    async def close(self) -> None:
        """Close the HTTP client and release resources."""
        await self.http_client.aclose()
    
    async def check_access(self, request: AccessRequest) -> AccessResult:
        """
        Check if a requested access is allowed based on OPA policies.
        
        The effect field in AccessRequest ("ALLOW"/"DENY") corresponds to
        BaseCommand.GIVE/BaseCommand.DENY from permission statements.
        
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
                    "properties": request.resource.properties
                },
                "context": request.context
            }
        }
        
        # Determine query path based on resource type and effect
        resource_type = request.resource.type.value.lower()
        # Effect values "ALLOW"/"DENY" correspond to BaseCommand.GIVE/BaseCommand.DENY
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
            error_msg = f"HTTP error {e.response.status_code} querying OPA: {str(e)}"
            logger.error(error_msg)
            return AccessResult(
                allowed=False,
                reason=error_msg
            )
        except httpx.RequestError as e:
            error_msg = f"Request error querying OPA: {str(e)}"
            logger.error(error_msg)
            return AccessResult(
                allowed=False,
                reason=error_msg
            )
    
    async def add_policy(self, policy: RegoPolicy) -> str:
        """
        Add a new Rego policy to OPA.
        
        Args:
            policy: The Rego policy to add
            
        Returns:
            str: The policy ID
            
        Raises:
            RuntimeError: If the policy could not be added to OPA
        """
        # Generate a policy ID if not present
        policy_id = policy.metadata.get("id")
        if not policy_id:
            policy_id = str(uuid.uuid4())
            policy.metadata["id"] = policy_id
        
        # Use a simpler policy path name derived from the package
        # OPA expects a policy name that is different from the package path
        simple_policy_path = policy.package_name.split(".")[-1]  # Use last segment
        
        # Log policy details for debugging
        logger.debug(f"Adding policy to OPA. Package: {policy.package_name}, Path: {simple_policy_path}")
        logger.debug(f"Policy content:\n{policy.policy_content}")
        
        # Add policy to OPA
        try:
            # Construct full URL for debugging
            opa_policy_url = f"{self.opa_url}/v1/policies/{simple_policy_path}"
            logger.debug(f"Sending policy to OPA URL: {opa_policy_url}")
            
            response = await self.http_client.put(
                opa_policy_url,
                content=policy.policy_content,
                headers={"Content-Type": "text/plain"}
            )
            
            # Log response details for debugging
            logger.debug(f"OPA response status: {response.status_code}")
            logger.debug(f"OPA response body: {response.text}")
            
            response.raise_for_status()
            
            # Store policy locally
            self.policies[policy_id] = policy
            
            return policy_id
        except httpx.HTTPStatusError as e:
            error_msg = f"HTTP error {e.response.status_code} adding policy to OPA: {str(e)}"
            # Log detailed response for debugging
            logger.error(error_msg)
            logger.error(f"Response body: {e.response.text}")
            raise RuntimeError(error_msg)
        except httpx.RequestError as e:
            error_msg = f"Request error adding policy to OPA: {str(e)}"
            logger.error(error_msg)
            raise RuntimeError(error_msg)
    
    async def remove_policy(self, policy_id: str) -> bool:
        """
        Remove a policy from OPA.
        
        Args:
            policy_id: The ID of the policy to remove
            
        Returns:
            bool: True if successfully removed, False otherwise
        """
        if policy_id not in self.policies:
            logger.warning(f"Attempted to remove non-existent policy: {policy_id}")
            return False
        
        policy = self.policies[policy_id]
        
        # Use a simpler policy path name, consistent with add_policy
        simple_policy_path = policy.package_name.split(".")[-1]
        
        try:
            response = await self.http_client.delete(
                f"{self.opa_url}/v1/policies/{simple_policy_path}"
            )
            response.raise_for_status()
            
            # Remove from local storage
            del self.policies[policy_id]
            
            return True
        except httpx.HTTPStatusError as e:
            error_msg = f"HTTP error {e.response.status_code} removing policy from OPA: {str(e)}"
            logger.error(error_msg)
            return False
        except httpx.RequestError as e:
            error_msg = f"Request error removing policy from OPA: {str(e)}"
            logger.error(error_msg)
            return False
    
    async def list_policies(self) -> List[RegoPolicy]:
        """
        List all policies in OPA.
        
        Returns:
            List[RegoPolicy]: All policies
            
        Note:
            This method attempts to fetch the current policies from OPA.
            If the fetch fails, it returns the locally cached policies
            but logs a warning about potential state inconsistency.
        """
        try:
            # Try to get a list of policies from OPA
            response = await self.http_client.get(f"{self.opa_url}/v1/policies")
            response.raise_for_status()
            
            # If successful, sync the local cache with OPA's state
            # This would require parsing the OPA response format
            # and creating RegoPolicy objects from it
            
            # For now, just log that we're returning cached policies
            # In a real implementation, you would parse the response and update self.policies
            logger.info("Successfully retrieved policies from OPA.")
            
            # If there are differences between OPA and local state, log them
            # This would be part of the sync logic
            
            return list(self.policies.values())
        except Exception as e:
            logger.warning(f"Failed to fetch policies from OPA, returning cached policies: {str(e)}")
            return list(self.policies.values())
    
    async def get_policy(self, policy_id: str) -> Optional[RegoPolicy]:
        """
        Get a policy by its ID.
        
        Args:
            policy_id: The ID of the policy to get
            
        Returns:
            Optional[RegoPolicy]: The policy if found, None otherwise
        """
        # First check the local cache
        if policy_id in self.policies:
            return self.policies.get(policy_id)
        
        # If not in local cache, we could try to fetch from OPA
        # but we'd need to know how the policy is stored in OPA
        # For now, just return None
        logger.info(f"Policy {policy_id} not found in local cache")
        return None
    
    async def check_health(self) -> Tuple[bool, Optional[str]]:
        """
        Check if OPA is healthy.
        
        Returns:
            Tuple[bool, Optional[str]]: (is_healthy, error_message)
            The first element is True if OPA is healthy, False otherwise.
            The second element contains an error message if not healthy, None otherwise.
        """
        try:
            response = await self.http_client.get(f"{self.opa_url}/health")
            if response.status_code == 200:
                return True, None
            else:
                error_msg = f"OPA health check failed with status code: {response.status_code}"
                logger.warning(error_msg)
                return False, error_msg
        except httpx.HTTPStatusError as e:
            error_msg = f"HTTP error during OPA health check: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
        except httpx.RequestError as e:
            error_msg = f"Request error during OPA health check: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
        except Exception as e:
            error_msg = f"Unexpected error during OPA health check: {str(e)}"
            logger.error(error_msg)
            return False, error_msg 