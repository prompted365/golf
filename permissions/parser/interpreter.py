"""Interpreter component for permission statements."""

from typing import List, Dict, Any

from ..base import InterpreterInterface
from ..models import (
    BaseCommand,
    AccessType,
    ResourceType,
    ConditionOperator,
    StructuralHelper,
    LogicalOperator,
    DataType
)

class SimpleInterpreter(InterpreterInterface):
    """Simple implementation of the InterpreterInterface."""
    
    def interpret(self, tokens: List[str]) -> Dict[str, Any]:
        """
        Interpret tokenized permission statement.
        
        Args:
            tokens: The tokens to interpret
            
        Returns:
            Dict[str, Any]: Structured representation of the statement
        """
        if not tokens:
            raise ValueError("No tokens to interpret")
        
        # Initialize the result structure
        result = {
            "command": None,
            "access_types": [],
            "resource_type": None,
            "conditions": [],
            "logical_operator": LogicalOperator.AND
        }
        
        # Parse the tokens based on a simple state machine
        state = "COMMAND"
        current_condition = {}
        
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
                    
                    # Check if next token is & or ACCESS TO
                    if i + 1 < len(tokens):
                        if tokens[i + 1] == "&":
                            # More access types coming
                            i += 1
                            continue
                        elif tokens[i + 1] == "ACCESS TO":
                            # Move to next state
                            state = "ACCESS_TO"
                    
                except ValueError:
                    # If it's not an access type, check if it's "ACCESS TO"
                    if token == "ACCESS TO":
                        state = "RESOURCE_TYPE"
                    else:
                        raise ValueError(f"Expected an access type (READ, WRITE, DELETE) or ACCESS TO, got {token}")
            
            elif state == "ACCESS_TO":
                # Expect "ACCESS TO"
                if token != "ACCESS TO":
                    raise ValueError(f"Expected 'ACCESS TO', got {token}")
                state = "RESOURCE_TYPE"
            
            elif state == "RESOURCE_TYPE":
                # Expect a resource type (EMAILS, PROJECTS, etc.)
                try:
                    result["resource_type"] = ResourceType(token)
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
                        result["logical_operator"] = LogicalOperator(token)
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
                    current_condition["operator"] = ConditionOperator(token)
                    state = "CONDITION_VALUE"
                except ValueError:
                    raise ValueError(f"Expected a condition operator (IS, CONTAINS, etc.), got {token}")
            
            elif state == "CONDITION_VALUE":
                # Value for the condition
                current_condition["value"] = token
                
                # Add the complete condition to the result
                field_type = self._infer_data_type(current_condition["field"], token)
                
                result["conditions"].append({
                    "field": current_condition["field"],
                    "operator": current_condition["operator"],
                    "value": self._convert_value(token, field_type),
                    "field_type": field_type
                })
                
                # Reset for next condition
                current_condition = {}
                
                # Check if there are more conditions
                if i + 1 < len(tokens):
                    if tokens[i + 1] == "AND" or tokens[i + 1] == "OR":
                        result["logical_operator"] = LogicalOperator(tokens[i + 1])
                        i += 1  # Skip the logical operator token
                        state = "CONDITION_START"
                    else:
                        state = "CONDITION_START"
                else:
                    # End of statement
                    break
            
            i += 1
        
        return result
    
    def _map_field_from_helper(self, helper: StructuralHelper, field_token: str) -> str:
        """
        Map a field token based on the structural helper.
        
        Args:
            helper: The structural helper
            field_token: The field token
            
        Returns:
            str: The mapped field name
        """
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
    
    def _infer_data_type(self, field: str, value: str) -> DataType:
        """
        Infer the data type of a field based on its name and value.
        
        Args:
            field: The field name
            value: The field value
            
        Returns:
            DataType: The inferred data type
        """
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
        
        # Value-based inference
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
    
    def _convert_value(self, value: str, data_type: DataType) -> Any:
        """
        Convert a value string to its appropriate type.
        
        Args:
            value: The value to convert
            data_type: The target data type
            
        Returns:
            Any: The converted value
        """
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