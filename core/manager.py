from typing import Any, Dict, List, Optional, Set
from pydantic import BaseModel, Field
import asyncio

from .context import ModuleContext, ModuleResult
from .module import Module
from .exceptions import (
    PipelineError, ModuleError, DependencyError, 
    ModuleNotFoundError, ConfigurationError,
    IdentityError, PermissionError, CredentialError, AuditError
)

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
        config: Optional[PipelineConfig] = None
    ):
        self.config = config or PipelineConfig()
        self.modules: Dict[str, Module] = {}
        self._execution_order: List[str] = []
        
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
        return self
    
    def _resolve_dependencies(self) -> List[str]:
        """Resolve module dependencies and determine execution order."""
        if not self.modules:
            return []
        
        # Map of module name to dependencies
        dependency_map: Dict[str, Set[str]] = {}
        for name, module in self.modules.items():
            dependency_map[name] = set(module.metadata.dependencies)
        
        # Resolve execution order using topological sort
        visited: Set[str] = set()
        temp_mark: Set[str] = set()
        order: List[str] = []
        
        def visit(name: str):
            if name in temp_mark:
                # Circular dependency detected
                raise DependencyError(name, list(dependency_map[name])[0])
            if name not in visited and name in dependency_map:
                temp_mark.add(name)
                for dep in dependency_map[name]:
                    if dep not in self.modules:
                        raise DependencyError(name, dep)
                    visit(dep)
                temp_mark.remove(name)
                visited.add(name)
                order.append(name)
        
        # Try to visit each module
        for name in self.modules:
            if name not in visited:
                visit(name)
        
        # Reverse the order to get dependency-first ordering
        return list(reversed(order))
    
    def _get_execution_order(self) -> List[str]:
        """Get the module execution order based on config and dependencies."""
        # If order is cached, return it
        if self._execution_order:
            return self._execution_order
        
        # Try to order by dependencies
        self._execution_order = self._resolve_dependencies()
        
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
            ModuleNotFoundError: If the module is not found
            ModuleError: If the module execution fails
        """
        if module_name not in self.modules:
            raise ModuleNotFoundError(module_name)
        
        module = self.modules[module_name]
        
        try:
            result = await module.process(context)
            return result
        except Exception as e:
            # Convert to appropriate error type
            error_msg = str(e)
            if module_name == self.IDENTITY_MODULE:
                raise IdentityError(error_msg, context)
            elif module_name == self.PERMISSIONS_MODULE:
                raise PermissionError(error_msg, context)
            elif module_name == self.CREDENTIALS_MODULE:
                raise CredentialError(error_msg, context)
            elif module_name == self.AUDIT_MODULE:
                raise AuditError(error_msg, context)
            else:
                raise ModuleError(module_name, error_msg, context)
    
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
        
        try:
            # Process each module in order
            for module_name in execution_order:
                if not self._is_module_enabled(module_name):
                    continue
                
                result = await self._process_module(module_name, context)
                
                # If module failed, let the module decide whether to continue
                # by returning success=False or raising an exception
                if not result.success:
                    # Still update context with result data
                    context = context.with_result(result)
                else:
                    # Update context with result data
                    context = context.with_result(result)
            
            return context
        except PipelineError:
            # Re-raise pipeline errors
            raise
        except Exception as e:
            # Wrap other exceptions
            raise PipelineError(str(e), context) 