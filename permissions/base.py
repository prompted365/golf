from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any

from .models import (
    AccessRequest, 
    AccessResult, 
    PermissionStatement, 
    RegoPolicy, 
    SchemaMapping,
    ResourceType
)

class PermissionStore(ABC):
    @abstractmethod
    async def check_access(self, request: AccessRequest) -> AccessResult:
        """
        Check if an agent has permission to perform an action on a resource.

        Parameters:
            request: The access request with action, resource, and context

        Returns:
            AccessResult: The access checking result
        """
        ...
    
    @abstractmethod
    async def has_permission(self, request: AccessRequest) -> bool:
        """
        Check if a request has permission.

        Parameters:
            request: The access request to check

        Returns:
            bool: True if the request is allowed, False otherwise
        """
        ...

class PermissionEngine(ABC):
    """Base interface for permission engines that evaluate access requests."""
    
    @abstractmethod
    async def check_access(self, request: AccessRequest) -> AccessResult:
        """
        Check if a requested access is allowed based on the defined policies.
        
        Args:
            request: The access request to check
            
        Returns:
            AccessResult: Result indicating whether access is allowed
        """
        ...
    
    @abstractmethod
    async def add_policy(self, policy: RegoPolicy) -> str:
        """
        Add a new Rego policy to the policy store.
        
        Args:
            policy: The Rego policy to add
            
        Returns:
            str: The policy ID
        """
        ...
    
    @abstractmethod
    async def remove_policy(self, policy_id: str) -> bool:
        """
        Remove a policy from the policy store.
        
        Args:
            policy_id: The ID of the policy to remove
            
        Returns:
            bool: True if successfully removed, False otherwise
        """
        ...
    
    @abstractmethod
    async def list_policies(self) -> List[RegoPolicy]:
        """
        List all policies in the policy store.
        
        Returns:
            List[RegoPolicy]: All policies in the store
        """
        ...

class PermissionTranslator(ABC):
    """Translates user-friendly permission statements into Rego policies."""
    
    @abstractmethod
    async def translate(self, statement: PermissionStatement) -> RegoPolicy:
        """
        Translate a permission statement into a Rego policy.
        
        Args:
            statement: The permission statement to translate
            
        Returns:
            RegoPolicy: The translated Rego policy
        """
        ...
    
    @abstractmethod
    async def parse_statement(self, statement_text: str) -> PermissionStatement:
        """
        Parse a text-based permission statement into a structured PermissionStatement.
        
        Args:
            statement_text: The text of the permission statement (e.g., "GIVE READ ACCESS TO EMAILS WITH TAGS = WORK")
            
        Returns:
            PermissionStatement: The parsed statement
        """
        ...

class SchemaMapper(ABC):
    """Maps external API schemas to internal resource types."""
    
    @abstractmethod
    async def add_mapping(self, mapping: SchemaMapping) -> str:
        """
        Add a new schema mapping.
        
        Args:
            mapping: The schema mapping to add
            
        Returns:
            str: The mapping ID
        """
        ...
    
    @abstractmethod
    async def get_mapping(self, source_api: str, resource_type: ResourceType) -> Optional[SchemaMapping]:
        """
        Get a schema mapping for a specific API and resource type.
        
        Args:
            source_api: The source API name
            resource_type: The resource type
            
        Returns:
            Optional[SchemaMapping]: The schema mapping if found, None otherwise
        """
        ...
    
    @abstractmethod
    async def transform_request(self, source_api: str, api_request: Dict[str, Any]) -> AccessRequest:
        """
        Transform an external API request into a standardized AccessRequest.
        
        Args:
            source_api: The source API name
            api_request: The API request parameters
            
        Returns:
            AccessRequest: The transformed request
        """
        ... 