# 办公智能体架构设计文档

## 1. 项目概述

本文档描述了办公智能体（Office Agent）的架构设计，这是一个基于 LangChain + LangGraph 构建的插件化智能体系统，旨在提供全面的办公自动化能力。

### 1.1 功能范围

| 功能模块 | 描述 | 状态 |
|---------|------|------|
| 邮件管理 | 发送、搜索、阅读邮件 | ✅ |
| 日历管理 | 查询日程、创建会议 | ✅ |
| 任务管理 | 创建、列表、状态更新 | ✅ |
| 文档处理 | Word/Excel/PDF读写 | ✅ |
| PPT生成 | 模板支持、图表嵌入 | ✅ |
| 知识库 | 向量检索、多模态支持 | ✅ |
| 图表报告 | 折线图、柱状图、雷达图等 | ✅ |
| 计算工具 | 公式计算、数据统计 | ✅ |
| 意图识别 | 上下文理解、多轮对话 | ✅ |
| 计算追溯 | 完整思考过程记录 | ✅ |

### 1.2 技术栈

- **框架**: LangChain + LangGraph
- **API框架**: FastAPI
- **向量数据库**: Milvus/Qdrant/Pinecone
- **文档处理**: python-docx, openpyxl, PyPDF2
- **PPT生成**: python-pptx
- **图表生成**: matplotlib, plotly
- **部署**: Docker, Docker Compose

## 2. 架构设计

### 2.1 整体架构

```
┌─────────────────────────────────────────────────────────────────┐
│                    Office Agent 办公智能体                       │
├─────────────────────────────────────────────────────────────────┤
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐        │
│  │   CLI    │  │  REST    │  │  Web UI  │  │  SDK     │        │
│  │ 入口层   │  │  API层   │  │  界面层  │  │  客户端  │        │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘        │
│       │             │             │             │               │
│  ┌────▼────────────────────────────────────┐                    │
│  │          Agent Core (智能体核心)         │                    │
│  │  ┌─────────────────────────────────┐    │                    │
│  │  │  IntentRecognizer (意图识别)     │    │                    │
│  │  │  PlanExecutor (计划执行器)       │    │                    │
│  │  │  MemoryManager (记忆管理)        │    │                    │
│  │  │  TraceRecorder (追溯记录器)      │    │                    │
│  │  └─────────────────────────────────┘    │                    │
│  └────┬────────────────────────────────────┘                    │
│       │                                                         │
│  ┌────▼─────────────────────────────────────────────────────┐   │
│  │                    Plugin System (插件系统)               │   │
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐        │   │
│  │  │ Email   │ │Calendar │ │  Task   │ │Document │        │   │
│  │  │  邮件   │ │ 日历    │ │  任务   │ │  文档   │        │   │
│  │  └─────────┘ └─────────┘ └─────────┘ └─────────┘        │   │
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐        │   │
│  │  │  PPT    │ │Knowledge│ │  Chart  │ │  Calc   │        │   │
│  │  │  演示   │ │  知识库  │ │  图表   │ │  计算   │        │   │
│  │  └─────────┘ └─────────┘ └─────────┘ └─────────┘        │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                               │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                    Data Layer (数据层)                   │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐   │   │
│  │  │ Vector DB    │  │  Relational  │  │  File Store  │   │   │
│  │  │  (向量数据库) │  │   Database   │  │   (文件存储) │   │   │
│  │  └──────────────┘  └──────────────┘  └──────────────┘   │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 核心组件

#### 2.2.1 Agent Core

| 组件 | 职责 | 关键特性 |
|-----|------|---------|
| **IntentRecognizer** | 意图识别与分类 | 上下文理解、多轮对话支持 |
| **PlanExecutor** | 任务规划与执行 | 工具调用协调、错误处理 |
| **MemoryManager** | 记忆管理 | 短期/长期记忆分离 |
| **TraceRecorder** | 执行追溯 | 完整思考过程记录、可视化 |

#### 2.2.2 Plugin System

| 插件 | 功能 | 依赖库 |
|-----|------|-------|
| **EmailPlugin** | 邮件发送/搜索/阅读 | smtplib, imaplib |
| **CalendarPlugin** | 日历查询/会议创建 | icalendar |
| **TaskPlugin** | 任务CRUD | SQLAlchemy |
| **DocumentPlugin** | 文档读写 | python-docx, openpyxl, PyPDF2 |
| **PPTPlugin** | PPT生成 | python-pptx |
| **KnowledgePlugin** | 知识库检索 | langchain-community |
| **ChartPlugin** | 图表生成 | matplotlib, plotly |
| **CalcPlugin** | 计算工具 | pandas, numpy |

## 3. 目录结构

```
langchain_office_assistant/
├── agents/                    # 智能体核心
│   ├── __init__.py
│   ├── core.py                # 智能体核心逻辑
│   ├── intent_recognizer.py   # 意图识别
│   ├── plan_executor.py       # 计划执行器
│   ├── memory_manager.py      # 记忆管理
│   └── trace_recorder.py      # 追溯记录器
├── plugins/                   # 插件系统
│   ├── __init__.py
│   ├── base.py                # 插件基类
│   ├── email/                 # 邮件插件
│   │   ├── __init__.py
│   │   └── plugin.py
│   ├── calendar/              # 日历插件
│   │   ├── __init__.py
│   │   └── plugin.py
│   ├── task/                  # 任务插件
│   │   ├── __init__.py
│   │   └── plugin.py
│   ├── document/              # 文档插件
│   │   ├── __init__.py
│   │   └── plugin.py
│   ├── ppt/                   # PPT插件
│   │   ├── __init__.py
│   │   └── plugin.py
│   ├── knowledge/             # 知识库插件
│   │   ├── __init__.py
│   │   └── plugin.py
│   ├── chart/                 # 图表插件
│   │   ├── __init__.py
│   │   └── plugin.py
│   └── calc/                  # 计算插件
│       ├── __init__.py
│       └── plugin.py
├── tools/                     # 工具封装
│   ├── __init__.py
│   └── registry.py            # 工具注册中心
├── utils/                     # 工具函数
│   ├── __init__.py
│   ├── config.py              # 配置管理
│   ├── logger.py              # 日志管理
│   └── helpers.py             # 辅助函数
├── data/                      # 数据层
│   ├── __init__.py
│   ├── vector_db.py           # 向量数据库
│   └── file_store.py          # 文件存储
├── api/                       # API服务
│   ├── __init__.py
│   ├── main.py                # FastAPI入口
│   ├── endpoints/             # API端点
│   │   ├── __init__.py
│   │   ├── chat.py            # 聊天接口
│   │   └── trace.py           # 追溯接口
│   └── dependencies.py        # 依赖注入
├── cli/                       # 命令行接口
│   ├── __init__.py
│   └── main.py
├── docker/                    # Docker配置
│   ├── Dockerfile
│   └── docker-compose.yml
├── tests/                     # 测试用例
│   ├── __init__.py
│   ├── test_agents.py
│   └── test_plugins.py
├── pyproject.toml
├── requirements.txt
└── README.md
```

## 4. 关键接口设计

### 4.1 插件基类

```python
class BasePlugin(ABC):
    name: str
    description: str
    version: str = "1.0.0"
    
    @abstractmethod
    def initialize(self, config: dict) -> None:
        """初始化插件"""
    
    @abstractmethod
    def get_tools(self) -> list[BaseTool]:
        """获取插件提供的工具列表"""
    
    @abstractmethod
    async def execute(self, tool_name: str, **kwargs) -> Any:
        """执行工具调用"""
```

### 4.2 智能体核心接口

```python
class OfficeAgent:
    def __init__(self, plugins: list[BasePlugin], config: dict):
        """初始化智能体"""
    
    async def chat(
        self, 
        message: str, 
        session_id: str = None,
        context: dict = None
    ) -> dict:
        """处理用户消息"""
    
    def get_trace(self, session_id: str) -> dict:
        """获取执行追溯信息"""
    
    def clear_memory(self, session_id: str) -> None:
        """清除会话记忆"""
```

### 4.3 API接口

| 端点 | 方法 | 描述 |
|-----|------|------|
| `/api/chat` | POST | 发送消息获取响应 |
| `/api/trace/{session_id}` | GET | 获取会话追溯 |
| `/api/plugins` | GET | 获取已加载插件列表 |
| `/api/health` | GET | 健康检查 |

## 5. 数据流设计

```
用户输入 → IntentRecognizer → 意图分类
                              ↓
                        PlanExecutor → 生成执行计划
                              ↓
                        调用对应Plugin工具
                              ↓
                        TraceRecorder记录
                              ↓
                        返回结果给用户
```

### 5.1 执行流程

1. **输入处理**: 用户消息进入系统
2. **意图识别**: 识别用户意图和需求
3. **计划生成**: 生成执行计划和工具调用序列
4. **工具执行**: 调用相应插件工具
5. **结果汇总**: 汇总工具执行结果
6. **响应生成**: 生成自然语言响应
7. **追溯记录**: 记录完整执行过程

## 6. 部署架构

### 6.1 Docker Compose服务

| 服务 | 镜像 | 端口 | 说明 |
|-----|------|------|------|
| api | office-agent | 8000 | 主API服务 |
| redis | redis:latest | 6379 | 缓存和会话存储 |
| milvus | milvusdb/milvus | 19530 | 向量数据库 |
| postgres | postgres:15 | 5432 | 关系数据库 |

### 6.2 环境变量

| 变量名 | 说明 | 默认值 |
|-------|------|-------|
| AGENT_MODEL | 语言模型名称 | gpt-4 |
| VECTOR_DB_URL | 向量数据库连接 | localhost:19530 |
| REDIS_URL | Redis连接 | redis://localhost:6379 |
| LOG_LEVEL | 日志级别 | INFO |

## 7. 安全考虑

- API认证：使用API Key或OAuth2
- 数据加密：传输和存储加密
- 权限控制：基于角色的访问控制
- 输入验证：防止注入攻击

## 8. 扩展计划

- WebSocket支持实时流式响应
- 多语言支持
- 自定义插件市场
- 移动端SDK