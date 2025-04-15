"""Authed 2.0 - Runtime access control layer for secure agent-to-agent interactions."""

# Base interfaces
from .base import (
    PermissionEngine,
    SchemaMapper,
    PermissionParser as BasePermissionParser,
    PolicyGenerator,
    BaseTokenizer, 
    BaseInterpreter, 
    BaseStatementBuilder,
    BaseSchemaProvider
)

# Models
from .models import (
    AccessRequest, 
    AccessResult, 
    AccessType, 
    ResourceType,
    Resource, 
    Condition,
    ConditionOperator,
    LogicalOperator,
    PermissionStatement, 
    RegoPolicy, 
    SchemaMapping,
    FieldPath,
    Integration,
    IntegrationResource,
    IntegrationParameter,
    DataType,
    BaseCommand
)

# Parser components
from .parser import (
    Tokenizer,
    Interpreter,
    SchemaProvider,
    StatementBuilder,
    PermissionParser
)

# Engine components
from .engine import (
    OPAClient,
    RegoGenerator
)

# Schema mapper
from .mapper import SimpleSchemaMapper

# Specification
from .spec import get_specification, get_version as get_spec_version

# Coercion engine
from .coercion_engine import CoercionEngine

# Permission middleware
from .middleware import PermissionMiddleware

__all__ = [
    # Base interfaces
    "PermissionEngine",
    "SchemaMapper",
    "BasePermissionParser",
    "PolicyGenerator",
    "BaseTokenizer",
    "BaseInterpreter",
    "BaseStatementBuilder",
    "BaseSchemaProvider",
    
    # Models
    "AccessRequest",
    "AccessResult",
    "AccessType",
    "ResourceType",
    "Resource",
    "Condition",
    "ConditionOperator",
    "LogicalOperator",
    "PermissionStatement",
    "RegoPolicy",
    "SchemaMapping",
    "FieldPath",
    "Integration",
    "IntegrationResource",
    "IntegrationParameter",
    "DataType",
    "BaseCommand",
    
    # Parser components
    "Tokenizer",
    "Interpreter",
    "SchemaProvider",
    "StatementBuilder",
    "PermissionParser",
    
    # Engine components
    "OPAClient",
    "RegoGenerator",
    
    # Schema mapper
    "SimpleSchemaMapper",
    
    # Specification
    "get_specification",
    "get_spec_version",
    
    # Coercion engine
    "CoercionEngine",
    
    # Permission middleware
    "PermissionMiddleware"
]

