from typing import Dict, List, Type, Any
from pydantic import BaseModel

from core.context import ModuleContext, ModuleResult
from core.module import BaseModule, ModuleMetadata
from identity.models import AgentIdentity
from permissions.models import AccessRequest, AccessResult, Role
# Import exceptions only when needed

class MockPermissionsConfig(BaseModel):
    """Mock configuration for permissions module."""
    enabled: bool = True
    # Define permissions by roles
    role_permissions: Dict[str, List[Dict[str, str]]] = {
        "user": [
            {"resource": "api/data", "action": "read"},
            {"resource": "api/data", "action": "write"},
            {"resource": "api/external", "action": "read"}
        ],
        "admin": [
            {"resource": "api/data", "action": "read"},
            {"resource": "api/data", "action": "write"},
            {"resource": "api/data", "action": "delete"},
            {"resource": "api/admin", "action": "read"},
            {"resource": "api/admin", "action": "write"},
            {"resource": "api/admin", "action": "delete"},
            {"resource": "api/external", "action": "read"},
            {"resource": "api/external", "action": "write"}
        ]
    }

class MockPermissionsModule(BaseModule[MockPermissionsConfig]):
    """Mock implementation of permissions module for testing."""
    
    def __init__(self):
        metadata = ModuleMetadata(
            name="permissions",
            version="0.1.0",
            description="Mock permissions module for testing"
        )
        # Avoid validation issues by setting metadata and config directly
        self._metadata = metadata
        self._config = MockPermissionsConfig()
    
    @property
    def config_model(self) -> Type[MockPermissionsConfig]:
        return MockPermissionsConfig
    
    async def process(self, context: ModuleContext) -> ModuleResult:
        """Process permission checking."""
        # Import exceptions only when needed
        from core.exceptions import PermissionValidation
        
        print(f"\n[PERMISSIONS] Processing context: {context.data}")
        
        # Get request details
        request = context.request
        if not isinstance(request, dict):
            print("[PERMISSIONS] Error: Invalid request format")
            raise PermissionValidation("Invalid request format", context)
        
        resource = request.get("resource")
        action = request.get("action")
        
        if not resource or not action:
            print("[PERMISSIONS] Error: Resource and action are required")
            raise PermissionValidation("Resource and action are required", context)
        
        print(f"[PERMISSIONS] Checking access to {resource}:{action}")
        
        # Get identity results from context data
        # The identity data should be accessible through the agent_id field in context.data
        if "agent_id" not in context.data:
            print("[PERMISSIONS] Error: Identity module must be executed first")
            raise PermissionValidation("Identity module must be executed first", context)
            
        # Get the identity object from context data (should be added by identity module)
        identity = context.data.get("identity")
        if not identity:
            print("[PERMISSIONS] Error: Identity verification failed")
            raise PermissionValidation("Identity verification failed", context)
        
        print(f"[PERMISSIONS] Found identity: {identity.id} with roles: {identity.claims.get('roles', [])}")
        
        # Check if agent has permission
        has_access = False
        roles = identity.claims.get("roles", [])
        
        for role in roles:
            if role in self.config.role_permissions:
                for permission in self.config.role_permissions[role]:
                    if permission["resource"] == resource and permission["action"] == action:
                        has_access = True
                        print(f"[PERMISSIONS] Access granted via role: {role}")
                        break
        
        if not has_access:
            print(f"[PERMISSIONS] Access denied for {identity.id} to {resource}:{action}")
            raise PermissionValidation(
                f"Access denied for {identity.id} to {resource}:{action}", 
                context
            )
        
        # Return success with access details
        result = ModuleResult(
            success=True,
            data={
                "has_access": True,
                "resource": resource,
                "action": action,
                "roles": roles
            }
        )
        print(f"[PERMISSIONS] Returning result: {result}")
        return result 