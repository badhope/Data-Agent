"""Document tools module."""

from langchain_core.tools import tool
from typing import Optional
import os


class MockDocumentStore:
    """Mock document data store."""

    def __init__(self):
        self.documents = {}

    def read(self, file_path: str) -> str:
        if file_path in self.documents:
            return self.documents[file_path]
        
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        
        return f"File not found: {file_path}"

    def write(self, file_path: str, content: str) -> bool:
        try:
            directory = os.path.dirname(file_path)
            if directory and not os.path.exists(directory):
                os.makedirs(directory)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        except Exception:
            return False


_doc_store = MockDocumentStore()


@tool
def read_document(file_path: str) -> str:
    """Read a document file."""
    try:
        content = _doc_store.read(file_path)
        return f"📄 Document content:\n\n{content}"
    except Exception as e:
        return f"❌ Failed to read document: {str(e)}"


@tool
def write_document(file_path: str, content: str) -> str:
    """Write content to a document file."""
    try:
        success = _doc_store.write(file_path, content)
        if success:
            return f"✅ Document saved successfully!\n\n📄 File: {file_path}"
        else:
            return f"❌ Failed to save document"
    except Exception as e:
        return f"❌ Failed to write document: {str(e)}"
