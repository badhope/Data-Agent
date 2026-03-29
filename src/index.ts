import {
  AIProviderFactory,
  AIConfigManager,
  AIController,
  AIAgent,
  createAIController,
  createAIAgent,
  ToolExecutor,
} from './ai';

async function main() {
  console.log('=== AI 控制架构示例 ===\n');

  // 方式1: 从环境变量加载配置
  AIConfigManager.loadFromEnv();

  // 方式2: 手动注册Provider
  AIProviderFactory.register({
    type: 'openai',
    name: 'openai-gpt4',
    apiKey: process.env.OPENAI_API_KEY || 'your-api-key',
    model: 'gpt-4',
  }, 10);

  AIProviderFactory.register({
    type: 'ollama',
    name: 'ollama-local',
    baseUrl: 'http://localhost:11434',
    model: 'llama2',
  }, 5);

  AIProviderFactory.register({
    type: 'lmstudio',
    name: 'lmstudio-local',
    baseUrl: 'http://localhost:1234/v1',
    model: 'local-model',
  }, 3);

  // 列出所有Provider
  console.log('已注册的Provider:');
  console.log(AIProviderFactory.list());
  console.log();

  // 创建简单的AI控制器
  const controller = createAIController({
    provider: 'openai-gpt4',
    fallbackEnabled: true,
    onProviderSwitch: (from, to) => {
      console.log(`Provider切换: ${from} -> ${to}`);
    },
    onError: (error, provider) => {
      console.error(`Provider ${provider} 错误:`, error.message);
    },
  });

  // 设置系统提示
  controller.setSystemPrompt('你是一个有帮助的AI助手。');

  // 注册工具
  const weatherTool: ToolExecutor = {
    name: 'get_weather',
    description: '获取指定城市的天气信息',
    execute: async (args) => {
      const city = args.city as string;
      return `${city}今天天气晴朗，温度25°C`;
    },
  };

  const searchTool: ToolExecutor = {
    name: 'search_web',
    description: '搜索网络信息',
    execute: async (args) => {
      const query = args.query as string;
      return `搜索结果: ${query} 的相关信息...`;
    },
  };

  controller.registerTools([weatherTool, searchTool]);

  // 使用工具进行对话
  try {
    console.log('测试对话 (带工具调用):');
    const response = await controller.chat('北京今天天气怎么样？', {
      useTools: true,
    });
    console.log('回复:', response);
    console.log();
  } catch (error) {
    console.error('对话错误:', (error as Error).message);
  }

  // 流式响应
  console.log('测试流式响应:');
  try {
    await controller.chat('请简单介绍一下永乐大典', {
      stream: true,
      onChunk: (chunk) => {
        if (chunk.delta.content) {
          process.stdout.write(chunk.delta.content);
        }
      },
    });
    console.log('\n');
  } catch (error) {
    console.error('流式响应错误:', (error as Error).message);
  }

  // 创建AI Agent
  const researchAgent = createAIAgent({
    name: 'research-assistant',
    description: '一个专门用于研究和信息整理的AI助手',
    capabilities: ['信息搜索', '内容总结', '数据分析'],
    systemPrompt: `你是一个研究助手。你的任务是帮助用户进行信息搜索和整理。
    你可以使用以下能力:
    - 信息搜索
    - 内容总结
    - 数据分析`,
    tools: [searchTool],
    options: {
      provider: 'ollama-local',
    },
  });

  console.log('Agent信息:');
  console.log('- 名称:', researchAgent.getName());
  console.log('- 描述:', researchAgent.getDescription());
  console.log('- 能力:', researchAgent.getCapabilities());
  console.log();

  // 检查Provider可用性
  console.log('检查Provider可用性:');
  const availability = await controller.checkProviders();
  console.log(availability);
  console.log();

  // 切换Provider
  console.log('切换到本地Ollama:');
  const switched = await controller.switchProvider('ollama-local');
  console.log('切换结果:', switched ? '成功' : '失败');
}

main().catch(console.error);

export async function quickStart() {
  AIConfigManager.loadFromEnv();

  const ai = createAIController();
  ai.setSystemPrompt('你是一个有帮助的AI助手。');

  const response = await ai.chat('你好！');
  console.log(response);
}

export async function localModelExample() {
  AIProviderFactory.register({
    type: 'ollama',
    name: 'local-llama',
    baseUrl: 'http://localhost:11434',
    model: 'llama2',
  });

  AIProviderFactory.setDefault('local-llama');

  const ai = createAIController({ provider: 'local-llama' });

  const response = await ai.chat('请用中文介绍一下你自己');
  console.log(response);
}

export async function multiProviderExample() {
  AIProviderFactory.registerMultiple([
    {
      config: {
        type: 'openai',
        name: 'gpt4',
        apiKey: process.env.OPENAI_API_KEY || '',
        model: 'gpt-4',
      },
      priority: 10,
    },
    {
      config: {
        type: 'ollama',
        name: 'local',
        baseUrl: 'http://localhost:11434',
        model: 'llama2',
      },
      priority: 5,
    },
  ]);

  const ai = createAIController({
    fallbackEnabled: true,
    onProviderSwitch: (from, to) => {
      console.log(`自动切换: ${from} -> ${to}`);
    },
  });

  const response = await ai.chat('Hello!');
  console.log(response);
}
