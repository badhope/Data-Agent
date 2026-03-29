import {
  BaseAIProvider,
  AIProviderConfig,
  AIRequest,
  AIResponse,
  AIStreamChunk,
  AIMessage,
  ToolCall,
} from './types';

interface OpenAIChatResponse {
  id: string;
  object: string;
  created: number;
  model: string;
  choices: Array<{
    index: number;
    message: {
      role: string;
      content: string | null;
      tool_calls?: Array<{
        id: string;
        type: string;
        function: {
          name: string;
          arguments: string;
        };
      }>;
    };
    finish_reason: string;
  }>;
  usage?: {
    prompt_tokens: number;
    completion_tokens: number;
    total_tokens: number;
  };
}

interface OpenAIStreamResponse {
  id: string;
  object: string;
  created: number;
  model: string;
  choices: Array<{
    index: number;
    delta: {
      role?: string;
      content?: string;
      tool_calls?: Array<{
        index: number;
        id?: string;
        type?: string;
        function?: {
          name?: string;
          arguments?: string;
        };
      }>;
    };
    finish_reason: string | null;
  }>;
}

export class OpenAIProvider extends BaseAIProvider {
  constructor(config: AIProviderConfig) {
    super(config);
  }

  protected getDefaultBaseUrl(): string {
    return 'https://api.openai.com/v1';
  }

  async chat(request: AIRequest): Promise<AIResponse> {
    const url = `${this.getBaseUrl()}/chat/completions`;
    
    const body = this.buildRequestBody(request);
    
    const response = await this.makeRequest(url, body);
    const data: OpenAIChatResponse = await response.json();
    
    return this.parseResponse(data);
  }

  async chatStream(
    request: AIRequest,
    onChunk: (chunk: AIStreamChunk) => void
  ): Promise<void> {
    const url = `${this.getBaseUrl()}/chat/completions`;
    
    const body = this.buildRequestBody({ ...request, stream: true });
    
    const response = await this.makeRequest(url, body);
    
    if (!response.body) {
      throw new Error('Response body is null');
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';
    let currentToolCalls: Map<number, ToolCall> = new Map();

    while (true) {
      const { done, value } = await reader.read();
      
      if (done) break;
      
      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n');
      buffer = lines.pop() || '';

      for (const line of lines) {
        const trimmed = line.trim();
        if (!trimmed || trimmed === 'data: [DONE]') continue;
        
        if (trimmed.startsWith('data: ')) {
          try {
            const json: OpenAIStreamResponse = JSON.parse(trimmed.slice(6));
            const chunk = this.parseStreamChunk(json, currentToolCalls);
            if (chunk) {
              onChunk(chunk);
            }
          } catch (e) {
            console.error('Failed to parse stream chunk:', e);
          }
        }
      }
    }
  }

  async isAvailable(): Promise<boolean> {
    try {
      const response = await fetch(`${this.getBaseUrl()}/models`, {
        headers: this.getHeaders(),
      });
      return response.ok;
    } catch {
      return false;
    }
  }

  async getModels(): Promise<string[]> {
    try {
      const response = await fetch(`${this.getBaseUrl()}/models`, {
        headers: this.getHeaders(),
      });
      
      if (!response.ok) return [];
      
      const data = await response.json();
      return data.data?.map((m: { id: string }) => m.id) || [];
    } catch {
      return [];
    }
  }

  private buildRequestBody(request: AIRequest): Record<string, unknown> {
    const body: Record<string, unknown> = {
      model: request.model || this.config.model,
      messages: request.messages.map(m => this.formatMessage(m)),
      stream: request.stream || false,
    };

    if (request.temperature !== undefined) {
      body.temperature = request.temperature;
    }

    if (request.maxTokens !== undefined) {
      body.max_tokens = request.maxTokens;
    }

    if (request.tools) {
      body.tools = request.tools;
    }

    if (request.toolChoice) {
      body.tool_choice = request.toolChoice;
    }

    return body;
  }

  private formatMessage(message: AIMessage): Record<string, unknown> {
    const formatted: Record<string, unknown> = {
      role: message.role,
      content: message.content,
    };

    if (message.name) {
      formatted.name = message.name;
    }

    if (message.toolCallId) {
      formatted.tool_call_id = message.toolCallId;
    }

    if (message.toolCalls) {
      formatted.tool_calls = message.toolCalls.map(tc => ({
        id: tc.id,
        type: tc.type,
        function: tc.function,
      }));
    }

    return formatted;
  }

  private async makeRequest(
    url: string,
    body: Record<string, unknown>
  ): Promise<Response> {
    const maxRetries = this.config.maxRetries || 3;
    const timeout = this.config.timeout || 60000;

    for (let attempt = 0; attempt < maxRetries; attempt++) {
      try {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), timeout);

        const response = await fetch(url, {
          method: 'POST',
          headers: this.getHeaders(),
          body: JSON.stringify(body),
          signal: controller.signal,
        });

        clearTimeout(timeoutId);

        if (!response.ok) {
          const error = await response.text();
          throw new Error(`API error: ${response.status} - ${error}`);
        }

        return response;
      } catch (error) {
        if (attempt === maxRetries - 1) {
          throw error;
        }
        await new Promise(resolve => setTimeout(resolve, 1000 * (attempt + 1)));
      }
    }

    throw new Error('Max retries exceeded');
  }

  private parseResponse(data: OpenAIChatResponse): AIResponse {
    const choice = data.choices[0];
    const message: AIMessage = {
      role: choice.message.role as AIMessage['role'],
      content: choice.message.content || '',
    };

    if (choice.message.tool_calls) {
      message.toolCalls = choice.message.tool_calls.map(tc => ({
        id: tc.id,
        type: 'function' as const,
        function: tc.function,
      }));
    }

    return {
      id: data.id,
      model: data.model,
      message,
      usage: data.usage
        ? {
            promptTokens: data.usage.prompt_tokens,
            completionTokens: data.usage.completion_tokens,
            totalTokens: data.usage.total_tokens,
          }
        : undefined,
      finishReason: choice.finish_reason as AIResponse['finishReason'],
    };
  }

  private parseStreamChunk(
    data: OpenAIStreamResponse,
    currentToolCalls: Map<number, ToolCall>
  ): AIStreamChunk | null {
    const choice = data.choices[0];
    if (!choice) return null;

    const delta = choice.delta;
    const message: Partial<AIMessage> = {};

    if (delta.role) {
      message.role = delta.role as AIMessage['role'];
    }

    if (delta.content) {
      message.content = delta.content;
    }

    if (delta.tool_calls) {
      for (const tc of delta.tool_calls) {
        if (tc.id) {
          currentToolCalls.set(tc.index, {
            id: tc.id,
            type: 'function',
            function: { name: '', arguments: '' },
          });
        }

        const existing = currentToolCalls.get(tc.index);
        if (existing && tc.function) {
          if (tc.function.name) {
            existing.function.name = tc.function.name;
          }
          if (tc.function.arguments) {
            existing.function.arguments += tc.function.arguments;
          }
        }
      }

      if (choice.finish_reason === 'tool_calls') {
        message.toolCalls = Array.from(currentToolCalls.values());
        currentToolCalls.clear();
      }
    }

    return {
      id: data.id,
      model: data.model,
      delta: message,
      finishReason: choice.finish_reason as AIStreamChunk['finishReason'],
    };
  }
}
