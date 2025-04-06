from typing import Any, Dict, List, Optional, TypeVar, Generic
from pydantic import BaseModel, Field
import uuid

class ModuleResult(BaseModel):
    """Result of module processing."""
    success: bool = True
    data: Dict[str, Any] = Field(default_factory=dict)
    error: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    @classmethod
    def success_result(cls, data: Dict[str, Any] = None, metadata: Dict[str, Any] = None) -> "ModuleResult":
        """Create a successful result."""
        return cls(
            success=True,
            data=data or {},
            metadata=metadata or {}
        )
    
    @classmethod
    def error_result(cls, error: str, metadata: Dict[str, Any] = None) -> "ModuleResult":
        """Create an error result."""
        return cls(
            success=False,
            error=error,
            metadata=metadata or {}
        )

class ModuleContext(BaseModel):
    """Context passed to modules."""
    request: Any
    run_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    runtime_type: str = "generic"
    data: Dict[str, Any] = Field(default_factory=dict)
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get a value from the context data."""
        return self.data.get(key, default)
    
    def with_data(self, **kwargs) -> "ModuleContext":
        """Create a new context with updated data."""
        new_data = self.data.copy()
        new_data.update(kwargs)
        return self.model_copy(update={"data": new_data})
    
    def with_result(self, result: ModuleResult) -> "ModuleContext":
        """Create a new context with data from a module result."""
        if not result.success:
            return self
        new_data = self.data.copy()
        new_data.update(result.data)
        return self.model_copy(update={"data": new_data})
    
    # Type-specific convenience methods
    def get_identity(self) -> Optional[Dict[str, Any]]:
        """Get identity data from context."""
        return self.get("identity")
    
    def get_permissions(self) -> Optional[Dict[str, Any]]:
        """Get permissions data from context."""
        return self.get("permissions")
    
    def get_credentials(self) -> Optional[Dict[str, Any]]:
        """Get credentials data from context."""
        return self.get("credentials") 