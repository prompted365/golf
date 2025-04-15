"""Linear integration mappings for the permissions system."""

from ..models import DataType, ResourceType, StructuralHelper, Integration, IntegrationResource, IntegrationParameter

# Linear resource definitions
LINEAR_RESOURCES = {
    # Helper mappings for structural helpers
    "_helper_mappings": {
        StructuralHelper.TAGGED.value: "labels",
        StructuralHelper.NAMED.value: "name",  # For all resources, use "name" as the common field
        StructuralHelper.ASSIGNED_TO.value: "assignee",
        StructuralHelper.FROM.value: "team",  # Team in Linear context
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
        "identifier": {
            "permission_field": "identifier",
            "data_type": DataType.STRING.value,
            "description": "Human-readable identifier (e.g., ENG-123)"
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
            "description": "Current status (state name) of the issue"
        },
        "priority": {
            "permission_field": "priority",
            "data_type": DataType.NUMBER.value,
            "description": "Priority level of the issue (0-4)"
        },
        "estimate": {
            "permission_field": "estimate",
            "data_type": DataType.NUMBER.value,
            "description": "Estimate points for the issue"
        },
        "due_date": {
            "permission_field": "due_date",
            "data_type": DataType.DATETIME.value,
            "description": "Due date of the issue"
        },
        "team": {
            "permission_field": "team",
            "data_type": DataType.STRING.value,
            "description": "Team the issue belongs to"
        },
        "project": {
            "permission_field": "project",
            "data_type": DataType.STRING.value,
            "description": "Project the issue belongs to"
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
            "api_version": "v2",
            "description": "Linear project management service - Issues"
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
            "description": "Short key of the team (e.g., ENG)"
        },
        "description": {
            "permission_field": "description",
            "data_type": DataType.STRING.value,
            "description": "Description of the team"
        },
        "color": {
            "permission_field": "color",
            "data_type": DataType.STRING.value,
            "description": "Color associated with the team"
        },
        "owner": {
            "permission_field": "owner",
            "data_type": DataType.USER.value,
            "description": "Owner (admin) of the team"
        },
        "members": {
            "permission_field": "members",
            "data_type": DataType.TAGS.value,
            "description": "List of team members"
        },
        "states": {
            "permission_field": "states",
            "data_type": DataType.TAGS.value,
            "description": "Issue states defined for this team"
        },
        "created_date": {
            "permission_field": "created_date",
            "data_type": DataType.DATETIME.value,
            "description": "Date when the team was created"
        },
        "updated_date": {
            "permission_field": "updated_date",
            "data_type": DataType.DATETIME.value,
            "description": "Date when the team was last updated"
        },
        "metadata": {
            "api_name": "Linear API",
            "api_version": "v2",
            "description": "Linear project management service - Teams"
        }
    },
    
    ResourceType.PROJECTS.value: {
        "id": {
            "permission_field": "id",
            "data_type": DataType.STRING.value,
            "description": "Unique identifier of the project"
        },
        "name": {
            "permission_field": "name",
            "data_type": DataType.STRING.value,
            "description": "Name of the project"
        },
        "description": {
            "permission_field": "description",
            "data_type": DataType.STRING.value,
            "description": "Description of the project"
        },
        "state": {
            "permission_field": "state",
            "data_type": DataType.STRING.value,
            "description": "Current state of the project"
        },
        "progress": {
            "permission_field": "progress",
            "data_type": DataType.NUMBER.value,
            "description": "Progress percentage of the project"
        },
        "team": {
            "permission_field": "team",
            "data_type": DataType.STRING.value,
            "description": "Team the project belongs to"
        },
        "members": {
            "permission_field": "members",
            "data_type": DataType.TAGS.value,
            "description": "List of project members"
        },
        "start_date": {
            "permission_field": "start_date",
            "data_type": DataType.DATETIME.value,
            "description": "Start date of the project"
        },
        "target_date": {
            "permission_field": "target_date",
            "data_type": DataType.DATETIME.value,
            "description": "Target completion date of the project"
        },
        "created_date": {
            "permission_field": "created_date",
            "data_type": DataType.DATETIME.value,
            "description": "Date when the project was created"
        },
        "updated_date": {
            "permission_field": "updated_date",
            "data_type": DataType.DATETIME.value,
            "description": "Date when the project was last updated"
        },
        "metadata": {
            "api_name": "Linear API",
            "api_version": "v2",
            "description": "Linear project management service - Projects"
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
            description="Filter issues by assignee name"
        ),
        IntegrationParameter(
            name="labels",
            data_type=DataType.TAGS,
            description="Filter issues by labels/tags"
        ),
        IntegrationParameter(
            name="status",
            data_type=DataType.STRING,
            description="Filter issues by status (state name)"
        ),
        IntegrationParameter(
            name="team",
            data_type=DataType.STRING,
            description="Filter issues by team name"
        ),
        IntegrationParameter(
            name="project",
            data_type=DataType.STRING,
            description="Filter issues by project name"
        )
    ]
)

linear_teams_resource = IntegrationResource(
    resource_type=ResourceType.TEAMS,
    parameters=[
        IntegrationParameter(
            name="owner",
            data_type=DataType.USER,
            description="Filter teams by owner (admin) name"
        ),
        IntegrationParameter(
            name="key",
            data_type=DataType.STRING,
            description="Filter teams by key (e.g., ENG)"
        )
    ]
)

linear_projects_resource = IntegrationResource(
    resource_type=ResourceType.PROJECTS,
    parameters=[
        IntegrationParameter(
            name="team_id",
            data_type=DataType.STRING,
            description="Filter projects by team ID"
        ),
        IntegrationParameter(
            name="state",
            data_type=DataType.STRING,
            description="Filter projects by state"
        )
    ]
)

# Create and register the Linear integration
linear_integration = Integration(
    name="linear",
    resources=[linear_issues_resource, linear_teams_resource, linear_projects_resource],
    description="Linear project management API integration"
) 