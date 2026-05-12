"""Configuration module for the chat application."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class LLMConfig:
    """Configuration for LLM settings."""
    
    model: str = "qwen-turbo"
    base_url: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    api_key: str = ""
    temperature: float = 0.7
    max_tokens: int = 4096


@dataclass
class AgentConfig:
    """Configuration for the agent."""
    
    name: str = "Data"
    description: str = "A versatile AI assistant that can help with various tasks"
    system_prompt: str = """You are Data, a versatile AI assistant that can help users with various tasks.

Capabilities:
- Web browsing and information retrieval
- File operations and document processing
- Python code execution
- Text editing and search
- And much more!

Guidelines:
- Always use the available tools to complete tasks
- Ask for clarification when user requests are ambiguous
- Provide clear, structured responses
- Confirm important actions before executing them
"""


def load_config() -> LLMConfig:
    """Load LLM configuration."""
    return LLMConfig(
        api_key="sk-b8669932bc524dd191a14fc417079e8e",
    )