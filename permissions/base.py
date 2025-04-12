"""Abstract base classes and interfaces for the permission system."""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
# Import DataType and StructuralHelper for proper type hinting in SchemaProviderInterface
from .models import (
    AccessRequest,
    AccessResult,
    PermissionStatement,
    RegoPolicy,
    SchemaMapping,
    ResourceType,
    Integration,
    DataType,
    StructuralHelper,
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
    
    @abstractmethod
    async def get_policy(self, policy_id: str) -> Optional[RegoPolicy]:
        """
        Get a policy by its ID.
        
        Args:
            policy_id: The ID of the policy to get
            
        Returns:
            Optional[RegoPolicy]: The policy if found, None otherwise
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
    
    @abstractmethod
    async def register_integration(self, integration: Integration) -> str:
        """
        Register a new integration with its resources and parameters.
        
        Args:
            integration: The integration to register
            
        Returns:
            str: The integration ID
        """
        ...
    
    @abstractmethod
    async def get_integration(self, integration_name: str) -> Optional[Integration]:
        """
        Get an integration by its name.
        
        Args:
            integration_name: The name of the integration
            
        Returns:
            Optional[Integration]: The integration if found, None otherwise
        """
        ...
    
    @abstractmethod
    async def list_integrations(self) -> List[Integration]:
        """
        List all registered integrations.
        
        Returns:
            List[Integration]: All registered integrations
        """
        ...

class TokenizerInterface(ABC):
    """Interface for tokenizing permission statements."""
    
    @abstractmethod
    def tokenize(self, statement_text: str) -> List[str]:
        """
        Tokenize a permission statement text.
        
        Args:
            statement_text: The text to tokenize
            
        Returns:
            List[str]: The tokens
        """
        ...

class InterpreterInterface(ABC):
    """Interface for interpreting tokenized statements."""
    
    @abstractmethod
    def interpret(self, tokens: List[str]) -> Dict[str, Any]:
        """
        Interpret tokenized permission statement.
        
        Args:
            tokens: The tokens to interpret
            
        Returns:
            Dict[str, Any]: Structured representation of the statement
        """
        ...

class StatementBuilderInterface(ABC):
    """Interface for building structured permission statements."""
    
    @abstractmethod
    def build(self, interpreted_data: Dict[str, Any]) -> PermissionStatement:
        """
        Build a structured permission statement from interpreted data.
        
        Args:
            interpreted_data: The interpreted data from the Interpreter
            
        Returns:
            PermissionStatement: The built permission statement
        """
        ...

class PermissionParser(ABC):
    """Combines tokenization, interpretation, and statement building."""
    
    @abstractmethod
    async def parse_statement(self, statement_text: str) -> PermissionStatement:
        """
        Parse a permission statement from text.
        
        Args:
            statement_text: The text to parse
            
        Returns:
            PermissionStatement: The parsed permission statement
        """
        ...

class PolicyGenerator(ABC):
    """Interface for generating Rego policies from permission statements."""
    
    @abstractmethod
    async def generate_policy(self, statement: PermissionStatement) -> RegoPolicy:
        """
        Generate a Rego policy from a permission statement.
        
        Args:
            statement: The permission statement
            
        Returns:
            RegoPolicy: The generated Rego policy
        """
        ...
    
    @abstractmethod
    async def get_template(self, template_name: str) -> str:
        """
        Get a Rego template by name.
        
        Args:
            template_name: The name of the template
            
        Returns:
            str: The template content
        """
        ...
    
    @abstractmethod
    async def register_template(self, template_name: str, template_content: str) -> None:
        """
        Register a new Rego template.
        
        Args:
            template_name: The name of the template
            template_content: The content of the template
        """
        ...

class SchemaProviderInterface(ABC):
    """Interface for providing schema information about resources, fields, and types."""
    
    @abstractmethod
    def map_field(self, helper: StructuralHelper, field_token: str, resource_type: ResourceType) -> Optional[str]:
        """
        Map a field token to an internal permission field based on the structural helper and resource type.
        
        Args:
            helper: The structural helper used in the permission statement
            field_token: The field token from the statement
            resource_type: The resource type being accessed
            
        Returns:
            Optional[str]: The mapped internal field name, or None if no mapping exists
        """
        ...
    
    @abstractmethod
    def get_field_type(self, field: str, resource_type: ResourceType) -> Optional[DataType]:
        """
        Get the data type of a field for a specific resource.
        
        Args:
            field: The field name
            resource_type: The resource type
            
        Returns:
            Optional[DataType]: The data type of the field, or None if unknown
        """
        ...
    
    @abstractmethod
    def get_resource_metadata(self, resource_type: ResourceType) -> Dict[str, Any]:
        """
        Get metadata about a resource type from the integration schema.
        
        Args:
            resource_type: The resource type
            
        Returns:
            Dict[str, Any]: Metadata about the resource type
        """
        ... 