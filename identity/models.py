from dataclasses import dataclass, field
from typing import Optional, Dict, Any

@dataclass
class AgentIdentity:
    id: str                                # Unique ID (e.g. DID, Authed ID)
    public_key: Optional[str] = None       # Used for crypto verification
    source: str = "unknown"                # e.g. 'authed', 'did:ethr', 'vc:jwt'
    claims: Optional[Dict[str, Any]] = field(default_factory=dict)  # Verified claims (e.g. roles, orgs)
    metadata: Optional[Dict[str, Any]] = field(default_factory=dict)  # Issuer, expiration, auth context 