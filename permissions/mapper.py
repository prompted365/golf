"""Schema mapping for external APIs to internal access requests."""

from typing import Dict, Optional, Any, List

from .base import SchemaMapper
from .models import (
    SchemaMapping, 
    AccessRequest, 
    Resource, 
    ResourceType, 
    AccessType,
    Integration,
    FieldPath
)

class SimpleSchemaMapper(SchemaMapper):
    """Simple implementation of the SchemaMapper interface."""
    
    def __init__(self):
        """Initialize the schema mapper."""
        self.mappings: Dict[str, Dict[str, SchemaMapping]] = {}
        self.mapping_ids: Dict[str, SchemaMapping] = {}
        self.integrations: Dict[str, Integration] = {}
    
    async def add_mapping(self, mapping: SchemaMapping) -> str:
        """
        Add a new schema mapping.
        
        Args:
            mapping: The schema mapping to add
            
        Returns:
            str: The mapping ID
        """
        # Generate a simple ID
        mapping_id = f"{mapping.source_api}_{mapping.resource_type.value.lower()}"
        
        # Store by source API and resource type
        if mapping.source_api not in self.mappings:
            self.mappings[mapping.source_api] = {}
        
        self.mappings[mapping.source_api][mapping.resource_type.value] = mapping
        self.mapping_ids[mapping_id] = mapping
        
        return mapping_id
    
    async def get_mapping(self, source_api: str, resource_type: ResourceType) -> Optional[SchemaMapping]:
        """
        Get a schema mapping for a specific API and resource type.
        
        Args:
            source_api: The source API name
            resource_type: The resource type
            
        Returns:
            Optional[SchemaMapping]: The schema mapping if found, None otherwise
        """
        if source_api in self.mappings and resource_type.value in self.mappings[source_api]:
            return self.mappings[source_api][resource_type.value]
        
        return None
    
    async def transform_request(self, source_api: str, api_request: Dict[str, Any]) -> AccessRequest:
        """
        Transform an external API request into a standardized AccessRequest.
        
        Args:
            source_api: The source API name
            api_request: The API request parameters
            
        Returns:
            AccessRequest: The transformed request
        """
        # Extract resource type from request
        if "resource_type" not in api_request:
            raise ValueError("API request must include 'resource_type'")
        
        resource_type_str = api_request["resource_type"].upper()
        try:
            resource_type = ResourceType(resource_type_str)
        except ValueError:
            raise ValueError(f"Unknown resource type: {resource_type_str}")
        
        # Get the mapping
        mapping = await self.get_mapping(source_api, resource_type)
        if not mapping:
            raise ValueError(f"No mapping found for {source_api} and {resource_type_str}")
        
        # Extract action
        if "action" not in api_request:
            raise ValueError("API request must include 'action'")
        
        action_str = api_request["action"].upper()
        try:
            action = AccessType(action_str)
        except ValueError:
            raise ValueError(f"Unknown action: {action_str}")
        
        # Map properties according to the mapping
        resource_properties = {}
        for target_prop, source_field_path in mapping.property_mappings.items():
            # Get value using the field path
            value = self._get_value_by_path(api_request, source_field_path)
            if value is not None:
                resource_properties[target_prop] = value
        
        # Apply transformations if any
        if mapping.transformation_rules:
            for prop, transform_rule in mapping.transformation_rules.items():
                if prop in resource_properties:
                    # Simple transformation rules, can be extended
                    if transform_rule == "to_upper":
                        resource_properties[prop] = resource_properties[prop].upper()
                    elif transform_rule == "to_lower":
                        resource_properties[prop] = resource_properties[prop].lower()
                    elif transform_rule == "to_list" and isinstance(resource_properties[prop], str):
                        resource_properties[prop] = [item.strip() for item in resource_properties[prop].split(",")]
                    elif transform_rule.startswith("format:"):
                        # Format using placeholders, e.g., "format:{name} ({email})"
                        format_str = transform_rule[len("format:"):]
                        try:
                            # Use the resource properties to format the string
                            resource_properties[prop] = format_str.format(**resource_properties)
                        except KeyError:
                            # If a placeholder is missing, keep the original value
                            pass
        
        # Create the standardized request
        return AccessRequest(
            action=action,
            resource=Resource(
                type=resource_type,
                properties=resource_properties
            ),
            context={
                "source_api": source_api,
                "original_request": api_request
            }
        )
    
    def _get_value_by_path(self, data: Dict[str, Any], field_path: FieldPath) -> Optional[Any]:
        """
        Get a value from a nested dictionary using a dot-notated path.
        
        Args:
            data: The dictionary to search
            field_path: The path to the field (e.g., "email.sender.domain")
            
        Returns:
            Optional[Any]: The value if found, None otherwise
        """
        if not field_path:
            return None
        
        # Handle JSONPath-like array access with [n] notation
        parts = []
        current_part = ""
        in_brackets = False
        
        for char in field_path:
            if char == '[':
                if current_part:
                    parts.append(current_part)
                    current_part = ""
                in_brackets = True
            elif char == ']':
                if in_brackets:
                    # Add the index as a separate part
                    try:
                        parts.append(int(current_part))
                    except ValueError:
                        # If not an integer, treat as a string key
                        parts.append(current_part)
                    current_part = ""
                    in_brackets = False
            elif char == '.' and not in_brackets:
                if current_part:
                    parts.append(current_part)
                    current_part = ""
            else:
                current_part += char
        
        # Add the last part if any
        if current_part:
            parts.append(current_part)
        
        # Traverse the data structure
        current = data
        for part in parts:
            if isinstance(current, dict):
                current = current.get(part)
            elif isinstance(current, list) and isinstance(part, int) and 0 <= part < len(current):
                current = current[part]
            else:
                return None
            
            if current is None:
                return None
        
        return current
    
    async def register_integration(self, integration: Integration) -> str:
        """
        Register a new integration with its resources and parameters.
        
        Args:
            integration: The integration to register
            
        Returns:
            str: The integration ID
        """
        # Store the integration
        self.integrations[integration.name] = integration
        return integration.name
    
    async def get_integration(self, integration_name: str) -> Optional[Integration]:
        """
        Get an integration by its name.
        
        Args:
            integration_name: The name of the integration
            
        Returns:
            Optional[Integration]: The integration if found, None otherwise
        """
        return self.integrations.get(integration_name)
    
    async def list_integrations(self) -> List[Integration]:
        """
        List all registered integrations.
        
        Returns:
            List[Integration]: All registered integrations
        """
        return list(self.integrations.values()) 