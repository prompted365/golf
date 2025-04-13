"""Playground session for parsing and testing permission statements."""

from typing import Dict, List, Any, Optional
import json
from pydantic import BaseModel

from permissions.parser import Tokenizer, Interpreter, StatementBuilder, PermissionParser
from permissions.models import PermissionStatement, ResourceType, AccessType, BaseCommand
from permissions.parser.interpreter import SchemaProvider
from permissions.integrations import get_integration_mappings


class TokenizationResult(BaseModel):
    """Result of tokenizing a permission statement."""
    original_text: str
    tokens: List[str]


class InterpretationResult(BaseModel):
    """Result of interpreting tokenized permission statement."""
    tokens: List[str]
    parsed_data: Dict[str, Any]


class StatementResult(BaseModel):
    """Result of building a structured permission statement."""
    statement: PermissionStatement
    json_representation: Dict[str, Any]


class OpaInputResult(BaseModel):
    """OPA input representation of a permission statement."""
    input: Dict[str, Any]


class PlaygroundResult(BaseModel):
    """Full result of parsing a permission statement in the playground."""
    tokenization: Optional[TokenizationResult] = None
    interpretation: Optional[InterpretationResult] = None
    statement: Optional[StatementResult] = None
    opa_input: Optional[OpaInputResult] = None
    error: Optional[str] = None


class PlaygroundSession:
    """
    Session for parsing and testing permission statements.
    
    This class manages the state of a playground session, including the current
    permission statement, tokenization, interpretation, and OPA input generation.
    """
    
    def __init__(self):
        """Initialize a new playground session."""
        # Get all integration mappings
        all_mappings = get_integration_mappings()
        self.schema_provider = SchemaProvider(all_mappings)
        self.tokenizer = Tokenizer()
        self.interpreter = Interpreter(schema_provider=self.schema_provider)
        self.statement_builder = StatementBuilder()
        self.parser = PermissionParser(
            tokenizer=self.tokenizer,
            interpreter=self.interpreter,
            builder=self.statement_builder
        )
        
        self.last_result: Optional[PlaygroundResult] = None
        self.current_statement: Optional[str] = None
    
    def process_statement(self, statement_text: str) -> PlaygroundResult:
        """
        Process a permission statement and return the full result.
        
        Args:
            statement_text: The permission statement text to process
            
        Returns:
            PlaygroundResult: The full result of processing the statement
        """
        result = PlaygroundResult()
        self.current_statement = statement_text
        
        # Step 1: Tokenize
        try:
            tokens = self.tokenizer.tokenize(statement_text)
            result.tokenization = TokenizationResult(
                original_text=statement_text,
                tokens=tokens
            )
        except Exception as e:
            result.error = f"Tokenization error: {str(e)}"
            self.last_result = result
            return result
        
        # Step 2: Interpret
        try:
            parsed_data = self.interpreter.interpret(tokens)
            result.interpretation = InterpretationResult(
                tokens=tokens,
                parsed_data=parsed_data
            )
        except Exception as e:
            result.error = f"Interpretation error: {str(e)}"
            self.last_result = result
            return result
        
        # Step 3: Build structured statement
        try:
            statement = self.statement_builder.build(parsed_data)
            result.statement = StatementResult(
                statement=statement,
                json_representation=statement.dict()
            )
        except Exception as e:
            result.error = f"Statement building error: {str(e)}"
            self.last_result = result
            return result
        
        # Step 4: Generate OPA input
        try:
            opa_input = self._generate_opa_input(statement)
            result.opa_input = OpaInputResult(input=opa_input)
        except Exception as e:
            result.error = f"OPA input generation error: {str(e)}"
        
        self.last_result = result
        return result
    
    def _generate_opa_input(self, statement: PermissionStatement) -> Dict[str, Any]:
        """
        Generate OPA input from a permission statement.
        
        Args:
            statement: The permission statement
            
        Returns:
            Dict[str, Any]: The OPA input
        """
        # Get the first access type (usually there's only one)
        action = statement.access_types[0] if statement.access_types else AccessType.READ
        
        # Build conditions list
        conditions = []
        for condition in statement.conditions:
            conditions.append({
                "field": condition.field,
                "operator": condition.operator.value,
                "value": condition.value
            })
        
        # Create OPA input structure
        return {
            "action": action.value,
            "resource": {
                "type": statement.resource_type.value,
                "conditions": conditions
            }
        }
    
    def get_resource_fields(self, resource_type_str: str) -> Dict[str, Dict[str, Any]]:
        """
        Get all available fields for a resource type.
        
        Args:
            resource_type_str: The resource type string (e.g., "ISSUES")
            
        Returns:
            Dict[str, Dict[str, Any]]: Fields and their metadata
        """
        try:
            resource_type = ResourceType(resource_type_str.upper())
            return self.schema_provider.get_resource_fields(resource_type)
        except (ValueError, KeyError):
            # If the resource type is not valid, return empty dict
            return {}
    
    def get_example_statements(self) -> List[str]:
        """
        Get example permission statements.
        
        Returns:
            List[str]: Example permission statements
        """
        return [
            "GIVE READ ACCESS TO ISSUES",
            "GIVE READ ACCESS TO ISSUES TAGGED = urgent",
            "DENY WRITE ACCESS TO ISSUES ASSIGNED TO antoni",
            "GIVE READ ACCESS TO TEAMS WITH NAME = Engineering",
            "GIVE READ & WRITE ACCESS TO ISSUES WITH STATUS = Done",
        ] 