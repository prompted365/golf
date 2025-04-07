from typing import List, Optional, Protocol, runtime_checkable, Type, TypeVar, Generic
from pydantic import BaseModel, Field
from .context import ModuleContext, ModuleResult

T = TypeVar('T', bound=BaseModel)

class ModuleMetadata(BaseModel):
    """Metadata for a module."""
    name: str
    version: str = "0.1.0"
    description: Optional[str] = None
    dependencies: List[str] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)

class BaseModuleConfig(BaseModel):
    """Base configuration for a module."""
    enabled: bool = True
    # The module should define its own config class extending this

@runtime_checkable
class Module(Protocol[T]):
    """Protocol defining the interface for a module."""
    
    @property
    def metadata(self) -> ModuleMetadata:
        """Get module metadata."""
        ...
    
    async def process(self, context: ModuleContext) -> ModuleResult:
        """Process the context and return a result."""
        ...
    
    def configure(self, config: T) -> None:
        """Configure the module with settings.
        
        Args:
            config: Module-specific configuration object
            
        Raises:
            ValidationError: If the config fails validation
        """
        ...
    
    @property
    def config_model(self) -> Type[T]:
        """Get the configuration model class for this module."""
        ...

class BaseModule(Generic[T], Module[T]):
    """Base implementation of a module."""
    
    def __init__(
        self, 
        *,
        metadata: Optional[ModuleMetadata] = None, 
        config: Optional[T] = None
    ):
        """Initialize the module.
        
        Args:
            metadata: Optional module metadata
            config: Optional module configuration. Must be of type T.
            
        Raises:
            TypeError: If config is not of the expected type T
            ValidationError: If config fails validation
        """
        self._metadata = metadata or self._get_default_metadata()
        if config is not None:
            # Validate config type and content
            if not isinstance(config, self.config_model):
                raise TypeError(f"Expected {self.config_model.__name__}, got {type(config).__name__}")
            # Let Pydantic validate the config
            self.config_model.model_validate(config.model_dump())
        self._config = config or self._get_default_config()
    
    @property
    def metadata(self) -> ModuleMetadata:
        """Get module metadata."""
        return self._metadata
    
    @property
    def config(self) -> T:
        """Get the current configuration."""
        return self._config
    
    @property
    def config_model(self) -> Type[T]:
        """Get the configuration model class for this module."""
        raise NotImplementedError("Subclasses must implement config_model property")
    
    def _get_default_metadata(self) -> ModuleMetadata:
        """Get default metadata for this module."""
        return ModuleMetadata(
            name=self.__class__.__name__,
            description=self.__class__.__doc__ or "No description"
        )
    
    def _get_default_config(self) -> T:
        """Get default configuration for this module.
        
        Returns:
            A new instance of the config model with default values
            
        Raises:
            ValidationError: If the default config fails validation
        """
        try:
            return self.config_model()
        except Exception as e:
            raise ValueError(f"Failed to create default config: {str(e)}") from e
    
    def configure(self, config: T) -> None:
        """Configure the module with settings.
        
        Args:
            config: Module-specific configuration object
            
        Raises:
            TypeError: If config is not of the expected type T
            ValidationError: If config fails validation
        """
        if not isinstance(config, self.config_model):
            raise TypeError(f"Expected {self.config_model.__name__}, got {type(config).__name__}")
        # Let Pydantic validate the config
        self.config_model.model_validate(config.model_dump())
        self._config = config
    
    async def process(self, context: ModuleContext) -> ModuleResult:
        """Process the context and return a result.
        
        This method should be overridden by subclasses.
        """
        raise NotImplementedError("Subclasses must implement process()") 