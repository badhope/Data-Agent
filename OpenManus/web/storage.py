"""
数据存储和管理模块
"""
import json
import os
from pathlib import Path
from typing import Dict, Any
from .models import Settings, KnowledgeBase, Skill, MCPServer


BASE_DIR = Path(__file__).parent.parent
CONFIG_DIR = BASE_DIR / "config"
DATA_DIR = BASE_DIR / "data"
KNOWLEDGE_DIR = DATA_DIR / "knowledge_bases"
SKILLS_DIR = DATA_DIR / "skills"
MCP_CONFIG_FILE = CONFIG_DIR / "mcp.json"
SETTINGS_FILE = CONFIG_DIR / "web_config.json"


# 全局数据存储
current_settings: Settings = Settings()
knowledge_bases: Dict[str, KnowledgeBase] = {}
skills: Dict[str, Skill] = {}
mcp_servers: Dict[str, MCPServer] = {}


def ensure_directories():
    """确保必要的目录存在"""
    for dir_path in [CONFIG_DIR, DATA_DIR, KNOWLEDGE_DIR, SKILLS_DIR]:
        dir_path.mkdir(parents=True, exist_ok=True)


def load_settings() -> Settings:
    """加载系统配置"""
    global current_settings
    if SETTINGS_FILE.exists():
        try:
            with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                current_settings = Settings(**data)
        except Exception as e:
            print(f"Error loading settings: {e}")
            current_settings = Settings()
    return current_settings


def save_settings(settings: Settings):
    """保存系统配置"""
    with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
        json.dump(settings.model_dump(), f, ensure_ascii=False, indent=2)
    global current_settings
    current_settings = settings


def load_knowledge_bases():
    """加载知识库列表"""
    global knowledge_bases
    index_file = KNOWLEDGE_DIR / "index.json"
    if index_file.exists():
        try:
            with open(index_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                knowledge_bases = {
                    kb_id: KnowledgeBase(**kb_data)
                    for kb_id, kb_data in data.items()
                }
        except Exception as e:
            print(f"Error loading knowledge bases: {e}")
    return knowledge_bases


def save_knowledge_bases(kbs=None):
    """保存知识库列表"""
    global knowledge_bases
    if kbs is not None:
        knowledge_bases = kbs
    index_file = KNOWLEDGE_DIR / "index.json"
    data = {kb_id: kb.model_dump() for kb_id, kb in knowledge_bases.items()}
    with open(index_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def init_builtin_skills():
    """初始化内置技能"""
    from datetime import datetime
    builtin_skills = [
        Skill(
            id="code_reviewer",
            name="代码审查专家",
            description="智能代码审查，发现潜在问题并提供优化建议",
            version="1.0.0",
            author="DATA-AI Team",
            category="code_generation",
            type="built_in",
            icon="🔍",
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat(),
            parameters=[
                {"name": "code", "type": "string", "description": "待审查的代码", "required": True},
                {"name": "language", "type": "string", "description": "编程语言", "required": False, "enum": ["python", "javascript", "typescript"]}
            ],
            prompts={
                "system_prompt": "你是一位资深的代码审查专家，请按照以下标准审查代码：\n1. 检查语法错误和潜在bug\n2. 评估代码风格和最佳实践\n3. 提供性能优化建议\n4. 指出安全隐患"
            }
        ),
        Skill(
            id="data_analyzer",
            name="数据分析助手",
            description="执行数据分析和可视化",
            version="1.0.0",
            author="DATA-AI Team",
            category="data_analysis",
            type="built_in",
            icon="📊",
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat(),
            parameters=[
                {"name": "data", "type": "string", "description": "数据", "required": True},
                {"name": "analysis_type", "type": "string", "description": "分析类型", "required": True, "enum": ["summary", "statistics", "visualization"]}
            ]
        ),
        Skill(
            id="document_processor",
            name="文档处理助手",
            description="提取、总结和分析文档内容",
            version="1.0.0",
            author="DATA-AI Team",
            category="document_processing",
            type="built_in",
            icon="📄",
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat(),
            parameters=[
                {"name": "content", "type": "string", "description": "文档内容", "required": True},
                {"name": "task", "type": "string", "description": "任务类型", "required": True, "enum": ["summary", "key_points", "translation"]}
            ]
        )
    ]
    for skill in builtin_skills:
        skills[skill.id] = skill
    save_skills()


def load_skills():
    """加载技能列表"""
    global skills
    index_file = SKILLS_DIR / "index.json"
    if index_file.exists():
        try:
            with open(index_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                skills = {
                    skill_id: Skill(**skill_data)
                    for skill_id, skill_data in data.items()
                }
        except Exception as e:
            print(f"Error loading skills: {e}")
    if not skills:
        init_builtin_skills()
    return skills


def save_skills(skills_data=None):
    """保存技能列表"""
    global skills
    if skills_data is not None:
        skills = skills_data
    index_file = SKILLS_DIR / "index.json"
    data = {skill_id: skill.model_dump() for skill_id, skill in skills.items()}
    with open(index_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def load_mcp_servers():
    """加载MCP服务器配置"""
    global mcp_servers
    if MCP_CONFIG_FILE.exists():
        try:
            with open(MCP_CONFIG_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if "mcpServers" in data:
                    for server_id, server_data in data["mcpServers"].items():
                        mcp_servers[server_id] = MCPServer(
                            id=server_id,
                            name=server_data.get("name", server_id),
                            type=server_data.get("type", "stdio"),
                            command=server_data.get("command", ""),
                            args=server_data.get("args", []),
                            url=server_data.get("url", ""),
                            env=server_data.get("env", {}),
                            enabled=server_data.get("enabled", True),
                            icon="🔌"
                        )
        except Exception as e:
            print(f"Error loading MCP servers: {e}")
    return mcp_servers


def save_mcp_servers(mcp_data=None):
    """保存MCP服务器配置"""
    global mcp_servers
    if mcp_data is not None:
        mcp_servers = mcp_data
    data = {
        "mcpServers": {
            server_id: {
                "type": server.type,
                "command": server.command,
                "args": server.args,
                "url": server.url,
                "env": server.env,
                "enabled": server.enabled
            }
            for server_id, server in mcp_servers.items()
        }
    }
    with open(MCP_CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def initialize_storage():
    """初始化存储系统"""
    ensure_directories()
    load_settings()
    load_knowledge_bases()
    load_skills()
    load_mcp_servers()


# 别名函数，保持API兼容性
get_settings = load_settings
get_knowledge_bases = load_knowledge_bases
get_skills = load_skills
get_mcp_servers = load_mcp_servers

