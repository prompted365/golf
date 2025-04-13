"""Integration definitions for various APIs."""

# Import integrations when they are available
# from .gmail import gmail_integration
# from .linear import linear_integration

# __all__ = [
#     "gmail_integration",
#     "linear_integration"
# ]

"""Integration mappings for the permissions system."""

from typing import Dict, Any, Optional, List, Union

# Global registry of integration mappings
_INTEGRATION_MAPPINGS: Dict[str, Dict[str, Any]] = {}

def register_integration(integration_name: str, resources: Dict[str, Any]) -> None:
    """
    Register an integration's resource mappings.
    
    Args:
        integration_name: Name of the integration (e.g., "gmail", "linear")
        resources: Dictionary mapping resource types to their field definitions
    """
    _INTEGRATION_MAPPINGS[integration_name] = resources

def get_integration_mappings() -> Dict[str, Dict[str, Any]]:
    """
    Get all registered integration mappings.
    
    Returns:
        Dict[str, Dict[str, Any]]: Dictionary mapping integration names to their resource definitions
    """
    return _INTEGRATION_MAPPINGS

def get_integration(integration_name: str) -> Optional[Dict[str, Any]]:
    """
    Get a specific integration's mappings.
    
    Args:
        integration_name: Name of the integration to get
        
    Returns:
        Optional[Dict[str, Any]]: The integration's resource definitions, or None if not found
    """
    return _INTEGRATION_MAPPINGS.get(integration_name)

def get_all_pipelines() -> Dict[str, List[Union[str, Dict[str, Any]]]]:
    """
    Get all coercion pipelines from all registered integrations.
    
    Returns:
        Dict[str, List[Union[str, Dict[str, Any]]]]: Dictionary mapping data type names 
        to their coercion pipelines
    """
    all_pipelines = {}
    
    # Collect pipelines from all integrations
    for integration_name, integration_data in _INTEGRATION_MAPPINGS.items():
        if "_pipelines" in integration_data:
            # Merge pipelines, with later integrations overriding earlier ones
            # for the same data type
            all_pipelines.update(integration_data["_pipelines"])
    
    return all_pipelines

# Import integrations modules to register them
from . import gmail, linear 