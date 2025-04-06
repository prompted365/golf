import time
from typing import Any, Dict, Optional
import httpx
from dataclasses import dataclass
from pydantic import BaseModel

from .base import IdentityResolver
from .models import AgentIdentity
from ..core.exceptions import IdentityError

@dataclass
class AuthedConfig:
    """Configuration for the Authed identity resolver."""
    registry_url: str = "https://api.getauthed.dev"
    verify_signatures: bool = True
    max_signature_age_seconds: int = 300

class AgentSignatureData(BaseModel):
    """Data extracted from an agent's signature."""
    agent_id: str
    key_id: str
    signature: str
    timestamp: int
    target: Optional[str] = None
    payload: Optional[Dict[str, Any]] = None

class AuthedIdentityResolver(IdentityResolver):
    """Identity resolver that integrates with Authed 1.0."""
    
    def __init__(self, config: Optional[AuthedConfig] = None):
        self.config = config or AuthedConfig()
    
    async def resolve(self, source: Any) -> AgentIdentity:
        """
        Resolve and verify an identity from a request or message.
        
        Parameters:
            source (Any): A request object that contains Authed signature headers
                
        Returns:
            AgentIdentity: A verified, normalized identity object
            
        Raises:
            IdentityError: If verification fails
        """
        try:
            # Extract signature data from request
            signature_data = await self._extract_signature(source)
            
            # Verify timestamp if enabled
            if self.config.verify_signatures:
                self._verify_timestamp(signature_data.timestamp)
            
            # Fetch agent identity from Authed registry
            agent = await self._fetch_agent(signature_data.agent_id)
            
            # Verify signature if enabled
            if self.config.verify_signatures:
                await self._verify_signature(signature_data, agent.get("public_key"))
            
            # Create identity object
            identity = AgentIdentity(
                id=signature_data.agent_id,
                public_key=agent.get("public_key"),
                source="authed",
                claims={"roles": agent.get("roles", [])},
                metadata={
                    "provider": agent.get("provider"),
                    "timestamp": signature_data.timestamp,
                    "key_id": signature_data.key_id,
                    "target": signature_data.target
                }
            )
            
            return identity
        except IdentityError:
            raise
        except Exception as e:
            raise IdentityError(f"Failed to resolve Authed identity: {str(e)}")
    
    async def _extract_signature(self, source: Any) -> AgentSignatureData:
        """Extract signature data from request headers."""
        try:
            # This implementation assumes HTTP requests with specific headers
            # Adjust based on your actual request structure
            headers = getattr(source, "headers", {})
            
            agent_id = headers.get("x-authed-agent-id")
            if not agent_id:
                raise IdentityError("Missing agent ID", "missing_agent_id")
            
            signature = headers.get("x-authed-signature")
            if not signature:
                raise IdentityError("Missing signature", "missing_signature")
            
            key_id = headers.get("x-authed-key-id")
            if not key_id:
                raise IdentityError("Missing key ID", "missing_key_id")
            
            timestamp_str = headers.get("x-authed-timestamp")
            if not timestamp_str:
                raise IdentityError("Missing timestamp", "missing_timestamp")
            
            try:
                timestamp = int(timestamp_str)
            except ValueError:
                raise IdentityError("Invalid timestamp format", "invalid_timestamp")
            
            target = headers.get("x-authed-target")
            
            return AgentSignatureData(
                agent_id=agent_id,
                key_id=key_id,
                signature=signature,
                timestamp=timestamp,
                target=target
            )
        except IdentityError:
            raise
        except Exception as e:
            raise IdentityError(f"Failed to extract signature data: {str(e)}")
    
    def _verify_timestamp(self, timestamp: int) -> None:
        """Verify that the signature timestamp is valid."""
        current_time = int(time.time())
        max_age = self.config.max_signature_age_seconds
        
        if timestamp < (current_time - max_age):
            raise IdentityError(
                f"Signature timestamp is too old (max age: {max_age}s)",
                "signature_expired"
            )
        
        if timestamp > (current_time + 60):  # Allow 1 minute for clock skew
            raise IdentityError(
                "Signature timestamp is in the future",
                "future_timestamp"
            )
    
    async def _fetch_agent(self, agent_id: str) -> Dict[str, Any]:
        """Fetch agent details from Authed registry."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.config.registry_url}/agents/{agent_id}"
                )
                
                if response.status_code == 404:
                    raise IdentityError(
                        f"Agent not found: {agent_id}",
                        "agent_not_found"
                    )
                
                if response.status_code != 200:
                    raise IdentityError(
                        f"Failed to fetch agent data: {response.text}",
                        "registry_error"
                    )
                
                return response.json()
        except httpx.RequestError as e:
            raise IdentityError(
                f"Registry connection error: {str(e)}",
                "registry_connection_error"
            )
    
    async def _verify_signature(self, data: AgentSignatureData, public_key: str) -> None:
        """Verify the signature using the agent's public key."""
        # For now, this is a placeholder for the actual signature verification
        # In a real implementation, you would:
        # 1. Construct the message that was signed (typically a string with timestamp, etc.)
        # 2. Verify the signature against this message using the public key
        
        # Example implementation:
        # message = f"{data.agent_id}:{data.timestamp}"
        # if data.target:
        #     message += f":{data.target}"
        # 
        # result = verify_signature(message, data.signature, public_key)
        # if not result:
        #     raise IdentityError("Invalid signature", "invalid_signature")
        
        # This is where you'd integrate with Authed 1.0 verification
        # For now, we'll just log a warning
        print("WARNING: Signature verification not implemented") 