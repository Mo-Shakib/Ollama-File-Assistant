import asyncio
import json
import logging
import os
import shutil
from pathlib import Path
from typing import Any, Dict, List, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('mcp_filesystem.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class MCPFilesystemServer:
    def __init__(self, allowed_directory: str):
        self.allowed_directory = Path(allowed_directory).resolve()
        logger.info(f"Initialized MCP Filesystem Server with directory: {self.allowed_directory}")
        
        # Ensure the directory exists
        if not self.allowed_directory.exists():
            raise ValueError(f"Directory does not exist: {self.allowed_directory}")
    
    def _is_path_allowed(self, path: str) -> bool:
        """Check if the path is within the allowed directory"""
        try:
            resolved_path = Path(path).resolve()
            return resolved_path.is_relative_to(self.allowed_directory)
        except Exception as e:
            logger.error(f"Error checking path {path}: {e}")
            return False
    
    def _get_safe_path(self, path: str) -> Path:
        """Get a safe path within the allowed directory"""
        if os.path.isabs(path):
            safe_path = Path(path).resolve()
        else:
            safe_path = (self.allowed_directory / path).resolve()
        
        if not self._is_path_allowed(str(safe_path)):
            raise PermissionError(f"Access denied to path: {path}")
        
        return safe_path
    
    async def list_directory(self, path: str = ".") -> Dict[str, Any]:
        """List contents of a directory"""
        try:
            logger.debug(f"Listing directory: {path}")
            safe_path = self._get_safe_path(path)
            
            if not safe_path.exists():
                return {"error": f"Directory does not exist: {path}"}
            
            if not safe_path.is_dir():
                return {"error": f"Path is not a directory: {path}"}
            
            items = []
            for item in safe_path.iterdir():
                item_info = {
                    "name": item.name,
                    "type": "directory" if item.is_dir() else "file",
                    "size": item.stat().st_size if item.is_file() else None,
                    "modified": item.stat().st_mtime
                }
                items.append(item_info)
            
            result = {
                "path": str(safe_path),
                "items": items,
                "count": len(items)
            }
            logger.info(f"Listed {len(items)} items in {safe_path}")
            return result
            
        except Exception as e:
            logger.error(f"Error listing directory {path}: {e}")
            return {"error": str(e)}
    
    async def read_file(self, path: str) -> Dict[str, Any]:
        """Read contents of a file"""
        try:
            logger.debug(f"Reading file: {path}")
            safe_path = self._get_safe_path(path)
            
            if not safe_path.exists():
                return {"error": f"File does not exist: {path}"}
            
            if not safe_path.is_file():
                return {"error": f"Path is not a file: {path}"}
            
            # Try to read as text first
            try:
                content = safe_path.read_text(encoding='utf-8')
                result = {
                    "path": str(safe_path),
                    "content": content,
                    "size": len(content),
                    "type": "text"
                }
            except UnicodeDecodeError:
                # If it's a binary file, read first 1024 bytes
                content = safe_path.read_bytes()[:1024]
                result = {
                    "path": str(safe_path),
                    "content": f"<Binary file, first 1024 bytes: {len(content)} bytes>",
                    "size": safe_path.stat().st_size,
                    "type": "binary"
                }
            
            logger.info(f"Read file {safe_path} ({result['size']} bytes)")
            return result
            
        except Exception as e:
            logger.error(f"Error reading file {path}: {e}")
            return {"error": str(e)}
    
    async def write_file(self, path: str, content: str) -> Dict[str, Any]:
        """Write content to a file"""
        try:
            logger.debug(f"Writing file: {path}")
            safe_path = self._get_safe_path(path)
            
            # Create parent directories if they don't exist
            safe_path.parent.mkdir(parents=True, exist_ok=True)
            
            safe_path.write_text(content, encoding='utf-8')
            
            result = {
                "path": str(safe_path),
                "size": len(content),
                "message": "File written successfully"
            }
            logger.info(f"Wrote {len(content)} bytes to {safe_path}")
            return result
            
        except Exception as e:
            logger.error(f"Error writing file {path}: {e}")
            return {"error": str(e)}
    
    async def create_directory(self, path: str) -> Dict[str, Any]:
        """Create a directory"""
        try:
            logger.debug(f"Creating directory: {path}")
            safe_path = self._get_safe_path(path)
            
            safe_path.mkdir(parents=True, exist_ok=True)
            
            result = {
                "path": str(safe_path),
                "message": "Directory created successfully"
            }
            logger.info(f"Created directory {safe_path}")
            return result
            
        except Exception as e:
            logger.error(f"Error creating directory {path}: {e}")
            return {"error": str(e)}
    
    async def delete_file(self, path: str) -> Dict[str, Any]:
        """Delete a file or directory"""
        try:
            logger.debug(f"Deleting: {path}")
            safe_path = self._get_safe_path(path)
            
            if not safe_path.exists():
                return {"error": f"Path does not exist: {path}"}
            
            if safe_path.is_file():
                safe_path.unlink()
                message = "File deleted successfully"
            elif safe_path.is_dir():
                shutil.rmtree(safe_path)
                message = "Directory deleted successfully"
            else:
                return {"error": f"Unknown path type: {path}"}
            
            result = {
                "path": str(safe_path),
                "message": message
            }
            logger.info(f"Deleted {safe_path}")
            return result
            
        except Exception as e:
            logger.error(f"Error deleting {path}: {e}")
            return {"error": str(e)}
    
    async def move_file(self, source: str, destination: str) -> Dict[str, Any]:
        """Move/rename a file or directory"""
        try:
            logger.debug(f"Moving {source} to {destination}")
            safe_source = self._get_safe_path(source)
            safe_dest = self._get_safe_path(destination)
            
            if not safe_source.exists():
                return {"error": f"Source does not exist: {source}"}
            
            # Create parent directory if it doesn't exist
            safe_dest.parent.mkdir(parents=True, exist_ok=True)
            
            shutil.move(str(safe_source), str(safe_dest))
            
            result = {
                "source": str(safe_source),
                "destination": str(safe_dest),
                "message": "File moved successfully"
            }
            logger.info(f"Moved {safe_source} to {safe_dest}")
            return result
            
        except Exception as e:
            logger.error(f"Error moving {source} to {destination}: {e}")
            return {"error": str(e)}
    
    async def get_file_info(self, path: str) -> Dict[str, Any]:
        """Get information about a file or directory"""
        try:
            logger.debug(f"Getting info for: {path}")
            safe_path = self._get_safe_path(path)
            
            if not safe_path.exists():
                return {"error": f"Path does not exist: {path}"}
            
            stat = safe_path.stat()
            result = {
                "path": str(safe_path),
                "name": safe_path.name,
                "type": "directory" if safe_path.is_dir() else "file",
                "size": stat.st_size,
                "created": stat.st_ctime,
                "modified": stat.st_mtime,
                "permissions": oct(stat.st_mode)[-3:]
            }
            
            logger.info(f"Got info for {safe_path}")
            return result
            
        except Exception as e:
            logger.error(f"Error getting info for {path}: {e}")
            return {"error": str(e)}
