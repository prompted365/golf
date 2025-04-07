from abc import ABC, abstractmethod
from typing import List, Optional

from identity.models import AgentIdentity
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
            PermissionValidation: If permission checking fails
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
            PermissionValidation: If role retrieval fails
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
            PermissionValidation: If role checking fails
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
            PermissionValidation: If rule listing fails
        """
        ...
    
    @abstractmethod
    async def add_role(self, role: Role) -> bool:
        """
        Add or update a role.

        Parameters:
            role: The role to add or update

        Returns:
            bool: True if the role was added/updated, False if it failed

        Raises:
            PermissionValidation: If role addition fails
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
            PermissionValidation: If role removal fails
        """
        ...

    async def check_permission(self, identity: AgentIdentity, resource: str, action: str) -> bool:
        """
        Check if an identity has permission to perform an action on a resource.
        
        Args:
            identity: The identity to check
            resource: The resource to check access for
            action: The action to check permission for
            
        Returns:
            bool: True if the identity has permission, False otherwise
            
        Raises:
            PermissionValidation: If permission checking fails
        """
        raise NotImplementedError()

    async def get_role(self, role_name: str) -> Role:
        """
        Get a role by name.
        
        Args:
            role_name: Name of the role to get
            
        Returns:
            Role: The role object
            
        Raises:
            PermissionValidation: If role retrieval fails
        """
        raise NotImplementedError()

    async def list_rules(self) -> List[PermissionRule]:
        """
        List all rules in the system.
        
        Returns:
            List[Rule]: List of all rules
            
        Raises:
            PermissionValidation: If rule listing fails
        """
        raise NotImplementedError()

    async def add_role(self, role: Role) -> None:
        """
        Add a new role to the system.
        
        Args:
            role: The role to add
            
        Raises:
            PermissionValidation: If role addition fails
        """
        raise NotImplementedError()

    async def remove_role(self, role_name: str) -> None:
        """
        Remove a role from the system.
        
        Args:
            role_name: Name of the role to remove
            
        Raises:
            PermissionValidation: If role removal fails
        """
        raise NotImplementedError() 