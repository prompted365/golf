from typing import Any, Dict, List, Optional
from pydantic import BaseModel
from contextlib import contextmanager

from .context import ModuleContext, ModuleResult
from .module import Module
from .exceptions import (
    PipelineError, ModuleError,
    ModuleNotRegistered, ConfigurationError,
    IdentityError, PermissionValidation, CredentialError, AuditError,
    ShutdownError
)
from .lifecycle import ModuleLifecycleManager, ModuleState, ModuleLifecycleEvent
from audit.base import AuditLogger

class PipelineConfig(BaseModel):
    """Configuration for the authentication pipeline."""
    identity: bool = True
    permissions: bool = True
    credentials: bool = True
    audit: bool = True

class AuthedManager:
    """Orchestrates the authentication and authorization pipeline."""
    
    # Standard module names
    IDENTITY_MODULE = "identity"
    PERMISSIONS_MODULE = "permissions"
    CREDENTIALS_MODULE = "credentials"
    AUDIT_MODULE = "audit"
    
    # Standard execution order
    DEFAULT_EXECUTION_ORDER = [
        IDENTITY_MODULE,
        PERMISSIONS_MODULE,
        CREDENTIALS_MODULE,
        AUDIT_MODULE
    ]
    
    def __init__(
        self,
        *,
        config: Optional[PipelineConfig] = None,
        audit_logger: Optional[AuditLogger] = None
    ):
        self.config = config or PipelineConfig()
        self.modules: Dict[str, Module] = {}
        self._execution_order: List[str] = []
        self.lifecycle_manager = ModuleLifecycleManager(audit_logger or AuditLogger())
        
    def register_module(self, module: Module) -> "AuthedManager":
        """Register a module with the manager.
        
        Args:
            module: The module to register
            
        Returns:
            Self for chaining
            
        Raises:
            ConfigurationError: If a module with the same name is already registered
        """
        if module.metadata.name in self.modules:
            raise ConfigurationError(f"Module {module.metadata.name} is already registered")
        
        self.modules[module.metadata.name] = module
        self._execution_order = []  # Invalidate cached execution order
        return self
    
    async def start(self) -> None:
        """Start all registered modules in dependency order."""
        execution_order = self._get_execution_order()
        
        for module_name in execution_order:
            if not self._is_module_enabled(module_name):
                continue
                
            module: Module = self.modules[module_name]
            await self.lifecycle_manager.start_module(
                module_name=module_name,
                module=module
            )
    
    async def stop(self) -> None:
        """Stop all modules in reverse dependency order."""
        execution_order = self._get_execution_order()
        errors = []
        
        for module_name in reversed(execution_order):
            if not self._is_module_enabled(module_name):
                continue
                
            try:
                await self.lifecycle_manager.stop_module(module_name)
            except Exception as e:
                errors.append((module_name, str(e)))
                await self.lifecycle_manager.audit_logger.log_event(
                    self.lifecycle_manager.contexts.get(module_name),
                    "module_stop_error",
                    {"module": module_name, "error": str(e)}
                )
        
        if errors:
            raise ShutdownError(errors)
    
    def is_module_running(self, module_name: str) -> bool:
        """Check if a module is currently running.
        
        Args:
            module_name: Name of the module to check
            
        Returns:
            True if the module is running, False otherwise
        """
        state = self.lifecycle_manager.get_module_state(module_name)
        return state == ModuleState.RUNNING
    
    def get_module_events(self, module_name: str) -> List[ModuleLifecycleEvent]:
        """Get lifecycle events for a module.
        
        Args:
            module_name: Name of the module
            
        Returns:
            List of lifecycle events for the module
        """
        return self.lifecycle_manager.get_module_events(module_name)
    
    def _get_execution_order(self) -> List[str]:
        """Get the module execution order based on config and dependencies."""
        # If order is cached, return it
        if self._execution_order:
            return self._execution_order
        
        # If no modules, use default order with enabled modules
        if not self._execution_order:
            self._execution_order = [
                m for m in self.DEFAULT_EXECUTION_ORDER
                if m in self.modules and self._is_module_enabled(m)
            ]
            
        return self._execution_order
    
    def _is_module_enabled(self, module_name: str) -> bool:
        """Check if a module is enabled based on configuration."""
        if module_name == self.IDENTITY_MODULE:
            return self.config.identity
        elif module_name == self.PERMISSIONS_MODULE:
            return self.config.permissions
        elif module_name == self.CREDENTIALS_MODULE:
            return self.config.credentials
        elif module_name == self.AUDIT_MODULE:
            return self.config.audit
        # For custom modules, assume enabled
        return True
    
    async def _process_module(
        self,
        module_name: str,
        context: ModuleContext
    ) -> ModuleResult:
        """Process a single module.
        
        Args:
            module_name: Name of the module to process
            context: Current context
            
        Returns:
            Module result
            
        Raises:
            ModuleNotRegistered: If the module is not registered
            ModuleError: If the module execution fails
        """
        if module_name not in self.modules:
            raise ModuleNotRegistered(module_name)
        
        if not self.is_module_running(module_name):
            raise ModuleError(module_name, "Module is not running", context)
        
        module = self.modules[module_name]
        
        try:
            result = await module.process(context)
            return result
        except Exception as e:
            # Convert to appropriate error type with exception chaining
            error_msg = str(e)
            if module_name == self.IDENTITY_MODULE:
                raise IdentityError(error_msg, context) from e
            elif module_name == self.PERMISSIONS_MODULE:
                raise PermissionValidation(error_msg, context) from e
            elif module_name == self.CREDENTIALS_MODULE:
                raise CredentialError(error_msg, context) from e
            elif module_name == self.AUDIT_MODULE:
                raise AuditError(error_msg, context) from e
            else:
                raise ModuleError(module_name, error_msg, context) from e
    
    async def process_request(self, request: Any) -> ModuleContext:
        """Process a request through the authentication pipeline.
        
        Args:
            request: The incoming request object
            
        Returns:
            The final context after processing
            
        Raises:
            PipelineError: If any stage of the pipeline fails
        """
        # Initialize context
        context = ModuleContext(request=request)
        
        # Get execution order
        execution_order = self._get_execution_order()
        
        # Store basic request info in context metadata for audit module to use later
        if isinstance(request, dict):
            context.metadata["resource"] = request.get("resource")
            context.metadata["action"] = request.get("action")
            context.metadata["request_type"] = "dict"
        else:
            context.metadata["request_type"] = type(request).__name__
        
        try:
            # Process each module in order
            for module_name in execution_order:
                if not self._is_module_enabled(module_name):
                    continue
                
                try:
                    # Process the module
                    result = await self._process_module(module_name, context)
                    
                    # Update context with result data
                    context = context.with_result(result)
                    
                except Exception as e:
                    # Re-raise the exception for normal error handling
                    raise
            
            return context
            
        except PipelineError as e:
            # Re-raise pipeline errors
            raise
            
        except Exception as e:
            # Wrap other exceptions
            raise PipelineError(str(e), context) 