"""Authed 2.0 - Runtime access control layer for secure agent-to-agent interactions."""

from .core import (
    AuthedManager, PipelineConfig, 
    Module, BaseModule, ModuleMetadata, ModuleConfig,
    ModuleContext, ModuleResult,
    AuthedError, PipelineError, ModuleError
)
from .runtime import RuntimeHandler, BaseRuntimeHandler

__version__ = "2.0.0"

__all__ = [
    # Core
    "AuthedManager",
    "PipelineConfig",
    "Module",
    "BaseModule",
    "ModuleMetadata",
    "ModuleConfig",
    "ModuleContext",
    "ModuleResult",
    "AuthedError",
    "PipelineError",
    "ModuleError",
    
    # Runtime
    "RuntimeHandler",
    "BaseRuntimeHandler"
]
