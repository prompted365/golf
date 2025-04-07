from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any

from ..identity.models import AgentIdentity
from .models import AuditEventType, AuditRecord

class AuditLogger(ABC):
    """Base class for audit loggers."""
    
    @abstractmethod
    async def log_record(self, record: AuditRecord) -> None:
        """
        Log a complete audit record.
        
        Parameters:
            record: The audit record to log
            
        Raises:
            AuditError: If the record cannot be logged
        """
        pass
    
    @abstractmethod
    async def query_records(self, 
                           start_time: Optional[str] = None, 
                           end_time: Optional[str] = None, 
                           run_id: Optional[str] = None,
                           identity_id: Optional[str] = None,
                           resource: Optional[str] = None,
                           action: Optional[str] = None,
                           success: Optional[bool] = None,
                           error_code: Optional[str] = None,
                           limit: int = 100,
                           offset: int = 0) -> List[AuditRecord]:
        """
        Query audit records with optional filters.
        
        Parameters:
            start_time: Optional ISO formatted start time filter
            end_time: Optional ISO formatted end time filter
            run_id: Optional run ID filter
            identity_id: Optional identity ID filter
            resource: Optional resource filter
            action: Optional action filter
            success: Optional success filter
            error_code: Optional error code filter
            limit: Maximum number of records to return
            offset: Offset for pagination
        
        Returns:
            List of audit records matching the filters
            
        Raises:
            AuditError: If the records cannot be queried
        """
        pass
    
    def create_record(self, 
                     resource_accessed: Optional[str] = None,
                     action_requested: Optional[str] = None,
                     metadata: Optional[Dict[str, Any]] = None) -> AuditRecord:
        """
        Create a new audit record.
        
        Parameters:
            resource_accessed: The resource being accessed
            action_requested: The action being performed
            metadata: Additional execution-wide metadata
            
        Returns:
            AuditRecord: A new audit record
        """
        record = AuditRecord(
            resource_accessed=resource_accessed,
            action_requested=action_requested,
            metadata=metadata or {}
        )
        return record
    
    async def log_event(self,
                        record: AuditRecord,
                        event_type: str,
                        data: Optional[Dict[str, Any]] = None,
                        **kwargs) -> None:
        """
        Log an event to the audit record.
        
        This is the primary method to add any type of event to an audit record.
        
        Parameters:
            record: The audit record to add the event to
            event_type: The type of event (can be from AuditEventType or a custom string)
            data: Event-specific data
            **kwargs: Any key-value pairs to include in the event data
        """
        # Combine data dict and kwargs
        event_data = data or {}
        event_data.update(kwargs)
        
        # Handle special fields that should also update the record
        if event_type == AuditEventType.REQUEST_STARTED:
            if "resource" in event_data and record.resource_accessed is None:
                record.resource_accessed = event_data["resource"]
            if "action" in event_data and record.action_requested is None:
                record.action_requested = event_data["action"]
            if "client_ip" in event_data and record.client_ip is None:
                record.client_ip = event_data["client_ip"]
            if "user_agent" in event_data and record.user_agent is None:
                record.user_agent = event_data["user_agent"]
        
        # Handle the identity object if provided
        if "identity" in event_data and hasattr(event_data["identity"], "id"):
            identity = event_data["identity"]
            event_data["identity_id"] = identity.id
            # Remove the full identity object to avoid serialization issues
            event_data.pop("identity", None)
        
        # Add the event to the record (which will handle module-specific data)
        record.add_event(event_type, event_data)