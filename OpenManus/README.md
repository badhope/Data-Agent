# Data-Agent

智能数据助手 - 基于 OpenManus 的 AI Agent 平台

## 简介

Data-Agent 是一个强大的 AI Agent 平台，支持多种 Agent 类型、丰富的工具集和灵活的配置系统。

## 核心功能

- **8 种 Agent 类型**: Data, DataAnalysis, Browser, SWE, MCP, ReAct, Sandbox, ToolCall
- **15+ 真实工具**: 网页搜索、浏览器自动化、文件操作、Python 执行、数据可视化等
- **多模型支持**: OpenAI, Anthropic, Azure, Google, Ollama, PPIO 等
- **多种运行方式**: CLI、Web API、Flow 编排、MCP 协议

## 快速开始

### 环境要求

- Python 3.10+
- pip 或 uv

### 安装（推荐）

```bash
# 克隆项目
git clone https://github.com/badhope/Data-Agent.git
cd Data-Agent/OpenManus

# 一键安装（自动安装依赖、创建配置文件）
./setup.sh
```

### 手动安装

```bash
# 安装依赖
pip install -r requirements.txt

# 复制配置模板
cp config/config.example.toml config/config.toml

# 编辑配置文件，填入你的 API Key
# 支持 OpenAI, Anthropic, Google, Ollama 等
```

### 验证安装

```bash
# 检查配置是否正确
python check_config.py
```

### 运行

```bash
# Web 模式（推荐）
python web_app.py
# 访问 http://localhost:8000

# CLI 模式
python main.py

# Flow 模式
python run_flow.py

# MCP 模式
python run_mcp.py
```

## 项目结构

```
Data-Agent/
├── OpenManus/           # 核心项目
│   ├── main.py          # CLI 入口
│   ├── web_app.py       # Web API 入口
│   ├── run_flow.py      # Flow 运行器
│   ├── run_mcp.py       # MCP Agent
│   ├── setup.sh         # 一键安装脚本
│   ├── check_config.py  # 配置检查工具
│   ├── app/
│   │   ├── agent/       # Agent 实现
│   │   ├── tool/        # 工具集
│   │   ├── flow/        # Flow 编排
│   │   ├── mcp/         # MCP 协议
│   │   └── prompt/      # Prompt 模板
│   └── config/          # 配置文件
├── .devcontainer/       # 开发容器配置
└── README.md
```

## Agent 类型

| Agent | 说明 |
|-------|------|
| Data | 数据处理 Agent |
| DataAnalysis | 数据分析 Agent |
| Browser | 浏览器自动化 Agent |
| SWE | 软件工程 Agent |
| MCP | MCP 协议 Agent |
| ReAct | ReAct 推理 Agent |
| Sandbox | 沙箱执行 Agent |
| ToolCall | 工具调用 Agent |

## 工具集

| 工具 | 说明 |
|------|------|
| bash | Shell 命令执行 |
| browser_use | 浏览器自动化 |
| crawl4ai | 网页爬取 |
| file_operators | 文件读写 |
| python_execute | Python 代码执行 |
| web_search | 网页搜索 |
| planning | 任务规划 |
| chart_visualization | 图表可视化 |

## 浏览器自动化（可选）

如需使用浏览器自动化功能，安装 Playwright：

```bash
pip install playwright
playwright install chromium
```

## 许可证

MIT License
