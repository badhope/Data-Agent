# Data-Agent 项目指南

## 项目概述

Data-Agent 是一个智能数据助手平台，基于 OpenManus 构建，支持多种 AI Agent 类型和丰富的工具集，包括完整的文档处理和办公自动化功能。

## 代码结构

```
Data-Agent/
├── OpenManus/           # 核心项目
│   ├── main.py          # CLI 入口
│   ├── web_app.py       # Web API 入口（FastAPI）
│   ├── app/
│   │   ├── agent/       # Agent 实现（Data, Browser, SWE, MCP 等）
│   │   ├── tool/        # 工具集（bash, browser, file, python, search 等）
│   │   ├── document/    # 文档处理模块（新增）
│   │   ├── flow/        # Flow 编排
│   │   └── mcp/         # MCP 协议实现
│   ├── routers/         # API 路由
│   └── config/          # 配置文件
└── .devcontainer/       # 开发容器配置
```

## 文档处理模块（新增）

### app/document/ 模块功能
- **ppt_generator.py**: PPT 生成器，支持多种模板
- **summarizer.py**: 文档摘要生成，抽取式/生成式
- **meeting_minutes.py**: 会议纪要自动生成
- **report_generator.py**: 工作汇报生成（日报/周报/月报）
- **formatter.py**: 中文文本格式化
- **citation_manager.py**: 引用管理
- **todo_extractor.py**: 待办事项提取

### API 路由
- **routers/documents.py**: 文档处理 API，12个REST端点

## 运行方式

- **CLI**: `python OpenManus/web_app.py`（推荐）
- **Web API**: `python OpenManus/web_app.py` 并访问 http://localhost:8000`
- **Flow**: `python OpenManus/run_flow.py`
- **MCP**: `python OpenManus/run_mcp.py`

## 配置

配置文件位于 `OpenManus/config/config.toml`，支持多模型：
- OpenAI
- Anthropic
- Google
- Azure
- Ollama

## 测试

```bash
cd OpenManus
pytest
```

## 代码规范

- Python 3.10+
- 使用类型提示
- 遵循 Ruff 格式化
