"""Main parser component that combines tokenizer, interpreter, and builder."""

from typing import Optional

from ..base import PermissionParser, TokenizerInterface, InterpreterInterface, StatementBuilderInterface
from ..models import PermissionStatement
from .tokenizer import SimpleTokenizer
from .interpreter import SimpleInterpreter
from .builder import SimpleStatementBuilder

class SimplePermissionParser(PermissionParser):
    """Simple implementation of the PermissionParser interface."""
    
    def __init__(
        self,
        tokenizer: Optional[TokenizerInterface] = None,
        interpreter: Optional[InterpreterInterface] = None,
        builder: Optional[StatementBuilderInterface] = None
    ):
        """
        Initialize the permission parser with optional components.
        
        Args:
            tokenizer: The tokenizer to use (defaults to SimpleTokenizer)
            interpreter: The interpreter to use (defaults to SimpleInterpreter)
            builder: The statement builder to use (defaults to SimpleStatementBuilder)
        """
        self.tokenizer = tokenizer or SimpleTokenizer()
        self.interpreter = interpreter or SimpleInterpreter()
        self.builder = builder or SimpleStatementBuilder()
    
    async def parse_statement(self, statement_text: str) -> PermissionStatement:
        """
        Parse a permission statement from text.
        
        Args:
            statement_text: The text to parse
            
        Returns:
            PermissionStatement: The parsed permission statement
        """
        # Tokenize the statement
        tokens = self.tokenizer.tokenize(statement_text)
        
        # Interpret the tokens
        interpreted_data = self.interpreter.interpret(tokens)
        
        # Build the statement
        return self.builder.build(interpreted_data) 