import asyncio
import json
import logging
import re
from typing import Dict, Any, List
from filesystem_server import MCPFilesystemServer
from ollama_client import OllamaClient

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('desktop_agent.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class DesktopAgent:
    def __init__(self, desktop_path: str = "/Users/shakib/Desktop/TestFolder"):
        self.filesystem = MCPFilesystemServer(desktop_path)
        self.ollama = OllamaClient(model="llama3.2")
        self.conversation_history = []
        self.desktop_path = desktop_path
        
        # Define available tools
        self.tools = [
            {
                "name": "list_directory",
                "description": "List contents of a directory. Usage: list_directory(path)",
                "function": self.filesystem.list_directory
            },
            {
                "name": "read_file",
                "description": "Read contents of a file. Usage: read_file(path)",
                "function": self.filesystem.read_file
            },
            {
                "name": "write_file",
                "description": "Write content to a file. Usage: write_file(path, content)",
                "function": self.filesystem.write_file
            },
            {
                "name": "create_directory",
                "description": "Create a directory. Usage: create_directory(path)",
                "function": self.filesystem.create_directory
            },
            {
                "name": "delete_file",
                "description": "Delete a file or directory. Usage: delete_file(path)",
                "function": self.filesystem.delete_file
            },
            {
                "name": "move_file",
                "description": "Move/rename a file or directory. Usage: move_file(source, destination)",
                "function": self.filesystem.move_file
            },
            {
                "name": "get_file_info",
                "description": "Get information about a file or directory. Usage: get_file_info(path)",
                "function": self.filesystem.get_file_info
            }
        ]
        
        logger.info(f"Initialized Desktop Agent with {len(self.tools)} tools")
    
    async def process_user_input(self, user_input: str) -> str:
        """Process user input and return response"""
        try:
            logger.info(f"Processing user input: {user_input[:100]}...")
            
            # Check for special commands that need multiple operations
            if "move" in user_input.lower() and "image" in user_input.lower():
                folder_match = re.search(r'to\s+(\w+)', user_input.lower())
                if folder_match:
                    folder_name = folder_match.group(1)
                    return await self.move_images_to_folder(folder_name)
            
            if "delete" in user_input.lower() and "image" in user_input.lower():
                return await self.delete_images()

            if "delete all files" in user_input.lower() or "clear all files" in user_input.lower():
                return await self.delete_all_files_in_current_folder()
            
            # Check for listing files in specific folder
            if "list" in user_input.lower() and ("in" in user_input.lower() or "folder" in user_input.lower()):
                folder_name = self.extract_folder_name(user_input)
                if folder_name:
                    return await self.list_folder_contents(folder_name)
            
            # Add user message to conversation history
            self.conversation_history.append({
                "role": "user",
                "content": user_input
            })
            
            # Generate response from Ollama
            response = await self.ollama.generate_response(
                self.conversation_history,
                self.tools
            )
            
            logger.debug(f"Ollama response: {response}")
            
            # Check if the response contains a tool call with better regex
            tool_call_patterns = [
                r'TOOL_CALL:\s*(\w+)\s*\((.*?)\)',
                r'USE_TOOL:\s*(\w+)\s*\((.*?)\)',
            ]
            
            tool_call_match = None
            for pattern in tool_call_patterns:
                tool_call_match = re.search(pattern, response, re.DOTALL) # Added re.DOTALL for multi-line content
                if tool_call_match:
                    break
            
            if tool_call_match:
                tool_name = tool_call_match.group(1)
                tool_args = tool_call_match.group(2).strip()
                
                # Validate tool name
                valid_tools = [t["name"] for t in self.tools]
                if tool_name not in valid_tools:
                    # Try to find a close match
                    if "list" in tool_name.lower():
                        tool_name = "list_directory"
                        tool_args = "." if not tool_args else tool_args
                    else:
                        return f"❌ Unknown tool: {tool_name}. Available tools: {', '.join(valid_tools)}"
                
                logger.info(f"Tool call detected: {tool_name}({tool_args})")
                
                # Execute the tool
                tool_result = await self.execute_tool(tool_name, tool_args)
                
                # Generate final response based on tool result
                final_response = await self.generate_final_response(tool_name, tool_result, user_input)
                
                # Add assistant response to conversation history
                self.conversation_history.append({
                    "role": "assistant",
                    "content": final_response
                })
                
                return final_response
            else:
                # No tool call, just return the response
                self.conversation_history.append({
                    "role": "assistant",
                    "content": response
                })
                return response
                
        except Exception as e:
            logger.error(f"Error processing user input: {e}")
            error_msg = f"Sorry, I encountered an error: {str(e)}"
            self.conversation_history.append({
                "role": "assistant",
                "content": error_msg
            })
            return error_msg
    
    def extract_folder_name(self, user_input: str) -> str:
        """Extract folder name from user input"""
        # Look for patterns like "list files in X folder" or "list X folder"
        patterns = [
            r'list.*?in\s+(\w+)\s+folder',
            r'list.*?(\w+)\s+folder',
            r'in\s+(\w+)\s+folder',
            r'folder\s+(\w+)',
            r'(\w+)\s+folder'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, user_input.lower())
            if match:
                return match.group(1)
        
        return None
    
    async def list_folder_contents(self, folder_name: str) -> str:
        """List contents of a specific folder"""
        try:
            # First, get all folders to find the exact match
            list_result = await self.filesystem.list_directory(".")
            if "error" in list_result:
                return f"❌ Error listing desktop: {list_result['error']}"
            
            # Find matching folder (case-insensitive)
            matching_folder = None
            for item in list_result.get("items", []):
                if item["type"] == "directory" and item["name"].lower().startswith(folder_name.lower()):
                    matching_folder = item["name"]
                    break
            
            if not matching_folder:
                return f"❌ No folder found starting with '{folder_name}'"
            
            # List contents of the found folder
            folder_result = await self.filesystem.list_directory(matching_folder)
            if "error" in folder_result:
                return f"❌ Error listing folder '{matching_folder}': {folder_result['error']}"
            
            items = folder_result.get("items", [])
            if not items:
                return f"📁 Folder '{matching_folder}' is empty"
            
            response = f"📁 Contents of '{matching_folder}' ({len(items)} items):\\n\\n"
            
            folders = [item for item in items if item["type"] == "directory"]
            files = [item for item in items if item["type"] == "file"]
            
            if folders:
                response += f"📁 Folders ({len(folders)}):\\n"
                for folder in folders:
                    response += f"  📁 {folder['name']}\\n"
            
            if files:
                response += f"\\n📄 Files ({len(files)}):\\n"
                for file in files:
                    size_kb = file.get("size", 0) / 1024 if file.get("size") else 0
                    response += f"  📄 {file['name']} ({size_kb:.1f} KB)\\n"
            
            return response
            
        except Exception as e:
            logger.error(f"Error listing folder {folder_name}: {e}")
            return f"❌ Error listing folder: {str(e)}"
    
    async def execute_tool(self, tool_name: str, tool_args: str) -> Dict[str, Any]:
        """Execute a tool with given arguments"""
        try:
            logger.debug(f"Executing tool: {tool_name} with args: {tool_args}")
            
            # Find the tool
            tool = None
            for t in self.tools:
                if t["name"] == tool_name:
                    tool = t
                    break
            
            if not tool:
                return {"error": f"Tool '{tool_name}' not found"}
            
            # Special handling for write_file to correctly parse path and content
            if tool_name == "write_file":
                # This regex handles arguments like 'filename.py', 'print("Hello")'
                # and also 'filename.py', '''
                # multiline
                # content
                # '''
                # It looks for the first argument (path) optionally quoted, then a comma,
                # then the rest as the second argument (content), optionally quoted.
                # re.DOTALL makes . match newlines.
                match = re.match(r'^\s*([\'"]?)(.*?)\1\s*,\s*([\'"]?)(.*)\3\s*$', tool_args, re.DOTALL)
                if match:
                    path = match.group(2).strip()
                    content = match.group(4).strip()
                    args = [path, content]
                else:
                    return {"error": f"Invalid arguments for write_file: {tool_args}. Expected 'path', 'content'"}
            else:
                # For other tools, use the existing simple comma-separated parsing
                args = self.parse_tool_arguments(tool_args)
            
            # Execute the tool function
            if tool_name == "write_file" and len(args) == 2:
                result = await tool["function"](args[0], args[1])
            elif tool_name == "move_file" and len(args) == 2:
                result = await tool["function"](args[0], args[1])
            elif len(args) >= 1:
                result = await tool["function"](args[0])
            else: # Fallback for list_directory with no path specified
                result = await tool["function"](".")
            
            logger.info(f"Tool {tool_name} executed successfully")
            return result
            
        except Exception as e:
            logger.error(f"Error executing tool {tool_name}: {e}")
            return {"error": str(e)}
    
    def parse_tool_arguments(self, args_str: str) -> List[str]:
        """Parse tool arguments from string (for non-write_file tools)"""
        if not args_str.strip():
            return ["."]
        
        # Simple argument parsing - split by comma and strip quotes
        args = []
        parts = args_str.split(',')
        for part in parts:
            part = part.strip()
            # Remove only the outermost quotes if present
            if (part.startswith('"') and part.endswith('"')) or \
               (part.startswith("'") and part.endswith("'")):
                part = part[1:-1]
            args.append(part)
        
        return args
    
    async def generate_final_response(self, tool_name: str, tool_result: Dict[str, Any], original_request: str) -> str:
        """Generate a final human-readable response based on tool result"""
        try:
            if "error" in tool_result:
                return f"❌ Error: {tool_result['error']}"
            
            if tool_name == "list_directory":
                return self.format_directory_listing(tool_result, original_request)
            elif tool_name == "read_file":
                return self.format_file_content(tool_result)
            elif tool_name == "write_file":
                return f"✅ Successfully wrote {tool_result.get('size', 0)} bytes to {tool_result.get('path', 'file')}"
            elif tool_name == "create_directory":
                return f"✅ Successfully created directory: {tool_result.get('path', 'directory')}"
            elif tool_name == "delete_file":
                return f"✅ Successfully deleted: {tool_result.get('path', 'file')}"
            elif tool_name == "move_file":
                return f"✅ Successfully moved {tool_result.get('source', 'file')} to {tool_result.get('destination', 'destination')}"
            elif tool_name == "get_file_info":
                return self.format_file_info(tool_result)
            
            return f"Tool {tool_name} completed: {json.dumps(tool_result, indent=2)}"
            
        except Exception as e:
            logger.error(f"Error generating final response: {e}")
            return f"Tool completed but error formatting response: {str(e)}"
    
    def format_directory_listing(self, tool_result: Dict[str, Any], original_request: str) -> str:
        """Format directory listing based on user request"""
        if "items" not in tool_result:
            return "❌ No items found"
        
        items = tool_result["items"]
        path = tool_result.get("path", "Desktop")
        
        # Filter based on request
        if any(ext in original_request.lower() for ext in ['.mp4', 'video', 'movie']):
            filtered_items = [item for item in items if item["name"].lower().endswith(('.mp4', '.avi', '.mov', '.mkv'))]
            if filtered_items:
                response = f"🎬 Found {len(filtered_items)} video files:\\n"
                for item in filtered_items:
                    size_mb = item.get("size", 0) / (1024*1024) if item.get("size") else 0
                    response += f"📹 {item['name']} ({size_mb:.1f} MB)\\n"
                return response
            else:
                return "❌ No video files found on Desktop"
        
        elif any(ext in original_request.lower() for ext in ['.jpg', '.png', '.jpeg', 'image', 'photo']):
            filtered_items = [item for item in items if item["name"].lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.bmp'))]
            if filtered_items:
                response = f"🖼️ Found {len(filtered_items)} image files:\\n"
                for item in filtered_items:
                    size_kb = item.get("size", 0) / 1024 if item.get("size") else 0
                    response += f"🖼️ {item['name']} ({size_kb:.1f} KB)\\n"
                return response
            else:
                return "❌ No image files found on Desktop"
        
        elif 'folder' in original_request.lower() or 'director' in original_request.lower():
            folders = [item for item in items if item["type"] == "directory"]
            if folders:
                response = f"📁 Found {len(folders)} folders on Desktop:\\n"
                for folder in folders[:20]:  # Limit to first 20
                    response += f"📁 {folder['name']}\\n"
                if len(folders) > 20:
                    response += f"... and {len(folders) - 20} more folders"
                return response
            else:
                return "❌ No folders found on Desktop"
        
        else:
            # General listing
            folders = [item for item in items if item["type"] == "directory"]
            files = [item for item in items if item["type"] == "file"]
            
            response = f" 📂 Desktop contents ({len(items)} total items):\\n\\n"
            
            if folders:
                response += f"📁 Folders ({len(folders)}):\\n"
                for folder in folders[:10]:
                    response += f"  📁 {folder['name']}\\n"
                if len(folders) > 10:
                    response += f"  ... and {len(folders) - 10} more folders\\n"
            
            if files:
                response += f"\\n📄 Files ({len(files)}):\\n"
                for file in files[:10]:
                    size_kb = file.get("size", 0) / 1024 if file.get("size") else 0
                    response += f"  📄 {file['name']} ({size_kb:.1f} KB)\\n"
                if len(files) > 10:
                    response += f"  ... and {len(files) - 10} more files\\n"
            
            return response
    
    def format_file_content(self, tool_result: Dict[str, Any]) -> str:
        """Format file content for display"""
        if "content" in tool_result:
            content = tool_result["content"]
            file_path = tool_result.get("path", "file")
            file_type = tool_result.get("type", "text")
            
            if file_type == "binary":
                return f"📄 {file_path} is a binary file ({tool_result.get('size', 0)} bytes)"
            else:
                preview = content[:500] + "..." if len(content) > 500 else content
                return f"📄 Content of {file_path} ({tool_result.get('size', 0)} bytes):\\n\\n{preview}"
        else:
            return "❌ Could not read file content"
    
    def format_file_info(self, tool_result: Dict[str, Any]) -> str:
        """Format file information for display"""
        info = tool_result
        return f"ℹ️ File info for {info.get('name', 'file')}:\\n" \
               f"📍 Path: {info.get('path', 'unknown')}\\n" \
               f"📁 Type: {info.get('type', 'unknown')}\\n" \
               f"📏 Size: {info.get('size', 0)} bytes\\n" \
               f"🔒 Permissions: {info.get('permissions', 'unknown')}"
    
    def clear_history(self):
        """Clear conversation history"""
        self.conversation_history = []
        logger.info("Conversation history cleared")
    
    async def move_images_to_folder(self, folder_name: str) -> str:
        """Helper method to move all image files to a specific folder"""
        try:
            # First, list all files
            list_result = await self.filesystem.list_directory(".")
            if "error" in list_result:
                return f"❌ Error listing files: {list_result['error']}"
            
            # Find image files
            image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp']
            image_files = []
            
            for item in list_result.get("items", []):
                if item["type"] == "file":
                    name_lower = item["name"].lower()
                    if any(name_lower.endswith(ext) for ext in image_extensions):
                        image_files.append(item["name"])
            
            if not image_files:
                return "❌ No image files found to move."
            
            # Move each image file to the specified folder
            for image_file in image_files:
                source_path = f"./{image_file}"
                destination_path = f"./{folder_name}/{image_file}"
                move_result = await self.filesystem.move_file(source_path, destination_path)
                if "error" in move_result:
                    return f"❌ Error moving {image_file}: {move_result['error']}"
            
            return f"✅ Successfully moved {len(image_files)} image files to {folder_name}."
        
        except Exception as e:
            logger.error(f"Error moving images to folder {folder_name}: {e}")
            return f"❌ An error occurred while moving images: {str(e)}"
    
    async def delete_images(self) -> str:
        """Helper method to delete all image files"""
        try:
            # First, list all files
            list_result = await self.filesystem.list_directory(".")
            if "error" in list_result:
                return f"❌ Error listing files: {list_result['error']}"
            
            # Find image files
            image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp']
            image_files = []
            
            for item in list_result.get("items", []):
                if item["type"] == "file":
                    name_lower = item["name"].lower()
                    if any(name_lower.endswith(ext) for ext in image_extensions):
                        image_files.append(item["name"])
            
            if not image_files:
                return "❌ No image files found to delete."
            
            # Delete each image file
            for image_file in image_files:
                delete_result = await self.filesystem.delete_file(image_file)
                if "error" in delete_result:
                    return f"❌ Error deleting {image_file}: {delete_result['error']}"
            
            return f"✅ Successfully deleted {len(image_files)} image files."
        
        except Exception as e:
            logger.error(f"Error deleting images: {e}")
            return f"❌ An error occurred while deleting images: {str(e)}"

    async def delete_all_files_in_current_folder(self) -> str:
        """Helper method to delete all files (but not directories) in the current folder."""
        try:
            logger.info("Attempting to delete all files in the current folder.")
            list_result = await self.filesystem.list_directory(".")
            if "error" in list_result:
                return f"❌ Error listing files to delete: {list_result['error']}"

            files_to_delete = [item["name"] for item in list_result.get("items", []) if item["type"] == "file"]

            if not files_to_delete:
                return "✅ No files found in the current folder to delete."

            deleted_count = 0
            errors = []
            for file_name in files_to_delete:
                delete_result = await self.filesystem.delete_file(file_name)
                if "error" in delete_result:
                    errors.append(f"❌ Error deleting {file_name}: {delete_result['error']}")
                else:
                    deleted_count += 1
            
            if errors:
                return f"✅ Deleted {deleted_count} files. Some errors occurred: {'; '.join(errors)}"
            else:
                return f"✅ Successfully deleted {deleted_count} files in the current folder."

        except Exception as e:
            logger.error(f"Error in delete_all_files_in_current_folder: {e}")
            return f"❌ An unexpected error occurred while deleting files: {str(e)}"
