import requests
import json
import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

class OllamaClient:
    def __init__(self, base_url: str = "http://localhost:11434", model: str = "thirdeyeai/qwen2.5-1.5b-instruct-uncensored:latest"): # Updated model here
        self.base_url = base_url
        self.model = model
        logger.info(f"Initialized Ollama client with model: {model}")
    
    async def generate_response(self, messages: List[Dict[str, str]], tools: List[Dict] = None) -> str:
        """Generate response from Ollama"""
        try:
            logger.debug(f"Generating response with {len(messages)} messages")
            
            # Prepare the prompt with better context
            prompt = self._format_messages_with_context(messages, tools)
            
            payload = {
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.3,  # Lower temperature for more consistent tool calls
                    "top_p": 0.9,
                    "num_predict": 2000  # Increased response length for code generation
                }
            }
            
            logger.debug(f"Sending request to Ollama")
            response = requests.post(f"{self.base_url}/api/generate", json=payload, timeout=60) # Increased timeout
            response.raise_for_status()
            
            result = response.json()
            generated_text = result.get("response", "").strip()
            
            logger.info(f"Generated response: {len(generated_text)} characters")
            return generated_text
            
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return f"Error communicating with Ollama: {str(e)}"
    
    def _format_messages_with_context(self, messages: List[Dict[str, str]], tools: List[Dict] = None) -> str:
        """Format messages with better context for tool usage"""
        prompt = """You are a desktop file management assistant. You work exclusively in the /Users/shakib/Desktop/TestFolder directory.

IMPORTANT RULES:
1. When users ask to list files/folders, or "list everything", use: TOOL_CALL:list_directory(.) The `desktop_agent` will then filter the results based on the user's specific request (e.g., "list all files", "list folders").
2. When users ask about specific file types (like .mp4, .jpg, .png), first list the directory (TOOL_CALL:list_directory(.)) then rely on the agent's internal filtering.
3. Always use relative paths from the Desktop directory (e.g., "my_file.txt", "my_folder/another_file.doc"). DO NOT include "/Users/shakib/Desktop/TestFolder" in the path you provide to tools.
4. For tool calls, use EXACTLY this format: TOOL_CALL:tool_name(arguments). Ensure arguments are properly quoted if they contain spaces or special characters.
5. When asked to create a new file or application (like a calculator or a game), use the `write_file` tool and directly provide the *complete, runnable code* as the content argument.
6. When writing code, choose an appropriate file extension (e.g., .py for Python, .js for JavaScript, .html for HTML). For Python code, ensure it's self-contained and runnable.
7. If the user asks to "rename" a file or folder, or "move" a file/folder to a new location, always use the `move_file(source, destination)` tool directly. For example, "rename folder A to B" should result in `TOOL_CALL:move_file('A', 'B')`. For existing items, make sure to specify the current full item name as `source` and the new name as `destination`.
8. When the user explicitly asks to "delete" a specific file (e.g., "delete cal.txt"), use the `delete_file(path)` tool directly. Do NOT list the directory first. Example: `TOOL_CALL:delete_file('cal.txt')`.
9. If the user asks "what can you do?" or "what are your capabilities?", summarize the available tools and their purposes concisely.
10. Be direct, helpful, and provide the most relevant action immediately. Avoid unnecessary steps or confirmations if the command is clear.

"""
        
        if tools:
            prompt += "Available tools:\\n"
            for tool in tools:
                prompt += f"- {tool['name']}: {tool['description']}\\n"
            prompt += "\\n"
        
        # Add conversation history
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            if role == "user":
                prompt += f"User: {content}\\n"
            elif role == "assistant":
                prompt += f"Assistant: {content}\\n"
            elif role == "system":
                prompt += f"System: {content}\\n"
        
        prompt += "Assistant: "
        return prompt
