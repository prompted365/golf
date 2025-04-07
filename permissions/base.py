from abc import ABC, abstractmethod
from typing import List, Optional

from ..identity.models import AgentIdentity
from .models import AccessRequest, AccessResult, Role, PermissionRule

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
            PermissionValidationError: If permission checking fails
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
            PermissionValidationError: If role retrieval fails
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
            PermissionValidationError: If role checking fails
        """
        ...
    
    @abstractmethod
    async def list_rules(self, role_name: Optional[str] = None) -> List[PermissionRule]:
        """
        List all permission rules, optionally filtered by role.

        Parameters:
            role_name: Optional role name to filter by

        Returns:
            List[PermissionRule]: The permission rules

        Raises:
            PermissionValidationError: If rule listing fails
        """
        ...
    
    @abstractmethod
    async def add_role(self, role: Role) -> None:
        """
        Add or update a role.

        Parameters:
            role: The role to add or update

        Raises:
            PermissionValidationError: If role addition fails
        """
        ...
    
    @abstractmethod
    async def remove_role(self, role_name: str) -> bool:
        """
        Remove a role.

        Parameters:
            role_name: The name of the role to remove

        Returns:
            bool: True if the role was removed, False if it didn't exist

        Raises:
            PermissionValidationError: If role removal fails
        """
        ... 