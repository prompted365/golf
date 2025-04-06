from typing import Optional
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

class ModuleNotFoundError(AuthedError):
    """Error when a required module is not found."""
    
    def __init__(self, module_name: str):
        self.module_name = module_name
        super().__init__(f"Module {module_name} not found")

class IdentityError(ModuleError):
    """Error during identity resolution."""
    
    def __init__(self, error: str, context: Optional[ModuleContext] = None):
        super().__init__("identity", error, context)

class PermissionError(ModuleError):
    """Error during permission checking."""
    
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