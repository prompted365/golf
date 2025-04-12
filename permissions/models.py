from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field
from enum import Enum

class AccessType(str, Enum):
    """Defines the type of access being requested."""
    READ = "READ"
    WRITE = "WRITE"
    DELETE = "DELETE"
    EXECUTE = "EXECUTE"

class ResourceType(str, Enum):
    """Defines the type of resource being accessed."""
    EMAILS = "EMAILS"
    PROJECTS = "PROJECTS"
    ISSUES = "ISSUES"
    CALENDAR = "CALENDAR"
    DOCUMENTS = "DOCUMENTS"
    # Can be extended as needed

class Condition(BaseModel):
    """Represents a condition in a permission statement."""
    field: str                       # The field to check (e.g., "tags", "name", "assignee")
    operator: str                    # The operator (e.g., "=", "in", ">", "<")
    value: Any                       # The value to compare against

class PermissionStatement(BaseModel):
    """Represents a user-friendly permission statement."""
    access_type: List[AccessType]    # Types of access (e.g., [READ, WRITE])
    resource_type: ResourceType      # Type of resource (e.g., EMAILS)
    conditions: List[Condition] = Field(default_factory=list)  # Conditions for the permission

class Resource(BaseModel):
    """Represents a resource being accessed."""
    type: ResourceType
    properties: Dict[str, Any] = Field(default_factory=dict)  # Resource properties (e.g., tags, name)

class AccessRequest(BaseModel):
    """Represents a request to access a resource."""
    action: AccessType
    resource: Resource
    context: Dict[str, Any] = Field(default_factory=dict)  # Additional context

class AccessResult(BaseModel):
    """The result of an access check."""
    allowed: bool                              # Whether access is allowed
    reason: Optional[str] = None               # Reason for the decision
    
class RegoPolicy(BaseModel):
    """Represents a Rego policy for OPA."""
    package_name: str = "authed.permissions"   # OPA package name
    policy_content: str                        # Rego policy content
    metadata: Dict[str, Any] = Field(default_factory=dict)

class SchemaMapping(BaseModel):
    """Maps external API schemas to internal resource types."""
    source_api: str                            # Name of the source API (e.g., "gmail", "jira")
    resource_type: ResourceType                # Internal resource type
    property_mappings: Dict[str, str]          # Maps API fields to internal properties
    transformation_rules: Optional[Dict[str, str]] = None  # Optional transformation rules 