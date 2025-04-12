"""Schema mapping for external APIs to internal access requests."""

from typing import Dict, Optional, Any

from .base import SchemaMapper
from .models import SchemaMapping, AccessRequest, Resource, ResourceType, AccessType

class SimpleSchemaMapper(SchemaMapper):
    """Simple implementation of the SchemaMapper interface."""
    
    def __init__(self):
        """Initialize the schema mapper."""
        self.mappings: Dict[str, Dict[str, SchemaMapping]] = {}
        self.mapping_ids: Dict[str, SchemaMapping] = {}
    
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
        for target_prop, source_prop in mapping.property_mappings.items():
            # Handle dot notation for nested properties
            if "." in source_prop:
                parts = source_prop.split(".")
                value = api_request
                for part in parts:
                    if isinstance(value, dict) and part in value:
                        value = value[part]
                    else:
                        value = None
                        break
                
                if value is not None:
                    resource_properties[target_prop] = value
            else:
                if source_prop in api_request:
                    resource_properties[target_prop] = api_request[source_prop]
        
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