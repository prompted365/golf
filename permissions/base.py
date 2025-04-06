from abc import ABC, abstractmethod
from typing import List

from ..identity.models import AgentIdentity
from .models import AccessRequest, AccessResult, Role

class PermissionStore(ABC):
    @abstractmethod
    async def check_access(self, identity: AgentIdentity, request: AccessRequest) -> AccessResult:
        """
        Check if an agent has permission to perform an action on a resource.

        Parameters:
            identity: The agent's identity
            request: The access request with action, resource, and context

        Returns:
            AccessResult: The access checking result

        Raises:
            PermissionVerificationError: If permission checking fails
        """
        ...
    
    @abstractmethod
    async def get_roles(self, identity: AgentIdentity) -> List[Role]:
        """
        Get all roles for an agent.

        Parameters:
            identity: The agent's identity

        Returns:
            List[Role]: The roles associated with the agent

        Raises:
            PermissionVerificationError: If role retrieval fails
        """
        ...
    
    @abstractmethod
    async def has_role(self, identity: AgentIdentity, role_name: str) -> bool:
        """
        Check if an agent has a specific role.

        Parameters:
            identity: The agent's identity
            role_name: The name of the role to check

        Returns:
            bool: True if the agent has the role, False otherwise

        Raises:
            PermissionVerificationError: If role checking fails
        """
        ... 