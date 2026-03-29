# Architecture Deep Dive / 架构深入解析

This document provides a comprehensive explanation of the AI Controller Architecture's design principles, components, and data flow.

本文档全面解释AI控制器架构的设计原则、组件和数据流。

---

## Table of Contents / 目录

- [Design Philosophy / 设计理念](#design-philosophy--设计理念)
- [Core Components / 核心组件](#core-components--核心组件)
- [Data Flow / 数据流](#data-flow--数据流)
- [Provider System / Provider系统](#provider-system--provider系统)
- [Tool Calling / 工具调用](#tool-calling--工具调用)
- [Error Handling / 错误处理](#error-handling--错误处理)

---

## Design Philosophy / 设计理念

### Abstraction Layer / 抽象层

The architecture uses a multi-layer abstraction design to decouple user code from specific AI implementations:

架构采用多层抽象设计，将用户代码与具体AI实现解耦：

```
User Code → Controller → Factory → Provider → AI Service
   │           │           │          │          │
   └───────────┴───────────┴──────────┴──────────┘
                    Unified Interface / 统一接口
```

### Key Principles / 核心原则

1. **Unified Interface / 统一接口**: All providers implement the same `AIProvider` interface
2. **Dependency Injection / 依赖注入**: Providers are registered and retrieved through factory
3. **Strategy Pattern / 策略模式**: Different providers can be swapped at runtime
4. **Observer Pattern / 观察者模式**: Streaming and events use callback hooks

---

## Core Components / 核心组件

### 1. Types (`types.ts`)

Defines all interfaces and types used throughout the system:

定义整个系统使用的所有接口和类型：

```typescript
// Core message structure / 核心消息结构
interface AIMessage {
  role: 'system' | 'user' | 'assistant' | 'tool';
  content: string;
  toolCalls?: ToolCall[];
}

// Request/Response types / 请求/响应类型
interface AIRequest { messages: AIMessage[]; ... }
interface AIResponse { message: AIMessage; ... }

// Provider interface / Provider接口
interface AIProvider {
  chat(request: AIRequest): Promise<AIResponse>;
  chatStream(request: AIRequest, onChunk: Function): Promise<void>;
}
```

### 2. AIProviderFactory (`factory.ts`)

Manages provider registration, selection, and fallback:

管理Provider注册、选择和降级：

```typescript
class AIProviderFactory {
  // Registry with priority / 按优先级注册
  private static providers: Map<string, ProviderRegistryEntry>;
  
  // Create provider instance / 创建Provider实例
  private static createProvider(config: AIProviderConfig): AIProvider;
  
  // Get by name or default / 按名称或默认获取
  static get(name: string): AIProvider;
  static getDefault(): AIProvider;
}
```

### 3. AIController (`controller.ts`)

High-level API for user interaction:

用户交互的高级API：

```typescript
class AIController {
  private conversationHistory: AIMessage[];
  private tools: Map<string, ToolExecutor>;
  
  // Main chat method / 主要对话方法
  async chat(content: string, options?: ChatOptions): Promise<string>;
  
  // Tool management / 工具管理
  registerTool(tool: ToolExecutor): void;
  
  // Provider switching / Provider切换
  async switchProvider(name: string): Promise<boolean>;
}
```

### 4. Providers (`providers/`)

Concrete implementations for different AI services:

不同AI服务的具体实现：

| Provider | Class | Endpoint | Notes |
|----------|-------|----------|-------|
| OpenAI | `OpenAIProvider` | api.openai.com | Full API support |
| Anthropic | `OpenAIProvider` | api.anthropic.com | Adapted headers |
| Ollama | `OllamaProvider` | localhost:11434 | Native API format |
| LM Studio | `LMStudioProvider` | localhost:1234 | OpenAI-compatible |

---

## Data Flow / 数据流

### Simple Chat Flow / 简单对话流程

```
┌──────────────────────────────────────────────────────────────────┐
│ 1. User calls: ai.chat("Hello")                                  │
└──────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────────┐
│ 2. AIController builds message array                             │
│    [{ role: 'user', content: 'Hello' }]                          │
└──────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────────┐
│ 3. AIProviderFactory.getDefault() returns Provider               │
└──────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────────┐
│ 4. Provider.chat() sends HTTP request to AI service              │
│    POST /chat/completions                                        │
│    Body: { model, messages, ... }                                │
└──────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────────┐
│ 5. AI service processes and returns response                     │
└──────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────────┐
│ 6. Provider parses response to AIResponse format                 │
└──────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────────┐
│ 7. AIController saves to history and returns content             │
└──────────────────────────────────────────────────────────────────┘
```

### Tool Calling Flow / 工具调用流程

```
┌──────────────────────────────────────────────────────────────────┐
│ User: "What's the weather in Beijing?"                           │
└──────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────────┐
│ AI Response: tool_calls: [{ name: 'get_weather', args: {...} }]  │
└──────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────────┐
│ AIController detects tool_calls                                  │
│ → Executes ToolExecutor.execute(args)                            │
│ → Returns: "Beijing: 25°C, Sunny"                                │
└──────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────────┐
│ AIController appends tool result to messages                     │
│ { role: 'tool', content: 'Beijing: 25°C, Sunny' }                │
└──────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────────┐
│ Second AI call with tool result                                  │
│ AI generates final response: "北京今天天气晴朗，温度25°C..."      │
└──────────────────────────────────────────────────────────────────┘
```

---

## Provider System / Provider系统

### Provider Registration / Provider注册

```typescript
// Register with priority (higher = preferred)
// 按优先级注册（越高越优先）
AIProviderFactory.register({
  type: 'openai',
  name: 'gpt4',
  apiKey: 'sk-xxx',
  model: 'gpt-4',
}, 10);  // Priority 10

AIProviderFactory.register({
  type: 'ollama',
  name: 'local',
  model: 'llama2',
}, 5);   // Priority 5
```

### Fallback Mechanism / 降级机制

```typescript
// When primary provider fails
// 当主Provider失败时
try {
  response = await primaryProvider.chat(request);
} catch (error) {
  // Try next available provider
  // 尝试下一个可用Provider
  for (const provider of fallbackProviders) {
    try {
      response = await provider.chat(request);
      break;
    } catch (e) {
      continue;
    }
  }
}
```

---

## Tool Calling / 工具调用

### Tool Definition / 工具定义

```typescript
interface ToolExecutor {
  name: string;           // Tool identifier / 工具标识
  description: string;    // For AI to understand purpose / 供AI理解用途
  execute: (args: Record<string, unknown>) => Promise<string>;
}
```

### Tool Execution / 工具执行

```typescript
// 1. AI decides to call tool
// AI决定调用工具
if (response.finishReason === 'tool_calls') {
  // 2. Execute each tool call
  // 执行每个工具调用
  for (const toolCall of response.message.toolCalls) {
    const tool = this.tools.get(toolCall.function.name);
    const args = JSON.parse(toolCall.function.arguments);
    const result = await tool.execute(args);
    
    // 3. Append result to conversation
    // 将结果追加到对话
    messages.push({
      role: 'tool',
      toolCallId: toolCall.id,
      content: result,
    });
  }
  
  // 4. Call AI again with tool results
  // 带工具结果再次调用AI
  return this.chat('', { useTools: true });
}
```

---

## Error Handling / 错误处理

### Retry Logic / 重试逻辑

```typescript
// Provider-level retry
// Provider级别重试
for (let attempt = 0; attempt < maxRetries; attempt++) {
  try {
    return await fetch(url, options);
  } catch (error) {
    if (attempt === maxRetries - 1) throw error;
    await delay(1000 * (attempt + 1));  // Exponential backoff
  }
}
```

### Error Types / 错误类型

| Error | Handling / 处理方式 |
|-------|---------------------|
| Network Error | Retry with backoff / 指数退避重试 |
| API Error (4xx) | Throw immediately / 立即抛出 |
| API Error (5xx) | Retry, then fallback / 重试后降级 |
| Timeout | Retry, then fallback / 重试后降级 |
| Provider Unavailable | Switch to fallback / 切换到备用 |

---

## Extension Points / 扩展点

### Adding a New Provider / 添加新Provider

```typescript
// 1. Create provider class
// 创建Provider类
class MyCustomProvider extends BaseAIProvider {
  protected getDefaultBaseUrl(): string {
    return 'https://my-api.com/v1';
  }
  
  async chat(request: AIRequest): Promise<AIResponse> {
    // Custom implementation
  }
  
  async chatStream(request: AIRequest, onChunk: Function): Promise<void> {
    // Custom implementation
  }
  
  async isAvailable(): Promise<boolean> {
    // Health check
  }
  
  async getModels(): Promise<string[]> {
    // List available models
  }
}

// 2. Register in factory
// 在工厂中注册
case 'my-custom':
  return new MyCustomProvider(config);
```

---

## Performance Considerations / 性能考虑

1. **Connection Pooling**: Reuse HTTP connections when possible
2. **Streaming**: Use streaming for long responses to reduce latency
3. **Caching**: Cache model lists and availability checks
4. **Concurrency**: Multiple tool calls can be executed in parallel

---

## Security / 安全

- Never log API keys
- Validate tool arguments before execution
- Sanitize user input
- Use HTTPS for all API calls
