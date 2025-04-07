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
    """An event in a module's lifecycle."""
    module: str
    state: ModuleState
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    metadata: Dict[str, Any] = Field(default_factory=dict)
    error: Optional[str] = None

    class Config:
        json_encoders = {
            datetime: lambda dt: dt.isoformat()
        } 