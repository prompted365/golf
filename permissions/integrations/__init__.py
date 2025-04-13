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