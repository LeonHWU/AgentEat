import json
import logging
import os
import sys
from pathlib import Path
import threading
import time
from typing import Dict, Optional, List

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse, FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
import click
import socket

# Add project root to sys.path
sys.path.append(str(Path(__file__).parent.parent.parent))

# Import shared utilities
from shared.config import load_env

# Import local modules
from frontend.src.crew_loader import (
    load_crew,
    load_crew_from_module,
    discover_available_crews,
)
from frontend.src.chat_handler import ChatHandler

# Load environment variables
load_env()

# Configure logging
logging.basicConfig(
    level=logging.WARNING, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

# Suppress Werkzeug logging
log = logging.getLogger("werkzeug")
log.setLevel(logging.ERROR)

# Create FastAPI app
app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Get the directory containing the built React app
ui_dir = Path(__file__).parent / "ui" / "build" / "client"

# Mount the static files from the React build
# Add error handling for the static files mounting
assets_dir = ui_dir / "assets"
try:
    if not assets_dir.exists():
        os.makedirs(assets_dir, exist_ok=True)
        logging.warning(f"Created missing assets directory: {assets_dir}")
    app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="assets")
except Exception as e:
    logging.error(f"Error mounting static files: {str(e)}")
    # Continue without static files, the app will still work but without styles

# Global state
chat_handler = None
chat_handlers: Dict[str, ChatHandler] = {}
chat_threads: Dict[str, Dict[str, List]] = {}
discovered_crews: List[Dict] = []


# Pydantic models for request/response validation
class ChatMessage(BaseModel):
    message: str
    crew_id: Optional[str] = None
    chat_id: Optional[str] = None


class InitializeRequest(BaseModel):
    crew_id: Optional[str] = None
    chat_id: Optional[str] = None


@app.post("/api/chat")
async def chat(message: ChatMessage) -> JSONResponse:
    """API endpoint to handle chat messages."""
    global chat_handler

    user_message = message.message
    crew_id = message.crew_id
    chat_id = message.chat_id
    logging.debug(f"Received chat message for chat_id: {chat_id}, crew_id: {crew_id}")

    if not user_message:
        logging.warning("No message provided in request")
        raise HTTPException(status_code=400, detail="No message provided")

    try:
        # If no chat_id is provided, we can't properly track the thread
        if not chat_id:
            raise HTTPException(
                status_code=400,
                detail="No chat ID provided. Unable to track conversation thread.",
            )

        # If a specific crew_id is provided, use that chat handler
        if crew_id and crew_id in chat_handlers:
            handler = chat_handlers[crew_id]
            # Update the global chat handler to track the currently active one
            chat_handler = handler
        elif chat_handler is None:
            raise HTTPException(
                status_code=400,
                detail="No crew has been initialized. Please select a crew first.",
            )

        # Always store messages in the appropriate chat thread
        # Initialize the thread if it doesn't exist
        if chat_id not in chat_threads:
            chat_threads[chat_id] = {"crew_id": crew_id, "messages": []}
            logging.debug(f"Created new chat thread for chat_id: {chat_id}")

        # Add user message to the thread
        chat_threads[chat_id]["messages"].append(
            {"role": "user", "content": user_message}
        )
        logging.debug(
            f"Added user message to chat_id: {chat_id}, message count: {len(chat_threads[chat_id]['messages'])}"
        )

        # Always restore the conversation history for this thread
        if hasattr(chat_handler, "messages"):
            # Save the current thread first if it exists and is different
            current_thread = getattr(chat_handler, "current_chat_id", None)
            if (
                current_thread
                and current_thread != chat_id
                and hasattr(chat_handler, "messages")
            ):
                # Create a deep copy of the messages to avoid reference issues
                chat_threads[current_thread] = {
                    "crew_id": (
                        crew_id
                        if crew_id
                        else getattr(chat_handler, "crew_name", "default")
                    ),
                    "messages": (
                        chat_handler.messages.copy()
                        if isinstance(chat_handler.messages, list)
                        else []
                    ),
                }
                logging.debug(
                    f"Saved {len(chat_handler.messages)} messages from previous thread: {current_thread}"
                )

            # Restore the thread we're working with - create a deep copy to avoid reference issues
            if chat_id in chat_threads:
                chat_handler.messages = (
                    chat_threads[chat_id]["messages"].copy()
                    if isinstance(chat_threads[chat_id]["messages"], list)
                    else []
                )
                # Mark the current thread
                chat_handler.current_chat_id = chat_id
                logging.debug(
                    f"Restored {len(chat_handler.messages)} messages for chat_id: {chat_id}"
                )

        logging.debug(f"Processing message with chat_handler for chat_id: {chat_id}")
        response = chat_handler.process_message(user_message)

        # Ensure we have content in the response
        if not response.get("content") and response.get("status") == "success":
            logging.warning("Response content is empty despite successful status")
            response["content"] = (
                "I'm sorry, but I couldn't generate a response. Please try again."
            )

        # Always add the response to the chat thread if it's valid
        if response.get("status") == "success" and response.get("content"):
            # Add the assistant response to the chat thread
            chat_threads[chat_id]["messages"].append(
                {"role": "assistant", "content": response["content"]}
            )

            # Ensure chat_handler.messages is synchronized with chat_threads
            # This is critical to ensure messages are preserved correctly
            if hasattr(chat_handler, "messages"):
                # Synchronize the chat handler's messages with the thread
                chat_handler.messages = chat_threads[chat_id]["messages"].copy()

            logging.debug(
                f"Added assistant response to chat_id: {chat_id}, message count: {len(chat_threads[chat_id]['messages'])}"
            )

        # Always include the chat_id in the response to ensure proper thread tracking
        response["chat_id"] = chat_id
        response["crew_id"] = (
            crew_id if crew_id else getattr(chat_handler, "crew_name", "default")
        )
        logging.debug(
            f"Sending response for chat_id: {chat_id}, crew_id: {response['crew_id']}"
        )

        return JSONResponse(content=response)
    except Exception as e:
        error_message = f"Error processing chat message: {str(e)}"
        logging.error(error_message, exc_info=True)
        raise HTTPException(status_code=500, detail=error_message)


@app.post("/api/initialize")
@app.get("/api/initialize")
async def initialize(request: InitializeRequest = None) -> JSONResponse:
    """Initialize the chat handler and return initial message."""
    global chat_handler

    # Handle both GET and POST requests
    chat_id = None
    if request:
        chat_id = request.chat_id

    logging.debug(f"Initializing chat with chat_id: {chat_id}")

    try:
        # We're only using the single pre-initialized ChatbotCrew
        if not chat_handler:
            crew_instance, crew_name = load_crew()
            chat_handler = ChatHandler(crew_instance, crew_name)
            # Add this to chat_handlers
            crew_id = discovered_crews[0]["id"]
            chat_handlers[crew_id] = chat_handler

        # Initialize the chat handler
        initial_message = chat_handler.initialize()

        # If a chat_id is provided, associate it with this chat handler
        if chat_id:
            # Set the current chat ID for this handler
            chat_handler.current_chat_id = chat_id

            # If this chat thread already exists, restore its messages
            if chat_id in chat_threads:
                # Create a deep copy of the messages to avoid reference issues
                chat_handler.messages = (
                    chat_threads[chat_id]["messages"].copy()
                    if isinstance(chat_threads[chat_id]["messages"], list)
                    else []
                )
                logging.debug(
                    f"Restored {len(chat_handler.messages)} messages for chat_id: {chat_id}"
                )
            else:
                # Initialize a new chat thread
                chat_threads[chat_id] = {"crew_id": discovered_crews[0]["id"], "messages": []}
                chat_handler.messages = []
                logging.debug(f"Created new chat thread for chat_id: {chat_id}")

        return JSONResponse(
            content={
                "status": "success",
                "message": initial_message,
                "required_inputs": [
                    {"name": field.name, "description": field.description}
                    for field in chat_handler.crew_chat_inputs.inputs
                ],
                "crew_id": discovered_crews[0]["id"],
                "crew_name": chat_handler.crew_name,
                "crew_description": chat_handler.crew_chat_inputs.crew_description,
                "chat_id": chat_id,
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/crews")
async def get_available_crews() -> JSONResponse:
    """Get a list of all available crews."""
    return JSONResponse(content={"status": "success", "crews": discovered_crews})


@app.get("/{full_path:path}")
async def serve_react_app(full_path: str):
    """Serve the React application and handle client-side routing."""
    # Check if the path points to an existing file in the build directory
    requested_file = ui_dir / full_path
    
    # Try to serve the requested file if it exists
    if requested_file.exists() and requested_file.is_file():
        return FileResponse(requested_file)
    
    # Always fallback to index.html for client-side routing
    index_path = ui_dir / "index.html"
    if index_path.exists():
        return FileResponse(index_path)
    
    # If index.html doesn't exist yet, return a basic HTML page
    # This is useful during development or when the UI hasn't been built
    fallback_html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Agent Eat Chatbot</title>
        <style>
            body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 2rem; }
            h1 { color: #333; }
            .message { background: #f0f0f0; padding: 1rem; border-radius: 4px; margin-bottom: 1rem; }
            .error { background: #fff0f0; color: #c00; }
        </style>
    </head>
    <body>
        <h1>Agent Eat Chatbot</h1>
        <div class="message">
            <p>The UI assets have not been built yet. You can build them by running:</p>
            <pre>cd src/crewai_chat_ui/ui && npm install && npm run build</pre>
        </div>
        <div class="message">
            <p>Or you can use the API directly at:</p>
            <ul>
                <li><a href="/api/crews">/api/crews</a> - List available crews</li>
                <li><a href="/api/initialize">/api/initialize</a> - Initialize a chat session</li>
            </ul>
        </div>
    </body>
    </html>
    """
    return HTMLResponse(content=fallback_html)


def show_loading(stop_event, message):
    """Display animated loading dots while processing."""
    counter = 0
    while not stop_event.is_set():
        dots = "." * (counter % 4)
        click.echo(f"\r{message}{dots.ljust(3)}", nl=False)
        counter += 1
        threading.Event().wait(0.5)
    click.echo()  # Final newline


def find_available_port(start_port: int = 8000, max_attempts: int = 100) -> int:
    """Find the next available port starting from start_port."""
    for port in range(start_port, start_port + max_attempts):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(("", port))
                return port
        except OSError:
            continue
    raise RuntimeError(
        f"Could not find an available port after {max_attempts} attempts"
    )


def main():
    """Start the web server."""
    # Get the single ChatbotCrew from backend/src
    global discovered_crews, chat_handler
    try:
        discovered_crews = discover_available_crews()
        
        # Pre-initialize the crew for faster startup
        crew_instance, crew_name = load_crew()
        chat_handler = ChatHandler(crew_instance, crew_name)
        
        # Add ID to the chat handler for tracking
        crew_id = discovered_crews[0]["id"]
        chat_handlers[crew_id] = chat_handler
        
        print(f"Successfully loaded Agent Eat chatbot crew.")
    except Exception as e:
        logging.error(f"Error initializing chatbot: {str(e)}")
        print(f"Error initializing chatbot: {str(e)}")
        sys.exit(1)

    # Find an available port
    port = find_available_port(start_port=8000)
    
    print(f"\nStarting Agent Eat Chatbot server on http://localhost:{port}")
    print("Press Ctrl+C to stop the server")
    
    try:
        # Start uvicorn server
        uvicorn.run(app, host="0.0.0.0", port=port)
    except KeyboardInterrupt:
        print("\nShutting down server...")


if __name__ == "__main__":
    main()
