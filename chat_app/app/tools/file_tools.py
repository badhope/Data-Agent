"""File operation tools for the agent."""

from langchain.tools import tool
from typing import Optional
import os


@tool
def write_file(file_path: str, content: str, append: Optional[bool] = False) -> str:
    """Write content to a file.
    
    Args:
        file_path: Path to the file to write
        content: Content to write to the file
        append: If True, append to existing file; otherwise overwrite
        
    Returns:
        Success or error message
    """
    try:
        mode = 'a' if append else 'w'
        with open(file_path, mode, encoding='utf-8') as f:
            f.write(content)
        return f"Successfully wrote to {file_path}"
    except Exception as e:
        return f"Failed to write file: {str(e)}"


@tool
def read_file(file_path: str) -> str:
    """Read content from a file.
    
    Args:
        file_path: Path to the file to read
        
    Returns:
        File content or error message
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        return f"File not found: {file_path}"
    except Exception as e:
        return f"Failed to read file: {str(e)}"


@tool
def list_files(directory: Optional[str] = ".") -> str:
    """List files in a directory.
    
    Args:
        directory: Directory path to list (default: current directory)
        
    Returns:
        List of files and directories
    """
    try:
        if not os.path.exists(directory):
            return f"Directory not found: {directory}"
            
        items = os.listdir(directory)
        if not items:
            return f"Directory is empty: {directory}"
            
        # Separate files and directories
        files = []
        dirs = []
        
        for item in items:
            full_path = os.path.join(directory, item)
            if os.path.isdir(full_path):
                dirs.append(f"📁 {item}/")
            else:
                files.append(f"📄 {item}")
        
        result = f"Contents of {directory}:\n\n"
        if dirs:
            result += "Directories:\n" + "\n".join(dirs) + "\n\n"
        if files:
            result += "Files:\n" + "\n".join(files)
            
        return result
    except Exception as e:
        return f"Failed to list directory: {str(e)}"