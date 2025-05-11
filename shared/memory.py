"""
Shared memory utilities for the Agent Eat Chatbot.
"""
from mem0 import Memory
from typing import List, Dict, Any, Optional
from pathlib import Path

from shared.config import get_chroma_db_path
from shared.logger import logger

def get_memory_config(collection_name="chatbot_memory"):
    """
    Get memory configuration for the chatbot.
    
    Args:
        collection_name: Name of the collection in ChromaDB
        
    Returns:
        dict: Memory configuration dictionary
    """
    return {
        "vector_store": {
            "provider": "chroma",
            "config": {
                "collection_name": collection_name,
                "path": get_chroma_db_path(),
            },
        },
    }

def create_memory(collection_name="chatbot_memory") -> Memory:
    """
    Create a memory instance.
    
    Args:
        collection_name: Name of the collection in ChromaDB
        
    Returns:
        Memory: Memory instance
    """
    config = get_memory_config(collection_name)
    logger.debug(f"Creating memory with config: {config}")
    return Memory.from_config(config)

def format_context(relevant_info) -> str:
    """
    Format relevant information into a context string.
    
    Args:
        relevant_info: List of relevant information from memory
        
    Returns:
        str: Formatted context string
    """
    if not relevant_info:
        return ""
        
    # Handle the case where relevant_info items might be strings rather than dictionaries
    return "\n".join(message if isinstance(message, str) else str(message) for message in relevant_info)

# Create a global memory instance for reuse
memory = create_memory() 