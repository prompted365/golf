from typing import Dict, List, Optional, Any
from .events import ModuleState, ModuleLifecycleEvent
from audit.base import AuditLogger
from audit.models import AuditContext
from datetime import datetime
from ..exceptions import ModuleNotRegistered

class ModuleLifecycleManager:
    """
    Manages the lifecycle of all modules in the system.
    Tracks state and provides access to the audit logger.
    """
    def __init__(self, audit_logger: AuditLogger):
        self.audit_logger = audit_logger
        self.modules: Dict[str, Any] = {}
        self.events: Dict[str, List[ModuleLifecycleEvent]] = {}
        
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

        # Update to running state
        event = ModuleLifecycleEvent(
            module=module_name,
            state=ModuleState.RUNNING,
            timestamp=datetime.now(),
            metadata=metadata or {}
        )
        self.events[module_name].append(event)

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
        
        # Record stopped event
        event = ModuleLifecycleEvent(
            module=module_name,
            state=ModuleState.STOPPED,
            timestamp=datetime.now(),
            metadata={"error": error} if error else {}
        )
        self.events[module_name].append(event)
              
        # Clean up
        if module_name in self.modules:
            del self.modules[module_name]
        if module_name in self.events:
            del self.events[module_name]

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