from typing import Dict, List, Optional, Any
import time
from pydantic import BaseModel, Field, SecretStr
from pydantic import model_validator

class Credential(BaseModel):
    """Represents a credential that can be used to access external resources."""
    id: str                                  # Unique ID for the credential
    type: str                                # Type of credential (e.g., "api_key", "oauth_token")
    value: SecretStr                         # The actual credential value/secret
    owner_id: Optional[str] = None           # ID of the owner (agent, user, or service)
    scopes: List[str] = Field(default_factory=list)  # Scopes or permissions associated with this credential
    expires_at: Optional[float] = None       # Expiration timestamp (or None if no expiration)
    created_at: float = Field(default_factory=time.time)  # Creation timestamp
    metadata: Dict[str, Any] = Field(default_factory=dict)  # Additional metadata

    def __str__(self) -> str:
        """String representation that hides sensitive data."""
        return f"Credential(id={self.id}, type={self.type}, owner_id={self.owner_id})"

    def __repr__(self) -> str:
        """Representation that hides sensitive data."""
        return f"Credential(id={self.id}, type={self.type}, owner_id={self.owner_id})"

    def dict(self, *args, **kwargs) -> Dict[str, Any]:
        """Override dict() to exclude sensitive data."""
        d = self.model_dump(*args, **kwargs)
        d['value'] = '********'  # Replace sensitive value with asterisks
        return d

    def json(self, *args, **kwargs) -> str:
        """Override json() to exclude sensitive data."""
        d = self.dict(*args, **kwargs)
        return self.model_dump_json(**kwargs)

class CredentialRequest(BaseModel):
    """Represents a request for a credential."""
    type: str                                # Type of credential requested
    resource: Optional[str] = None           # Resource to access (e.g., "github.com")
    scopes: List[str] = Field(default_factory=list)  # Requested scopes
    owner_id: Optional[str] = None           # ID of the owner
    context: Dict[str, Any] = Field(default_factory=dict)  # Additional context

class CredentialResult(BaseModel):
    """Result of a credential resolution request."""
    credential: Optional[Credential] = None  # The resolved credential (if successful)
    error: Optional[str] = None              # Error message (if unsuccessful)
    metadata: Dict[str, Any] = Field(default_factory=dict)  # Additional metadata
    
    @model_validator(mode='after')
    def validate_result(self) -> 'CredentialResult':
        """Validate that success and error are mutually exclusive."""
        if self.credential is not None and self.error is not None:
            raise ValueError("Credential result cannot have both a credential and an error")
        return self
    
    @property
    def success(self) -> bool:
        """Whether the credential resolution was successful."""
        return self.credential is not None and self.error is None 