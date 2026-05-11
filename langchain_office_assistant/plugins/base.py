from abc import ABC, abstractmethod
from typing import List, Any, Dict
from langchain_core.tools import BaseTool

class BasePlugin(ABC):
    name: str
    description: str
    version: str = "1.0.0"
    enabled: bool = True
    
    def __init__(self):
        self.tools: List[BaseTool] = []
    
    @abstractmethod
    def initialize(self, config: Dict) -> None:
        pass
    
    @abstractmethod
    def get_tools(self) -> List[BaseTool]:
        pass
    
    @abstractmethod
    async def execute(self, tool_name: str, **kwargs) -> Any:
        pass
    
    def get_info(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "version": self.version,
            "enabled": self.enabled,
            "tools": [t.name for t in self.get_tools()],
        }