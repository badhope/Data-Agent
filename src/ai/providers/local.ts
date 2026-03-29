import {
  BaseAIProvider,
  AIProviderConfig,
  AIRequest,
  AIResponse,
  AIStreamChunk,
  AIMessage,
} from '../types';

interface OllamaGenerateResponse {
  model: string;
  created_at: string;
  response: string;
  done: boolean;
  context?: number[];
  total_duration?: number;
  load_duration?: number;
  prompt_eval_count?: number;
  eval_count?: number;
  eval_duration?: number;
}

interface OllamaChatResponse {
  model: string;
  created_at: string;
  message: {
    role: string;
    content: string;
  };
  done: boolean;
  total_duration?: number;
  load_duration?: number;
  prompt_eval_count?: number;
  eval_count?: number;
  eval_duration?: number;
}

interface OllamaModelInfo {
  name: string;
  modified_at: string;
  size: number;
  digest: string;
  details?: {
    format: string;
    family: string;
    parameter_size: string;
    quantization_level: string;
  };
}

export class OllamaProvider extends BaseAIProvider {
  constructor(config: AIProviderConfig) {
    super(config);
  }

  protected getDefaultBaseUrl(): string {
    return 'http://localhost:11434';
  }

  protected getHeaders(): Record<string, string> {
    return {
      'Content-Type': 'application/json',
    };
  }

  async chat(request: AIRequest): Promise<AIResponse> {
    const url = `${this.getBaseUrl()}/api/chat`;
    
    const body = {
      model: request.model || this.config.model,
      messages: request.messages,
      stream: false,
      options: {
        temperature: request.temperature,
        num_predict: request.maxTokens,
      },
    };

    const response = await fetch(url, {
      method: 'POST',
      headers: this.getHeaders(),
      body: JSON.stringify(body),
    });

    if (!response.ok) {
      throw new Error(`Ollama API error: ${response.status}`);
    }

    const data: OllamaChatResponse = await response.json();

    return {
      id: `ollama-${Date.now()}`,
      model: data.model,
      message: {
        role: data.message.role as AIMessage['role'],
        content: data.message.content,
      },
      usage: data.prompt_eval_count
        ? {
            promptTokens: data.prompt_eval_count,
            completionTokens: data.eval_count || 0,
            totalTokens: (data.prompt_eval_count || 0) + (data.eval_count || 0),
          }
        : undefined,
      finishReason: data.done ? 'stop' : 'length',
    };
  }

  async chatStream(
    request: AIRequest,
    onChunk: (chunk: AIStreamChunk) => void
  ): Promise<void> {
    const url = `${this.getBaseUrl()}/api/chat`;
    
    const body = {
      model: request.model || this.config.model,
      messages: request.messages,
      stream: true,
      options: {
        temperature: request.temperature,
        num_predict: request.maxTokens,
      },
    };

    const response = await fetch(url, {
      method: 'POST',
      headers: this.getHeaders(),
      body: JSON.stringify(body),
    });

    if (!response.ok) {
      throw new Error(`Ollama API error: ${response.status}`);
    }

    if (!response.body) {
      throw new Error('Response body is null');
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';
    const id = `ollama-${Date.now()}`;

    while (true) {
      const { done, value } = await reader.read();
      
      if (done) break;
      
      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n');
      buffer = lines.pop() || '';

      for (const line of lines) {
        if (!line.trim()) continue;
        
        try {
          const data: OllamaChatResponse = JSON.parse(line);
          
          const chunk: AIStreamChunk = {
            id,
            model: data.model,
            delta: {
              content: data.message.content,
            },
            finishReason: data.done ? 'stop' : undefined,
          };
          
          onChunk(chunk);
        } catch (e) {
          console.error('Failed to parse Ollama stream chunk:', e);
        }
      }
    }
  }

  async isAvailable(): Promise<boolean> {
    try {
      const response = await fetch(`${this.getBaseUrl()}/api/tags`);
      return response.ok;
    } catch {
      return false;
    }
  }

  async getModels(): Promise<string[]> {
    try {
      const response = await fetch(`${this.getBaseUrl()}/api/tags`);
      
      if (!response.ok) return [];
      
      const data = await response.json();
      return data.models?.map((m: OllamaModelInfo) => m.name) || [];
    } catch {
      return [];
    }
  }

  async pullModel(modelName: string): Promise<void> {
    const url = `${this.getBaseUrl()}/api/pull`;
    
    await fetch(url, {
      method: 'POST',
      headers: this.getHeaders(),
      body: JSON.stringify({ name: modelName, stream: false }),
    });
  }

  async embed(texts: string[]): Promise<number[][]> {
    const url = `${this.getBaseUrl()}/api/embeddings`;
    
    const embeddings: number[][] = [];
    
    for (const text of texts) {
      const response = await fetch(url, {
        method: 'POST',
        headers: this.getHeaders(),
        body: JSON.stringify({
          model: this.config.model,
          prompt: text,
        }),
      });
      
      if (!response.ok) {
        throw new Error(`Ollama embedding error: ${response.status}`);
      }
      
      const data = await response.json();
      embeddings.push(data.embedding);
    }
    
    return embeddings;
  }
}

export class LMStudioProvider extends BaseAIProvider {
  constructor(config: AIProviderConfig) {
    super(config);
  }

  protected getDefaultBaseUrl(): string {
    return 'http://localhost:1234/v1';
  }

  async chat(request: AIRequest): Promise<AIResponse> {
    const url = `${this.getBaseUrl()}/chat/completions`;
    
    const body = {
      model: request.model || this.config.model || 'local-model',
      messages: request.messages,
      temperature: request.temperature,
      max_tokens: request.maxTokens,
      stream: false,
    };

    const response = await fetch(url, {
      method: 'POST',
      headers: this.getHeaders(),
      body: JSON.stringify(body),
    });

    if (!response.ok) {
      throw new Error(`LM Studio API error: ${response.status}`);
    }

    const data = await response.json();

    return {
      id: data.id || `lmstudio-${Date.now()}`,
      model: data.model,
      message: {
        role: data.choices[0].message.role,
        content: data.choices[0].message.content,
      },
      usage: data.usage
        ? {
            promptTokens: data.usage.prompt_tokens,
            completionTokens: data.usage.completion_tokens,
            totalTokens: data.usage.total_tokens,
          }
        : undefined,
      finishReason: data.choices[0].finish_reason,
    };
  }

  async chatStream(
    request: AIRequest,
    onChunk: (chunk: AIStreamChunk) => void
  ): Promise<void> {
    const url = `${this.getBaseUrl()}/chat/completions`;
    
    const body = {
      model: request.model || this.config.model || 'local-model',
      messages: request.messages,
      temperature: request.temperature,
      max_tokens: request.maxTokens,
      stream: true,
    };

    const response = await fetch(url, {
      method: 'POST',
      headers: this.getHeaders(),
      body: JSON.stringify(body),
    });

    if (!response.ok) {
      throw new Error(`LM Studio API error: ${response.status}`);
    }

    if (!response.body) {
      throw new Error('Response body is null');
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';

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
            const data = JSON.parse(trimmed.slice(6));
            const choice = data.choices[0];
            
            if (choice?.delta) {
              const chunk: AIStreamChunk = {
                id: data.id,
                model: data.model,
                delta: {
                  content: choice.delta.content || '',
                },
                finishReason: choice.finish_reason,
              };
              
              onChunk(chunk);
            }
          } catch (e) {
            console.error('Failed to parse LM Studio stream chunk:', e);
          }
        }
      }
    }
  }

  async isAvailable(): Promise<boolean> {
    try {
      const response = await fetch(`${this.getBaseUrl()}/models`);
      return response.ok;
    } catch {
      return false;
    }
  }

  async getModels(): Promise<string[]> {
    try {
      const response = await fetch(`${this.getBaseUrl()}/models`);
      
      if (!response.ok) return [];
      
      const data = await response.json();
      return data.data?.map((m: { id: string }) => m.id) || [];
    } catch {
      return [];
    }
  }
}
