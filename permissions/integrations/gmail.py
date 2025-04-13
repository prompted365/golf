"""Gmail integration mappings for the permissions system."""

from . import register_integration
from ..models import DataType, ResourceType, StructuralHelper

# Gmail resource definitions
GMAIL_RESOURCES = {
    # Helper mappings for structural helpers
    "_helper_mappings": {
        StructuralHelper.TAGGED.value: "tags",
        StructuralHelper.NAMED.value: "name",
        StructuralHelper.FROM.value: "sender",
        StructuralHelper.ASSIGNED_TO.value: "assignee",
    },
    
    # Type interpretation rules
    "_type_interpretation": {
        DataType.BOOLEAN.value: {
            "true_values": ["true", "yes", "on", "1"],
            "false_values": ["false", "no", "off", "0"]
        },
        DataType.TAGS.value: {
            "separator": ",",
            "strip_whitespace": True
        },
        DataType.EMAIL_ADDRESS.value: {
            "validation_pattern": r"^[\w\.-]+@[\w\.-]+\.\w+$"
        }
    },
    
    ResourceType.EMAILS.value: {
        "tags": {
            "permission_field": "tags",
            "data_type": DataType.TAGS.value,
            "description": "Tags/labels applied to the email"
        },
        "sender": {
            "permission_field": "sender",
            "data_type": DataType.EMAIL_ADDRESS.value,
            "description": "Email address of the sender"
        },
        "recipient": {
            "permission_field": "recipient",
            "data_type": DataType.EMAIL_ADDRESS.value,
            "description": "Email address of the recipient"
        },
        "subject": {
            "permission_field": "name",
            "data_type": DataType.STRING.value,
            "description": "Subject line of the email"
        },
        "date": {
            "permission_field": "date",
            "data_type": DataType.DATETIME.value,
            "description": "Date the email was received"
        },
        "attachments": {
            "permission_field": "has_attachments",
            "data_type": DataType.BOOLEAN.value,
            "description": "Whether the email has attachments"
        },
        "sender_domain": {
            "permission_field": "domain",
            "data_type": DataType.DOMAIN.value,
            "description": "Domain of the sender's email address"
        },
        "metadata": {
            "api_name": "Gmail API",
            "api_version": "v1",
            "description": "Google Mail service"
        }
    },
    ResourceType.ATTACHMENTS.value: {
        "name": {
            "permission_field": "name",
            "data_type": DataType.STRING.value,
            "description": "Filename of the attachment"
        },
        "size": {
            "permission_field": "size",
            "data_type": DataType.NUMBER.value,
            "description": "Size of the attachment in bytes"
        },
        "mime_type": {
            "permission_field": "type",
            "data_type": DataType.STRING.value,
            "description": "MIME type of the attachment"
        },
        "metadata": {
            "api_name": "Gmail API",
            "api_version": "v1",
            "description": "Google Mail service - Attachments"
        }
    }
}

# Register the Gmail integration
register_integration("gmail", GMAIL_RESOURCES) 