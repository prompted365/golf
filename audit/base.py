from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from datetime import datetime
from .models import AuditContext, AuditRecord, AuditEventType
from ..core.exceptions import AuditError

class AuditLogger(ABC):
    """
    Base interface for all audit loggers.
    Supports span-based or log-based backends (e.g., OpenTelemetry, file, DB).
    """

    @abstractmethod
    async def start(
        self,
        run_id: str,
        identity_id: Optional[str] = None,
        resource: Optional[str] = None,
        action: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> AuditContext:
        """
        Initialize a new audit context. May start a span or trace under the hood.
        
        Parameters:
            run_id: Unique identifier for this audit session
            identity_id: Optional identity being audited
            resource: Optional resource being accessed
            action: Optional action being performed
            metadata: Optional additional metadata
            
        Returns:
            AuditContext: The initialized audit context
        """
        pass

    @abstractmethod
    async def log_event(
        self,
        context: AuditContext,
        event_type: AuditEventType,
        attributes: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Record an audit event, optionally structured (e.g., log line, span event).
        
        Parameters:
            context: The audit context this event belongs to
            event_type: Type of event from AuditEventType enum
            attributes: Optional event-specific attributes
        """
        pass

    @abstractmethod
    async def end(
        self,
        context: AuditContext,
        success: bool,
        error: Optional[str] = None,
    ) -> None:
        """
        Finalize the audit session (e.g., end span, flush logs).
        
        Parameters:
            context: The audit context to finalize
            success: Whether the operation was successful (required)
            error: Optional error message if unsuccessful
        """
        pass

    @abstractmethod
    async def query_records(self, 
                           start_time: Optional[datetime] = None, 
                           end_time: Optional[datetime] = None, 
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
            start_time: Optional start time filter
            end_time: Optional end time filter
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
    
    @abstractmethod
    async def create_record(self, 
                     resource: str,
                     action: str,
                     metadata: Optional[Dict[str, Any]] = None) -> AuditRecord:
        """
        Create a new audit record.
        
        Parameters:
            resource: The resource being accessed (required)
            action: The action being performed (required)
            metadata: Additional execution-wide metadata
            
        Returns:
            AuditRecord: A new audit record with required fields initialized
        """
        record = AuditRecord(
            started_at=datetime.now(),
            resource=resource,
            action=action,
            metadata=metadata or {}
        )
        return record