from abc import ABC, abstractmethod
from typing import Any
from .models import AgentIdentity
from ..core.exceptions import IdentityVerificationError

class IdentityResolver(ABC):
    @abstractmethod
    async def resolve(self, source: Any) -> AgentIdentity:
        """
        Resolve and verify an identity from a request or message.

        Parameters:
            source (Any): A generic object containing identity data.
                Could be:
                - an HTTP request (Starlette/FastAPI)
                - an MCP message
                - a raw token or credential

        Returns:
            AgentIdentity: A verified, normalized identity object.

        Raises:
            IdentityVerificationError: if resolution or verification fails.
        """
        ... 