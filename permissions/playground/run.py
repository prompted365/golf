#!/usr/bin/env python3
"""
Entry point for running the permissions playground.

Usage:
    python permissions/playground/run.py
"""

import sys
import os

# Add the parent directory to sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from permissions.playground.cli import start_cli

if __name__ == "__main__":
    start_cli() 