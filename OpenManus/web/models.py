"""
数据模型定义模块
"""
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from datetime import datetime
import json


class Settings(BaseModel):
    """系统配置模型"""
    llm: Dict[str, Any] = Field(default_factory=lambda: {
        "provider": "aliyun",
        "model": "qwen-plus-latest",
        "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "api_key": "",
        "max_tokens": 4096,
        "temperature": 0.7,
        "top_p": 0.9,
        "stream": False
    })
    sandbox: Dict[str, Any] = Field(default_factory=lambda: {
        "enabled": True,
        "timeout": 60,
        "allow_network": False
    })
    knowledge_base: Dict[str, Any] = Field(default_factory=lambda: {
        "enabled": True,
        "vector_db": "sqlite",
        "chunk_size": 1000,
        "chunk_overlap": 200,
        "embedding_model": "text-embedding-v3"
    })
    conversation: Dict[str, Any] = Field(default_factory=lambda: {
        "history_enabled": True,
        "max_history": 50,
        "auto_title": True
    })
    display: Dict[str, Any] = Field(default_factory=lambda: {
        "theme": "dark",
        "thinking_chain": True,
        "code_highlight": True,
        "markdown_render": True
    })
    agent: Dict[str, Any] = Field(default_factory=lambda: {
        "max_steps": 5,
        "auto_mode": True,
        "reasoning_mode": "auto"
    })
    langsmith: Dict[str, Any] = Field(default_factory=lambda: {
        "enabled": False,
        "api_key": "",
        "project": "dataagent",
        "endpoint": "https://api.smith.langchain.com"
    })


class KnowledgeBase(BaseModel):
    """知识库模型"""
    id: str
    name: str
    description: str = ""
    created_at: str
    updated_at: str
    embedding_model: str = "text-embedding-v3"
    indexing_technique: str = "high_quality"
    permission: str = "only_me"


class Document(BaseModel):
    """文档模型"""
    id: str
    knowledge_base_id: str
    name: str
    data_source_type: str
    status: str
    file_path: str
    created_at: str
    content: Optional[str] = None
    error: Optional[str] = None


class ProcessingRule(BaseModel):
    """数据处理规则"""
    mode: str = "automatic"
    rules: Dict[str, Any] = Field(default_factory=lambda: {
        "pre_processing_rules": [
            {"id": "remove_extra_spaces", "enabled": True},
            {"id": "remove_urls_emails", "enabled": False}
        ],
        "segmentation": {
            "separator": "\n\n",
            "max_tokens": 1000,
            "chunk_size": 1000,
            "chunk_overlap": 200
        }
    })


class Skill(BaseModel):
    """技能模型"""
    id: str
    name: str
    description: str
    version: str = "1.0.0"
    author: str = ""
    category: str = "custom"
    type: str = "custom"
    icon: str = "⚡"
    status: str = "published"
    created_at: str
    updated_at: str
    parameters: List[Dict[str, Any]] = Field(default_factory=list)
    prompts: Dict[str, Any] = Field(default_factory=dict)
    tools: List[Dict[str, Any]] = Field(default_factory=list)


class MCPServer(BaseModel):
    """MCP服务器模型"""
    id: str
    name: str
    type: str
    command: str = ""
    args: List[str] = Field(default_factory=list)
    url: str = ""
    env: Dict[str, str] = Field(default_factory=dict)
    status: str = "inactive"
    enabled: bool = True
    icon: str = "🔌"

