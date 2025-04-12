"""Authed 2.0 - Runtime access control layer for secure agent-to-agent interactions."""

# Base interfaces
from .base import (
    PermissionEngine,
    SchemaMapper,
    PermissionParser,
    PolicyGenerator,
    TokenizerInterface,
    InterpreterInterface,
    StatementBuilderInterface
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
    SimpleTokenizer,
    SimpleInterpreter,
    SimpleStatementBuilder,
    SimplePermissionParser
)

# Engine components
from .engine import (
    OPAClient,
    RegoPolicyGenerator
)

# Schema mapper
from .mapper import SimpleSchemaMapper

# Default instances
from .default import (
    get_default_engine,
    get_default_translator,
    get_default_mapper,
    get_default_policy_generator
)

# Specification
from .spec import get_specification, get_version as get_spec_version

__all__ = [
    # Base interfaces
    "PermissionEngine",
    "SchemaMapper",
    "PermissionParser",
    "PolicyGenerator",
    "TokenizerInterface",
    "InterpreterInterface",
    "StatementBuilderInterface",
    
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
    "SimpleTokenizer",
    "SimpleInterpreter",
    "SimpleStatementBuilder",
    "SimplePermissionParser",
    
    # Engine components
    "OPAClient",
    "RegoPolicyGenerator",
    
    # Schema mapper
    "SimpleSchemaMapper",
    
    # Default instances
    "get_default_engine",
    "get_default_translator",
    "get_default_mapper",
    "get_default_policy_generator",
    
    # Specification
    "get_specification",
    "get_spec_version"
]

