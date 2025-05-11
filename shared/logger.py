"""
Shared logging utilities for the Agent Eat Chatbot.
"""
import logging
import os
import sys
from pathlib import Path

try:
    from shared.config import get_log_level, is_debug_mode
except ImportError:
    # Fallback if config not yet available
    def get_log_level():
        return logging.INFO
    def is_debug_mode():
        return False

def setup_logger(name, level=None):
    """
    Set up a logger with consistent formatting and handlers.
    
    Args:
        name: Name of the logger
        level: Logging level (default: from environment or INFO)
        
    Returns:
        logging.Logger: Configured logger instance
    """
    # Use environment variable if level not specified
    if level is None:
        level = get_log_level()
    
    # Add more verbose logging in debug mode
    if is_debug_mode():
        level = min(level, logging.DEBUG)
    
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Clear existing handlers
    if logger.handlers:
        logger.handlers.clear()
    
    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    
    # Create formatter
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(formatter)
    
    # Add handler to logger
    logger.addHandler(console_handler)
    
    # In debug mode, add a file handler
    if is_debug_mode():
        try:
            # Create logs directory if it doesn't exist
            logs_dir = Path(__file__).parent.parent / "logs"
            logs_dir.mkdir(exist_ok=True)
            
            # Create file handler
            file_handler = logging.FileHandler(logs_dir / f"{name}.log")
            file_handler.setLevel(level)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        except Exception as e:
            # Don't fail if file logging can't be set up
            print(f"Could not set up file logging: {str(e)}")
    
    return logger

# Create default logger for imports
logger = setup_logger('agent_eat') 