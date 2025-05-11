#!/usr/bin/env python
"""
Main runner script for Agent Eat Chatbot.
This script starts the web UI which automatically connects to the backend.
"""
import os
import sys
from pathlib import Path

# Add the project root to Python path
sys.path.append(str(Path(__file__).resolve().parent))

# Import shared utilities
from shared.config import load_env

# Load environment variables
load_env()

# Start the web server
from frontend.src.server import main

if __name__ == "__main__":
    main() 