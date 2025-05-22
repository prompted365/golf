"""Authentication module for GolfMCP servers.

This module provides a simple API for configuring OAuth authentication
for GolfMCP servers. Users can configure authentication in their pre_build.py
file without needing to understand the complexities of the MCP SDK.
"""

from typing import List, Optional, Tuple

from mcp.server.auth.settings import AuthSettings, ClientRegistrationOptions

from .provider import ProviderConfig
from .oauth import GolfOAuthProvider, create_callback_handler
from .helpers import get_access_token, get_provider_token, extract_token_from_header

class AuthConfig:
    """Configuration for OAuth authentication in GolfMCP."""
    
    def __init__(
        self,
        provider_config: ProviderConfig,
        required_scopes: List[str],
        callback_path: str = "/auth/callback",
        login_path: str = "/login",
        error_path: str = "/auth-error",
        redirect_uri: str = "http://localhost:5173/callback",
    ):
        """Initialize authentication configuration.
        
        Args:
            provider_config: Configuration for the OAuth provider
            required_scopes: Scopes required for all authenticated requests
            callback_path: Path for the OAuth callback
            login_path: Path for the login redirect
            error_path: Path for displaying authentication errors
        """
        self.provider_config = provider_config
        self.required_scopes = required_scopes
        self.callback_path = callback_path
        self.login_path = login_path
        self.error_path = error_path
        self.redirect_uri = redirect_uri
        
        # Create the OAuth provider
        self.provider = GolfOAuthProvider(provider_config)
        # Make the configured redirect URI available to the provider
        self.provider.default_redirect_uri = redirect_uri
        
        # Create auth settings for FastMCP
        self.auth_settings = AuthSettings(
            issuer_url=provider_config.issuer_url or "http://localhost:3000",
            client_registration_options=ClientRegistrationOptions(
                enabled=True,
                valid_scopes=provider_config.scopes,
                default_scopes=provider_config.scopes
            ),
            required_scopes=required_scopes or provider_config.scopes
        )

# Global state for the build process
_auth_config: Optional[AuthConfig] = None

def configure_auth(
    provider_config=None,
    provider=None,
    required_scopes: Optional[List[str]] = None,
    callback_path: str = "/auth/callback",
    redirect_uri: str = "http://localhost:5173/callback",
) -> None:
    """Configure authentication for a GolfMCP server.
    
    This function should be called in pre_build.py to set up authentication.
    
    Args:
        provider_config: Configuration for the OAuth provider (new parameter name)
        provider: Configuration for the OAuth provider (old parameter name, deprecated)
        required_scopes: Scopes required for authentication
        callback_path: Path for the OAuth callback
        redirect_uri: Redirect URI used for the default login route
        public_paths: List of paths that don't require authentication (deprecated, no longer used)
    """
    global _auth_config
    
    # Handle backward compatibility with old parameter name
    if provider_config is None and provider is not None:
        provider_config = provider
    elif provider_config is None and provider is None:
        raise ValueError("Either provider_config or provider must be provided")
    
    _auth_config = AuthConfig(
        provider_config=provider_config,
        required_scopes=required_scopes or provider_config.scopes,
        callback_path=callback_path,
        redirect_uri=redirect_uri,
    )

def get_auth_config() -> Tuple[Optional[ProviderConfig], List[str], str]:
    """Get the current authentication configuration.
    
    Returns:
        Tuple of (provider_config, required_scopes, redirect_uri)
    """
    if _auth_config:
        return (
            _auth_config.provider_config,
            _auth_config.required_scopes,
            _auth_config.redirect_uri,
        )
    return None, [], "http://localhost:5173/callback"

def create_auth_provider() -> Optional[GolfOAuthProvider]:
    """Create an OAuth provider from the configured provider settings.
    
    Returns:
        GolfOAuthProvider instance or None if not configured
    """
    if not _auth_config:
        return None
        
    return _auth_config.provider 