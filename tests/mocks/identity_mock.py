from typing import Any, Dict, Type
from pydantic import BaseModel

from core.context import ModuleContext, ModuleResult
from core.module import BaseModule, ModuleMetadata
from identity.models import AgentIdentity
# Import exceptions only when needed

class MockIdentityConfig(BaseModel):
    """Mock configuration for identity module."""
    enabled: bool = True
    valid_tokens: Dict[str, Dict[str, Any]] = {
        "valid_token": {
            "id": "agent-123",
            "public_key": "mock-key-123",
            "source": "test",
            "claims": {"roles": ["user"]},
            "metadata": {"test": True}
        },
        "admin_token": {
            "id": "agent-admin",
            "public_key": "mock-key-admin",
            "source": "test",
            "claims": {"roles": ["admin", "user"]},
            "metadata": {"test": True}
        }
    }

class MockIdentityModule(BaseModule[MockIdentityConfig]):
    """Mock implementation of identity module for testing."""
    
    def __init__(self):
        metadata = ModuleMetadata(
            name="identity",
            version="0.1.0",
            description="Mock identity module for testing"
        )
        # Avoid validation issues by setting metadata and config directly
        self._metadata = metadata
        self._config = MockIdentityConfig()
    
    @property
    def config_model(self) -> Type[MockIdentityConfig]:
        return MockIdentityConfig
    
    async def process(self, context: ModuleContext) -> ModuleResult:
        """Process identity verification."""
        # Import exceptions only when needed
        from core.exceptions import IdentityError
        
        print(f"\n[IDENTITY] Processing request: {context.request}")
        
        # Get token from request
        request = context.request
        if not isinstance(request, dict) or "token" not in request:
            print("[IDENTITY] Error: Token not provided")
            raise IdentityError("Token not provided in request", context)
        
        token = request["token"]
        print(f"[IDENTITY] Token: {token}")
        
        # Check if token is valid
        if token not in self.config.valid_tokens:
            print(f"[IDENTITY] Error: Invalid token: {token}")
            raise IdentityError(f"Invalid token: {token}", context)
        
        # Create agent identity from valid token
        agent_data = self.config.valid_tokens[token]
        agent_identity = AgentIdentity(
            id=agent_data["id"],
            public_key=agent_data["public_key"],
            source=agent_data["source"],
            claims=agent_data["claims"],
            metadata=agent_data["metadata"]
        )
        
        print(f"[IDENTITY] Created identity: {agent_identity}")
        
        # Return success with agent identity
        result = ModuleResult(
            success=True,
            data={
                "agent_id": agent_identity.id,
                "identity": agent_identity
            }
        )
        print(f"[IDENTITY] Returning result: {result}")
        return result 