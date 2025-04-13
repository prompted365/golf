"""Interpreter component for permission statements."""

from typing import List, Dict, Any, Optional, TypedDict

from ..base import BaseInterpreter, BaseSchemaProvider
from ..models import (
    BaseCommand,
    AccessType,
    ResourceType,
    ConditionOperator,
    StructuralHelper,
    LogicalOperator,
    DataType
)

class ConditionDict(TypedDict):
    """Type definition for a condition dictionary."""
    field: str
    operator: ConditionOperator
    value: Any
    field_type: DataType
    logical_operator: LogicalOperator

class InterpretedStatement(TypedDict, total=False):
    """Type definition for the interpreted statement returned by the interpreter."""
    command: BaseCommand
    access_types: List[AccessType]
    resource_type: ResourceType
    conditions: List[ConditionDict]
    integration_data: Dict[str, Any]

class SchemaProvider(BaseSchemaProvider):
    """
    Implementation of BaseSchemaProvider that uses integration mappings.
    
    This implementation loads all field mappings and type information from
    integration definitions.
    """
    
    def __init__(self, integration_mappings: Optional[Dict[str, Dict[str, Any]]] = None):
        """
        Initialize the schema provider with integration mappings.
        
        Args:
            integration_mappings: Dictionary mapping integration names to their resource definitions.
                                 If None, an empty mapping is used.
        """
        # Initialize with provided mappings or empty dict
        self.integration_mappings = integration_mappings or {}
        
        # Load helper mappings from integrations
        self.helper_mappings = self._load_helper_mappings()
        
        # Load type interpretation rules
        self.type_interpretation = self._load_type_interpretation()
        
    def _load_helper_mappings(self) -> Dict[StructuralHelper, Dict[str, Any]]:
        """
        Load structural helper mappings from integration definitions.
        
        Returns:
            Dict[StructuralHelper, Dict[str, Any]]: Dictionary mapping helpers to their field mappings
        """
        helper_mappings = {}
        
        # Iterate through all integrations
        for integration_name, integration_data in self.integration_mappings.items():
            # Check if the integration has helper mappings
            if "_helper_mappings" in integration_data:
                helper_data = integration_data["_helper_mappings"]
                
                # Each helper can map to a different field name
                for helper_str, field_name in helper_data.items():
                    try:
                        helper = StructuralHelper(helper_str)
                        if helper not in helper_mappings:
                            helper_mappings[helper] = {}
                        helper_mappings[helper][integration_name] = field_name
                    except ValueError:
                        # Skip invalid helper enum values
                        pass
                        
        return helper_mappings
        
    def _load_type_interpretation(self) -> Dict[DataType, Dict[str, Any]]:
        """
        Load type interpretation rules from integration definitions.
        
        Returns:
            Dict[DataType, Dict[str, Any]]: Dictionary mapping data types to their interpretation rules
        """
        type_interpretation = {}
        
        # Iterate through all integrations
        for integration_name, integration_data in self.integration_mappings.items():
            # Check if the integration has type interpretation rules
            if "_type_interpretation" in integration_data:
                type_rules = integration_data["_type_interpretation"]
                
                # Process each type's rules
                for type_str, rules in type_rules.items():
                    try:
                        data_type = DataType(type_str)
                        if data_type not in type_interpretation:
                            type_interpretation[data_type] = {}
                        
                        # Merge in the rules from this integration
                        # In case of conflict, last one wins
                        type_interpretation[data_type].update(rules)
                    except ValueError:
                        # Skip invalid data type values
                        pass
                        
        return type_interpretation
    
    def get_type_rules(self, data_type: DataType) -> Dict[str, Any]:
        """
        Get the interpretation rules for a given data type.
        
        Args:
            data_type: The data type to get rules for
            
        Returns:
            Dict[str, Any]: The interpretation rules for the type, or empty dict if none defined
        """
        return self.type_interpretation.get(data_type, {})
        
    def map_field(self, helper: StructuralHelper, field_token: str) -> Optional[str]:
        """
        Map a field token based on the structural helper.
        
        Uses the integration mappings to determine the appropriate field name.
        
        Args:
            helper: The structural helper used in the permission statement
            field_token: The field token from the statement
            
        Returns:
            Optional[str]: The mapped internal field name, or None if no mapping exists
        """
        # For the WITH helper, use the field token as is (default behavior)
        if helper == StructuralHelper.WITH:
            return field_token.lower()
            
        # Check if we have a mapping for this helper
        if helper in self.helper_mappings:
            # Use the first available mapping (could be enhanced to use integration-specific mapping)
            for integration_name, field_name in self.helper_mappings[helper].items():
                return field_name
                
        # If no mapping found, just return the lowercase field token
        return field_token.lower()
    
    def convert_value(self, value: str, data_type: DataType) -> Any:
        """
        Convert a value based on the data type's rules from the integration mappings.
        
        Args:
            value: The value to convert
            data_type: The target data type
            
        Returns:
            Any: The converted value
        """
        # Get the rules for this data type
        rules = self.get_type_rules(data_type)
        
        # Handle based on data type
        if data_type == DataType.BOOLEAN:
            # Check if the value is in the true_values list
            true_values = rules.get("true_values", ["true", "yes", "1", "on"])
            false_values = rules.get("false_values", ["false", "no", "0", "off"])
            
            # Case-insensitive comparison
            value_lower = value.lower()
            if value_lower in true_values:
                return True
            elif value_lower in false_values:
                return False
            
            # Default to Python's bool() if not in either list
            return bool(value)
            
        elif data_type == DataType.NUMBER:
            # Try to convert to int or float
            parse_as_int_first = rules.get("parse_as_int_first", True)
            
            try:
                if parse_as_int_first:
                    return int(value)
                else:
                    return float(value)
            except ValueError:
                if parse_as_int_first:
                    try:
                        return float(value)
                    except ValueError:
                        return value
                else:
                    return value
                    
        elif data_type == DataType.TAGS:
            # Handle list conversion
            if isinstance(value, list):
                return value
                
            separator = rules.get("separator", ",")
            strip_whitespace = rules.get("strip_whitespace", True)
            
            if separator in value:
                if strip_whitespace:
                    return [tag.strip() for tag in value.split(separator)]
                else:
                    return value.split(separator)
            
            # Single tag
            return [value]
            
        # Default to returning as-is
        return value
        
    def get_field_type(self, field: str, resource_type: ResourceType) -> Optional[DataType]:
        """
        Get the data type of a field for a specific resource.
        
        Looks up the field type in all integration mappings for the given resource type.
        
        Args:
            field: The field name
            resource_type: The resource type
            
        Returns:
            Optional[DataType]: The data type of the field, or None if unknown
        """
        # Look up the field type in integration mappings
        for integration_name, integration_data in self.integration_mappings.items():
            # Check if this integration has the resource type
            if resource_type.value in integration_data:
                resource_data = integration_data[resource_type.value]
                # Check if the field is defined for this resource
                if field in resource_data:
                    field_data = resource_data[field]
                    # Check if the field has a data_type defined
                    if "data_type" in field_data:
                        # Convert string data type to DataType enum
                        data_type_str = field_data["data_type"]
                        try:
                            return DataType(data_type_str)
                        except ValueError:
                            # If the data type string is not a valid DataType enum value
                            pass
        
        # No mapping found
        return None
    
    def get_resource_metadata(self, resource_type: ResourceType) -> Dict[str, Any]:
        """
        Get metadata about a resource type from the integration schema.
        
        Args:
            resource_type: The resource type
            
        Returns:
            Dict[str, Any]: Metadata about the resource type
        """
        # Collect metadata from all integrations that define this resource type
        metadata = {}
        
        for integration_name, integration_data in self.integration_mappings.items():
            if resource_type.value in integration_data:
                resource_data = integration_data[resource_type.value]
                if "metadata" in resource_data:
                    # Merge metadata from this integration
                    metadata.update(resource_data["metadata"])
        
        return metadata

class Interpreter(BaseInterpreter):
    """Simple implementation of the BaseInterpreter."""
    
    def __init__(self, schema_provider: Optional[BaseSchemaProvider] = None, 
                 integration_mappings: Optional[Dict[str, Dict[str, Any]]] = None):
        """
        Initialize the interpreter with an optional schema provider.
        
        Args:
            schema_provider: Optional SchemaProvider for field mapping and type information
            integration_mappings: Optional dictionary of integration mappings to use if no schema_provider is provided
        """
        self.schema_provider = schema_provider or SchemaProvider(integration_mappings)
    
    def interpret(self, tokens: List[str]) -> InterpretedStatement:
        """
        Interpret tokenized permission statement.
        
        Args:
            tokens: The tokens to interpret
            
        Returns:
            InterpretedStatement: Structured representation of the statement with proper typing
        """
        if not tokens:
            raise ValueError("No tokens to interpret")
        
        # Initialize the result structure
        result: Dict[str, Any] = {
            "command": None,
            "access_types": [],
            "resource_type": None,
            "conditions": [],
            "integration_data": {},
            # Note: In the future, consider implementing a tree structure for nested logical expressions
            # This flat list approach works well for simple AND/OR combinations but has limitations
            # for complex nested logic
        }
        
        # Parse the tokens based on a simple state machine
        state = "COMMAND"
        current_condition = {}
        current_logical_op = LogicalOperator.AND  # Default logical operator
        
        i = 0
        while i < len(tokens):
            token = tokens[i]
            
            if state == "COMMAND":
                # Expect a command (GIVE or DENY)
                try:
                    result["command"] = BaseCommand(token)
                    state = "ACCESS_TYPE"
                except ValueError:
                    raise ValueError(f"Expected a command (GIVE, DENY), got {token}")
            
            elif state == "ACCESS_TYPE":
                # Expect access types (READ, WRITE, DELETE)
                try:
                    # Check for ampersand for multiple access types
                    if token == "&":
                        i += 1
                        continue
                    
                    result["access_types"].append(AccessType(token))
                    
                    # Check if next token is & or ACCESS_TO
                    if i + 1 < len(tokens):
                        if tokens[i + 1] == "&":
                            # More access types coming
                            i += 1
                            continue
                        elif tokens[i + 1] == "ACCESS_TO":
                            # Move to next state
                            state = "ACCESS_TO"
                    
                except ValueError:
                    # If it's not an access type, check if it's "ACCESS_TO"
                    if token == "ACCESS_TO":
                        state = "RESOURCE_TYPE"
                    else:
                        raise ValueError(f"Expected an access type (READ, WRITE, DELETE) or ACCESS TO, got {token}")
            
            elif state == "ACCESS_TO":
                # Expect "ACCESS_TO"
                if token != "ACCESS_TO":
                    raise ValueError(f"Expected 'ACCESS TO', got {token}")
                state = "RESOURCE_TYPE"
            
            elif state == "RESOURCE_TYPE":
                # Expect a resource type (EMAILS, PROJECTS, etc.)
                try:
                    result["resource_type"] = ResourceType(token)
                    # If we have a schema provider, initialize any resource-specific data
                    if self.schema_provider:
                        result["integration_data"] = self.schema_provider.get_resource_metadata(result["resource_type"])
                    state = "CONDITION_START"
                except ValueError:
                    raise ValueError(f"Expected a resource type, got {token}")
            
            elif state == "CONDITION_START":
                # Expect a structural helper (WITH, NAMED, etc.) or end of statement
                if i == len(tokens) - 1:
                    # End of statement, no conditions
                    break
                
                try:
                    helper = StructuralHelper(token)
                    current_condition = {"helper": helper}
                    state = "CONDITION_FIELD"
                except ValueError:
                    # If not a structural helper, should be end of statement
                    if token == "AND" or token == "OR":
                        current_logical_op = LogicalOperator(token)
                        state = "CONDITION_START"
                    else:
                        raise ValueError(f"Expected a structural helper (WITH, NAMED, etc.) or end of statement, got {token}")
            
            elif state == "CONDITION_FIELD":
                # Field name for the condition
                current_condition["field"] = self._map_field_from_helper(current_condition["helper"], token)
                state = "CONDITION_OPERATOR"
            
            elif state == "CONDITION_OPERATOR":
                # Operator for the condition
                try:
                    # Check for compound operators like "IS NOT", "GREATER THAN", etc.
                    # Simple 2-token operators
                    compound_operators = {
                        "IS": {"NOT": ConditionOperator.IS_NOT},
                        "GREATER": {"THAN": ConditionOperator.GREATER_THAN},
                        "LESS": {"THAN": ConditionOperator.LESS_THAN}
                    }
                    
                    # Handle 3-token operators first (higher priority)
                    if (token in ["GREATER", "LESS"] and 
                        i + 2 < len(tokens) and 
                        tokens[i + 1] == "OR" and 
                        tokens[i + 2] == "EQUAL"):
                        if token == "GREATER":
                            current_condition["operator"] = ConditionOperator.GREATER_OR_EQUAL
                        else:  # token == "LESS"
                            current_condition["operator"] = ConditionOperator.LESS_OR_EQUAL
                        i += 2  # Skip "OR EQUAL"
                    # Handle 2-token operators next
                    elif token in compound_operators and i + 1 < len(tokens):
                        second_part = tokens[i + 1]
                        if second_part in compound_operators[token]:
                            current_condition["operator"] = compound_operators[token][second_part]
                            i += 1  # Skip the second part of the compound operator
                        else:
                            # Handle the token as a single operator
                            current_condition["operator"] = ConditionOperator(token)
                    else:
                        # Single token operator
                        current_condition["operator"] = ConditionOperator(token)
                    state = "CONDITION_VALUE"
                except ValueError:
                    raise ValueError(f"Expected a condition operator (IS, CONTAINS, etc.), got {token}")
            
            elif state == "CONDITION_VALUE":
                # Value for the condition
                current_condition["value"] = token
                
                # Try to get field type from schema provider if possible
                field_type = None
                if self.schema_provider and "resource_type" in result:
                    field_type = self.schema_provider.get_field_type(current_condition["field"], result["resource_type"])
                
                # If no field type from schema, infer based on value
                if field_type is None:
                    field_type = self._infer_data_type(token)
                
                # Convert the value based on its type, using schema provider's rules if available
                converted_value = token
                if self.schema_provider and isinstance(self.schema_provider, SchemaProvider):
                    converted_value = self.schema_provider.convert_value(token, field_type)
                else:
                    # Fallback to our simple converter
                    converted_value = self._convert_value(token, field_type)
                
                result["conditions"].append({
                    "field": current_condition["field"],
                    "operator": current_condition["operator"],
                    "value": converted_value,
                    "field_type": field_type,
                    "logical_operator": current_logical_op  # Save the logical operator with each condition
                })
                
                # Reset for next condition
                current_condition = {}
                
                # Check if there are more conditions
                if i + 1 < len(tokens):
                    if tokens[i + 1] == "AND" or tokens[i + 1] == "OR":
                        # Update the logical operator for the next condition
                        # TODO: In a future enhancement, this could be used to build a tree structure
                        # that better represents nested logical expressions
                        current_logical_op = LogicalOperator(tokens[i + 1])
                        i += 1  # Skip the logical operator token
                        state = "CONDITION_START"
                    else:
                        state = "CONDITION_START"
                else:
                    # End of statement
                    break
            
            i += 1
        
        # Ensure all required fields are present for proper typing
        if "integration_data" not in result:
            result["integration_data"] = {}
            
        # Return the typed result
        return result
    
    def _map_field_from_helper(self, helper: StructuralHelper, field_token: str, resource_type: Optional[ResourceType] = None) -> str:
        """
        Map a field token based on the structural helper and resource type.
        
        Args:
            helper: The structural helper
            field_token: The field token
            resource_type: The optional resource type for schema lookup
            
        Returns:
            str: The mapped field name
        """
        # Use schema provider for mapping
        if resource_type:
            return self.schema_provider.map_field(helper, field_token, resource_type) or field_token.lower()
        return field_token.lower()
    
    def _infer_data_type(self, value: str) -> DataType:
        """
        Infer the data type of a field based on its name and value.
        
        Uses only value-based inference since schema-based inference is handled
        at a higher level with proper resource_type information.
        
        Args:
            field: The field name
            value: The field value
            
        Returns:
            DataType: The inferred data type
        """
        # Use only value-based inference
        # Boolean values
        if value.lower() in ["true", "false", "yes", "no", "on", "off"]:
            return DataType.BOOLEAN
        
        # Check if appears to be a number
        try:
            float(value)  # Try parsing as number
            return DataType.NUMBER
        except ValueError:
            pass
            
        # Check if appears to be an email
        if "@" in value and "." in value.split("@")[1]:
            return DataType.EMAIL_ADDRESS
            
        # Default to string for anything else
        return DataType.STRING
    
    def _convert_value(self, value: str, data_type: DataType) -> Any:
        """
        Convert a value string to its appropriate type based on the data type.
        
        Args:
            value: The value to convert
            data_type: The target data type
            
        Returns:
            Any: The converted value
        """
        # Handle conversions based on the target data type
        if data_type == DataType.BOOLEAN:
            # Use a simple heuristic for boolean conversion 
            # This should ideally be configurable per integration
            value_lower = value.lower()
            if value_lower in ["true", "yes", "on", "1"]:
                return True
            elif value_lower in ["false", "no", "off", "0"]:
                return False
            return bool(value)  # Default Python truthiness
            
        elif data_type == DataType.NUMBER:
            try:
                # Try integer first
                return int(value)
            except ValueError:
                try:
                    # Then float
                    return float(value)
                except ValueError:
                    # If conversion fails, leave as string
                    return value
                    
        elif data_type == DataType.TAGS:
            # Handle tags as list
            if isinstance(value, list):
                return value
            elif "," in value:
                return [tag.strip() for tag in value.split(",")]
            else:
                return [value]
                
        # For all other types, return as string
        return value 