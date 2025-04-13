#!/usr/bin/env python3
"""
Entry point for running the permissions playground.

Usage:
    python -m permissions.playground.run
"""

from permissions.playground.cli import start_cli

if __name__ == "__main__":
    start_cli() 