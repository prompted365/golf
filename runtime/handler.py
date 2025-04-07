from typing import Any, Protocol, runtime_checkable
from ..core import AuthedManager, ModuleContext

@runtime_checkable
class RuntimeHandler(Protocol):
    """Protocol for runtime-specific request handlers."""
    
    async def __call__(self, request: Any) -> Any:
        """Process a request through the Authed pipeline."""
        ...

class BaseRuntimeHandler:
    """Base implementation of a runtime handler."""
    
    def __init__(self, manager: AuthedManager):
        self.manager = manager
    
    async def __call__(self, request: Any) -> ModuleContext:
        """Process a request through the Authed pipeline.
        
        Args:
            request: The incoming request object
            
        Returns:
            The processed context
        """
        return await self.manager.process_request(request) 