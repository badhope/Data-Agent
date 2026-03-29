import { AIProvider, AIProviderConfig } from './types';
import { OpenAIProvider } from './providers/openai';
import { OllamaProvider, LMStudioProvider } from './providers/local';

export type ProviderType = 'openai' | 'anthropic' | 'ollama' | 'lmstudio' | 'custom';

export interface ProviderRegistryEntry {
  type: ProviderType;
  name: string;
  provider: AIProvider;
  priority: number;
  enabled: boolean;
}

export class AIProviderFactory {
  private static providers: Map<string, ProviderRegistryEntry> = new Map();
  private static defaultProvider: string | null = null;

  static register(config: AIProviderConfig, priority: number = 0): void {
    const provider = this.createProvider(config);
    
    this.providers.set(config.name, {
      type: config.type,
      name: config.name,
      provider,
      priority,
      enabled: true,
    });
    
    if (this.defaultProvider === null) {
      this.defaultProvider = config.name;
    }
  }

  static registerMultiple(configs: Array<{ config: AIProviderConfig; priority?: number }>): void {
    configs.forEach(({ config, priority = 0 }) => {
      this.register(config, priority);
    });
  }

  private static createProvider(config: AIProviderConfig): AIProvider {
    switch (config.type) {
      case 'openai':
        return new OpenAIProvider(config);
      case 'ollama':
        return new OllamaProvider(config);
      case 'lmstudio':
        return new LMStudioProvider(config);
      case 'anthropic':
        return new OpenAIProvider({
          ...config,
          baseUrl: config.baseUrl || 'https://api.anthropic.com/v1',
          extraHeaders: {
            'anthropic-version': '2023-06-01',
            ...config.extraHeaders,
          },
        });
      case 'custom':
        return new OpenAIProvider(config);
      default:
        throw new Error(`Unknown provider type: ${config.type}`);
    }
  }

  static get(name: string): AIProvider | undefined {
    const entry = this.providers.get(name);
    return entry?.enabled ? entry.provider : undefined;
  }

  static getDefault(): AIProvider | undefined {
    if (!this.defaultProvider) return undefined;
    return this.get(this.defaultProvider);
  }

  static setDefault(name: string): void {
    if (!this.providers.has(name)) {
      throw new Error(`Provider "${name}" not found`);
    }
    this.defaultProvider = name;
  }

  static getAll(): AIProvider[] {
    return Array.from(this.providers.values())
      .filter(entry => entry.enabled)
      .sort((a, b) => b.priority - a.priority)
      .map(entry => entry.provider);
  }

  static getAvailable(): AIProvider[] {
    return this.getAll().filter(p => {
      try {
        return p.isAvailable();
      } catch {
        return false;
      }
    });
  }

  static enable(name: string): void {
    const entry = this.providers.get(name);
    if (entry) {
      entry.enabled = true;
    }
  }

  static disable(name: string): void {
    const entry = this.providers.get(name);
    if (entry) {
      entry.enabled = false;
    }
  }

  static remove(name: string): void {
    this.providers.delete(name);
    if (this.defaultProvider === name) {
      this.defaultProvider = this.providers.keys().next().value || null;
    }
  }

  static clear(): void {
    this.providers.clear();
    this.defaultProvider = null;
  }

  static list(): Array<{ name: string; type: string; enabled: boolean; priority: number }> {
    return Array.from(this.providers.values())
      .sort((a, b) => b.priority - a.priority)
      .map(entry => ({
        name: entry.name,
        type: entry.type,
        enabled: entry.enabled,
        priority: entry.priority,
      }));
  }
}

export class AIConfigManager {
  private static config: AIConfig = {
    providers: [],
    defaultProvider: null,
    fallbackEnabled: true,
    retryAttempts: 3,
    timeout: 60000,
  };

  static setConfig(config: Partial<AIConfig>): void {
    this.config = { ...this.config, ...config };
    this.applyConfig();
  }

  static getConfig(): AIConfig {
    return { ...this.config };
  }

  static loadFromEnv(): void {
    const providers: AIProviderConfig[] = [];

    if (process.env.OPENAI_API_KEY) {
      providers.push({
        type: 'openai',
        name: 'openai',
        apiKey: process.env.OPENAI_API_KEY,
        model: process.env.OPENAI_MODEL || 'gpt-4',
        baseUrl: process.env.OPENAI_BASE_URL,
      });
    }

    if (process.env.ANTHROPIC_API_KEY) {
      providers.push({
        type: 'anthropic',
        name: 'anthropic',
        apiKey: process.env.ANTHROPIC_API_KEY,
        model: process.env.ANTHROPIC_MODEL || 'claude-3-opus-20240229',
        baseUrl: process.env.ANTHROPIC_BASE_URL,
      });
    }

    if (process.env.OLLAMA_ENABLED === 'true' || process.env.OLLAMA_BASE_URL) {
      providers.push({
        type: 'ollama',
        name: 'ollama',
        baseUrl: process.env.OLLAMA_BASE_URL || 'http://localhost:11434',
        model: process.env.OLLAMA_MODEL || 'llama2',
      });
    }

    if (process.env.LMSTUDIO_ENABLED === 'true' || process.env.LMSTUDIO_BASE_URL) {
      providers.push({
        type: 'lmstudio',
        name: 'lmstudio',
        baseUrl: process.env.LMSTUDIO_BASE_URL || 'http://localhost:1234/v1',
        model: process.env.LMSTUDIO_MODEL || 'local-model',
      });
    }

    providers.forEach((config, index) => {
      AIProviderFactory.register(config, providers.length - index);
    });

    if (process.env.DEFAULT_PROVIDER) {
      AIProviderFactory.setDefault(process.env.DEFAULT_PROVIDER);
    }
  }

  static loadFromFile(path: string): void {
    try {
      const fs = require('fs');
      const content = fs.readFileSync(path, 'utf-8');
      const config = JSON.parse(content);
      this.setConfig(config);
    } catch (error) {
      console.error('Failed to load config file:', error);
    }
  }

  static saveToFile(path: string): void {
    try {
      const fs = require('fs');
      fs.writeFileSync(path, JSON.stringify(this.config, null, 2));
    } catch (error) {
      console.error('Failed to save config file:', error);
    }
  }

  private static applyConfig(): void {
    AIProviderFactory.clear();

    this.config.providers.forEach((providerConfig, index) => {
      AIProviderFactory.register(providerConfig, this.config.providers.length - index);
    });

    if (this.config.defaultProvider) {
      AIProviderFactory.setDefault(this.config.defaultProvider);
    }
  }
}

export interface AIConfig {
  providers: AIProviderConfig[];
  defaultProvider: string | null;
  fallbackEnabled: boolean;
  retryAttempts: number;
  timeout: number;
}

export const defaultConfig: AIConfig = {
  providers: [
    {
      type: 'openai',
      name: 'openai',
      model: 'gpt-4',
    },
    {
      type: 'ollama',
      name: 'ollama',
      model: 'llama2',
    },
  ],
  defaultProvider: null,
  fallbackEnabled: true,
  retryAttempts: 3,
  timeout: 60000,
};
