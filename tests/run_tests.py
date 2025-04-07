#!/usr/bin/env python3
"""
Test runner for Authed 2.0.
"""

import pytest
import asyncio
import os
import sys

if __name__ == "__main__":
    # Add the parent directory to the path for imports
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
    
    # Run all tests in the tests directory
    pytest.main(["-xvs", os.path.dirname(__file__)]) 