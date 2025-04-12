from typing import Dict, List, Optional, Any, Literal, NewType
from pydantic import BaseModel, Field
from enum import Enum

# Field path for accessing nested properties (e.g., "email.sender.domain")
FieldPath = NewType('FieldPath', str)

# ---------------
# Static Data Models
# ---------------

class BaseCommand(str, Enum):
    """Base commands for permission statements."""
    GIVE = "GIVE"
    DENY = "DENY"

class AccessType(str, Enum):
    """Defines the type of access being requested."""
    READ = "READ"
    WRITE = "WRITE"
    DELETE = "DELETE"

class ResourceType(str, Enum):
    """Defines the type of resource being accessed."""
    EMAILS = "EMAILS"
    ATTACHMENTS = "ATTACHMENTS"
    PROJECTS = "PROJECTS"
    ISSUES = "ISSUES"
    TEAMS = "TEAMS"
    CALENDAR = "CALENDAR"
    DOCUMENTS = "DOCUMENTS"

class ConditionOperator(str, Enum):
    """Operators for condition expressions at the field level."""
    # Equality operators
    IS = "IS"
    IS_NOT = "IS_NOT"
    CONTAINS = "CONTAINS"
    
    # Comparison operators
    GREATER_THAN = "GREATER_THAN"
    LESS_THAN = "LESS_THAN"
    GREATER_OR_EQUAL = "GREATER_OR_EQUAL"
    LESS_OR_EQUAL = "LESS_OR_EQUAL"
    BEFORE = "BEFORE"  # for datetime comparison
    AFTER = "AFTER"    # for datetime comparison

class LogicalOperator(str, Enum):
    """Logical operators for combining conditions at the statement level."""
    AND = "AND"
    OR = "OR"
    NOT = "NOT"  # Usually used in more complex expressions

class StructuralHelper(str, Enum):
    """Structural helpers for permission statements."""
    WITH = "WITH"
    NAMED = "NAMED"
    ASSIGNED_TO = "ASSIGNED_TO"  # Will be parsed as "ASSIGNED TO" in tokenizer
    ACCESS_TO = "ACCESS_TO"      # Will be parsed as "ACCESS TO" in tokenizer
    TAGGED = "TAGGED"
    FROM = "FROM"
    
    @classmethod
    def get_display_value(cls, member):
        """Get the display value for a member (with spaces where needed)."""
        if member == cls.ASSIGNED_TO:
            return "ASSIGNED TO"
        elif member == cls.ACCESS_TO:
            return "ACCESS TO"
        return member.value

class DataType(str, Enum):
    """Data types for permission values."""
    DATETIME = "datetime"
    EMAIL_ADDRESS = "email_address"
    USER = "user"
    STRING = "string"
    TAGS = "tags"
    BOOLEAN = "boolean"
    NUMBER = "number"
    DOMAIN = "domain"

# ---------------
# Dynamic Data Models
# ---------------

class Condition(BaseModel):
    """Represents a condition in a permission statement."""
    field: str                      # Field to check (e.g., "tags", "name", "assignee")
    operator: ConditionOperator     # Operator type (e.g., IS, CONTAINS)
    value: Any                      # Value to compare against
    field_type: Optional[DataType] = None  # Type of the field value

class ResourceCondition(BaseModel):
    """Represents conditions applied to a resource."""
    conditions: List[Condition] = Field(default_factory=list)
    logical_operator: Optional[LogicalOperator] = LogicalOperator.AND  # Default to AND for multiple conditions

class Resource(BaseModel):
    """Represents a resource being accessed with its conditions."""
    type: ResourceType
    conditions: ResourceCondition = Field(default_factory=ResourceCondition)
    properties: Dict[str, Any] = Field(default_factory=dict)  # Additional properties

class AccessRequest(BaseModel):
    """Represents a request to access a resource."""
    action: AccessType
    resource: Resource
    effect: Optional[Literal["ALLOW", "DENY"]] = "ALLOW"  # Default is ALLOW
    context: Dict[str, Any] = Field(default_factory=dict)  # Additional context

class AccessResult(BaseModel):
    """The result of an access check."""
    allowed: bool                   # Whether access is allowed
    reason: Optional[str] = None    # Reason for the decision

class PermissionStatement(BaseModel):
    """Represents a structured permission statement."""
    command: BaseCommand            # GIVE or DENY
    access_types: List[AccessType]   # Types of access (e.g., [READ, WRITE])
    resource_type: ResourceType     # Type of resource (e.g., EMAILS)
    conditions: List[Condition] = Field(default_factory=list)  # Conditions for the permission
    logical_operator: LogicalOperator = LogicalOperator.AND  # How conditions combine

class RegoPolicy(BaseModel):
    """Represents a Rego policy for OPA."""
    package_name: str = "authed.permissions"   # OPA package name
    policy_content: str             # Rego policy content
    metadata: Dict[str, Any] = Field(default_factory=dict)

class IntegrationParameter(BaseModel):
    """Defines a parameter for an integration resource."""
    name: str                      # Parameter name
    data_type: DataType            # Data type of the parameter
    description: Optional[str] = None  # Description of the parameter

class IntegrationResource(BaseModel):
    """Defines a resource type for an integration."""
    resource_type: ResourceType    # Type of resource
    parameters: List[IntegrationParameter] = Field(default_factory=list)  # Parameters of the resource

class Integration(BaseModel):
    """Defines an integration with its resources and parameters."""
    name: str                      # Integration name (e.g., gmail, linear)
    resources: List[IntegrationResource] = Field(default_factory=list)  # Resources provided by the integration

class SchemaMapping(BaseModel):
    """Maps external API schemas to internal resource types."""
    source_api: str                           # Name of the source API (e.g., "gmail", "jira")
    resource_type: ResourceType               # Internal resource type
    property_mappings: Dict[str, FieldPath]   # Maps internal fields to external API field paths
    transformation_rules: Optional[Dict[str, str]] = None  # Optional transformation rules 