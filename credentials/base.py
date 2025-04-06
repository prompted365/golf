from abc import ABC, abstractmethod
from typing import List, Optional

from ..identity.models import AgentIdentity
from .models import Credential, CredentialRequest, CredentialResult

class CredentialResolver(ABC):
    @abstractmethod
    async def resolve(self, identity: AgentIdentity, request: CredentialRequest) -> CredentialResult:
        """
        Resolve a credential for an agent to access a resource.

        Parameters:
            identity: The agent's identity
            request: The credential request with type, resource, and scopes

        Returns:
            CredentialResult: The credential resolution result

        Raises:
            CredentialError: If credential resolution fails
        """
        ...
    
    @abstractmethod
    async def list_credentials(self, identity: AgentIdentity, type: Optional[str] = None) -> List[Credential]:
        """
        List all credentials available to an agent, optionally filtered by type.

        Parameters:
            identity: The agent's identity
            type: Optional credential type to filter by

        Returns:
            List[Credential]: The available credentials

        Raises:
            CredentialError: If credential listing fails
        """
        ...
    
    @abstractmethod
    async def store_credential(self, credential: Credential) -> None:
        """
        Store a new credential or update an existing one.

        Parameters:
            credential: The credential to store

        Raises:
            CredentialError: If credential storage fails
        """
        ...
    
    @abstractmethod
    async def revoke_credential(self, credential_id: str) -> bool:
        """
        Revoke a credential by ID.

        Parameters:
            credential_id: ID of the credential to revoke

        Returns:
            bool: True if the credential was revoked, False if it didn't exist

        Raises:
            CredentialError: If credential revocation fails
        """
        ...
    
    async def has_access(self, identity: AgentIdentity, resource: str, required_scopes: List[str] = None) -> bool:
        """
        Check if an agent has access to a resource with the required scopes.

        Parameters:
            identity: The agent's identity
            resource: The resource to check access for
            required_scopes: Optional list of required scopes

        Returns:
            bool: True if the agent has access, False otherwise
        """
        try:
            # Default implementation - can be overridden by subclasses
            request = CredentialRequest(
                type="*",  # Any credential type
                resource=resource,
                scopes=required_scopes or []
            )
            
            result = await self.resolve(identity, request)
            return result.success and result.credential is not None
        except Exception:
            return False 