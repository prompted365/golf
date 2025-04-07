from typing import Dict, List, Optional, Any
import time
from pydantic import BaseModel, Field

class Credential(BaseModel):
    """Represents a credential that can be used to access external resources."""
    id: str                                  # Unique ID for the credential
    type: str                                # Type of credential (e.g., "api_key", "oauth_token")
    value: str                               # The actual credential value/secret
    owner_id: Optional[str] = None           # ID of the owner (agent, user, or service)
    scopes: List[str] = Field(default_factory=list)  # Scopes or permissions associated with this credential
    expires_at: Optional[float] = None       # Expiration timestamp (or None if no expiration)
    created_at: float = Field(default_factory=time.time)  # Creation timestamp
    metadata: Dict[str, Any] = Field(default_factory=dict)  # Additional metadata


class CredentialRequest(BaseModel):
    """Represents a request for a credential."""
    type: str                                # Type of credential requested
    resource: Optional[str] = None           # Resource to access (e.g., "github.com")
    scopes: List[str] = Field(default_factory=list)  # Requested scopes
    owner_id: Optional[str] = None           # ID of the owner
    context: Dict[str, Any] = Field(default_factory=dict)  # Additional context

class CredentialResult(BaseModel):
    """Result of a credential resolution request."""
    success: bool                            # Whether the resolution was successful
    credential: Optional[Credential] = None  # The resolved credential (if successful)
    error: Optional[str] = None              # Error message (if unsuccessful)
    metadata: Dict[str, Any] = Field(default_factory=dict)  # Additional metadata 