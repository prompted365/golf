"""Authed 2.0 - Runtime access control layer for secure agent-to-agent interactions."""

# Base interfaces
from .base import PermissionEngine, PermissionTranslator, SchemaMapper, PermissionStore

# Models
from .models import (
    AccessRequest, 
    AccessResult, 
    AccessType, 
    ResourceType,
    Resource, 
    Condition, 
    PermissionStatement, 
    RegoPolicy, 
    SchemaMapping
)

# Implementations
from .opa import OPAPermissionEngine
from .translator import SimplePermissionTranslator
from .mapper import SimpleSchemaMapper

__all__ = [
    # Base interfaces
    "PermissionEngine",
    "PermissionTranslator",
    "SchemaMapper",
    "PermissionStore",
    
    # Models
    "AccessRequest",
    "AccessResult",
    "AccessType",
    "ResourceType",
    "Resource",
    "Condition",
    "PermissionStatement",
    "RegoPolicy",
    "SchemaMapping",
    
    # Implementations
    "OPAPermissionEngine",
    "SimplePermissionTranslator",
    "SimpleSchemaMapper"
]

