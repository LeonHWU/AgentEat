"""
Shared data models for the Agent Eat Chatbot.
"""
from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

class Role(str, Enum):
    """Possible message roles"""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"

class Message(BaseModel):
    """Chat message model"""
    role: Role
    content: str
    timestamp: Optional[int] = None
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)
    
    class Config:
        use_enum_values = True 