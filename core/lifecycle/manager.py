from typing import Dict, List, Optional, Any
from .events import ModuleState, ModuleLifecycleEvent
from audit.base import AuditLogger
from audit.models import AuditContext, AuditEventType
from datetime import datetime
from ..exceptions import ModuleNotRegistered
import uuid

class ModuleLifecycleManager:
    """
    Manages the lifecycle of all modules in the system.
    Tracks state and provides access to the audit logger.
    """
    def __init__(self, audit_logger: AuditLogger):
        self.audit_logger = audit_logger
        self.modules: Dict[str, Any] = {}
        self.events: Dict[str, List[ModuleLifecycleEvent]] = {}
        self.contexts: Dict[str, AuditContext] = {}  # Store audit contexts for each module
        
    async def start_module(self, module_name: str, module: Any, metadata: Optional[Dict[str, Any]] = None) -> None:
        """Start a module and begin tracking its lifecycle."""
        if module_name in self.modules:
            raise ValueError(f"Module {module_name} is already running")

        # Initialize module tracking
        self.modules[module_name] = module
        self.events[module_name] = []

        # Record start event
        event = ModuleLifecycleEvent(
            module=module_name,
            state=ModuleState.STARTING,
            timestamp=datetime.now(),
            metadata=metadata or {}
        )
        self.events[module_name].append(event)

        # Create an audit context for this module
        run_id = str(uuid.uuid4())  # Generate a unique run ID
        context = await self.audit_logger.start(
            run_id=run_id,
            resource=module_name,
            action="module_lifecycle",
            metadata={"state": "starting", "module": module_name}
        )
        self.contexts[module_name] = context

        # Log module start event
        await self.audit_logger.log_event(
            context,
            AuditEventType.MODULE_STARTED,
            {"module": module_name, "metadata": metadata or {}}
        )

        # Update to running state
        event = ModuleLifecycleEvent(
            module=module_name,
            state=ModuleState.RUNNING,
            timestamp=datetime.now(),
            metadata=metadata or {}
        )
        self.events[module_name].append(event)

        # Log module running event
        await self.audit_logger.log_event(
            context,
            AuditEventType.MODULE_RUNNING,
            {"module": module_name, "state": "running"}
        )

    async def stop_module(self, module_name: str, error: Optional[str] = None) -> None:
        """Stop a module and record the event."""
        if module_name not in self.modules:
            raise ModuleNotRegistered(module_name)
            
        # Record stopping event
        event = ModuleLifecycleEvent(
            module=module_name,
            state=ModuleState.STOPPING,
            timestamp=datetime.now(),
            metadata={"error": error} if error else {}
        )
        self.events[module_name].append(event)
        
        # Get the audit context for this module
        context = self.contexts.get(module_name)
        if context:
            # Log module stopping event
            await self.audit_logger.log_event(
                context,
                AuditEventType.MODULE_STOPPING,
                {"module": module_name, "error": error if error else None}
            )
        
        # Record stopped event
        event = ModuleLifecycleEvent(
            module=module_name,
            state=ModuleState.STOPPED,
            timestamp=datetime.now(),
            metadata={"error": error} if error else {}
        )
        self.events[module_name].append(event)
        
        # Finalize the audit context if it exists
        if context:
            # Log module stopped event
            await self.audit_logger.log_event(
                context,
                AuditEventType.MODULE_STOPPED,
                {"module": module_name, "error": error if error else None}
            )
            
            # End the audit context
            await self.audit_logger.end(
                context,
                success=(error is None),  # Success is True if there's no error
                error=error
            )
              
        # Clean up
        if module_name in self.modules:
            del self.modules[module_name]
        if module_name in self.events:
            del self.events[module_name]
        if module_name in self.contexts:
            del self.contexts[module_name]

    def get_module_state(self, module_name: str) -> Optional[ModuleState]:
        """Get the current state of a module."""
        if module_name not in self.events or not self.events[module_name]:
            return None
        return self.events[module_name][-1].state

    def get_module_events(self, module_name: str) -> List[ModuleLifecycleEvent]:
        """Get all events for a module."""
        return self.events.get(module_name, [])

    async def get_module(self, module_name: str) -> Any:
        """Get a module by name."""
        if module_name not in self.modules:
            raise ModuleNotRegistered(module_name)
        return self.modules[module_name] 