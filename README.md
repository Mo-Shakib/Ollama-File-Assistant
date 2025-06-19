# Ollama File Assistant

A powerful desktop file management agent that combines the capabilities of Ollama AI with a web-based interface for intelligent file operations. This project provides both command-line and web UI interfaces for managing files on your desktop using natural language commands.

## Features

- **Natural Language File Operations**: Use plain English to perform file operations
- **Web-based Interface**: Modern, responsive UI built with React and Tailwind CSS
- **Command-line Interface**: Terminal-based interaction for power users
- **Comprehensive File Management**:
  - List files and directories with intelligent filtering
  - Create, read, write, and delete files
  - Move and rename files/folders
  - Get detailed file information
  - Bulk operations (e.g., "delete all images", "move all videos to folder")
- **AI-Powered**: Uses Ollama for natural language understanding
- **Safe Operations**: Restricted to designated directory for security
- **Real-time Responses**: Asynchronous processing with live feedback

## Architecture

The project consists of several key components:

- **Desktop Agent** (`desktop_agent.py`): Core AI agent that processes natural language commands
- **Filesystem Server** (`filesystem_server.py`): Secure file operations handler
- **Ollama Client** (`ollama_client.py`): Interface to Ollama AI model
- **API Server** (`api_server.py`): Flask-based REST API for web interface
- **Web UI** (`web.html`): React-based frontend interface
- **CLI Interface** (`main.py`): Command-line application

## Prerequisites

- Python 3.8 or higher
- [Ollama](https://ollama.ai/) installed and running
- Required Python packages (see Installation section)

## Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/Mo-Shakib/Ollama-File-Assistant.git
   cd Ollama-File-Assistant
   ```

2. **Install required Python packages:**
   ```bash
   pip install requests flask flask-cors asyncio
   ```

3. **Install and setup Ollama:**
   ```bash
   # Install Ollama (visit https://ollama.ai for platform-specific instructions)
   
   # Pull the required model
   ollama pull llama3.2
   ```

4. **Create the test directory:**
   ```bash
   mkdir -p /Users/shakib/Desktop/TestFolder
   ```

## Usage

### Web Interface

1. **Start the API server:**
   ```bash
   python api_server.py
   ```
   The server will start on `http://localhost:5001`

2. **Open the web interface:**
   Open `web.html` in your browser, or serve it through a web server.

3. **Start using natural language commands:**
   - "List all files"
   - "Create a Python calculator app"
   - "Show me all images"
   - "Delete all .txt files"
   - "Move all videos to Movies folder"

### Command Line Interface

1. **Start the CLI application:**
   ```bash
   python main.py
   ```

2. **Use natural language commands:**
   ```
   👤 You: list all files
   👤 You: create a new file called notes.txt with content "Hello World"
   👤 You: show me all Python files
   ```

3. **Special commands:**
   - `quit` or `exit`: Exit the application
   - `clear`: Clear conversation history

## Example Commands

### File Listing
- "List all files"
- "Show me all folders"
- "Find all .mp4 files"
- "List contents of Documents folder"

### File Creation
- "Create a file called test.txt"
- "Make a Python calculator app"
- "Create a simple HTML page"

### File Operations
- "Delete file.txt"
- "Move image.jpg to Photos folder"
- "Rename old_name.txt to new_name.txt"
- "Delete all image files"

### File Information
- "Show info about document.pdf"
- "Read the contents of config.txt"

## Configuration

### Changing the Working Directory

Edit the `DESKTOP_PATH` variable in `api_server.py` and the default path in `main.py`:

```python
DESKTOP_PATH = "/path/to/your/directory"
```

### Changing the AI Model

Modify the model in `ollama_client.py`:

```python
def __init__(self, base_url: str = "http://localhost:11434", model: str = "your-preferred-model"):
```

## API Endpoints

### POST /command

Send natural language commands to the agent.

**Request:**
```json
{
  "command": "list all files"
}
```

**Response:**
```json
{
  "response": "📂 Desktop contents (5 total items):\n\n📁 Folders (2):\n  📁 Documents\n  📁 Images\n\n📄 Files (3):\n  📄 notes.txt (0.1 KB)\n  📄 script.py (1.2 KB)\n  📄 readme.md (2.5 KB)"
}
```

## Security Features

- **Sandboxed Operations**: All file operations are restricted to the designated directory
- **Path Validation**: Prevents directory traversal attacks
- **Safe File Handling**: Proper error handling and validation for all operations

## Logging

The application generates detailed logs:

- `main.log`: CLI application logs
- `desktop_agent.log`: Agent processing logs
- `mcp_filesystem.log`: File operation logs
- `api_server.log`: Web API logs

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## Troubleshooting

### Common Issues

1. **Ollama Connection Error:**
   - Ensure Ollama is running: `ollama serve`
   - Check if the model is available: `ollama list`

2. **Permission Denied:**
   - Ensure the target directory exists and is writable
   - Check file permissions

3. **Port Already in Use:**
   - Change the port in `api_server.py` if 5001 is occupied
   - Update the corresponding port in `web.html`

4. **Model Not Found:**
   - Pull the required model: `ollama pull llama3.2`
   - Or update the model name in `ollama_client.py`

## License

This project is open source and available under the [MIT License](LICENSE).

## Acknowledgments

- [Ollama](https://ollama.ai/) for providing the AI model infrastructure
- [Flask](https://flask.palletsprojects.com/) for the web framework
- [React](https://reactjs.org/) for the frontend interface
- [Tailwind CSS](https://tailwindcss.com/) for styling

## Support

If you encounter any issues or have questions, please open an issue on the GitHub repository.