from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field

class AuditEventType(str, Enum):
    """Types of audit events that can be logged."""
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    CREDENTIAL_ACCESS = "credential_access"
    CREDENTIAL_MODIFY = "credential_modify"
    SYSTEM = "system"
    CUSTOM = "custom"

class AuditEvent(BaseModel):
    """An audit event that can be logged."""
    id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    event_type: AuditEventType
    agent_id: Optional[str] = None
    action: str
    resource: Optional[str] = None
    status: str
    details: Dict[str, Any] = Field(default_factory=dict)
    source_ip: Optional[str] = None
    user_agent: Optional[str] = None
    
    class Config:
        json_encoders = {
            datetime: lambda dt: dt.isoformat()
        } 