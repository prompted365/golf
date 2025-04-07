from datetime import datetime, UTC
from enum import Enum
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field

class ModuleState(str, Enum):
    """Possible states for a module's lifecycle."""
    INITIALIZED = "initialized"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    STOPPED = "stopped"
    ERROR = "error"

class ModuleLifecycleEvent(BaseModel):
    """Represents a lifecycle event for a module."""
    module: str
    state: ModuleState
    timestamp: datetime
    metadata: Dict[str, Any] = Field(default_factory=dict)
    error: Optional[str] = None
    
    model_config = {
        "json_encoders": {
            datetime: lambda dt: dt.isoformat()
        }
    }