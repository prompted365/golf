"""Authed 2.0 - Runtime access control layer for secure agent-to-agent interactions."""

from .core import (
    AuthedManager, PipelineConfig, 
    Module, BaseModule, ModuleMetadata, BaseModuleConfig,
    ModuleContext, ModuleResult,
    AuthedError, PipelineError, ModuleError
)
from .runtime import RuntimeHandler, BaseRuntimeHandler
from .identity import IdentityResolver, AgentIdentity
from .permissions import PermissionStore
from .credentials import CredentialResolver, Credential
from .audit import AuditLogger, AuditEvent, AuditEventType

__version__ = "2.0.0"

__all__ = [
    # Core
    "AuthedManager",
    "PipelineConfig",
    "Module",
    "BaseModule",
    "ModuleMetadata",
    "BaseModuleConfig",
    "ModuleContext",
    "ModuleResult",
    "AuthedError",
    "PipelineError",
    "ModuleError",
    
    # Runtime
    "RuntimeHandler",
    "BaseRuntimeHandler",
    
    # Identity
    "IdentityResolver",
    "AgentIdentity",
    
    # Permissions
    "PermissionStore",
    
    # Credentials
    "CredentialResolver",
    "Credential",
    
    # Audit
    "AuditLogger",
    "AuditEvent",
    "AuditEventType"
]
