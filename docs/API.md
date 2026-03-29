# API Reference / API参考

Complete API documentation for AI Controller Architecture.

AI控制器架构完整API文档。

---

## Table of Contents / 目录

- [Types / 类型定义](#types--类型定义)
- [AIController](#aicontroller)
- [AIProviderFactory](#aiproviderfactory)
- [AIConfigManager](#aiconfigmanager)
- [Providers](#providers)

---

## Types / 类型定义

### AIMessage

```typescript
interface AIMessage {
  role: 'system' | 'user' | 'assistant' | 'tool';
  content: string;
  name?: string;
  toolCallId?: string;
  toolCalls?: ToolCall[];
}
```

| Field | Type | Description |
|-------|------|-------------|
| `role` | string | Message role |
| `content` | string | Message content |
| `name` | string? | Optional name for tool messages |
| `toolCallId` | string? | Tool call ID for tool responses |
| `toolCalls` | ToolCall[]? | Tool calls from assistant |

### AIRequest

```typescript
interface AIRequest {
  messages: AIMessage[];
  model?: string;
  temperature?: number;
  maxTokens?: number;
  tools?: ToolDefinition[];
  toolChoice?: 'auto' | 'none' | { type: 'function'; function: { name: string } };
  stream?: boolean;
}
```

### AIResponse

```typescript
interface AIResponse {
  id: string;
  model: string;
  message: AIMessage;
  usage?: {
    promptTokens: number;
    completionTokens: number;
    totalTokens: number;
  };
  finishReason: 'stop' | 'tool_calls' | 'length' | 'content_filter';
}
```

### AIProviderConfig

```typescript
interface AIProviderConfig {
  type: 'openai' | 'anthropic' | 'ollama' | 'lmstudio' | 'custom';
  name: string;
  apiKey?: string;
  baseUrl?: string;
  model: string;
  defaultModel?: string;
  maxRetries?: number;
  timeout?: number;
  extraHeaders?: Record<string, string>;
}
```

### ToolExecutor

```typescript
interface ToolExecutor {
  name: string;
  description: string;
  execute: (args: Record<string, unknown>) => Promise<string>;
}
```

---

## AIController

Main controller for AI interactions.

AI交互的主控制器。

### Constructor

```typescript
constructor(options?: AIControllerOptions)
```

#### Options

```typescript
interface AIControllerOptions {
  provider?: string;           // Provider name
  fallbackEnabled?: boolean;   // Enable auto fallback (default: true)
  retryAttempts?: number;      // Retry count (default: 3)
  timeout?: number;            // Timeout in ms (default: 60000)
  onProviderSwitch?: (from: string, to: string) => void;
  onError?: (error: Error, provider: string) => void;
}
```

### Methods

#### chat()

Send a message and get AI response.

发送消息并获取AI响应。

```typescript
async chat(
  content: string,
  options?: {
    model?: string;
    temperature?: number;
    maxTokens?: number;
    useTools?: boolean;
    stream?: boolean;
    onChunk?: (chunk: AIStreamChunk) => void;
  }
): Promise<string>
```

**Example / 示例:**

```typescript
const ai = createAIController();

// Simple chat / 简单对话
const response = await ai.chat('Hello!');

// With options / 带选项
const response = await ai.chat('Tell me a story', {
  temperature: 0.8,
  maxTokens: 1000,
});

// Streaming / 流式
await ai.chat('Long story', {
  stream: true,
  onChunk: (chunk) => console.log(chunk.delta.content),
});

// With tools / 使用工具
await ai.chat('What is the weather?', { useTools: true });
```

#### setSystemPrompt()

Set the system prompt for conversations.

设置对话的系统提示。

```typescript
setSystemPrompt(prompt: string): void
```

**Example / 示例:**

```typescript
ai.setSystemPrompt('You are a helpful assistant specialized in Chinese history.');
ai.setSystemPrompt('你是一个专门研究中国历史的助手。');
```

#### registerTool()

Register a tool for AI to call.

注册供AI调用的工具。

```typescript
registerTool(tool: ToolExecutor): void
```

**Example / 示例:**

```typescript
ai.registerTool({
  name: 'search',
  description: 'Search for information',
  execute: async (args) => {
    const results = await searchDatabase(args.query);
    return JSON.stringify(results);
  },
});
```

#### registerTools()

Register multiple tools at once.

一次性注册多个工具。

```typescript
registerTools(tools: ToolExecutor[]): void
```

#### clearHistory()

Clear conversation history.

清除对话历史。

```typescript
clearHistory(): void
```

#### getHistory()

Get current conversation history.

获取当前对话历史。

```typescript
getHistory(): AIMessage[]
```

#### setHistory()

Set conversation history.

设置对话历史。

```typescript
setHistory(messages: AIMessage[]): void
```

#### switchProvider()

Switch to a different provider.

切换到不同的Provider。

```typescript
async switchProvider(name: string): Promise<boolean>
```

**Returns / 返回:** `true` if switch successful, `false` otherwise

#### checkProviders()

Check availability of all providers.

检查所有Provider的可用性。

```typescript
async checkProviders(): Promise<Array<{ name: string; available: boolean }>>
```

---

## AIProviderFactory

Factory for managing AI providers.

管理AI Provider的工厂。

### Static Methods

#### register()

Register a new provider.

注册新的Provider。

```typescript
static register(config: AIProviderConfig, priority?: number): void
```

**Parameters / 参数:**
- `config` - Provider configuration
- `priority` - Priority level (higher = preferred, default: 0)

**Example / 示例:**

```typescript
AIProviderFactory.register({
  type: 'openai',
  name: 'main-gpt',
  apiKey: process.env.OPENAI_API_KEY,
  model: 'gpt-4',
}, 10);
```

#### registerMultiple()

Register multiple providers at once.

一次性注册多个Provider。

```typescript
static registerMultiple(
  configs: Array<{ config: AIProviderConfig; priority?: number }>
): void
```

#### get()

Get a provider by name.

按名称获取Provider。

```typescript
static get(name: string): AIProvider | undefined
```

#### getDefault()

Get the default provider.

获取默认Provider。

```typescript
static getDefault(): AIProvider | undefined
```

#### setDefault()

Set the default provider.

设置默认Provider。

```typescript
static setDefault(name: string): void
```

#### getAll()

Get all registered providers.

获取所有已注册的Provider。

```typescript
static getAll(): AIProvider[]
```

#### enable() / disable()

Enable or disable a provider.

启用或禁用Provider。

```typescript
static enable(name: string): void
static disable(name: string): void
```

#### remove()

Remove a provider.

移除Provider。

```typescript
static remove(name: string): void
```

#### list()

List all providers with their status.

列出所有Provider及其状态。

```typescript
static list(): Array<{
  name: string;
  type: string;
  enabled: boolean;
  priority: number;
}>
```

---

## AIConfigManager

Configuration manager for AI settings.

AI设置的配置管理器。

### Static Methods

#### setConfig()

Set configuration.

设置配置。

```typescript
static setConfig(config: Partial<AIConfig>): void
```

#### getConfig()

Get current configuration.

获取当前配置。

```typescript
static getConfig(): AIConfig
```

#### loadFromEnv()

Load configuration from environment variables.

从环境变量加载配置。

```typescript
static loadFromEnv(): void
```

**Environment Variables / 环境变量:**

| Variable | Description |
|----------|-------------|
| `OPENAI_API_KEY` | OpenAI API key |
| `OPENAI_MODEL` | Default model |
| `OPENAI_BASE_URL` | Custom endpoint |
| `ANTHROPIC_API_KEY` | Anthropic API key |
| `OLLAMA_ENABLED` | Enable Ollama |
| `OLLAMA_BASE_URL` | Ollama endpoint |
| `LMSTUDIO_ENABLED` | Enable LM Studio |
| `DEFAULT_PROVIDER` | Default provider name |

#### loadFromFile()

Load configuration from JSON file.

从JSON文件加载配置。

```typescript
static loadFromFile(path: string): void
```

#### saveToFile()

Save configuration to JSON file.

保存配置到JSON文件。

```typescript
static saveToFile(path: string): void
```

---

## Providers

### OpenAIProvider

```typescript
import { OpenAIProvider } from 'yongledadian';

const provider = new OpenAIProvider({
  type: 'openai',
  name: 'my-openai',
  apiKey: 'sk-xxx',
  model: 'gpt-4',
});
```

### OllamaProvider

```typescript
import { OllamaProvider } from 'yongledadian';

const provider = new OllamaProvider({
  type: 'ollama',
  name: 'local',
  baseUrl: 'http://localhost:11434',
  model: 'llama2',
});

// Additional methods / 额外方法
await provider.pullModel('llama2');  // Download model
await provider.embed(['text1', 'text2']);  // Get embeddings
```

### LMStudioProvider

```typescript
import { LMStudioProvider } from 'yongledadian';

const provider = new LMStudioProvider({
  type: 'lmstudio',
  name: 'local',
  baseUrl: 'http://localhost:1234/v1',
  model: 'local-model',
});
```

---

## Utility Functions / 工具函数

### createAIController()

Create an AI controller instance.

创建AI控制器实例。

```typescript
function createAIController(options?: AIControllerOptions): AIController
```

### createAIAgent()

Create an AI agent with predefined configuration.

创建预配置的AI代理。

```typescript
function createAIAgent(config: {
  name: string;
  description: string;
  capabilities?: string[];
  systemPrompt?: string;
  tools?: ToolExecutor[];
  options?: AIControllerOptions;
}): AIAgent
```

**Example / 示例:**

```typescript
const agent = createAIAgent({
  name: 'research-assistant',
  description: 'Research and analysis assistant',
  capabilities: ['search', 'summarize', 'analyze'],
  systemPrompt: 'You are a research assistant.',
  tools: [searchTool, summarizeTool],
});

await agent.execute('Research AI trends in 2024');
```
