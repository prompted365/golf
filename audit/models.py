from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
import uuid

class AuditEventType(str, Enum):
    """Types of audit events that can be logged."""
    IDENTITY_RESOLVED = "identity_resolved"
    ACCESS_CHECKED = "access_checked"
    CREDENTIAL_RESOLVED = "credential_resolved"
    CREDENTIAL_STORED = "credential_stored"
    CREDENTIAL_REVOKED = "credential_revoked"
    SYSTEM = "system"
    CUSTOM = "custom"

class AuditEvent(BaseModel):
    """An audit event that occurs during a pipeline execution."""
    event_type: str  # Can be from AuditEventType or a custom string
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    data: Dict[str, Any] = Field(default_factory=dict)  # Event-specific payload/details
    
    class Config:
        json_encoders = {
            datetime: lambda dt: dt.isoformat()
        }

class AuditRecord(BaseModel):
    """A complete audit record for an entire execution pipeline."""
    run_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    started_at: datetime = Field(default_factory=datetime.utcnow)
    ended_at: Optional[datetime] = None

    identity_id: Optional[str] = None          # AgentIdentity.id if resolved
    resource_accessed: Optional[str] = None    # e.g. "documents/123"
    action_requested: Optional[str] = None     # e.g. "read"

    success: Optional[bool] = None             # Was the overall execution successful?
    error_code: Optional[str] = None           # Error code, if applicable
    error_message: Optional[str] = None        # Human-readable error, if applicable

    events: List[AuditEvent] = Field(default_factory=list)  # Batched flow events
    metadata: Dict[str, Any] = Field(default_factory=dict)  # Additional execution-wide metadata
    
    def add_event(self, event_type: str, data: Dict[str, Any]) -> None:
        """Add an event to this audit record."""
        self.events.append(AuditEvent(
            event_type=event_type,
            timestamp=datetime.utcnow(),
            data=data
        ))
    
    def complete(self, success: bool, error_code: Optional[str] = None, error_message: Optional[str] = None) -> None:
        """Complete this audit record with success/failure information."""
        self.ended_at = datetime.utcnow()
        self.success = success
        self.error_code = error_code
        self.error_message = error_message
    
    class Config:
        json_encoders = {
            datetime: lambda dt: dt.isoformat()
        } 