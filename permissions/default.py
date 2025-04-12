"""Default implementation of the permission system."""

from .opa import OPAPermissionEngine
from .translator import SimplePermissionTranslator
from .mapper import SimpleSchemaMapper

# Create default instances
default_engine = OPAPermissionEngine()
default_translator = SimplePermissionTranslator()
default_mapper = SimpleSchemaMapper()

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