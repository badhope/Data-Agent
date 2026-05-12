"""Configuration module for the chat application."""

from dataclasses import dataclass
from typing import Optional
import os


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
    description: str = "A versatile AI assistant"
    system_prompt: str = """You are Data, a versatile AI assistant.

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
"""


@dataclass
class AppConfig:
    """Application-level configuration."""
    
    # Logging settings
    log_level: str = "INFO"  # DEBUG, INFO, WARNING, ERROR
    log_file: str = "./logs/data_agent.log"
    enable_file_logging: bool = True
    
    # UI settings
    theme: str = "light"
    show_tool_calls: bool = True
    enable_streaming: bool = True


def load_config() -> LLMConfig:
    """Load LLM configuration."""
    return LLMConfig(
        api_key="sk-b8669932bc524dd191a14fc417079e8e",
    )


def ensure_log_directory():
    """Ensure log directory exists."""
    log_dir = "./logs"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)