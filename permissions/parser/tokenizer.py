"""Tokenizer component for permission statements."""

import re
from typing import List

from ..base import TokenizerInterface
from ..models import (
    BaseCommand,
    AccessType,
    ResourceType,
    ConditionOperator,
    StructuralHelper,
    LogicalOperator
)

class SimpleTokenizer(TokenizerInterface):
    """Simple implementation of the TokenizerInterface."""
    
    def __init__(self):
        """Initialize the tokenizer."""
        # Create regex patterns for matching different parts of the statement
        self.patterns = {
            "command": self._create_enum_pattern(BaseCommand),
            "access_type": self._create_enum_pattern(AccessType),
            "resource_type": self._create_enum_pattern(ResourceType),
            "structural_helper": self._create_enum_pattern_with_aliases(StructuralHelper),
            "logical_operator": self._create_enum_pattern(LogicalOperator),
            "condition_operator": self._create_enum_pattern(ConditionOperator),
            "quoted_string": r'"((?:\\.|[^"\\])*)"',  # Match anything in double quotes, including escaped chars
            "non_quoted_string": r'[\w\.@_-]+',  # Match word characters, dots, @, _, -
        }
    
    def _create_enum_pattern(self, enum_class) -> str:
        """Create a regex pattern from an Enum class values."""
        # Sort by length (longest first) to ensure proper matching
        values = sorted([e.value for e in enum_class], key=len, reverse=True)
        
        # Escape special regex characters and join with pipe
        escaped_values = [re.escape(value) for value in values]
        return '|'.join(escaped_values)
    
    def _create_enum_pattern_with_aliases(self, enum_class) -> str:
        """Create a regex pattern that includes aliases for enum values."""
        values = []
        
        # Add all regular enum values
        enum_values = sorted([e.value for e in enum_class], key=len, reverse=True)
        values.extend(enum_values)
        
        # Add display values (aliases) if available
        if hasattr(enum_class, 'get_display_value'):
            for member in enum_class:
                display_value = enum_class.get_display_value(member)
                if display_value != member.value:
                    values.append(display_value)
        
        # Escape special regex characters and join with pipe
        escaped_values = [re.escape(value) for value in values]
        return '|'.join(escaped_values)
    
    def tokenize(self, statement_text: str) -> List[str]:
        """
        Tokenize a permission statement into a list of tokens.
        
        Args:
            statement_text: The permission statement to tokenize
            
        Returns:
            List[str]: The tokenized statement
        """
        # Normalize the statement
        statement = statement_text.strip()
        
        # Replace special patterns
        tokens = []
        remaining = statement
        
        # Process the statement until it's empty
        while remaining:
            remaining = remaining.strip()
            if not remaining:
                break
            
            # Try to match each pattern type
            matched = False
            
            # First try to match quoted strings
            quoted_match = re.match(f'^{self.patterns["quoted_string"]}', remaining)
            if quoted_match:
                # Process escaped characters in the string
                quoted_content = quoted_match.group(1)
                processed_content = re.sub(r'\\(.)', r'\1', quoted_content)  # Replace \x with x
                tokens.append(processed_content)
                remaining = remaining[quoted_match.end():]
                matched = True
                continue
            
            # Check for special helper phrases first
            if remaining.upper().startswith("ASSIGNED TO"):
                tokens.append("ASSIGNED_TO")  # Use enum value internally
                remaining = remaining[len("ASSIGNED TO"):]
                matched = True
                continue
                
            if remaining.upper().startswith("ACCESS TO"):
                tokens.append("ACCESS_TO")  # Use enum value internally
                remaining = remaining[len("ACCESS TO"):]
                matched = True
                continue
            
            # Then try to match command keywords (GIVE, DENY)
            command_match = re.match(f'^({self.patterns["command"]})', remaining, re.IGNORECASE)
            if command_match:
                tokens.append(command_match.group(1).upper())
                remaining = remaining[command_match.end():]
                matched = True
                continue
            
            # Try to match access types (READ, WRITE, etc.)
            access_match = re.match(f'^({self.patterns["access_type"]})', remaining, re.IGNORECASE)
            if access_match:
                tokens.append(access_match.group(1).upper())
                remaining = remaining[access_match.end():]
                matched = True
                continue
            
            # Try to match resource types (EMAILS, PROJECTS, etc.)
            resource_match = re.match(f'^({self.patterns["resource_type"]})', remaining, re.IGNORECASE)
            if resource_match:
                tokens.append(resource_match.group(1).upper())
                remaining = remaining[resource_match.end():]
                matched = True
                continue
            
            # Try to match structural helpers (WITH, NAMED, etc.)
            helper_match = re.match(f'^({self.patterns["structural_helper"]})', remaining, re.IGNORECASE)
            if helper_match:
                # Map the display value to the enum value if needed
                helper_token = helper_match.group(1).upper()
                if helper_token == "ASSIGNED TO":
                    helper_token = "ASSIGNED_TO"
                elif helper_token == "ACCESS TO":
                    helper_token = "ACCESS_TO"
                tokens.append(helper_token)
                remaining = remaining[helper_match.end():]
                matched = True
                continue
            
            # Try to match logical operators (AND, OR)
            logical_match = re.match(f'^({self.patterns["logical_operator"]})', remaining, re.IGNORECASE)
            if logical_match:
                tokens.append(logical_match.group(1).upper())
                remaining = remaining[logical_match.end():]
                matched = True
                continue
            
            # Try to match condition operators (IS, CONTAINS, etc.)
            operator_match = re.match(f'^({self.patterns["condition_operator"]})', remaining, re.IGNORECASE)
            if operator_match:
                tokens.append(operator_match.group(1).upper())
                remaining = remaining[operator_match.end():]
                matched = True
                continue
            
            # Handle special tokens like &
            if remaining.startswith("&"):
                tokens.append("&")
                remaining = remaining[1:]
                matched = True
                continue
            
            if remaining.startswith("="):
                tokens.append("IS")  # Convert = to IS
                remaining = remaining[1:]
                matched = True
                continue
            
            # If no patterns matched, try to match a non-quoted string
            non_quoted_match = re.match(f'^{self.patterns["non_quoted_string"]}', remaining)
            if non_quoted_match:
                tokens.append(non_quoted_match.group(0))
                remaining = remaining[non_quoted_match.end():]
                matched = True
                continue
            
            # If nothing matched, just skip this character
            if not matched:
                remaining = remaining[1:]
        
        return tokens 