"""
DataAgent - 数据持久化层
全局状态管理、数据加载/保存、内置技能初始化
"""

import json
import datetime
from pathlib import Path
from typing import Dict

from config import *
from models import Settings, KnowledgeBase, Document, Skill, MCPServer, Database

# ============================================================
# 全局状态字典
# ============================================================

current_settings: Settings = Settings()
knowledge_bases: Dict[str, KnowledgeBase] = {}
documents: Dict[str, Document] = {}
skills: Dict[str, Skill] = {}
mcp_servers: Dict[str, MCPServer] = {}
conversations: Dict[str, dict] = {}
databases: Dict[str, Database] = {}

# ============================================================
# 会话 (Conversations) 加载/保存
# ============================================================

def load_conversations():
    if CONVERSATIONS_FILE.exists():
        try:
            with open(CONVERSATIONS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading conversations: {e}")
    return {}

def save_conversations():
    with open(CONVERSATIONS_FILE, 'w', encoding='utf-8') as f:
        json.dump(conversations, f, ensure_ascii=False, indent=2)

# ============================================================
# 设置 (Settings) 加载/保存
# ============================================================

def load_settings():
    if SETTINGS_FILE.exists():
        try:
            with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return Settings(**data)
        except Exception as e:
            print(f"Error loading settings: {e}")
    return Settings()

def save_settings(settings: Settings):
    with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
        json.dump(settings.model_dump(), f, ensure_ascii=False, indent=2)

# ============================================================
# 知识库 (Knowledge Bases) 加载/保存
# ============================================================

def load_knowledge_bases():
    index_file = KNOWLEDGE_DIR / "index.json"
    if index_file.exists():
        try:
            with open(index_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                for kb_id, kb_data in data.items():
                    knowledge_bases[kb_id] = KnowledgeBase(**kb_data)
        except Exception as e:
            print(f"Error loading knowledge bases: {e}")

def save_knowledge_bases():
    index_file = KNOWLEDGE_DIR / "index.json"
    data = {kb_id: kb.model_dump() for kb_id, kb in knowledge_bases.items()}
    with open(index_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# ============================================================
# 技能 (Skills) 加载/保存
# ============================================================

def load_skills():
    index_file = SKILLS_DIR / "index.json"
    if index_file.exists():
        try:
            with open(index_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                for skill_id, skill_data in data.items():
                    skills[skill_id] = Skill(**skill_data)
        except Exception as e:
            print(f"Error loading skills: {e}")
    if not skills:
        init_builtin_skills()

def save_skills():
    index_file = SKILLS_DIR / "index.json"
    data = {skill_id: skill.model_dump() for skill_id, skill in skills.items()}
    with open(index_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# ============================================================
# 内置技能初始化
# ============================================================

def init_builtin_skills():
    builtin = [
        Skill(
            id="code_reviewer",
            name="代码审查专家",
            description="智能代码审查，发现潜在问题并提供优化建议",
            version="1.0.0",
            author="DataAgent Team",
            category="code_generation",
            type="built_in",
            icon="🔍",
            created_at=datetime.datetime.now().isoformat(),
            updated_at=datetime.datetime.now().isoformat(),
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
            author="DataAgent Team",
            category="data_analysis",
            type="built_in",
            icon="📊",
            created_at=datetime.datetime.now().isoformat(),
            updated_at=datetime.datetime.now().isoformat(),
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
            author="DataAgent Team",
            category="document_processing",
            type="built_in",
            icon="📄",
            created_at=datetime.datetime.now().isoformat(),
            updated_at=datetime.datetime.now().isoformat(),
            parameters=[
                {"name": "content", "type": "string", "description": "文档内容", "required": True},
                {"name": "task", "type": "string", "description": "任务类型", "required": True, "enum": ["summary", "key_points", "translation"]}
            ]
        )
    ]
    for skill in builtin:
        skills[skill.id] = skill
    save_skills()

# ============================================================
# MCP 服务器加载/保存
# ============================================================

def load_mcp_servers():
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

def save_mcp_servers():
    data = {
        "mcpServers": {
            server_id: {
                "type": server.type,
                "command": server.command,
                "args": server.args,
                "url": server.url,
                "env": server.env,
                "enabled": server.enabled
            } for server_id, server in mcp_servers.items()
        }
    }
    with open(MCP_CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# ============================================================
# 数据库 (Databases) 加载/保存
# ============================================================

def load_databases():
    db_file = DATA_DIR / "databases.json"
    if db_file.exists():
        try:
            with open(db_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return {k: Database(**v) for k, v in data.items()}
        except Exception as e:
            print(f"Error loading databases: {e}")
    return {}

def save_databases():
    with open(DATA_DIR / "databases.json", 'w', encoding='utf-8') as f:
        json.dump({k: v.model_dump() if hasattr(v, 'model_dump') else v for k, v in databases.items()}, f, ensure_ascii=False, indent=2)

# ============================================================
# 初始化：启动时加载所有数据
# ============================================================

def init_all():
    """启动时加载所有持久化数据到全局状态"""
    global current_settings, conversations, databases

    # 加载设置
    current_settings = load_settings()

    # 加载会话
    conversations = load_conversations()

    # 加载知识库
    load_knowledge_bases()

    # 加载技能（内部会调用 init_builtin_skills 如果为空）
    load_skills()

    # 加载 MCP 服务器
    load_mcp_servers()

    # 加载数据库
    databases = load_databases()
