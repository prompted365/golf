"""Linear integration mappings for the permissions system."""

from ..models import DataType, ResourceType, StructuralHelper, Integration, IntegrationResource

# Linear resource definitions
LINEAR_RESOURCES = {
    # Helper mappings for structural helpers
    "_helper_mappings": {
        StructuralHelper.TAGGED.value: "tags",
        StructuralHelper.NAMED.value: "name",
        StructuralHelper.ASSIGNED_TO.value: "assignee",
    },
    
    # Coercion pipelines for data types
    "_pipelines": {
        DataType.BOOLEAN.value: [
            "lowercase",
            {"map_values": {
                "true": ["true", "yes", "on", "1", "active", "enabled"],
                "false": ["false", "no", "off", "0", "inactive", "disabled"]
            }}
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
        ]
    },
    
    ResourceType.ISSUES.value: {
        "id": {
            "permission_field": "id",
            "data_type": DataType.STRING.value,
            "description": "Unique identifier of the issue"
        },
        "title": {
            "permission_field": "name",
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
            "permission_field": "tags",
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
        "metadata": {
            "api_name": "Linear API",
            "api_version": "v1",
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
        "owner": {
            "permission_field": "owner",
            "data_type": DataType.USER.value,
            "description": "Owner of the team"
        },
        "metadata": {
            "api_name": "Linear API",
            "api_version": "v1",
            "description": "Linear project management service - Teams"
        }
    }
}

# Create Linear integration resource objects
linear_issues_resource = IntegrationResource(
    resource_type=ResourceType.ISSUES,
    parameters=[]  # You can add parameters if needed
)

linear_teams_resource = IntegrationResource(
    resource_type=ResourceType.TEAMS,
    parameters=[]  # You can add parameters if needed
)

# Create and register the Linear integration
linear_integration = Integration(
    name="linear",
    resources=[linear_issues_resource, linear_teams_resource],
    description="Linear project management API integration"
) 