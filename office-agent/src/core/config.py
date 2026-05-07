# Office Agent Configuration
"""
Office Agent Configuration Module
配置管理模块，支持从环境变量和配置文件加载
"""

import os
from dataclasses import dataclass, field
from typing import List, Optional
from dotenv import load_dotenv

load_dotenv()


@dataclass
class LLMConfig:
    """LLM 配置"""
    provider: str = "openai"
    model: str = "gpt-4"
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    temperature: float = 0.7
    max_tokens: int = 2000

    def __post_init__(self):
        # 从环境变量覆盖
        self.api_key = self.api_key or os.getenv("OPENAI_API_KEY")
        self.base_url = self.base_url or os.getenv("OPENAI_BASE_URL")
        self.model = self.model or os.getenv("LLM_MODEL", "gpt-4")


@dataclass
class EmailConfig:
    """邮件服务配置"""
    smtp_host: str = "smtp.company.com"
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    from_address: str = "assistant@company.com"
    use_tls: bool = True

    def __post_init__(self):
        self.smtp_host = os.getenv("SMTP_HOST", self.smtp_host)
        self.smtp_port = int(os.getenv("SMTP_PORT", str(self.smtp_port)))
        self.smtp_user = os.getenv("SMTP_USER", self.smtp_user)
        self.smtp_password = os.getenv("SMTP_PASSWORD", self.smtp_password)
        self.from_address = os.getenv("EMAIL_FROM", self.from_address)


@dataclass
class CalendarConfig:
    """日历服务配置"""
    provider: str = "local"  # local, google, microsoft, dingtalk
    calendar_id: str = "primary"
    timezone: str = "Asia/Shanghai"

    def __post_init__(self):
        self.provider = os.getenv("CALENDAR_PROVIDER", self.provider)
        self.timezone = os.getenv("TIMEZONE", self.timezone)


@dataclass
class MemoryConfig:
    """记忆系统配置"""
    type: str = "buffer"  # buffer, summary, vector
    redis_url: Optional[str] = None
    vector_store_path: str = "./data/vector_store"

    def __post_init__(self):
        self.type = os.getenv("MEMORY_TYPE", self.type)
        self.redis_url = self.redis_url or os.getenv("REDIS_URL")
        self.vector_store_path = os.getenv("VECTOR_STORE_PATH", self.vector_store_path)


@dataclass
class AgentConfig:
    """Agent 核心配置"""
    name: str = "Office Assistant"
    description: str = "专业的办公助手，帮助处理邮件、日程、文档和任务"
    verbose: bool = True
    handle_parsing_errors: bool = True
    max_iterations: int = 15
    early_stopping_method: str = "generate"


@dataclass
class OfficeAgentConfig:
    """Office Agent 总配置"""
    llm: LLMConfig = field(default_factory=LLMConfig)
    email: EmailConfig = field(default_factory=EmailConfig)
    calendar: CalendarConfig = field(default_factory=CalendarConfig)
    memory: MemoryConfig = field(default_factory=MemoryConfig)
    agent: AgentConfig = field(default_factory=AgentConfig)

    @classmethod
    def from_env(cls) -> "OfficeAgentConfig":
        """从环境变量加载配置"""
        return cls(
            llm=LLMConfig(),
            email=EmailConfig(),
            calendar=CalendarConfig(),
            memory=MemoryConfig(),
            agent=AgentConfig()
        )

    @classmethod
    def from_file(cls, config_path: str) -> "OfficeAgentConfig":
        """从配置文件加载"""
        import json
        with open(config_path, 'r') as f:
            data = json.load(f)
        return cls(**data)


# 默认配置实例
default_config = OfficeAgentConfig.from_env()
