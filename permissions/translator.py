"""Translator for permission statements to Rego policies."""

import re

from .base import PermissionTranslator
from .models import (
    PermissionStatement,
    RegoPolicy,
    Condition,
    AccessType,
    ResourceType
)

class SimplePermissionTranslator(PermissionTranslator):
    """Implements a simple translator for permission statements to Rego policies."""
    
    async def translate(self, statement: PermissionStatement) -> RegoPolicy:
        """
        Translate a permission statement into a Rego policy.
        
        Args:
            statement: The permission statement to translate
            
        Returns:
            RegoPolicy: The translated Rego policy
        """
        # Start with the policy template
        policy_content = """package authed.permissions

default allow = false

allow {
    # Check resource type
    input.resource.type == "%s"
    
    # Check action
    %s
    
    # Check conditions
    %s
}
"""
        
        # Translate actions
        actions_rego = "\n    ".join(
            f'input.action == "{action}"' for action in statement.access_type
        )
        
        if len(statement.access_type) > 1:
            actions_rego = "# Check for any of the allowed actions\n    (" + actions_rego + "\n    )"
        
        # Translate conditions
        conditions_rego = ""
        if statement.conditions:
            conditions = []
            for condition in statement.conditions:
                if condition.operator == "=":
                    conditions.append(f'input.resource.{condition.field} == "{condition.value}"')
                elif condition.operator == "in":
                    conditions.append(f'"{condition.value}" in input.resource.{condition.field}')
                elif condition.operator == ">":
                    conditions.append(f'input.resource.{condition.field} > {condition.value}')
                elif condition.operator == "<":
                    conditions.append(f'input.resource.{condition.field} < {condition.value}')
                elif condition.operator == "contains":
                    conditions.append(f'contains(input.resource.{condition.field}, "{condition.value}")')
            
            conditions_rego = "\n    ".join(conditions)
        else:
            conditions_rego = "# No conditions to check"
        
        # Format the policy
        formatted_policy = policy_content % (
            statement.resource_type,
            actions_rego,
            conditions_rego
        )
        
        return RegoPolicy(
            package_name=f"authed.permissions.{statement.resource_type.lower()}",
            policy_content=formatted_policy
        )
    
    async def parse_statement(self, statement_text: str) -> PermissionStatement:
        """
        Parse a text-based permission statement into a structured PermissionStatement.
        
        Args:
            statement_text: The text of the permission statement (e.g., "GIVE READ ACCESS TO EMAILS WITH TAGS = WORK")
            
        Returns:
            PermissionStatement: The parsed statement
        """
        # Expected format: 
        # GIVE <ACCESS_TYPE> [& <ACCESS_TYPE>] ACCESS TO <RESOURCE_TYPE> [WITH <FIELD> <OPERATOR> <VALUE>]
        
        # Normalize the statement
        statement = statement_text.upper().strip()
        
        # Parse access types
        access_types = []
        if "READ" in statement:
            access_types.append(AccessType.READ)
        if "WRITE" in statement:
            access_types.append(AccessType.WRITE)
        if "DELETE" in statement:
            access_types.append(AccessType.DELETE)
        if "EXECUTE" in statement:
            access_types.append(AccessType.EXECUTE)
        
        # Parse resource type
        resource_type = None
        for rt in ResourceType:
            if rt.value in statement:
                resource_type = rt
                break
        
        if not resource_type:
            raise ValueError(f"Could not identify resource type in statement: {statement_text}")
        
        # Parse conditions
        conditions = []
        
        # Look for WITH keyword followed by conditions
        with_parts = statement.split(" WITH ")
        if len(with_parts) > 1:
            conditions_text = with_parts[1]
            
            # Support for multiple conditions with AND
            condition_parts = conditions_text.split(" AND ")
            
            for condition_text in condition_parts:
                # Match pattern: <FIELD> <OPERATOR> <VALUE>
                match = re.match(r'([A-Z_]+)\s*([=><]|IN|CONTAINS)\s*(\w+)', condition_text)
                if match:
                    field, operator, value = match.groups()
                    
                    # Normalize operator
                    if operator == "=":
                        normalized_operator = "="
                    elif operator == ">":
                        normalized_operator = ">"
                    elif operator == "<":
                        normalized_operator = "<"
                    elif operator == "IN":
                        normalized_operator = "in"
                    elif operator == "CONTAINS":
                        normalized_operator = "contains"
                    else:
                        normalized_operator = operator
                    
                    # Create condition
                    conditions.append(Condition(
                        field=field.lower(),
                        operator=normalized_operator,
                        value=value
                    ))
        
        return PermissionStatement(
            access_type=access_types,
            resource_type=resource_type,
            conditions=conditions
        ) 