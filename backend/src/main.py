#!/usr/bin/env python
from .crew import ChatbotCrew
import os
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.append(str(Path(__file__).parent.parent.parent))

# Import shared utilities
from shared.config import load_env
from shared.memory import memory, format_context
from shared.logger import setup_logger

# Load environment variables
load_env()

# Set up logger
logger = setup_logger("backend")

def run():
    """Run the CLI chatbot interface."""
    logger.info("Starting Agent Eat CLI chatbot...")
    print("Starting Agent Eat CLI chatbot...")
    print("Type 'exit', 'quit', or 'bye' to exit.")
    print("-" * 50)
    
    while True:
        user_input = input("You: ")
        if user_input.lower() in ["exit", "quit", "bye"]:
            print("Chatbot: Goodbye! It was nice talking to you.")
            break

        try:
            # Add user input to memory
            memory.add(f"User: {user_input}", user_id="user")
            logger.debug(f"Added user input to memory: {user_input}")

            # Retrieve relevant information from vector store
            relevant_info = memory.search(query=user_input, limit=3, user_id="user")
            context = format_context(relevant_info)
            logger.debug(f"Retrieved context: {context[:100]}...")

            inputs = {
                "user_message": f"{user_input}",
                "context": f"{context}",
            }

            # Create a new crew instance for each response to avoid state issues
            response = ChatbotCrew().crew().kickoff(inputs=inputs)
            
            # Convert response to string first if needed
            response_str = str(response)
            logger.debug(f"Generated response: {response_str[:100] if len(response_str) > 100 else response_str}...")

            # Add chatbot response to memory
            memory.add(f"Assistant: {response_str}", user_id="assistant")
            print(f"Assistant: {response_str}")
            
        except Exception as e:
            logger.error(f"Error processing input: {str(e)}", exc_info=True)
            print(f"Error: {str(e)}")
            print("Please try again with a different input.")
