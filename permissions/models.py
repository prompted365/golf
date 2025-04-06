from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any

@dataclass
class AccessRequest:
    """A request for access to a resource."""
    action: str                         # The action being performed (e.g., "read", "write")
    resource: str                       # The resource being accessed (e.g., "documents/123")
    context: Dict[str, Any] = field(default_factory=dict)  # Additional context for the request

@dataclass
class Role:
    """A role with associated permissions."""
    name: str                           # The name of the role (e.g., "admin", "user")
    permissions: List[str] = field(default_factory=list)  # List of permission patterns
    metadata: Dict[str, Any] = field(default_factory=dict)  # Additional metadata

@dataclass
class Permission:
    """A permission pattern."""
    pattern: str                        # The permission pattern (e.g., "documents:read:*")
    description: Optional[str] = None   # Optional description of the permission
    metadata: Dict[str, Any] = field(default_factory=dict)  # Additional metadata

@dataclass
class AccessResult:
    """The result of an access check."""
    allowed: bool                       # Whether access is allowed
    role: Optional[str] = None          # The role that granted access, if any
    permission: Optional[str] = None    # The permission that granted access, if any
    reason: Optional[str] = None        # The reason for the decision
    metadata: Dict[str, Any] = field(default_factory=dict)  # Additional metadata 