<p align="center">
  <a href="#%23-%E4%B8%AD%E6%96%87%E8%8B%A8"><img alt="README in 中文" src="https://img.shields.io/badge/中文-FF8c00"></a>
  <a href="#%23-english"><img alt="README in English" src="https://img.shields.io/badge/English-3399ff"></a>
</p>

# Data-Agent - Intelligent Office Assistant

## Introduction

Data-Agent is an enterprise-grade intelligent office assistant platform built on Dify. It combines AI workflows, RAG (Retrieval-Augmented Generation), agent capabilities, and model management to streamline office work, helping you handle emails, schedules, documents, and tasks with AI-powered efficiency.

This platform is a customized version of [Dify](https://github.com/langgenius/dify), enhanced specifically for office automation scenarios.

## Key Features

### Core Features:

1. **AI Workflow**: Build visual workflows for email processing, document summarization, meeting scheduling, and more

2. **Multi-Model Support**: Seamless integration with OpenAI, Claude, Llama3, and any OpenAI-compatible models

3. **RAG Pipeline**: Advanced document processing and retrieval for knowledge management

4. **Agent Capabilities**: 50+ built-in tools for email, calendar, documents, and custom tools

5. **LLMOps**: Monitor and optimize your office agent over time

## Quick Start

System Requirements:
- CPU >= 2 Core
- RAM >= 4 GiB
- Docker & Docker Compose installed

```bash
cd Data-Agent/docker
cp .env.example .env
docker compose up -d
```

After running, access at [http://localhost/install](http://localhost/install) to complete initialization.

## Building an Office Assistant

Create your intelligent office assistant in 4 steps:

1. **Create Application**: Choose Agent or Chatflow
2. **Configure Model**: Connect your LLM (OpenAI, Claude, local model, etc.)
3. **Add Tools**: Integrate email, calendar, document processing tools
4. **Test & Deploy**: Deploy your customized office assistant

## Built-in Office Tools

- **Email Management**: Send, search, read emails via Gmail/Outlook API
- **Calendar**: Schedule meetings, check calendars via Google Calendar
- **Document**: Summarize, search, and manage documents
- **Task**: Create, list tasks with priority and deadlines

## Project Structure

```
Data-Agent/
├── api/              # Backend (Flask + Python)
├── web/              # Frontend (Next.js)
├── docker/          # Docker deployment
└── docs/            # Documentation
```

## Community & Contact

- [Dify Documentation](https://docs.dify.ai)
- [GitHub Issues](https://github.com/badhope/Data-Agent/issues)

## License

This repository is licensed under the Dify Open Source License based on Apache 2.0 with additional conditions.

---
---

# Data-Agent - 智能办公助手

## 简介

Data-Agent 是一个基于 Dify 构建的企业级智能办公助手平台。它结合了 AI 工作流、RAG（检索增强生成）、Agent 能力和模型管理，帮助您用 AI 高效处理邮件、日程、文档和任务。

本项目是 [Dify](https://github.com/langgenius/dify) 的定制版本，专门针对办公自动化场景进行了增强。

## 核心功能

主要特性：

1. **AI 工作流**：构建邮件处理、文档摘要、会议安排等可视化工作流

2. **多模型支持**：无缝集成 OpenAI、Claude、Llama3 及所有 OpenAI 兼容模型

3. **RAG 管道**：高级文档处理和检索能力，用于知识管理

4. **Agent 能力**：50+ 内置工具，支持邮件、日历、文档及自定义工具

5. **LLMOps**：持续监控和优化您的办公助手

## 快速开始

系统要求：
- CPU >= 2 核
- RAM >= 4 GiB
- 已安装 Docker 和 Docker Compose

```bash
cd Data-Agent/docker
cp .env.example .env
docker compose up -d
```

启动后，访问 [http://localhost/install](http://localhost/install) 完成初始化。

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
├── api/              # 后端 (Flask + Python)
├── web/              # 前端 (Next.js)
├── docker/          # Docker 部署
└── docs/            # 文档
```

## 社区与联系方式

- [Dify 官方文档](https://docs.dify.ai)
- [GitHub Issues](https://github.com/badhope/Data-Agent/issues)

## 许可证

本仓库采用基于 Apache 2.0 的 Dify 开源许可证。
