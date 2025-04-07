from typing import Optional, List, Tuple
from .context import ModuleContext

class AuthedError(Exception):
    """Base exception for all Authed errors."""
    pass

class PipelineError(AuthedError):
    """Error during pipeline execution."""
    
    def __init__(self, message: str, context: Optional[ModuleContext] = None):
        self.context = context
        super().__init__(message)

class ModuleError(PipelineError):
    """Error during module execution."""
    
    def __init__(self, module_name: str, error: str, context: Optional[ModuleContext] = None):
        self.module_name = module_name
        self.error = error
        super().__init__(f"Error in module {module_name}: {error}", context)

class ConfigurationError(AuthedError):
    """Error during configuration."""
    pass

class DependencyError(AuthedError):
    """Error during dependency resolution."""
    
    def __init__(self, module: str, dependency: str):
        self.module = module
        self.dependency = dependency
        super().__init__(f"Module {module} depends on {dependency}, but it is not available")

class ModuleNotRegisteredError(AuthedError):
    """Error when a required module is not registered."""
    
    def __init__(self, module_name: str):
        self.module_name = module_name
        super().__init__(f"Module {module_name} is not registered")

class IdentityError(ModuleError):
    """Error during identity resolution."""
    
    def __init__(self, error: str, context: Optional[ModuleContext] = None):
        super().__init__("identity", error, context)

class PermissionValidationError(ModuleError):
    """Raised when permission validation fails."""
    def __init__(self, error: str, context: Optional[ModuleContext] = None):
        super().__init__("permissions", error, context)

class CredentialError(ModuleError):
    """Error during credential resolution."""
    
    def __init__(self, error: str, context: Optional[ModuleContext] = None):
        super().__init__("credentials", error, context)

class AuditError(ModuleError):
    """Error during audit logging."""
    
    def __init__(self, error: str, context: Optional[ModuleContext] = None):
        super().__init__("audit", error, context)

class ShutdownError(AuthedError):
    """Error during module shutdown."""
    
    def __init__(self, errors: List[Tuple[str, str]], context: Optional[ModuleContext] = None):
        self.errors = errors
        self.context = context
        error_msg = "\n".join(f"Failed to stop {name}: {error}" for name, error in errors)
        super().__init__(error_msg) 