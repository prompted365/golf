from typing import Optional, Dict, Any, List
from datetime import datetime, UTC
from enum import Enum
from pydantic import BaseModel, Field
import uuid

class AuditEventType(str, Enum):
    """Types of audit events that can be logged within the Authed system."""
    # Identity module events
    IDENTITY_RESOLVED = "identity_resolved"        # Successfully resolved an identity
    IDENTITY_VERIFICATION_FAILED = "identity_verification_failed"  # Failed to verify identity
    
    # Permissions module events
    PERMISSION_GRANTED = "permission_granted"      # Permission was granted
    PERMISSION_DENIED = "permission_denied"        # Permission was denied
    ROLE_ASSIGNED = "role_assigned"                # Role was assigned to an identity
    ROLE_REVOKED = "role_revoked"                  # Role was revoked from an identity
    
    # Credentials module events
    CREDENTIAL_RESOLVED = "credential_resolved"    # Credential was retrieved
    CREDENTIAL_STORED = "credential_stored"        # Credential was stored
    CREDENTIAL_REVOKED = "credential_revoked"      # Credential was revoked
    CREDENTIAL_EXPIRED = "credential_expired"      # Credential expired
    CREDENTIAL_REFRESH = "credential_refresh"      # Credential was refreshed
    
    # Pipeline events
    REQUEST_STARTED = "request_started"            # Request pipeline started
    REQUEST_COMPLETED = "request_completed"        # Request pipeline completed
    
    # Module lifecycle events
    MODULE_STARTING = "module_starting"            # Module is starting
    MODULE_STARTED = "module_started"              # Module has started
    MODULE_RUNNING = "module_running"              # Module is running
    MODULE_STOPPING = "module_stopping"            # Module is stopping
    MODULE_STOPPED = "module_stopped"              # Module has stopped
    
    # Module processing events
    MODULE_PROCESSING_START = "module_processing_start"  # Module processing is starting
    MODULE_PROCESSING_SUCCESS = "module_processing_success"  # Module processing succeeded
    
    # Error events
    MODULE_ERROR = "module_error"                  # A module encountered an error
    PIPELINE_ERROR = "pipeline_error"              # Pipeline encountered an error
    
    # Custom events
    CUSTOM = "custom"                              # Custom event type

class AuditEvent(BaseModel):
    """Represents a single audit event."""
    type: AuditEventType
    timestamp: datetime
    attributes: Dict[str, Any] = Field(default_factory=dict)
    
    model_config = {
        "json_encoders": {
            datetime: lambda dt: dt.isoformat()
        }
    }

class AuditContext(BaseModel):
    """
    Shared context object passed through the audit flow.
    Holds core metadata and optional telemetry-related state.
    """
    run_id: str
    identity_id: Optional[str] = None
    resource: Optional[str] = None
    action: Optional[str] = None
    start_time: datetime = Field(default_factory=lambda: datetime.now(UTC))
    metadata: Dict[str, Any] = Field(default_factory=dict)
    telemetry: Dict[str, Any] = Field(default_factory=dict, exclude=True)

    def set_telemetry(self, key: str, value: Any) -> None:
        self.telemetry[key] = value

    def get_telemetry(self, key: str) -> Any:
        return self.telemetry.get(key)

    def has_telemetry(self, key: str) -> bool:
        return key in self.telemetry

    class Config:
        json_encoders = {
            datetime: lambda dt: dt.isoformat()
        }

class AuditRecord(BaseModel):
    """Represents an audit record containing multiple events."""
    started_at: datetime
    ended_at: Optional[datetime] = None
    run_id: Optional[str] = None
    identity_id: Optional[str] = None
    resource: Optional[str] = None
    action: Optional[str] = None
    client_ip: Optional[str] = None
    user_agent: Optional[str] = None
    
    # Module-specific flags
    identity_resolved: Optional[bool] = None
    permission_checked: Optional[bool] = None
    credential_resolved: Optional[bool] = None
    
    # Result
    success: Optional[bool] = None
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    error_module: Optional[str] = None
    
    # Events and metadata
    events: List[AuditEvent] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    model_config = {
        "json_encoders": {
            datetime: lambda dt: dt.isoformat()
        }
    }

    def add_event(self, event_type: AuditEventType, attributes: Optional[Dict[str, Any]] = None) -> None:
        """Add an event to the record.
        
        Args:
            event_type: Type of event to add
            attributes: Optional event attributes
        """
        event = AuditEvent(
            type=event_type,
            timestamp=datetime.now(),
            attributes=attributes or {}
        )
        self.events.append(event)

    def complete(self, success: bool, error_code: Optional[str] = None, 
                error_message: Optional[str] = None, error_module: Optional[str] = None) -> None:
        """Complete this audit record with success/failure information."""
        self.ended_at = datetime.now(UTC)
        self.success = success
        
        if not success:
            self.error_code = error_code
            self.error_message = error_message
            self.error_module = error_module
            
        # Add a final event for the completion
        self.add_event(
            AuditEventType.REQUEST_COMPLETED,
            {
                "success": success,
                "error_code": error_code,
                "error_message": error_message,
                "error_module": error_module
            }
        ) 