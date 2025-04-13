"""Linear integration mappings for the permissions system."""

from ..models import DataType, ResourceType, StructuralHelper, Integration, IntegrationResource, IntegrationParameter

# Linear resource definitions
LINEAR_RESOURCES = {
    # Helper mappings for structural helpers
    "_helper_mappings": {
        StructuralHelper.TAGGED.value: "labels",
        StructuralHelper.NAMED.value: "title",  # For issues, "name" maps to "title"
        StructuralHelper.ASSIGNED_TO.value: "assignee",
    },
    
    # Coercion pipelines for data types
    "_pipelines": {
        DataType.BOOLEAN.value: [
            "lowercase",
            {"map_values": {
                "true": ["true", "yes", "on", "1", "active", "enabled"],
                "false": ["false", "no", "off", "0", "inactive", "disabled"]
            }},
            {"default": False}
        ],
        DataType.TAGS.value: [
            {"split": {
                "separator": ",",
                "strip_whitespace": True
            }}
        ],
        DataType.NUMBER.value: [
            "try_int",
            "try_float"
        ],
        DataType.USER.value: [
            "lowercase"  # Convert user names to lowercase for case-insensitive comparison
        ],
        DataType.DATETIME.value: [
            # No transformation needed, handled by API response format
        ]
    },
    
    ResourceType.ISSUES.value: {
        "id": {
            "permission_field": "id",
            "data_type": DataType.STRING.value,
            "description": "Unique identifier of the issue"
        },
        "title": {
            "permission_field": "name",  # Maps to internal field "name"
            "data_type": DataType.STRING.value,
            "description": "Title of the issue"
        },
        "description": {
            "permission_field": "description",
            "data_type": DataType.STRING.value,
            "description": "Description of the issue"
        },
        "assignee": {
            "permission_field": "assignee",
            "data_type": DataType.USER.value,
            "description": "User assigned to the issue"
        },
        "labels": {
            "permission_field": "tags",  # Maps to internal field "tags"
            "data_type": DataType.TAGS.value,
            "description": "Labels/tags applied to the issue"
        },
        "status": {
            "permission_field": "status",
            "data_type": DataType.STRING.value,
            "description": "Current status of the issue"
        },
        "created_date": {
            "permission_field": "created_date",
            "data_type": DataType.DATETIME.value,
            "description": "Date when the issue was created"
        },
        "updated_date": {
            "permission_field": "updated_date",
            "data_type": DataType.DATETIME.value,
            "description": "Date when the issue was last updated"
        },
        "priority": {
            "permission_field": "priority",
            "data_type": DataType.NUMBER.value,
            "description": "Priority level of the issue"
        },
        "metadata": {
            "api_name": "Linear API",
            "api_version": "v2",
            "description": "Linear project management service"
        }
    },
    ResourceType.TEAMS.value: {
        "id": {
            "permission_field": "id",
            "data_type": DataType.STRING.value,
            "description": "Unique identifier of the team"
        },
        "name": {
            "permission_field": "name",
            "data_type": DataType.STRING.value,
            "description": "Name of the team"
        },
        "key": {
            "permission_field": "key",
            "data_type": DataType.STRING.value,
            "description": "Short key of the team"
        },
        "description": {
            "permission_field": "description",
            "data_type": DataType.STRING.value,
            "description": "Description of the team"
        },
        "owner": {
            "permission_field": "owner",
            "data_type": DataType.USER.value,
            "description": "Owner of the team"
        },
        "metadata": {
            "api_name": "Linear API",
            "api_version": "v2",
            "description": "Linear project management service - Teams"
        }
    }
}

# Create Linear integration resource objects with parameters
linear_issues_resource = IntegrationResource(
    resource_type=ResourceType.ISSUES,
    parameters=[
        IntegrationParameter(
            name="assignee",
            data_type=DataType.USER,
            description="Filter issues by assignee"
        ),
        IntegrationParameter(
            name="labels",
            data_type=DataType.TAGS,
            description="Filter issues by labels/tags"
        ),
        IntegrationParameter(
            name="status",
            data_type=DataType.STRING,
            description="Filter issues by status"
        )
    ]
)

linear_teams_resource = IntegrationResource(
    resource_type=ResourceType.TEAMS,
    parameters=[
        IntegrationParameter(
            name="owner",
            data_type=DataType.USER,
            description="Filter teams by owner"
        )
    ]
)

# Create and register the Linear integration
linear_integration = Integration(
    name="linear",
    resources=[linear_issues_resource, linear_teams_resource],
    description="Linear project management API integration"
) 