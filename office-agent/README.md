# Office Agent - 基于 LangChain 的智能办公助手

基于 LangChain 构建的智能办公助手 Agent，支持邮件、日程、文档和任务管理。

## 功能特性

- 📧 **邮件管理** - 发送、回复、搜索邮件
- 📅 **日程安排** - 创建会议、查看日程、查找空闲时间
- 📄 **文档处理** - 读取、总结、创建文档
- ✅ **任务管理** - 创建、追踪、完成待办

## 快速开始

### 1. 安装依赖

```bash
cd office-agent
pip install -r requirements.txt
```

### 2. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env 填入您的 OPENAI_API_KEY
```

### 3. 运行

```bash
# 交互模式
python main.py

# 演示模式
python main.py --mode demo
```

## 项目结构

```
office-agent/
├── src/
│   ├── core/           # 核心 Agent 框架
│   │   ├── agent.py    # Agent 主类
│   │   └── config.py   # 配置管理
│   ├── tools/          # 工具集
│   │   ├── email_tools.py
│   │   ├── calendar_tools.py
│   │   ├── document_tools.py
│   │   └── task_tools.py
│   └── memory/         # 记忆系统
├── main.py             # 程序入口
└── requirements.txt     # 依赖列表
```

## 技术栈

- **LangChain** - Agent 框架
- **LangChain OpenAI** - LLM 接口
- **Python 3.10+** - 运行环境
