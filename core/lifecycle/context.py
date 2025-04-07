from typing import Optional, Any, Dict
from contextlib import asynccontextmanager
from .manager import ModuleLifecycleManager

@asynccontextmanager
async def module_lifecycle(
    manager: ModuleLifecycleManager,
    module_name: str,
    module: Any,
    metadata: Optional[Dict[str, Any]] = None
):
    """
    Context manager for module lifecycle management.
    
    Usage:
        async with module_lifecycle(manager, "my_module", module_instance) as module:
            # Use the module
            await module.do_something()
    """
    try:
        await manager.start_module(module_name, module, metadata)
        yield module
        await manager.stop_module(module_name)
    except Exception as e:
        await manager.stop_module(module_name, error=e)
        raise