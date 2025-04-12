"""Engine module for evaluating permission policies."""

from .opa_client import OPAClient
from .policy_generator import RegoPolicyGenerator

__all__ = [
    "OPAClient",
    "RegoPolicyGenerator"
] 