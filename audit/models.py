from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
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
    
    # Error events
    MODULE_ERROR = "module_error"                  # A module encountered an error
    
    # Custom events
    CUSTOM = "custom"                              # Custom event type

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

    # Identity information
    identity_id: Optional[str] = None          # AgentIdentity.id if resolved
    identity_source: Optional[str] = None      # Source of identity (e.g., "authed", "jwt")
    
    # Request information
    resource_accessed: Optional[str] = None    # e.g. "documents/123"
    action_requested: Optional[str] = None     # e.g. "read"

    # Result information
    success: Optional[bool] = None             # Was the overall execution successful?
    error_code: Optional[str] = None           # Error code, if applicable
    error_message: Optional[str] = None        # Human-readable error, if applicable
    error_module: Optional[str] = None         # Module where the error occurred

    # Module completion status
    identity_resolved: Optional[bool] = None   # Did identity resolution succeed?
    permission_checked: Optional[bool] = None  # Did permission check succeed?
    credential_resolved: Optional[bool] = None # Did credential resolution succeed?

    # Detailed events
    events: List[AuditEvent] = Field(default_factory=list)  # Batched flow events
    metadata: Dict[str, Any] = Field(default_factory=dict)  # Additional execution-wide metadata
    
    def add_event(self, event_type: str, data: Dict[str, Any]) -> None:
        """Add an event to this audit record."""
        self.events.append(AuditEvent(
            event_type=event_type,
            timestamp=datetime.utcnow(),
            data=data
        ))
        
        # Update module status based on event type
        if event_type == AuditEventType.IDENTITY_RESOLVED:
            self.identity_resolved = True
            if "identity_id" in data:
                self.identity_id = data["identity_id"]
            if "source" in data:
                self.identity_source = data["source"]
                
        elif event_type == AuditEventType.IDENTITY_VERIFICATION_FAILED:
            self.identity_resolved = False
            
        elif event_type in (AuditEventType.PERMISSION_GRANTED, AuditEventType.PERMISSION_DENIED):
            self.permission_checked = True
            if event_type == AuditEventType.PERMISSION_GRANTED:
                # This doesn't set the overall success, just the permission check
                self.metadata["permission_granted"] = True
            else:
                self.metadata["permission_granted"] = False
                
        elif event_type == AuditEventType.CREDENTIAL_RESOLVED:
            self.credential_resolved = True
            if "credential_id" in data:
                self.metadata["credential_id"] = data["credential_id"]
                
        elif event_type == AuditEventType.MODULE_ERROR:
            if "module" in data:
                self.error_module = data["module"]
            if "error_code" in data:
                self.error_code = data["error_code"]
            if "error_message" in data:
                self.error_message = data["error_message"]
    
    def complete(self, success: bool, error_code: Optional[str] = None, error_message: Optional[str] = None, error_module: Optional[str] = None) -> None:
        """Complete this audit record with success/failure information."""
        self.ended_at = datetime.utcnow()
        self.success = success
        
        if not success:
            self.error_code = error_code
            self.error_message = error_message
            self.error_module = error_module
            
        # Add a final event for the completion
        event_type = AuditEventType.REQUEST_COMPLETED
        event_data = {"success": success}
        
        if not success:
            event_data["error_code"] = error_code
            event_data["error_message"] = error_message
            event_data["error_module"] = error_module
            
        self.add_event(event_type, event_data)
    
    class Config:
        json_encoders = {
            datetime: lambda dt: dt.isoformat()
        } 