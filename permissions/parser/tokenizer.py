"""Tokenizer component for permission statements."""

import re
import logging
from typing import List

from ..base import BaseTokenizer
from ..models import (
    BaseCommand,
    AccessType,
    ResourceType,
    ConditionOperator,
    StructuralHelper,
    LogicalOperator
)

# Setup logging
logger = logging.getLogger(__name__)

class Tokenizer(BaseTokenizer):
    """Simple implementation of the BaseTokenizer."""
    
    # Map of special phrases to their normalized token values
    SPECIAL_PHRASES = {
        "ASSIGNED TO": "ASSIGNED_TO",
        "ACCESS TO": "ACCESS_TO"
    }
    
    # Map of standard escape sequences
    ESCAPE_SEQUENCES = {
        'n': '\n',   # newline
        't': '\t',   # tab
        'r': '\r',   # carriage return
        'b': '\b',   # backspace
        'f': '\f',   # form feed
        '\\': '\\',  # backslash
        '"': '"',    # double quote
        "'": "'"     # single quote
    }
    
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
    
    def _process_escape_sequences(self, s: str) -> str:
        """
        Process escape sequences in a string.
        
        Args:
            s: String containing escape sequences
            
        Returns:
            String with escape sequences replaced by their actual values
        """
        result = []
        i = 0
        while i < len(s):
            if s[i] == '\\' and i + 1 < len(s):
                # Handle standard escape sequences
                if s[i+1] in self.ESCAPE_SEQUENCES:
                    result.append(self.ESCAPE_SEQUENCES[s[i+1]])
                    i += 2
                # Handle hex escape sequences \xhh
                elif s[i+1] == 'x' and i + 3 < len(s) and all(c in '0123456789abcdefABCDEF' for c in s[i+2:i+4]):
                    hex_value = s[i+2:i+4]
                    result.append(chr(int(hex_value, 16)))
                    i += 4
                # Handle unicode escape sequences \uhhhh
                elif s[i+1] == 'u' and i + 5 < len(s) and all(c in '0123456789abcdefABCDEF' for c in s[i+2:i+6]):
                    unicode_value = s[i+2:i+6]
                    result.append(chr(int(unicode_value, 16)))
                    i += 6
                # Unknown escape sequence - just include the character
                else:
                    result.append(s[i+1])
                    i += 2
            else:
                result.append(s[i])
                i += 1
        return ''.join(result)
    
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
        unmatched_chars = []
        
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
                processed_content = self._process_escape_sequences(quoted_content)
                tokens.append(processed_content)
                remaining = remaining[quoted_match.end():]
                matched = True
                continue
            
            # Check for special phrases first (like "ASSIGNED TO", "ACCESS TO")
            for phrase, normalized in self.SPECIAL_PHRASES.items():
                if remaining.upper().startswith(phrase):
                    tokens.append(normalized)
                    remaining = remaining[len(phrase):]
                    matched = True
                    break
                    
            if matched:
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
                helper_token = helper_match.group(1).upper()
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
                unmatched_char = remaining[0]
                unmatched_chars.append(unmatched_char)
                remaining = remaining[1:]
        
        # If we skipped characters, log a warning
        if unmatched_chars:
            logger.warning(f"Skipped unmatched characters during tokenization: {repr(''.join(unmatched_chars))}")
        
        return tokens 