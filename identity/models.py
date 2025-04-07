from typing import Optional, Dict, Any
from pydantic import BaseModel, Field

class AgentIdentity(BaseModel):
    """Represents an authenticated agent's identity."""
    id: str                                # Unique ID (e.g. DID, Authed ID)
    public_key: Optional[str] = None       # Used for crypto verification
    source: str = "unknown"                # e.g. 'authed', 'did:ethr', 'vc:jwt'
    claims: Dict[str, Any] = Field(default_factory=dict)  # Verified claims (e.g. roles, orgs)
    metadata: Dict[str, Any] = Field(default_factory=dict)  # Issuer, expiration, auth context 