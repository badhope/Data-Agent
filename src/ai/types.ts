export interface AIMessage {
  role: 'system' | 'user' | 'assistant' | 'tool';
  content: string;
  name?: string;
  toolCallId?: string;
  toolCalls?: ToolCall[];
}

export interface ToolCall {
  id: string;
  type: 'function';
  function: {
    name: string;
    arguments: string;
  };
}

export interface ToolDefinition {
  type: 'function';
  function: {
    name: string;
    description: string;
    parameters: Record<string, unknown>;
  };
}

export interface AIRequest {
  messages: AIMessage[];
  model?: string;
  temperature?: number;
  maxTokens?: number;
  tools?: ToolDefinition[];
  toolChoice?: 'auto' | 'none' | { type: 'function'; function: { name: string } };
  stream?: boolean;
}

export interface AIResponse {
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

export interface AIStreamChunk {
  id: string;
  model: string;
  delta: Partial<AIMessage>;
  finishReason?: 'stop' | 'tool_calls' | 'length' | 'content_filter';
}

export interface AIProviderConfig {
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

export interface AIProvider {
  readonly name: string;
  readonly type: string;
  
  chat(request: AIRequest): Promise<AIResponse>;
  chatStream(request: AIRequest, onChunk: (chunk: AIStreamChunk) => void): Promise<void>;
  isAvailable(): Promise<boolean>;
  getModels(): Promise<string[]>;
}

export abstract class BaseAIProvider implements AIProvider {
  readonly name: string;
  readonly type: string;
  protected config: AIProviderConfig;
  
  constructor(config: AIProviderConfig) {
    this.name = config.name;
    this.type = config.type;
    this.config = config;
  }
  
  abstract chat(request: AIRequest): Promise<AIResponse>;
  abstract chatStream(request: AIRequest, onChunk: (chunk: AIStreamChunk) => void): Promise<void>;
  abstract isAvailable(): Promise<boolean>;
  abstract getModels(): Promise<string[]>;
  
  protected getHeaders(): Record<string, string> {
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
    };
    
    if (this.config.apiKey) {
      headers['Authorization'] = `Bearer ${this.config.apiKey}`;
    }
    
    if (this.config.extraHeaders) {
      Object.assign(headers, this.config.extraHeaders);
    }
    
    return headers;
  }
  
  protected getBaseUrl(): string {
    return this.config.baseUrl || this.getDefaultBaseUrl();
  }
  
  protected abstract getDefaultBaseUrl(): string;
}
