"""Integration definitions for various APIs."""

# Import integrations when they are available
from .gmail import gmail_integration
from .linear import linear_integration

# Also expose the modules themselves
from . import gmail
from . import linear

__all__ = [
    "gmail_integration",
    "linear_integration",
    "get_integration_mappings",
    "get_all_pipelines",
    "gmail",
    "linear"
]

def get_integration_mappings():
    """
    Get a dictionary of all registered integration mappings.
    
    Returns:
        dict: A dictionary with integration names as keys and their resources as values
    """
    # Import inline to avoid circular imports
    from .gmail import GMAIL_RESOURCES
    from .linear import LINEAR_RESOURCES
    
    return {
        "gmail": GMAIL_RESOURCES,
        "linear": LINEAR_RESOURCES
    }

def get_all_pipelines():
    """
    Get all coercion pipelines from registered integrations.
    
    Returns:
        dict: A dictionary with data types as keys and their coercion pipelines as values
    """
    # Import inline to avoid circular imports
    from .gmail import GMAIL_RESOURCES
    from .linear import LINEAR_RESOURCES
    
    all_pipelines = {}
    
    # Merge pipelines from all integrations
    for resources in [GMAIL_RESOURCES, LINEAR_RESOURCES]:
        if "_pipelines" in resources:
            for data_type, pipeline in resources["_pipelines"].items():
                all_pipelines[data_type] = pipeline
    
    return all_pipelines 