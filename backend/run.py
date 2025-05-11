#!/usr/bin/env python
"""
Backend runner script for Agent Eat Chatbot.
This script starts the CLI version of the chatbot.
"""
import os
import sys
from pathlib import Path

# Add the project root to Python path
sys.path.append(str(Path(__file__).resolve().parent.parent))

# Import shared utilities
from shared.config import load_env

# Load environment variables
load_env()

# Import the backend runner
from backend.src.main import run

if __name__ == "__main__":
    run() 