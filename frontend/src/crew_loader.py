import os
import sys
from pathlib import Path
from typing import Optional, Tuple, List, Dict, Any

from crewai.crew import Crew

# Add backend to path and import ChatbotCrew
sys.path.append(str(Path(os.getcwd())))
try:
    from backend.src.crew import ChatbotCrew
except ImportError:
    # Try relative to parent directory
    try:
        sys.path.append(str(Path(os.getcwd()).parent))
        from backend.src.crew import ChatbotCrew
    except ImportError:
        print("Error: Could not import ChatbotCrew from backend/src")
        sys.exit(1)


def load_crew_from_module(crew_path: Path = None) -> Tuple[Crew, str]:
    """
    Load the ChatbotCrew from backend/src directly.
    
    Args:
        crew_path: Path parameter (unused but kept for compatibility)
        
    Returns:
        Tuple[Crew, str]: A tuple containing the crew instance and crew name
    """
    try:
        # Create an instance of the ChatbotCrew
        crew_instance = ChatbotCrew().crew()
        crew_name = "Agent Eat"
        return crew_instance, crew_name
    except Exception as e:
        raise ValueError(f"Could not initialize ChatbotCrew: {str(e)}")


def discover_available_crews(directory: Optional[Path] = None) -> List[Dict[str, Any]]:
    """
    Returns a fixed list with only the ChatbotCrew from backend/src.
    
    Args:
        directory: Optional directory parameter (unused but kept for compatibility)
        
    Returns:
        List with a single dictionary containing crew information
    """
    # Standard path to the crew file
    crew_path = Path(os.getcwd()) / "backend" / "src" / "crew.py"
    
    return [{
        "id": "agent_eat_crew",
        "path": str(crew_path),
        "name": "Agent Eat",
        "directory": "backend"
    }]


def load_crew() -> Tuple[Crew, str]:
    """
    Load the ChatbotCrew from backend/src directly.

    Returns:
        Tuple[Crew, str]: A tuple containing the crew instance and crew name
    """
    return load_crew_from_module()
