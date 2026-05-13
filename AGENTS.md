# Data-Agent 项目指南

## 项目概述

Data-Agent 是一个智能数据助手平台，基于 OpenManus 构建，支持多种 AI Agent 类型和丰富的工具集。

## 代码结构

```
Data-Agent/
├── OpenManus/           # 核心项目
│   ├── main.py          # CLI 入口
│   ├── web_app.py       # Web API 入口（FastAPI）
│   ├── app/
│   │   ├── agent/       # Agent 实现（Data, Browser, SWE, MCP 等）
│   │   ├── tool/        # 工具集（bash, browser, file, python, search 等）
│   │   ├── flow/        # Flow 编排
│   │   └── mcp/         # MCP 协议实现
│   └── config/          # 配置文件
└── .devcontainer/       # 开发容器配置
```

## 运行方式

- **CLI**: `python OpenManus/main.py`
- **Web API**: `python OpenManus/web_app.py`
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

- Python 3.12+
- 使用类型提示
- 遵循 Ruff 格式化
