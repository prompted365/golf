from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any

@dataclass
class AccessRequest:
    """Represents a request to access a specific resource."""
    action: str                               # e.g. 'read', 'write', 'delete'
    resource: str                             # e.g. 'documents/123'
    context: Dict[str, Any] = field(default_factory=dict)  # e.g. {'tenant': 'abc', 'env': 'prod'}
    scope: Optional[str] = None               # Optional scope identifier

@dataclass
class PermissionRule:
    """Defines a permission rule that can be checked against access requests."""
    action: str                               # e.g. 'documents:read', 'users:invite'
    resource_pattern: str                     # e.g. 'documents/*', 'users/*'
    conditions: Optional[Dict[str, Any]] = None  # ABAC-style conditions (optional)
    description: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class Role:
    """Groups multiple permission rules under a named identity."""
    name: str
    rules: List[PermissionRule] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class AccessResult:
    """The result of an access check."""
    allowed: bool                             # Final access decision
    matched_role: Optional[str] = None        # Role that granted access (if any)
    matched_rule: Optional[PermissionRule] = None  # Permission rule that matched (if any)
    reason: Optional[str] = None              # The reason for the decision
    metadata: Dict[str, Any] = field(default_factory=lambda: {
        "policy_version": None,               # Version or hash of policy/rules evaluated
        "request_id": None,                   # Unique identifier of the request (for tracing)
    }) 