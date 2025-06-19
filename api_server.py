import asyncio
import json
import logging
from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import sys

# Add the parent directory of this script to the Python path
# This assumes desktop_agent.py, filesystem_server.py, ollama_client.py are in the same directory
script_dir = os.path.dirname(__file__)
sys.path.insert(0, script_dir)

from desktop_agent import DesktopAgent

# Configure logging for the Flask app itself
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('api_server.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
# Enable CORS for all routes, allowing communication from your web UI
CORS(app) 

# Initialize the DesktopAgent globally or when the app starts
# IMPORTANT: Replace "/Users/shakib/Desktop/TFolder" with the actual path
# where your agent should operate if it's different.
# It's crucial for the agent to have correct permissions to this directory.
DESKTOP_PATH = "/Users/shakib/Desktop/TestFolder" # <<< Verify this path!

# Agent is initialized here, when the script starts
agent = None

@app.route('/command', methods=['POST'])
async def handle_command():
    global agent # Declare agent as global to ensure it's accessible and modified if needed
    if agent is None:
        return jsonify({"error": "Desktop Agent not initialized."}), 500

    data = request.json
    user_command = data.get('command')

    if not user_command:
        return jsonify({"error": "No command provided."}), 400

    logger.info(f"Received command from UI: {user_command}")
    
    try:
        # Use asyncio.run to execute the async agent method
        response = await agent.process_user_input(user_command)
        logger.info(f"Agent response: {response}")
        return jsonify({"response": response})
    except Exception as e:
        logger.error(f"Error processing command: {e}")
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500

@app.route('/')
def index():
    return "Desktop Agent API is running. Send POST requests to /command."

if __name__ == '__main__':
    # Initialize the agent here, before running the Flask app
    try:
        agent = DesktopAgent(DESKTOP_PATH)
        logger.info(f"Desktop Agent initialized successfully for path: {DESKTOP_PATH}")
    except Exception as e:
        logger.error(f"Failed to initialize Desktop Agent: {e}")
        # The app will still run, but the /command endpoint will return an error
        # if the agent failed to initialize.

    # Flask's debug mode for development: enables reloader and debugger
    # For production, use a production-ready WSGI/ASGI server like Gunicorn/Uvicorn
    # and disable debug.
    logger.info("Starting Flask API server...")
    # Changed the port from 5000 to 5001 to resolve "Address already in use" error
    app.run(debug=True, port=5001, host='0.0.0.0')
