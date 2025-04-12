# Authed Permissions System

The Authed Permissions System is an extensible framework for defining, managing, and enforcing access controls using natural language-like permission statements.

## Core Features

- **User-Friendly Permission Language**: Express permissions in plain English-like syntax
- **API Integration Support**: Map permissions to various API schemas (Gmail, Linear, etc.)
- **OPA Integration**: Use Open Policy Agent as the policy engine
- **Nested Field Path Support**: Access deeply nested properties in API responses
- **Extensible Architecture**: Add new integrations or modify existing ones easily

## Quick Start

### Basic Permission Statement

```python
from permissions import SimplePermissionTranslator

translator = SimplePermissionTranslator()
statement = await translator.parse_statement("GIVE READ ACCESS TO EMAILS WITH TAGS = WORK")
```

### Policy Generation

```python
from permissions import get_default_engine, SimplePermissionTranslator

engine = get_default_engine()
translator = SimplePermissionTranslator()

statement = await translator.parse_statement("GIVE READ ACCESS TO EMAILS TAGGED = WORK")
policy = await translator.translate(statement)
policy_id = await engine.add_policy(policy)
```

### Request Authorization

```python
from permissions import get_default_engine, get_default_mapper

engine = get_default_engine()
mapper = get_default_mapper()

# Transform an external API request into our internal format
gmail_request = {
    "action": "read",
    "resource_type": "emails",
    "payload": {
        "headers": {
            "from": "john@example.com",
            "to": "mary@example.com"
        }
    },
    "labelIds": "WORK,IMPORTANT"
}

internal_request = await mapper.transform_request("gmail", gmail_request)
result = await engine.check_access(internal_request)

if result.allowed:
    print("Access granted!")
else:
    print(f"Access denied: {result.reason}")
```

## Example Permission Statements

- `GIVE READ ACCESS TO EMAILS TAGGED = WORK`
- `DENY READ ACCESS TO EMAILS FROM DOMAIN = personal.com`
- `GIVE READ & WRITE ACCESS TO PROJECTS NAMED = BACKLOG`
- `DENY READ ACCESS TO ISSUES ASSIGNED TO ANTONI AND NAMED = "Urgent Bug"`

## Architecture

The system follows a layered architecture to separate concerns:

1. **Parser Layer**: Tokenizes and interprets permission statements
2. **Schema Mapping Layer**: Maps between external APIs and internal models
3. **Policy Engine Layer**: Evaluates requests against policies using OPA

## Supported Integrations

- **Gmail**: Email access controls 
- **Linear**: Issue and team access controls

## Adding a New Integration

To add a new integration:

1. Define the integration resources and parameters
2. Create field mappings from external API to internal model
3. Register the integration with the schema mapper

```python
from permissions.models import (
    Integration, 
    IntegrationResource, 
    IntegrationParameter, 
    ResourceType, 
    DataType,
    SchemaMapping,
    FieldPath
)

# Define parameters
my_api_parameters = [
    IntegrationParameter(
        name="id",
        data_type=DataType.STRING,
        description="Resource ID"
    ),
    # ... more parameters
]

# Define resources
my_api_resources = [
    IntegrationResource(
        resource_type=ResourceType.DOCUMENTS,
        parameters=my_api_parameters
    )
]

# Create integration
my_api_integration = Integration(
    name="my_api",
    resources=my_api_resources
)

# Define schema mapping
my_api_mapping = SchemaMapping(
    source_api="my_api",
    resource_type=ResourceType.DOCUMENTS,
    property_mappings={
        "id": FieldPath("id"),
        "name": FieldPath("attributes.title"),
        "owner": FieldPath("relationships.user.data.id")
    }
)

# Register integration and mapping
mapper = get_default_mapper()
await mapper.register_integration(my_api_integration)
await mapper.add_mapping(my_api_mapping)
```

## License

See the project LICENSE file for details. 