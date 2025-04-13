"""Context-aware completions for permission statements."""

from typing import List, Dict, Set
import re

from permissions.models import (
    BaseCommand, 
    AccessType, 
    ResourceType, 
    ConditionOperator,
    StructuralHelper
)
from permissions.integrations.linear import LINEAR_RESOURCES


class Completer:
    """
    Context-aware completer for permission statements.
    
    This class provides completion suggestions based on the current
    token position and the tokens parsed so far.
    """
    
    def __init__(self):
        """Initialize the completer with known command components."""
        self.base_commands = [cmd.value for cmd in BaseCommand]
        self.access_types = [access.value for access in AccessType]
        self.resource_types = [resource.value for resource in ResourceType]
        self.condition_operators = [op.value for op in ConditionOperator]
        self.structural_helpers = [
            StructuralHelper.get_display_value(helper) for helper in StructuralHelper
        ]
        
        # Linear-specific resources
        self.linear_resources = LINEAR_RESOURCES
        
        # Extract field names from Linear resources
        self.resource_fields: Dict[str, Set[str]] = {}
        for resource_type, fields in LINEAR_RESOURCES.items():
            if resource_type.startswith("_"):  # Skip helper mappings
                continue
            self.resource_fields[resource_type] = set(fields.keys())
    
    def complete(self, text: str, current_position: int) -> List[str]:
        """
        Get completion suggestions based on the current text and cursor position.
        
        Args:
            text: The current input text
            current_position: The current cursor position
            
        Returns:
            List[str]: List of completion suggestions
        """
        # Get the text up to the cursor position
        text_to_cursor = text[:current_position]
        
        # Tokenize the text
        tokens = self._tokenize(text_to_cursor)
        
        # Determine the context for suggestions
        return self._get_suggestions(tokens)
    
    def _tokenize(self, text: str) -> List[str]:
        """
        Simple tokenizer for completion purposes.
        
        Args:
            text: The text to tokenize
            
        Returns:
            List[str]: List of tokens
        """
        # This is a simplified tokenizer for completion purposes
        # It's not meant to be as robust as the real tokenizer
        tokens = []
        
        # Split on spaces, keeping quoted strings together
        pattern = r'(?:[^\s"]+|"[^"]*"?)+'
        matches = re.findall(pattern, text)
        
        for match in matches:
            # Remove quotes from quoted strings
            if match.startswith('"') and match.endswith('"'):
                match = match[1:-1]
            tokens.append(match)
        
        return tokens
    
    def _get_suggestions(self, tokens: List[str]) -> List[str]:
        """
        Get completion suggestions based on the tokens parsed so far.
        
        Args:
            tokens: The tokens parsed so far
            
        Returns:
            List[str]: List of completion suggestions
        """
        # Empty statement - suggest base commands
        if not tokens:
            return self.base_commands
        
        # Start of statement
        if len(tokens) == 1 and tokens[0] in self.base_commands:
            return self.access_types
        
        # After "GIVE READ" or similar
        if len(tokens) == 2 and tokens[0] in self.base_commands and tokens[1] in self.access_types:
            return ["ACCESS TO"]
        
        # After "GIVE READ ACCESS TO" - suggest resource types
        if len(tokens) >= 3 and tokens[-2] == "ACCESS" and tokens[-1] == "TO":
            return self.resource_types
        
        # After resource type - suggest structural helpers
        if len(tokens) >= 4 and tokens[-2] == "TO" and tokens[-1] in self.resource_types:
            return self.structural_helpers
        
        # After structural helper - suggest condition operators
        if len(tokens) >= 5 and tokens[-1] in self.structural_helpers:
            return self.condition_operators
        
        # After condition operator - suggest field values
        if len(tokens) >= 6 and tokens[-1] in self.condition_operators:
            # Get resource type and field to suggest values
            resource_idx = tokens.index("TO") + 1 if "TO" in tokens else -1
            if resource_idx >= 0 and resource_idx < len(tokens):
                resource_type = tokens[resource_idx]
                # Get last structural helper
                struct_helpers = [t for t in tokens if t in self.structural_helpers]
                if struct_helpers:
                    last_helper = struct_helpers[-1]
                    # Check if we have sample values for this field
                    if last_helper == "TAGGED":
                        return ["urgent", "bug", "feature", "backlog", "wip"]
                    elif last_helper == "ASSIGNED TO":
                        return ["antoni", "john", "jane", "unassigned"]
                    elif last_helper == "WITH" and tokens[-3] == "STATUS":
                        return ["Todo", "In Progress", "Done", "Canceled"]
        
        # Default to no suggestions
        return []
        
    def get_field_suggestions(self, resource_type: str) -> List[str]:
        """
        Get suggestions for fields of a resource type.
        
        Args:
            resource_type: The resource type
            
        Returns:
            List[str]: List of field suggestions
        """
        resource_type = resource_type.upper()
        if resource_type in self.resource_fields:
            return sorted(list(self.resource_fields[resource_type]))
        return []
        
    def _get_fields_for_resource(self, resource_type: str) -> List[str]:
        """
        Get all fields for a resource type.
        
        Args:
            resource_type: The resource type (case insensitive)
            
        Returns:
            List[str]: List of fields for the resource type
        """
        resource_type = resource_type.upper()
        
        # First check if we have this resource in our fields
        if resource_type in self.resource_fields:
            return list(self.resource_fields[resource_type])
            
        # If not, use hardcoded defaults for common resource types
        defaults = {
            "ISSUES": ["id", "title", "description", "assignee", "labels", "status"],
            "EMAILS": ["sender", "recipient", "subject", "body", "date", "attachments", "tags"],
            "TEAMS": ["name", "id", "key", "owner"],
        }
        
        return defaults.get(resource_type, []) 