"""Tools module for the chat agent."""

from .search_tools import web_search
from .file_tools import write_file, read_file, list_files

__all__ = [
    'web_search',
    'write_file',
    'read_file',
    'list_files',
]

def get_all_tools():
    """Get all available tools as a list."""
    return [
        web_search,
        write_file,
        read_file,
        list_files,
    ]