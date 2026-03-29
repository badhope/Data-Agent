import {
  AIProvider,
  AIRequest,
  AIResponse,
  AIStreamChunk,
  AIMessage,
  ToolDefinition,
} from './types';
import { AIProviderFactory, AIConfigManager } from './factory';

export interface AIControllerOptions {
  provider?: string;
  fallbackEnabled?: boolean;
  retryAttempts?: number;
  timeout?: number;
  onProviderSwitch?: (from: string, to: string) => void;
  onError?: (error: Error, provider: string) => void;
}

export interface ConversationContext {
  messages: AIMessage[];
  metadata: Record<string, unknown>;
}

export interface ToolExecutor {
  name: string;
  description: string;
  execute: (args: Record<string, unknown>) => Promise<string>;
}

export class AIController {
  private options: AIControllerOptions;
  private tools: Map<string, ToolExecutor> = new Map();
  private conversationHistory: AIMessage[] = [];
  private systemPrompt: string = '';

  constructor(options: AIControllerOptions = {}) {
    this.options = {
      fallbackEnabled: true,
      retryAttempts: 3,
      timeout: 60000,
      ...options,
    };
  }

  setSystemPrompt(prompt: string): void {
    this.systemPrompt = prompt;
  }

  registerTool(tool: ToolExecutor): void {
    this.tools.set(tool.name, tool);
  }

  registerTools(tools: ToolExecutor[]): void {
    tools.forEach(tool => this.registerTool(tool));
  }

  getToolDefinitions(): ToolDefinition[] {
    return Array.from(this.tools.values()).map(tool => ({
      type: 'function' as const,
      function: {
        name: tool.name,
        description: tool.description,
        parameters: {
          type: 'object',
          properties: {},
          required: [],
        },
      },
    }));
  }

  async chat(
    content: string,
    options: {
      model?: string;
      temperature?: number;
      maxTokens?: number;
      useTools?: boolean;
      stream?: boolean;
      onChunk?: (chunk: AIStreamChunk) => void;
    } = {}
  ): Promise<string> {
    const userMessage: AIMessage = { role: 'user', content };
    this.conversationHistory.push(userMessage);

    const messages = this.buildMessages();

    const request: AIRequest = {
      messages,
      model: options.model,
      temperature: options.temperature,
      maxTokens: options.maxTokens,
      tools: options.useTools ? this.getToolDefinitions() : undefined,
      toolChoice: options.useTools ? 'auto' : undefined,
      stream: options.stream,
    };

    if (options.stream && options.onChunk) {
      return this.handleStreamChat(request, options.onChunk);
    }

    return this.handleChat(request);
  }

  private buildMessages(): AIMessage[] {
    const messages: AIMessage[] = [];
    
    if (this.systemPrompt) {
      messages.push({ role: 'system', content: this.systemPrompt });
    }
    
    messages.push(...this.conversationHistory);
    
    return messages;
  }

  private async handleChat(request: AIRequest): Promise<string> {
    const provider = this.getProvider();
    
    if (!provider) {
      throw new Error('No AI provider available');
    }

    let response: AIResponse;
    
    try {
      response = await provider.chat(request);
    } catch (error) {
      if (this.options.fallbackEnabled) {
        response = await this.handleFallback(request, error as Error);
      } else {
        throw error;
      }
    }

    if (response.finishReason === 'tool_calls' && response.message.toolCalls) {
      return this.handleToolCalls(response.message.toolCalls);
    }

    const assistantMessage = response.message.content;
    this.conversationHistory.push({
      role: 'assistant',
      content: assistantMessage,
    });

    return assistantMessage;
  }

  private async handleStreamChat(
    request: AIRequest,
    onChunk: (chunk: AIStreamChunk) => void
  ): Promise<string> {
    const provider = this.getProvider();
    
    if (!provider) {
      throw new Error('No AI provider available');
    }

    let fullContent = '';
    const toolCalls: Map<number, { id: string; name: string; arguments: string }> = new Map();

    await provider.chatStream(request, (chunk) => {
      if (chunk.delta.content) {
        fullContent += chunk.delta.content;
      }
      
      if (chunk.delta.toolCalls) {
        for (const tc of chunk.delta.toolCalls) {
          toolCalls.set(0, {
            id: tc.id,
            name: tc.function.name,
            arguments: tc.function.arguments,
          });
        }
      }
      
      onChunk(chunk);
    });

    if (toolCalls.size > 0) {
      const calls = Array.from(toolCalls.values()).map(tc => ({
        id: tc.id,
        type: 'function' as const,
        function: { name: tc.name, arguments: tc.arguments },
      }));
      return this.handleToolCalls(calls);
    }

    this.conversationHistory.push({
      role: 'assistant',
      content: fullContent,
    });

    return fullContent;
  }

  private async handleToolCalls(toolCalls: Array<{ id: string; type: 'function'; function: { name: string; arguments: string } }>): Promise<string> {
    const results: AIMessage[] = [];

    for (const toolCall of toolCalls) {
      const tool = this.tools.get(toolCall.function.name);
      
      if (!tool) {
        results.push({
          role: 'tool',
          toolCallId: toolCall.id,
          content: `Tool "${toolCall.function.name}" not found`,
        });
        continue;
      }

      try {
        const args = JSON.parse(toolCall.function.arguments);
        const result = await tool.execute(args);
        
        results.push({
          role: 'tool',
          toolCallId: toolCall.id,
          content: result,
        });
      } catch (error) {
        results.push({
          role: 'tool',
          toolCallId: toolCall.id,
          content: `Error: ${(error as Error).message}`,
        });
      }
    }

    this.conversationHistory.push(
      { role: 'assistant', content: '', toolCalls },
      ...results
    );

    return this.chat('', { useTools: true });
  }

  private async handleFallback(request: AIRequest, originalError: Error): Promise<AIResponse> {
    const providers = AIProviderFactory.getAll();
    const currentProvider = this.options.provider || AIProviderFactory.getDefault()?.name;
    
    for (const provider of providers) {
      if (provider.name === currentProvider) continue;
      
      try {
        this.options.onProviderSwitch?.(currentProvider || 'unknown', provider.name);
        return await provider.chat(request);
      } catch (error) {
        this.options.onError?.(error as Error, provider.name);
        continue;
      }
    }
    
    throw originalError;
  }

  private getProvider(): AIProvider | undefined {
    if (this.options.provider) {
      return AIProviderFactory.get(this.options.provider);
    }
    return AIProviderFactory.getDefault();
  }

  clearHistory(): void {
    this.conversationHistory = [];
  }

  getHistory(): AIMessage[] {
    return [...this.conversationHistory];
  }

  setHistory(messages: AIMessage[]): void {
    this.conversationHistory = [...messages];
  }

  async switchProvider(name: string): Promise<boolean> {
    const provider = AIProviderFactory.get(name);
    if (!provider) return false;
    
    const available = await provider.isAvailable();
    if (!available) return false;
    
    this.options.provider = name;
    return true;
  }

  async checkProviders(): Promise<Array<{ name: string; available: boolean }>> {
    const providers = AIProviderFactory.getAll();
    const results: Array<{ name: string; available: boolean }> = [];
    
    for (const provider of providers) {
      try {
        const available = await provider.isAvailable();
        results.push({ name: provider.name, available });
      } catch {
        results.push({ name: provider.name, available: false });
      }
    }
    
    return results;
  }
}

export class AIAgent extends AIController {
  private name: string;
  private description: string;
  private capabilities: string[] = [];

  constructor(config: {
    name: string;
    description: string;
    capabilities?: string[];
    systemPrompt?: string;
    tools?: ToolExecutor[];
    options?: AIControllerOptions;
  }) {
    super(config.options);
    this.name = config.name;
    this.description = config.description;
    this.capabilities = config.capabilities || [];
    
    if (config.systemPrompt) {
      this.setSystemPrompt(config.systemPrompt);
    }
    
    if (config.tools) {
      this.registerTools(config.tools);
    }
  }

  getName(): string {
    return this.name;
  }

  getDescription(): string {
    return this.description;
  }

  getCapabilities(): string[] {
    return [...this.capabilities];
  }

  async execute(task: string, context?: Record<string, unknown>): Promise<string> {
    if (context) {
      const contextMessage = Object.entries(context)
        .map(([k, v]) => `${k}: ${JSON.stringify(v)}`)
        .join('\n');
      
      return this.chat(`Context:\n${contextMessage}\n\nTask: ${task}`, {
        useTools: true,
      });
    }
    
    return this.chat(task, { useTools: true });
  }
}

export function createAIController(options?: AIControllerOptions): AIController {
  return new AIController(options);
}

export function createAIAgent(config: {
  name: string;
  description: string;
  capabilities?: string[];
  systemPrompt?: string;
  tools?: ToolExecutor[];
  options?: AIControllerOptions;
}): AIAgent {
  return new AIAgent(config);
}
