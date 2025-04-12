"""Default implementation of the permission system."""

from .engine.opa_client import OPAClient
from .engine.policy_generator import RegoGenerator
from .parser.parser import PermissionParser
from .mapper import SimpleSchemaMapper

# Create default instances
default_engine = OPAClient()
default_translator = PermissionParser()
default_mapper = SimpleSchemaMapper()
default_policy_generator = RegoGenerator()

# Function to get default engine
def get_default_engine():
    """Get the default permission engine."""
    return default_engine

# Function to get default translator
def get_default_translator():
    """Get the default permission translator."""
    return default_translator

# Function to get default mapper
def get_default_mapper():
    """Get the default schema mapper."""
    return default_mapper

# Function to get default policy generator
def get_default_policy_generator():
    """Get the default policy generator."""
    return default_policy_generator