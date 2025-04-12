"""Specification module for the permissions system."""

import os

def get_specification_path() -> str:
    """Get the path to the specification file."""
    return os.path.join(os.path.dirname(__file__), "specification.md")

def get_specification() -> str:
    """Get the content of the specification file."""
    with open(get_specification_path(), "r") as f:
        return f.read()

def get_version() -> str:
    """Get the version of the specification."""
    content = get_specification()
    for line in content.split("\n"):
        if line.startswith("**Version:**"):
            return line.replace("**Version:**", "").strip()
    return "Unknown" 