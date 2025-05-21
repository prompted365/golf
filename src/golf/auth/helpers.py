"""Helper functions for working with authentication in MCP context."""

from typing import Optional

# Re-export get_access_token from the MCP SDK
from mcp.server.auth.middleware.auth_context import get_access_token

_active_golf_oauth_provider = None

def _set_active_golf_oauth_provider(provider_instance) -> None:
    """
    Sets the active GolfOAuthProvider instance.
    Should only be called once during server startup.
    """
    global _active_golf_oauth_provider
    _active_golf_oauth_provider = provider_instance

def get_provider_token() -> Optional[str]:
    """
    Get a provider token (e.g., GitHub token) associated with the current
    MCP session's access token.

    This relies on _set_active_golf_oauth_provider being called at server startup.
    """
    mcp_access_token = get_access_token() # From MCP SDK, uses its own ContextVar
    if not mcp_access_token:
        # No active MCP session token.
        return None

    provider = _active_golf_oauth_provider
    if not provider:
        return None
    
    if not hasattr(provider, "get_provider_token"):
        return None

    # Call the get_provider_token method on the actual GolfOAuthProvider instance
    return provider.get_provider_token(mcp_access_token.token)

def extract_token_from_header(auth_header: str) -> Optional[str]:
    """Extract bearer token from Authorization header.

    Args:
        auth_header: Authorization header value

    Returns:
        Bearer token or None if not present/valid
    """
    if not auth_header:
        return None

    parts = auth_header.split()
    if len(parts) != 2 or parts[0].lower() != 'bearer':
        return None

    return parts[1] 