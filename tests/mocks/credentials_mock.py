from typing import Dict, List, Type, Optional, Any
from pydantic import BaseModel, SecretStr

from core.context import ModuleContext, ModuleResult
from core.module import BaseModule, ModuleMetadata
from identity.models import AgentIdentity
from credentials.models import Credential, CredentialRequest, CredentialResult
from core.exceptions import CredentialError

class MockCredentialsConfig(BaseModel):
    """Mock configuration for credentials module."""
    enabled: bool = True
    # Define available credentials
    available_credentials: Dict[str, Dict[str, Any]] = {
        "api_key": {
            "id": "cred-api-123",
            "type": "api_key",
            "value": "test-api-key-12345",
            "scopes": ["read", "write"]
        },
        "oauth_token": {
            "id": "cred-oauth-456",
            "type": "oauth_token",
            "value": "test-oauth-token-67890",
            "scopes": ["read", "write", "delete"]
        }
    }

class MockCredentialsModule(BaseModule[MockCredentialsConfig]):
    """Mock implementation of credentials module for testing."""
    
    def __init__(self):
        metadata = ModuleMetadata(
            name="credentials",
            version="0.1.0",
            description="Mock credentials module for testing"
        )
        self._metadata = metadata
        self._config = MockCredentialsConfig()
    
    @property
    def config_model(self) -> Type[MockCredentialsConfig]:
        return MockCredentialsConfig
    
    async def process(self, context: ModuleContext) -> ModuleResult:
        """Process credential resolution."""
        # Import AuditError only when needed
        from core.exceptions import CredentialError
        
        print(f"\n[CREDENTIALS] Processing context: {context.data}")
        
        # Get request details
        request = context.request
        if not isinstance(request, dict):
            print("[CREDENTIALS] Error: Invalid request format")
            raise CredentialError("Invalid request format", context)
        
        # Get credential type from request or use default
        credential_type = request.get("credential_type", "api_key")
        print(f"[CREDENTIALS] Requested credential type: {credential_type}")
        
        # Get identity from context data
        identity = context.data.get("identity")
        if not identity:
            print("[CREDENTIALS] Error: Identity verification failed")
            raise CredentialError("Identity verification failed", context)
        
        print(f"[CREDENTIALS] Identity found: {identity.id}")
        
        # Check if permissions have been processed
        if "has_access" not in context.data:
            print("[CREDENTIALS] Error: Permissions module must be executed first")
            raise CredentialError("Permissions module must be executed first", context)
        
        # Ensure access was granted
        if not context.data.get("has_access"):
            print("[CREDENTIALS] Error: Permission check failed")
            raise CredentialError("Permission check failed", context)
        
        print("[CREDENTIALS] Permission check passed")
        
        # Check if requested credential is available
        if credential_type not in self.config.available_credentials:
            print(f"[CREDENTIALS] Error: No credential found for type: {credential_type}")
            raise CredentialError(f"No credential found for type: {credential_type}", context)
        
        # Get credential data
        cred_data = self.config.available_credentials[credential_type]
        
        # Create credential
        credential = Credential(
            id=cred_data["id"],
            type=cred_data["type"],
            value=SecretStr(cred_data["value"]),
            scopes=cred_data["scopes"],
            owner_id=identity.id
        )
        
        print(f"[CREDENTIALS] Created credential: {credential.id} (type: {credential.type})")
        
        # Return success with credential
        result = ModuleResult(
            success=True,
            data={
                "credential": credential,
                "credential_id": credential.id,
                "credential_type": credential.type
            }
        )
        print(f"[CREDENTIALS] Returning result: {result}")
        return result 