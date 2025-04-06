from typing import Any, Dict, List, Optional, Protocol, runtime_checkable
from pydantic import BaseModel, Field
from .context import ModuleContext, ModuleResult

class ModuleMetadata(BaseModel):
    """Metadata for a module."""
    name: str
    version: str = "0.1.0"
    description: Optional[str] = None
    dependencies: List[str] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)

class ModuleConfig(BaseModel):
    """Base configuration for a module."""
    enabled: bool = True

@runtime_checkable
class Module(Protocol):
    """Protocol defining the interface for a module."""
    
    @property
    def metadata(self) -> ModuleMetadata:
        """Get module metadata."""
        ...
    
    async def process(self, context: ModuleContext) -> ModuleResult:
        """Process the context and return a result."""
        ...
    
    def configure(self, config: Dict[str, Any]) -> None:
        """Configure the module with settings."""
        ...

class BaseModule:
    """Base implementation of a module."""
    
    def __init__(self, metadata: Optional[ModuleMetadata] = None, config: Optional[Dict[str, Any]] = None):
        self._metadata = metadata or self._get_default_metadata()
        self._config = {}
        if config:
            self.configure(config)
    
    @property
    def metadata(self) -> ModuleMetadata:
        """Get module metadata."""
        return self._metadata
    
    def _get_default_metadata(self) -> ModuleMetadata:
        """Get default metadata for this module."""
        return ModuleMetadata(
            name=self.__class__.__name__,
            description=self.__class__.__doc__ or "No description"
        )
    
    def configure(self, config: Dict[str, Any]) -> None:
        """Configure the module with settings."""
        self._config.update(config)
    
    async def process(self, context: ModuleContext) -> ModuleResult:
        """Process the context and return a result."""
        raise NotImplementedError("Subclasses must implement process()") 