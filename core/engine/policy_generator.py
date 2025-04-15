"""Policy generator for creating Rego policies from permission statements."""

import os
import uuid
import logging
from typing import Dict, Optional

from ..base import PolicyGenerator
from ..models import (
    PermissionStatement,
    RegoPolicy,
    BaseCommand,
    ConditionOperator,
    DataType,
    LogicalOperator
)

# Set up logging
logger = logging.getLogger(__name__)

class RegoGenerator(PolicyGenerator):
    """Generates Rego policies from permission statements."""
    
    def __init__(self, templates_dir: Optional[str] = None):
        """
        Initialize the policy generator.
        
        Args:
            templates_dir: Directory containing Rego templates
        """
        self.templates: Dict[str, str] = {}
        
        # Set templates directory
        if templates_dir and os.path.isdir(templates_dir):
            self.templates_dir = templates_dir
            self._load_templates()
        else:
            self.templates_dir = None
            # Add default template
            self.templates["default"] = self._default_template()
    
    def _load_templates(self) -> None:
        """Load templates from the templates directory."""
        for filename in os.listdir(self.templates_dir):
            if filename.endswith(".rego"):
                template_name = filename[:-5]  # Remove .rego extension
                with open(os.path.join(self.templates_dir, filename), "r") as f:
                    self.templates[template_name] = f.read()
    
    def _default_template(self) -> str:
        """Return the default template for Rego policies."""
        return """package {package}

default {default_rule} = {default_value}

{rule_type} = true if {{
    {conditions}
}}
"""
    
    async def get_template(self, template_name: str) -> str:
        """
        Get a Rego template by name.
        
        Args:
            template_name: The name of the template
            
        Returns:
            str: The template content
        """
        if template_name in self.templates:
            return self.templates[template_name]
        else:
            raise ValueError(f"Template {template_name} not found")
    
    async def register_template(self, template_name: str, template_content: str) -> None:
        """
        Register a new Rego template.
        
        Args:
            template_name: The name of the template
            template_content: The content of the template
        """
        self.templates[template_name] = template_content
    
    async def generate_policy(self, statement: PermissionStatement) -> RegoPolicy:
        """
        Generate a Rego policy from a permission statement.
        
        Args:
            statement: The permission statement
            
        Returns:
            RegoPolicy: The generated Rego policy
        """
        # Log the input statement
        logger.info(f"Generating policy for statement: {statement}")
        logger.debug(f"Statement has {len(statement.conditions)} conditions: {statement.conditions}")
        
        # Get default template
        template = await self.get_template("default")
        
        # Determine the package name based on resource type
        package_name = f"authed.permissions.{statement.resource_type.value.lower()}"
        
        # Determine the rule type and default value based on the command
        if statement.command == BaseCommand.GIVE:
            # BaseCommand.GIVE corresponds to the "allow" rule in Rego
            rule_type = "allow"
            default_rule = "allow"
            default_value = "false"
        else:  # DENY
            # BaseCommand.DENY corresponds to the "deny" rule in Rego
            rule_type = "deny"
            default_rule = "deny"
            default_value = "false"
        
        # Generate conditions
        conditions = []
        
        # Add resource type check
        conditions.append(f'input.resource.type == "{statement.resource_type.value}"')
        
        # Add action check for each access type
        action_conditions = []
        for access_type in statement.access_types:
            action_conditions.append(f'input.action == "{access_type.value}"')
        
        if len(action_conditions) == 1:
            conditions.append(action_conditions[0])
        else:
            # Join multiple action conditions with OR
            conditions.append("(" + " || ".join(action_conditions) + ")")
        
        # Add statement conditions
        statement_conditions = []
        for condition in statement.conditions:
            cond = self._format_condition(condition)
            if cond:
                statement_conditions.append(cond)
        
        # Combine statement conditions based on logical operator
        if statement_conditions:
            if statement.logical_operator == LogicalOperator.AND:
                logger.debug("Using AND operator for conditions")
                conditions.extend(statement_conditions)
            elif statement.logical_operator == LogicalOperator.OR:
                logger.debug("Using OR operator for conditions")
                combined_condition = "(" + " || ".join(statement_conditions) + ")"
                conditions.append(combined_condition)
        else:
            logger.warning("No statement conditions were successfully formatted")
        
        # Format conditions with indentation
        formatted_conditions = "\n    ".join(conditions)
        
        # Log the final conditions
        logger.debug(f"Final formatted conditions:\n{formatted_conditions}")
        
        # Fill in the template
        policy_content = template.format(
            package=package_name,
            default_rule=default_rule,
            default_value=default_value,
            rule_type=rule_type,
            conditions=formatted_conditions
        )
        
        # Create and return the RegoPolicy
        return RegoPolicy(
            package_name=package_name,
            policy_content=policy_content,
            metadata={
                "statement": statement.dict(),
                "id": str(uuid.uuid4())
            }
        )
    
    def _format_condition(self, condition) -> Optional[str]:
        """
        Format a condition for Rego.
        
        Args:
            condition: The condition to format (Pydantic model or dictionary)
            
        Returns:
            Optional[str]: The formatted condition or None if invalid
        """
        # Check if condition is a dictionary or a Pydantic model
        if hasattr(condition, "field"):
            # It's a Pydantic model, access attributes directly
            field = condition.field
            operator = condition.operator
            value = condition.value
            field_type = condition.field_type
        else:
            # Assume it's a dictionary
            field = condition.get("field")
            operator = condition.get("operator")
            value = condition.get("value")
            field_type = condition.get("field_type")
        
        # Log what we're working with
        logger.debug(f"Formatting condition: field={field}, operator={operator}, value={value}")
        
        # Skip formatting if any required fields are missing
        if field is None or operator is None or value is None:
            logger.warning(f"Missing required field in condition: {condition}")
            return None
            
        logger.debug(f"Field type: {field_type}")
        
        # Format field
        field_path = f"input.resource.properties.{field}"
        
        # Format value based on field type
        if field_type == DataType.STRING or field_type == DataType.EMAIL_ADDRESS or field_type == DataType.USER or field_type == DataType.DOMAIN:
            formatted_value = f'"{value}"'
        elif field_type == DataType.BOOLEAN:
            formatted_value = str(value).lower()
        elif field_type == DataType.NUMBER:
            formatted_value = str(value)
        elif field_type == DataType.TAGS:
            logger.debug(f"Processing TAGS condition: {value}, {type(value)}")
            if isinstance(value, list):
                # For lists, we need special handling based on the operator
                if operator == ConditionOperator.IS:
                    # Check if tags is exactly this list - use Rego's semicolons for AND operations
                    tags_check = []
                    for tag in value:
                        tags_check.append(f'"{tag}" in {field_path}')
                    
                    # In Rego, each statement needs to be on its own line
                    # Just check for tag inclusion, don't enforce exact count
                    result = []
                    for tag_check in tags_check:
                        result.append(tag_check)
                    
                    return "\n    ".join(result)
                elif operator == ConditionOperator.CONTAINS:
                    # Check if any of these tags are in the list - OR can still use pipes in Rego
                    tags_check = []
                    for tag in value:
                        tags_check.append(f'"{tag}" in {field_path}')
                    return " || ".join(tags_check)
            
            # Single tag value
            formatted_value = f'"{value}"'
        else:
            # Default to string format
            formatted_value = f'"{value}"'
        
        # Format operator
        if operator == ConditionOperator.IS:
            # For numeric field types, use to_number() for type-safe comparison
            if field_type == DataType.NUMBER:
                return f"to_number({field_path}) == to_number({formatted_value})"
            return f"{field_path} == {formatted_value}"
        elif operator == ConditionOperator.IS_NOT:
            # For numeric field types, use to_number() for type-safe comparison
            if field_type == DataType.NUMBER:
                return f"to_number({field_path}) != to_number({formatted_value})"
            return f"{field_path} != {formatted_value}"
        elif operator == ConditionOperator.CONTAINS:
            if field_type == DataType.TAGS:
                return f"{formatted_value} in {field_path}"
            else:
                return f"contains({field_path}, {formatted_value})"
        elif operator == ConditionOperator.GREATER_THAN:
            # For numeric field types, use to_number() for type-safe comparison
            if field_type == DataType.NUMBER:
                return f"to_number({field_path}) > to_number({formatted_value})"
            return f"{field_path} > {formatted_value}"
        elif operator == ConditionOperator.LESS_THAN:
            # For numeric field types, use to_number() for type-safe comparison
            if field_type == DataType.NUMBER:
                return f"to_number({field_path}) < to_number({formatted_value})"
            return f"{field_path} < {formatted_value}"
        elif operator == ConditionOperator.GREATER_OR_EQUAL:
            # For numeric field types, use to_number() for type-safe comparison
            if field_type == DataType.NUMBER:
                return f"to_number({field_path}) >= to_number({formatted_value})"
            return f"{field_path} >= {formatted_value}"
        elif operator == ConditionOperator.LESS_OR_EQUAL:
            # For numeric field types, use to_number() for type-safe comparison
            if field_type == DataType.NUMBER:
                return f"to_number({field_path}) <= to_number({formatted_value})"
            return f"{field_path} <= {formatted_value}"
        elif operator == ConditionOperator.BEFORE:
            return f"time.parse_rfc3339_ns({field_path}) < time.parse_rfc3339_ns({formatted_value})"
        elif operator == ConditionOperator.AFTER:
            return f"time.parse_rfc3339_ns({field_path}) > time.parse_rfc3339_ns({formatted_value})"
        else:
            return None 