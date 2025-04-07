from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any

from ..identity.models import AgentIdentity
from .models import AuditEvent, AuditEventType

class AuditLogger(ABC):
    """Base class for audit loggers."""
    
    @abstractmethod
    async def log_event(self, event: AuditEvent) -> None:
        """
        Log an audit event.
        
        Parameters:
            event: The audit event to log
            
        Raises:
            AuditError: If the event cannot be logged
        """
        pass
    
    @abstractmethod
    async def query_events(self, 
                          start_time: Optional[str] = None, 
                          end_time: Optional[str] = None, 
                          event_type: Optional[AuditEventType] = None,
                          agent_id: Optional[str] = None,
                          resource: Optional[str] = None,
                          action: Optional[str] = None,
                          status: Optional[str] = None,
                          limit: int = 100,
                          offset: int = 0) -> List[AuditEvent]:
        """
        Query audit events with optional filters.
        
        Parameters:
            start_time: Optional ISO formatted start time filter
            end_time: Optional ISO formatted end time filter
            event_type: Optional event type filter
            agent_id: Optional agent ID filter
            resource: Optional resource filter
            action: Optional action filter
            status: Optional status filter
            limit: Maximum number of events to return
            offset: Offset for pagination
        
        Returns:
            List of audit events matching the filters
            
        Raises:
            AuditError: If the events cannot be queried
        """
        pass
    
    async def log_authentication(self, 
                               identity: Optional[AgentIdentity], 
                               success: bool, 
                               details: Dict[str, Any] = None,
                               source_ip: Optional[str] = None,
                               user_agent: Optional[str] = None) -> None:
        """
        Log an authentication event.
        
        Parameters:
            identity: The agent identity, if authentication was successful
            success: Whether authentication was successful
            details: Additional details about the authentication
            source_ip: Source IP address
            user_agent: User agent string
            
        Raises:
            AuditError: If the event cannot be logged
        """
        from uuid import uuid4
        
        event = AuditEvent(
            id=str(uuid4()),
            event_type=AuditEventType.AUTHENTICATION,
            agent_id=identity.id if identity else None,
            action="authenticate",
            resource=None,
            status="success" if success else "failure",
            details=details or {},
            source_ip=source_ip,
            user_agent=user_agent
        )
        
        await self.log_event(event)
    
    async def log_authorization(self,
                              identity: AgentIdentity,
                              action: str,
                              resource: str,
                              success: bool,
                              details: Dict[str, Any] = None) -> None:
        """
        Log an authorization event.
        
        Parameters:
            identity: The agent identity requesting authorization
            action: The action being authorized
            resource: The resource being accessed
            success: Whether authorization was successful
            details: Additional details about the authorization
            
        Raises:
            AuditError: If the event cannot be logged
        """
        from uuid import uuid4
        
        event = AuditEvent(
            id=str(uuid4()),
            event_type=AuditEventType.AUTHORIZATION,
            agent_id=identity.id,
            action=action,
            resource=resource,
            status="success" if success else "failure",
            details=details or {}
        )
        
        await self.log_event(event)
    
    async def log_credential_access(self,
                                  identity: AgentIdentity,
                                  credential_id: str,
                                  action: str,
                                  success: bool,
                                  details: Dict[str, Any] = None) -> None:
        """
        Log a credential access event.
        
        Parameters:
            identity: The agent identity accessing the credential
            credential_id: The ID of the credential being accessed
            action: The action being performed (e.g., "retrieve", "list")
            success: Whether access was successful
            details: Additional details about the access
            
        Raises:
            AuditError: If the event cannot be logged
        """
        from uuid import uuid4
        
        event = AuditEvent(
            id=str(uuid4()),
            event_type=AuditEventType.CREDENTIAL_ACCESS,
            agent_id=identity.id,
            action=action,
            resource=f"credential:{credential_id}",
            status="success" if success else "failure",
            details=details or {}
        )
        
        await self.log_event(event)
    
    async def log_credential_modify(self,
                                  identity: AgentIdentity,
                                  credential_id: str,
                                  action: str,
                                  success: bool,
                                  details: Dict[str, Any] = None) -> None:
        """
        Log a credential modification event.
        
        Parameters:
            identity: The agent identity modifying the credential
            credential_id: The ID of the credential being modified
            action: The action being performed (e.g., "create", "update", "revoke")
            success: Whether modification was successful
            details: Additional details about the modification
            
        Raises:
            AuditError: If the event cannot be logged
        """
        from uuid import uuid4
        
        event = AuditEvent(
            id=str(uuid4()),
            event_type=AuditEventType.CREDENTIAL_MODIFY,
            agent_id=identity.id,
            action=action,
            resource=f"credential:{credential_id}",
            status="success" if success else "failure",
            details=details or {}
        )
        
        await self.log_event(event)
    
    async def log_system_event(self,
                             action: str,
                             success: bool,
                             details: Dict[str, Any] = None) -> None:
        """
        Log a system event.
        
        Parameters:
            action: The system action being performed
            success: Whether the action was successful
            details: Additional details about the system event
            
        Raises:
            AuditError: If the event cannot be logged
        """
        from uuid import uuid4
        
        event = AuditEvent(
            id=str(uuid4()),
            event_type=AuditEventType.SYSTEM,
            action=action,
            status="success" if success else "failure",
            details=details or {}
        )
        
        await self.log_event(event)
    
    async def log_custom_event(self,
                             action: str,
                             agent_id: Optional[str] = None,
                             resource: Optional[str] = None,
                             status: str = "info",
                             details: Dict[str, Any] = None) -> None:
        """
        Log a custom event.
        
        Parameters:
            action: The custom action
            agent_id: Optional agent ID related to the event
            resource: Optional resource related to the event
            status: Status of the event
            details: Additional details about the event
            
        Raises:
            AuditError: If the event cannot be logged
        """
        from uuid import uuid4
        
        event = AuditEvent(
            id=str(uuid4()),
            event_type=AuditEventType.CUSTOM,
            agent_id=agent_id,
            action=action,
            resource=resource,
            status=status,
            details=details or {}
        )
        
        await self.log_event(event) 