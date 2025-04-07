from typing import Dict, List, Optional, Any
from .events import ModuleState, ModuleLifecycleEvent
from audit.base import AuditLogger
from audit.models import AuditContext

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

    async def stop_module(self, module_name: str, error: Optional[str] = None) -> None:
        """Stop a module and finalize its lifecycle."""
        if module_name not in self.modules:
            raise ValueError(f"Module {module_name} is not running")

        context = self.contexts[module_name]

        try:
            # Record stopping event
            event = ModuleLifecycleEvent(
                module=module_name,
                state=ModuleState.STOPPING,
                error=error
            )
            self.events[module_name].append(event)
            await self.audit_logger.log_event(
                context,
                "module_stopping",
                {"module": module_name, "error": error}
            )

            # Clean up in reverse order of dependency
            try:
                del self.modules[module_name]
            except KeyError:
                pass  # Already removed

            try:
                del self.events[module_name]
            except KeyError:
                pass  # Already removed

            try:
                del self.contexts[module_name]
            except KeyError:
                pass  # Already removed

            # Finalize audit context
            await self.audit_logger.end(
                context,
                success=error is None,
                error=error
            )
        except Exception as e:
            # Log the cleanup error but don't re-raise to ensure cleanup continues
            await self.audit_logger.log_event(
                context,
                "module_cleanup_error",
                {"module": module_name, "error": str(e)}
            )

    def get_module_state(self, module_name: str) -> Optional[ModuleState]:
        """Get the current state of a module."""
        if module_name not in self.events or not self.events[module_name]:
            return None
        return self.events[module_name][-1].state

    def get_module_events(self, module_name: str) -> List[ModuleLifecycleEvent]:
        """Get all events for a module."""
        return self.events.get(module_name, []) 