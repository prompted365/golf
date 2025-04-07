from typing import Dict, List, Optional, Any
from .events import ModuleState, ModuleLifecycleEvent
from audit.base import AuditLogger
from audit.models import AuditContext
from datetime import datetime

class ModuleLifecycleManager:
    """
    Manages the lifecycle of all modules in the system.
    Tracks state and integrates with the audit system.
    """
    def __init__(self, audit_logger: AuditLogger):
        self.audit_logger = audit_logger
        self.modules: Dict[str, Any] = {}
        self.events: Dict[str, List[ModuleLifecycleEvent]] = {}
        self.contexts: Dict[str, AuditContext] = {}

    async def start_module(self, module_name: str, module: Any, metadata: Optional[Dict[str, Any]] = None) -> None:
        """Start a module and begin tracking its lifecycle."""
        if module_name in self.modules:
            raise ValueError(f"Module {module_name} is already running")

        try:
            # Start audit context
            context = await self.audit_logger.start(
                run_id=f"module-{module_name}",
                resource=f"module/{module_name}",
                action="start",
                metadata=metadata or {}
            )
            self.contexts[module_name] = context

            # Initialize module tracking
            self.modules[module_name] = module
            self.events[module_name] = []

            try:
                # Record start event
                event = ModuleLifecycleEvent(
                    module=module_name,
                    state=ModuleState.STARTING,
                    metadata=metadata or {}
                )
                self.events[module_name].append(event)
                await self.audit_logger.log_event(
                    context,
                    "module_starting",
                    {"module": module_name, "metadata": metadata or {}}
                )

                # Update to running state
                event = ModuleLifecycleEvent(
                    module=module_name,
                    state=ModuleState.RUNNING,
                    metadata=metadata or {}
                )
                self.events[module_name].append(event)
                await self.audit_logger.log_event(
                    context,
                    "module_running",
                    {"module": module_name, "metadata": metadata or {}}
                )
            except Exception as e:
                # Clean up on event logging failure
                await self.stop_module(module_name, f"Failed to log module events: {str(e)}")
                raise
        except Exception as e:
            # Clean up on any failure
            if module_name in self.modules:
                del self.modules[module_name]
            if module_name in self.events:
                del self.events[module_name]
            if module_name in self.contexts:
                del self.contexts[module_name]
            raise RuntimeError(f"Failed to start module {module_name}: {str(e)}")

    async def stop_module(self, module_name: str, error: Optional[str] = None) -> None:
        """Stop a module and record the event."""
        if module_name not in self.contexts:
            raise ModuleNotFoundError(module_name)
            
        context = self.contexts[module_name]
        
        # Record stopping event
        event = ModuleLifecycleEvent(
            module=module_name,
            state=ModuleState.STOPPING,
            timestamp=datetime.now(),
            metadata={"error": error} if error else None
        )
        self.events[module_name].append(event)
        
        # Record stopped event
        event = ModuleLifecycleEvent(
            module=module_name,
            state=ModuleState.STOPPED,
            timestamp=datetime.now(),
            metadata={"error": error} if error else None
        )
        self.events[module_name].append(event)
        
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