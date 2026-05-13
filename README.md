<p align="center">
  <a href="#%23-中文"><img alt="README in 中文" src="https://img.shields.io/badge/中文-FF8c00"></a>
  <a href="#%23-english"><img alt="README in English" src="https://img.shields.io/badge/English-3399ff"></a>
</p>

# Data-Agent - 智能办公助手

## 简介

Data-Agent 是一个企业级智能办公助手平台，基于 Dify 构建，结合了 AI 工作流、RAG（检索增强生成）、Agent 能力和模型管理，帮助您用 AI 高效处理邮件、日程、文档和任务。

## 核心功能

1. **AI 工作流**：构建邮件处理、文档摘要、会议安排等可视化工作流
2. **多模型支持**：无缝集成 OpenAI、Claude、Llama3 及所有 OpenAI 兼容模型
3. **RAG 管道**：高级文档处理和检索能力，用于知识管理
4. **Agent 能力**：50+ 内置工具，支持邮件、日历、文档及自定义工具
5. **LLMOps**：持续监控和优化您的办公助手

## 快速开始

### 环境要求

- CPU >= 2 核
- RAM >= 4 GiB
- Docker & Docker Compose
- Python 3.12+
- Node.js 22+

### 一键部署（推荐）

Docker 方式会自动下载并配置所有依赖环境（数据库、缓存、向量数据库等），无需手动安装：

```bash
git clone https://github.com/badhope/Data-Agent.git
cd Data-Agent/docker
cp .env.example .env
docker compose up -d
```

启动后，访问 [http://localhost/install](http://localhost/install) 完成初始化，即可使用 Web 前端。

### 本地开发

如需本地开发调试：

```bash
# 1. 克隆项目
git clone https://github.com/badhope/Data-Agent.git
cd Data-Agent

# 2. 启动中间件服务（PostgreSQL、Redis 等）
cd docker
cp .env.example .env
docker compose -f docker-compose.middleware.yaml up -d

# 3. 安装前端依赖并启动
cd ../web
cp .env.example .env.local
pnpm install
pnpm dev

# 4. 安装后端依赖并启动（需要 Python 3.12+）
cd ../api
uv sync
flask upgrade-db
flask run
```

## 构建办公助手

分 4 步创建您的智能办公助手：

1. **创建应用**：选择 Agent 或 Chatflow
2. **配置模型**：连接您的 LLM（OpenAI、Claude、本地模型等）
3. **添加工具**：集成邮件、日历、文档处理工具
4. **测试和部署**：部署您定制的办公助手

## 内置办公工具

- **邮件管理**：通过 Gmail/Outlook API 发送、搜索、读取邮件
- **日历**：安排会议、通过 Google Calendar 查看日程
- **文档**：摘要、搜索和管理文档
- **任务**：创建、列出带优先级和截止日期的任务

## 项目结构

```
Data-Agent/
├── web/              # 前端 (Next.js) - 默认入口
├── api/              # 后端 (Flask + Python)
├── docker/           # Docker 部署配置
├── OpenManus/        # AI Agent 模块
└── docs/             # 文档
```

## 技术栈

| 组件 | 技术 |
|------|------|
| 前端 | Next.js 16, React 19, TypeScript, Tailwind CSS |
| 后端 | Python 3.12+, Flask, LangChain, Celery |
| 数据库 | PostgreSQL 15, Redis |
| 向量数据库 | Weaviate / Qdrant / PGVector / Milvus（可选） |
| 部署 | Docker, Docker Compose, Nginx |

## 社区与联系方式

- [Dify 官方文档](https://docs.dify.ai)
- [GitHub Issues](https://github.com/badhope/Data-Agent/issues)

## 许可证

本仓库采用基于 Apache 2.0 的 Dify 开源许可证。

---
---

# Data-Agent - Intelligent Office Assistant

## Introduction

Data-Agent is an enterprise-grade intelligent office assistant platform built on Dify. It combines AI workflows, RAG (Retrieval-Augmented Generation), agent capabilities, and model management to streamline office work, helping you handle emails, schedules, documents, and tasks with AI-powered efficiency.

## Key Features

1. **AI Workflow**: Build visual workflows for email processing, document summarization, meeting scheduling, and more
2. **Multi-Model Support**: Seamless integration with OpenAI, Claude, Llama3, and any OpenAI-compatible models
3. **RAG Pipeline**: Advanced document processing and retrieval for knowledge management
4. **Agent Capabilities**: 50+ built-in tools for email, calendar, documents, and custom tools
5. **LLMOps**: Monitor and optimize your office agent over time

## Quick Start

### Requirements

- CPU >= 2 Cores
- RAM >= 4 GiB
- Docker & Docker Compose
- Python 3.12+
- Node.js 22+

### One-Click Deployment (Recommended)

Docker deployment automatically downloads and configures all dependencies (databases, caches, vector databases, etc.):

```bash
git clone https://github.com/badhope/Data-Agent.git
cd Data-Agent/docker
cp .env.example .env
docker compose up -d
```

After startup, visit [http://localhost/install](http://localhost/install) to complete initialization.

### Local Development

```bash
# 1. Clone the project
git clone https://github.com/badhope/Data-Agent.git
cd Data-Agent

# 2. Start middleware services
cd docker
cp .env.example .env
docker compose -f docker-compose.middleware.yaml up -d

# 3. Install and start frontend
cd ../web
cp .env.example .env.local
pnpm install
pnpm dev

# 4. Install and start backend (Python 3.12+)
cd ../api
uv sync
flask upgrade-db
flask run
```

## License

This repository is licensed under the Dify Open Source License based on Apache 2.0 with additional conditions.
