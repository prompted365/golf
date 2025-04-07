from typing import Dict, List, Type, Any
from pydantic import BaseModel
import time

from core.context import ModuleContext, ModuleResult
from core.module import BaseModule, ModuleMetadata
from audit.models import AuditContext, AuditRecord
from audit.base import AuditLogger

class MockAuditLogger(AuditLogger):
    """Mock implementation of AuditLogger for testing."""
    
    def __init__(self):
        self.records: List[AuditRecord] = []
        self.events: List[Dict[str, Any]] = []
        self.contexts: Dict[str, AuditContext] = {}
    
    async def start(
        self,
        run_id: str,
        identity_id: str = None,
        resource: str = None,
        action: str = None,
        metadata: Dict[str, Any] = None,
    ) -> AuditContext:
        """Start a new audit context."""
        context = AuditContext(
            run_id=run_id,
            resource=resource,
            action=action,
            identity_id=identity_id,
            metadata=metadata or {}
        )
        self.contexts[run_id] = context
        return context
    
    async def log_event(
        self,
        context: AuditContext,
        event_type: str,
        attributes: Dict[str, Any] = None,
    ) -> None:
        """Log an audit event."""
        self.events.append({
            "run_id": context.run_id,
            "event_type": event_type,
            "attributes": attributes or {},
            "timestamp": time.time()
        })
    
    async def end(
        self,
        context: AuditContext,
        success: bool,
        error: str = None,
    ) -> None:
        """End an audit context."""
        # Get the start time - try both fields for compatibility
        start_time = getattr(context, 'started_at', None) or getattr(context, 'start_time', time.time())
        
        record = AuditRecord(
            run_id=context.run_id,
            resource=context.resource,
            action=context.action,
            identity_id=context.identity_id,
            metadata=context.metadata,
            success=success,
            error=error,
            started_at=start_time,
            ended_at=time.time()
        )
        self.records.append(record)
        
        # Clean up context
        if context.run_id in self.contexts:
            del self.contexts[context.run_id]
    
    async def query_records(self, **kwargs) -> List[AuditRecord]:
        """Query audit records."""
        # For testing, just return all records
        return self.records
    
    async def create_record(self, resource: str, action: str, metadata: Dict[str, Any] = None) -> AuditRecord:
        """Create a new audit record."""
        return await super().create_record(resource, action, metadata)

    # Add a convenience method to log errors directly without needing a context
    async def log_error(self, error_type: str, error_message: str, metadata: Dict[str, Any] = None) -> None:
        """Log an error event without requiring a context."""
        temp_context = AuditContext(
            run_id=f"error-{time.time()}",
            resource="error",
            action="error",
            metadata=metadata or {}
        )
        
        await self.log_event(
            context=temp_context,
            event_type=error_type,
            attributes={
                "error": error_message,
                "metadata": metadata or {}
            }
        )

class MockAuditConfig(BaseModel):
    """Mock configuration for audit module."""
    enabled: bool = True

class MockAuditModule(BaseModule[MockAuditConfig]):
    """Mock implementation of audit module for testing."""
    
    def __init__(self):
        metadata = ModuleMetadata(
            name="audit",
            version="0.1.0",
            description="Mock audit module for testing"
        )
        super().__init__(metadata=metadata, config=MockAuditConfig())
        self.audit_logger = MockAuditLogger()
    
    @property
    def config_model(self) -> Type[MockAuditConfig]:
        return MockAuditConfig
    
    async def process(self, context: ModuleContext) -> ModuleResult:
        """Process audit logging."""
        # Import AuditError only when needed
        from core.exceptions import AuditError
        
        print(f"\n[AUDIT] Processing context: {context.data}")
        
        # Get request details
        request = context.request
        if not isinstance(request, dict):
            print("[AUDIT] Error: Invalid request format")
            raise AuditError("Invalid request format", context)
        
        # Check if identity module was executed
        if "agent_id" not in context.data:
            print("[AUDIT] Error: Identity module must be executed first")
            raise AuditError("Identity module must be executed first", context)
        
        # Get identity from context data
        identity = context.data.get("identity")
        if not identity:
            print("[AUDIT] Error: Identity verification failed")
            raise AuditError("Identity verification failed", context)
        
        print(f"[AUDIT] Found identity: {identity.id}")
        
        # Create a complete audit trace of the pipeline execution
        audit_context = await self.audit_logger.start(
            run_id=context.run_id,  # Use the same run_id as the context for consistency
            identity_id=identity.id if identity else None,
            resource=request.get("resource") or context.metadata.get("resource"),
            action=request.get("action") or context.metadata.get("action"),
            metadata=context.data  # Pass entire context data
        )
        
        print(f"[AUDIT] Created audit context: {audit_context.run_id}")
        
        # Log information about each module that was executed
        # ModuleContext doesn't have a results attribute, so infer from context data
        if "identity" in context.data:
            await self.audit_logger.log_event(
                context=audit_context,
                event_type="IDENTITY_PROCESSED",
                attributes={
                    "success": True,
                    "module": "identity",
                    "result_keys": ["identity", "agent_id"]
                }
            )
        
        if "has_access" in context.data:
            await self.audit_logger.log_event(
                context=audit_context,
                event_type="PERMISSIONS_PROCESSED",
                attributes={
                    "success": True,
                    "module": "permissions",
                    "result_keys": ["has_access", "permissions"]
                }
            )
        
        if "credential" in context.data:
            await self.audit_logger.log_event(
                context=audit_context,
                event_type="CREDENTIALS_PROCESSED",
                attributes={
                    "success": True,
                    "module": "credentials",
                    "result_keys": ["credential", "credential_id"]
                }
            )
        
        # Log request completion
        await self.audit_logger.log_event(
            context=audit_context,
            event_type="request_processed",
            attributes={
                "resource": request.get("resource"),
                "action": request.get("action"),
                "status": "success"
            }
        )
        
        print("[AUDIT] Logged request event")
        
        # End audit context
        await self.audit_logger.end(
            context=audit_context,
            success=True
        )
        
        print("[AUDIT] Ended audit context")
        
        # Return success with audit info
        result = ModuleResult(
            success=True,
            data={
                "audit_id": audit_context.run_id,
                "recorded_at": time.time()
            }
        )
        print(f"[AUDIT] Returning result: {result}")
        return result

class AuditContext:
    """Simple audit context class for testing."""
    
    def __init__(
        self,
        run_id: str,
        identity_id: str = None,
        resource: str = None,
        action: str = None,
        metadata: Dict[str, Any] = None,
    ):
        self.run_id = run_id
        self.resource = resource
        self.action = action
        self.identity_id = identity_id
        self.metadata = metadata or {}
        self.started_at = time.time()
        self.events = []
        
    @property
    def start_time(self):
        """Alias for started_at for compatibility."""
        return self.started_at