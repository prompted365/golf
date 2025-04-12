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
    """Default implementation of BaseSchemaProvider with hardcoded mappings."""
    
    def map_field(self, helper: StructuralHelper, field_token: str, resource_type: ResourceType) -> Optional[str]:
        """Map a field token based on the structural helper and resource type."""
        # Simple default mapping
        if helper == StructuralHelper.TAGGED:
            return "tags"
        elif helper == StructuralHelper.NAMED:
            return "name"
        elif helper == StructuralHelper.ASSIGNED_TO:
            return "assignee"
        elif helper == StructuralHelper.FROM:
            return "sender"
        elif helper == StructuralHelper.WITH:
            # For WITH, use the field token as is
            return field_token.lower()
        else:
            return field_token.lower()
    
    def get_field_type(self, field: str, resource_type: ResourceType) -> Optional[DataType]:
        """Infer the data type of a field based on its name and resource type."""
        # Field-based inference
        if field in ["tags"]:
            return DataType.TAGS
        elif field in ["assignee", "owner", "user"]:
            return DataType.USER
        elif field in ["email", "sender", "recipient"]:
            return DataType.EMAIL_ADDRESS
        elif field in ["date", "created_date", "updated_date"]:
            return DataType.DATETIME
        elif field in ["domain"]:
            return DataType.DOMAIN
        return None
    
    def get_resource_metadata(self, resource_type: ResourceType) -> Dict[str, Any]:
        """Get metadata about a resource type."""
        # Return empty metadata for now
        return {}

class Interpreter(BaseInterpreter):
    """Simple implementation of the BaseInterpreter."""
    
    def __init__(self, schema_provider: Optional[BaseSchemaProvider] = None):
        """
        Initialize the interpreter with an optional schema provider.
        
        Args:
            schema_provider: Optional SchemaProvider for field mapping and type information
        """
        self.schema_provider = schema_provider or SchemaProvider()
    
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
                current_condition["field"] = self._map_field_from_helper(current_condition["helper"], token, result["resource_type"])
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
                
                # Add the complete condition to the result
                field_type = self._infer_data_type(current_condition["field"], token, result["resource_type"], current_condition["field"])
                
                result["conditions"].append({
                    "field": current_condition["field"],
                    "operator": current_condition["operator"],
                    "value": self._convert_value(token, field_type, result["resource_type"], current_condition["field"]),
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
    
    def _infer_data_type(self, field: str, value: str, resource_type: Optional[ResourceType] = None, field_name: Optional[str] = None) -> DataType:
        """
        Infer the data type of a field based on its name, value, and resource type.
        
        Args:
            field: The field name
            value: The field value
            resource_type: The optional resource type for schema lookup
            field_name: Optional alternative field name (useful when field is a derived/mapped value)
            
        Returns:
            DataType: The inferred data type
        """
        # Use schema provider for type inference
        if resource_type:
            schema_type = self.schema_provider.get_field_type(field, resource_type)
            if schema_type:
                return schema_type
                
            # Try with the alternative field name if provided and different
            if field_name and field_name != field:
                schema_type = self.schema_provider.get_field_type(field_name, resource_type)
                if schema_type:
                    return schema_type
        
        # Fallback to value-based inference
        if value.lower() in ["true", "false"]:
            return DataType.BOOLEAN
        
        try:
            int(value)
            return DataType.NUMBER
        except ValueError:
            try:
                float(value)
                return DataType.NUMBER
            except ValueError:
                # If contains @, likely an email
                if "@" in value:
                    return DataType.EMAIL_ADDRESS
                
                # Default to string
                return DataType.STRING
    
    def _convert_value(self, value: str, data_type: DataType, resource_type: Optional[ResourceType] = None, field: Optional[str] = None) -> Any:
        """
        Convert a value string to its appropriate type.
        
        Args:
            value: The value to convert
            data_type: The target data type
            resource_type: Optional resource type for schema-specific conversion
            field: Optional field name for schema-specific conversion
            
        Returns:
            Any: The converted value
        """
        # For more complex conversions, we could use the schema provider and resource_type/field
        if data_type == DataType.BOOLEAN:
            return value.lower() == "true"
        elif data_type == DataType.NUMBER:
            try:
                return int(value)
            except ValueError:
                try:
                    return float(value)
                except ValueError:
                    return value
        elif data_type == DataType.TAGS:
            # If it's a comma-separated list, split it
            if "," in value:
                return [tag.strip() for tag in value.split(",")]
            return [value]
        else:
            return value 