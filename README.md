<div align="center">

# 🤖 AI Controller Architecture

**Universal AI Integration Framework for API & Local LLMs**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.3-blue.svg)](https://www.typescriptlang.org/)
[![Node.js](https://img.shields.io/badge/Node.js-18+-green.svg)](https://nodejs.org/)

[English](#english-documentation) | [中文文档](#中文文档)

---

**A flexible, extensible AI control architecture that seamlessly integrates OpenAI, Anthropic, Ollama, LM Studio, and custom AI backends with unified interfaces.**

</div>

---

# English Documentation

## ✨ Features

| Feature | Description |
|---------|-------------|
| 🔌 **Multi-Provider Support** | OpenAI, Anthropic, Ollama, LM Studio, Custom APIs |
| 🔄 **Auto Fallback** | Automatic provider switching on failure |
| 🌊 **Streaming Response** | Real-time SSE streaming output |
| 🛠️ **Tool Calling** | Built-in Function Calling support |
| 💬 **Session Management** | Conversation history tracking |
| ⚙️ **Flexible Config** | Environment variables, JSON files, or code |
| 🏠 **Local LLM Ready** | Zero-cost local model support |

## 📦 Installation

```bash
npm install agent
# or
yarn add agent
# or
pnpm add agent
```

## 🚀 Quick Start

### Basic Usage

```typescript
import { createAIController, AIProviderFactory } from 'agent';

// Register your AI provider
AIProviderFactory.register({
  type: 'openai',
  name: 'my-gpt',
  apiKey: process.env.OPENAI_API_KEY,
  model: 'gpt-4',
});

// Create controller and chat
const ai = createAIController();
const response = await ai.chat('Hello, AI!');
console.log(response);
```

### Using Local Models (Ollama)

```typescript
import { createAIController, AIProviderFactory } from 'agent';

// Register local Ollama
AIProviderFactory.register({
  type: 'ollama',
  name: 'local-llama',
  baseUrl: 'http://localhost:11434',
  model: 'llama2',
});

// Use local model - completely free!
const ai = createAIController({ provider: 'local-llama' });
const response = await ai.chat('你好！');
```

### Streaming Response

```typescript
await ai.chat('Tell me a story', {
  stream: true,
  onChunk: (chunk) => {
    process.stdout.write(chunk.delta.content || '');
  },
});
```

### Tool Calling

```typescript
const ai = createAIController();

// Register tools
ai.registerTool({
  name: 'get_weather',
  description: 'Get weather information for a city',
  execute: async (args) => {
    return `${args.city}: 25°C, Sunny`;
  },
});

// AI will automatically call tools when needed
const response = await ai.chat('What\'s the weather in Beijing?', {
  useTools: true,
});
```

### Multi-Provider Fallback

```typescript
import { AIProviderFactory, createAIController } from 'agent';

// Register multiple providers with priority
AIProviderFactory.register({ type: 'openai', name: 'primary', ... }, 10);
AIProviderFactory.register({ type: 'ollama', name: 'backup', ... }, 5);

// Auto fallback when primary fails
const ai = createAIController({
  fallbackEnabled: true,
  onProviderSwitch: (from, to) => console.log(`Switched: ${from} → ${to}`),
});
```

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      User Application                        │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    AIController                              │
│  • Conversation Management                                   │
│  • Tool Orchestration                                        │
│  • Streaming Control                                         │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                   AIProviderFactory                          │
│  • Provider Registration                                     │
│  • Priority Management                                       │
│  • Auto Fallback                                             │
└─────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        ▼                     ▼                     ▼
┌─────────────┐       ┌─────────────┐       ┌─────────────┐
│ OpenAI      │       │ Ollama      │       │ LM Studio   │
│ Provider    │       │ Provider    │       │ Provider    │
└─────────────┘       └─────────────┘       └─────────────┘
        │                     │                     │
        ▼                     ▼                     ▼
   Cloud API            Local Server           Local Server
```

## 📋 Supported Providers

| Provider | Type | Endpoint | Features |
|----------|------|----------|----------|
| OpenAI | `openai` | api.openai.com | Full API support |
| Anthropic | `anthropic` | api.anthropic.com | Claude models |
| Ollama | `ollama` | localhost:11434 | Local, free |
| LM Studio | `lmstudio` | localhost:1234 | OpenAI-compatible |
| Custom | `custom` | Your endpoint | Any OpenAI-compatible API |

## ⚙️ Configuration

### Environment Variables

```bash
# .env file
OPENAI_API_KEY=sk-xxx
OPENAI_MODEL=gpt-4

OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama2

DEFAULT_PROVIDER=openai
```

### JSON Configuration

```json
{
  "providers": [
    { "type": "openai", "name": "main", "model": "gpt-4" },
    { "type": "ollama", "name": "local", "model": "llama2" }
  ],
  "defaultProvider": "main",
  "fallbackEnabled": true
}
```

## 📚 API Reference

### AIController

| Method | Description |
|--------|-------------|
| `chat(content, options)` | Send message and get response |
| `setSystemPrompt(prompt)` | Set system prompt |
| `registerTool(tool)` | Register a tool |
| `clearHistory()` | Clear conversation history |
| `switchProvider(name)` | Switch to another provider |

### AIProviderFactory

| Method | Description |
|--------|-------------|
| `register(config, priority)` | Register a provider |
| `get(name)` | Get provider by name |
| `getDefault()` | Get default provider |
| `setDefault(name)` | Set default provider |
| `getAll()` | Get all providers |

---

# 中文文档

## ✨ 特性

| 特性 | 说明 |
|------|------|
| 🔌 **多后端支持** | OpenAI、Anthropic、Ollama、LM Studio、自定义API |
| 🔄 **自动降级** | Provider失败时自动切换备用服务 |
| 🌊 **流式响应** | 实时SSE流式输出 |
| 🛠️ **工具调用** | 内置Function Calling支持 |
| 💬 **会话管理** | 对话历史追踪 |
| ⚙️ **灵活配置** | 环境变量、JSON文件或代码配置 |
| 🏠 **本地模型** | 支持零成本的本地大模型 |

## 📦 安装

```bash
npm install agent
```

## 🚀 快速开始

### 基础使用

```typescript
import { createAIController, AIProviderFactory } from 'agent';

// 注册AI服务
AIProviderFactory.register({
  type: 'openai',
  name: 'my-gpt',
  apiKey: process.env.OPENAI_API_KEY,
  model: 'gpt-4',
});

// 创建控制器并对话
const ai = createAIController();
const response = await ai.chat('你好！');
console.log(response);
```

### 使用本地模型 (Ollama)

```typescript
import { createAIController, AIProviderFactory } from 'agent';

// 注册本地Ollama
AIProviderFactory.register({
  type: 'ollama',
  name: 'local-llama',
  baseUrl: 'http://localhost:11434',
  model: 'llama2',
});

// 使用本地模型 - 完全免费！
const ai = createAIController({ provider: 'local-llama' });
const response = await ai.chat('你好！');
```

### 流式响应

```typescript
await ai.chat('讲个故事', {
  stream: true,
  onChunk: (chunk) => {
    process.stdout.write(chunk.delta.content || '');
  },
});
```

### 工具调用

```typescript
const ai = createAIController();

// 注册工具
ai.registerTool({
  name: 'get_weather',
  description: '获取城市天气信息',
  execute: async (args) => {
    return `${args.city}: 25°C, 晴天`;
  },
});

// AI会自动判断并调用工具
const response = await ai.chat('北京今天天气怎么样？', {
  useTools: true,
});
```

### 多服务降级

```typescript
import { AIProviderFactory, createAIController } from 'agent';

// 按优先级注册多个服务
AIProviderFactory.register({ type: 'openai', name: 'primary', ... }, 10);
AIProviderFactory.register({ type: 'ollama', name: 'backup', ... }, 5);

// 主服务失败时自动切换
const ai = createAIController({
  fallbackEnabled: true,
  onProviderSwitch: (from, to) => console.log(`切换: ${from} → ${to}`),
});
```

## 🏗️ 架构设计

```
┌─────────────────────────────────────────────────────────────┐
│                      用户应用层                              │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    AIController 控制层                       │
│  • 对话管理  • 工具编排  • 流式控制                          │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                   AIProviderFactory 工厂层                   │
│  • Provider注册  • 优先级管理  • 自动降级                    │
└─────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        ▼                     ▼                     ▼
┌─────────────┐       ┌─────────────┐       ┌─────────────┐
│ OpenAI      │       │ Ollama      │       │ LM Studio   │
│ 云端API     │       │ 本地服务    │       │ 本地服务    │
└─────────────┘       └─────────────┘       └─────────────┘
```

## 📋 支持的AI服务

| 服务 | 类型 | 端点 | 特点 |
|------|------|------|------|
| OpenAI | `openai` | api.openai.com | 完整API支持 |
| Anthropic | `anthropic` | api.anthropic.com | Claude模型 |
| Ollama | `ollama` | localhost:11434 | 本地免费 |
| LM Studio | `lmstudio` | localhost:1234 | OpenAI兼容 |
| 自定义 | `custom` | 您的端点 | 任何OpenAI兼容API |

## ⚙️ 配置方式

### 环境变量

```bash
# .env 文件
OPENAI_API_KEY=sk-xxx
OPENAI_MODEL=gpt-4

OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama2

DEFAULT_PROVIDER=openai
```

### JSON配置文件

```json
{
  "providers": [
    { "type": "openai", "name": "main", "model": "gpt-4" },
    { "type": "ollama", "name": "local", "model": "llama2" }
  ],
  "defaultProvider": "main",
  "fallbackEnabled": true
}
```

## 📚 API参考

### AIController

| 方法 | 说明 |
|------|------|
| `chat(content, options)` | 发送消息并获取响应 |
| `setSystemPrompt(prompt)` | 设置系统提示 |
| `registerTool(tool)` | 注册工具 |
| `clearHistory()` | 清除对话历史 |
| `switchProvider(name)` | 切换Provider |

### AIProviderFactory

| 方法 | 说明 |
|------|------|
| `register(config, priority)` | 注册Provider |
| `get(name)` | 按名称获取Provider |
| `getDefault()` | 获取默认Provider |
| `setDefault(name)` | 设置默认Provider |
| `getAll()` | 获取所有Provider |

---

## 📄 License

[MIT License](LICENSE)

## 🤝 Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for details.

## 📧 Contact

- Issues: [GitHub Issues](https://github.com/your-repo/Agent/issues)
- Discussions: [GitHub Discussions](https://github.com/your-repo/Agent/discussions)
