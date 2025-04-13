"""Linear integration mappings for the permissions system."""

from . import register_integration
from ..models import DataType, ResourceType, StructuralHelper

# Linear resource definitions
LINEAR_RESOURCES = {
    # Helper mappings for structural helpers
    "_helper_mappings": {
        StructuralHelper.TAGGED.value: "tags",
        StructuralHelper.NAMED.value: "name",
        StructuralHelper.ASSIGNED_TO.value: "assignee",
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

# Register the Linear integration
register_integration("linear", LINEAR_RESOURCES) 