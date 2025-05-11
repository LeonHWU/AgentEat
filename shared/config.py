"""
Environment and configuration utilities for the Agent Eat Chatbot.
"""
import os
import logging
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
def load_env(env_file=None):
    """
    Load environment variables from .env file.
    
    Args:
        env_file: Optional path to a specific .env file
    """
    if env_file and os.path.exists(env_file):
        load_dotenv(env_file)
    else:
        # Try different locations
        root_dir = Path(__file__).parent.parent
        
        # Root .env file is the source of truth
        env_path = root_dir / ".env"
        if env_path.exists():
            load_dotenv(env_path)
        else:
            print("Warning: No .env file found. Using default environment variables.")

# Get application root directory
def get_root_dir():
    """
    Returns the root directory of the application.
    
    Returns:
        Path: Path to the root directory
    """
    return Path(__file__).parent.parent

# Get path to data directory
def get_data_path():
    """
    Returns the path to the data directory.
    
    Returns:
        Path: Path to the data directory
    """
    data_path = os.getenv("CHROMA_DB_PATH", "data/chroma_db").split("/")[0]
    return get_root_dir() / data_path

# Get path to ChromaDB
def get_chroma_db_path():
    """
    Returns the path to the ChromaDB directory.
    
    Returns:
        str: Path to the ChromaDB directory
    """
    chroma_path = os.getenv("CHROMA_DB_PATH", "data/chroma_db")
    return str(get_root_dir() / chroma_path)

# Get OpenAI API key
def get_openai_api_key():
    """
    Returns the OpenAI API key from environment variables.
    
    Returns:
        str: OpenAI API key
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable not set")
    return api_key

# Get Groq API key (if available)
def get_groq_api_key():
    """
    Returns the Groq API key from environment variables.
    
    Returns:
        str or None: Groq API key if available, None otherwise
    """
    return os.getenv("GROQ_API_KEY")

# Get debug mode
def is_debug_mode():
    """
    Returns whether debug mode is enabled.
    
    Returns:
        bool: True if debug mode is enabled, False otherwise
    """
    return os.getenv("DEBUG", "false").lower() in ["true", "1", "yes"]

# Get log level
def get_log_level():
    """
    Returns the log level.
    
    Returns:
        int: Logging level
    """
    level = os.getenv("LOG_LEVEL", "INFO").upper()
    return getattr(logging, level, logging.INFO) 