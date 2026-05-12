"""Agent manager module for creating and managing AI agents using LangGraph."""

from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from app.config import LLMConfig, AgentConfig, load_config
from app.tools import get_all_tools


class AgentManager:
    """Manager for creating and managing AI agents."""
    
    def __init__(self, llm_config: LLMConfig = None, agent_config: AgentConfig = None):
        self.llm_config = llm_config or load_config()
        self.agent_config = agent_config or AgentConfig()
        self._agent = None
        
    def _create_llm(self) -> ChatOpenAI:
        """Create the LLM instance."""
        return ChatOpenAI(
            model=self.llm_config.model,
            base_url=self.llm_config.base_url,
            api_key=self.llm_config.api_key,
            temperature=self.llm_config.temperature,
            max_tokens=self.llm_config.max_tokens,
            streaming=True
        )
    
    def _create_tools(self):
        """Get all available tools."""
        return get_all_tools()
    
    def get_agent(self):
        """Get or create the agent instance."""
        if self._agent is None:
            llm = self._create_llm()
            tools = self._create_tools()
            
            # Create react agent without state_modifier parameter
            self._agent = create_react_agent(
                llm,
                tools
            )
        
        return self._agent
    
    def reset(self):
        """Reset the agent instance."""
        self._agent = None


# Global agent manager instance
_agent_manager = None


def get_agent_manager() -> AgentManager:
    """Get the global agent manager instance."""
    global _agent_manager
    if _agent_manager is None:
        _agent_manager = AgentManager()
    return _agent_manager


def create_agent():
    """Create and return a new agent instance."""
    manager = get_agent_manager()
    return manager.get_agent()