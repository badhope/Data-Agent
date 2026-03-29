# Changelog / 更新日志

All notable changes to this project will be documented in this file.

本项目的所有重要更改都将记录在此文件中。

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.0.0] - 2024-01-XX

### Added / 新增

- Initial release / 初始版本
- Multi-provider support (OpenAI, Anthropic, Ollama, LM Studio, Custom) / 多Provider支持
- Unified AI interface / 统一AI接口
- Streaming response support / 流式响应支持
- Tool calling (Function Calling) support / 工具调用支持
- Auto fallback mechanism / 自动降级机制
- Conversation history management / 对话历史管理
- Environment variable configuration / 环境变量配置
- JSON configuration file support / JSON配置文件支持
- TypeScript type definitions / TypeScript类型定义
- Bilingual documentation (English/Chinese) / 双语文档（中英文）

### Features / 特性

- `AIController` - High-level API for AI interactions / AI交互高级API
- `AIProviderFactory` - Provider management factory / Provider管理工厂
- `AIConfigManager` - Configuration management / 配置管理
- `OpenAIProvider` - OpenAI API integration / OpenAI API集成
- `OllamaProvider` - Local Ollama integration / 本地Ollama集成
- `LMStudioProvider` - LM Studio integration / LM Studio集成

---

## Future Plans / 未来计划

### [1.1.0] - Planned

- [ ] Add more local LLM support (vLLM, llama.cpp) / 添加更多本地LLM支持
- [ ] Add caching layer / 添加缓存层
- [ ] Add rate limiting / 添加速率限制
- [ ] Add request/response interceptors / 添加请求/响应拦截器

### [1.2.0] - Planned

- [ ] Add embedding support for all providers / 为所有Provider添加嵌入支持
- [ ] Add image generation support / 添加图像生成支持
- [ ] Add audio transcription support / 添加音频转录支持
