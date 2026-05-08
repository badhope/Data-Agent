# LangChain Office Assistant

基于 LangChain 构建的智能办公助手 Agent，支持邮件、日程、文档和任务管理。

## 功能特性

- 📧 **邮件管理** - 发送、搜索、读取邮件
- 📅 **日程安排** - 查看日历、安排会议
- ✅ **任务管理** - 创建、追踪、列出任务
- 📄 **文档处理** - 搜索、总结文档

## 技术栈

- **LangChain** - Agent 框架
- **Chainlit** - 前端界面
- **LangGraph** - 状态图和运行时

## 快速开始

### 1. 安装依赖

```bash
pip install -e ".[cli]"
pip install chainlit pydantic==2.9.2
```

### 2. 设置环境变量

```bash
export OPENAI_API_KEY=sk-your-key
export LANGSMITH_TRACING=false
```

### 3. 启动

```bash
# Chainlit 前端
chainlit run chainlit_app.py

# 访问 http://localhost:8000
```

## 项目结构

```
.
├── chainlit_app.py                  # Chainlit 前端
├── pyproject.toml                   # 项目配置
└── langchain_office_assistant/
    ├── __init__.py                 # 主入口
    ├── tools/                      # 工具集
    │   └── __init__.py             # 9个工具
    └── agents/                     # Agent 模块
        └── __init__.py             # create_office_agent()
```

## 工具列表

| 工具 | 功能 |
|------|------|
| `send_email` | 发送邮件 |
| `search_emails` | 搜索邮件 |
| `read_email` | 读取邮件 |
| `check_calendar` | 查看日历 |
| `schedule_meeting` | 安排会议 |
| `create_task` | 创建任务 |
| `list_tasks` | 列出任务 |
| `search_documents` | 搜索文档 |
| `summarize_document` | 总结文档 |

## License

MIT
