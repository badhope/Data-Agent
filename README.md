# Data-Agent 智能助手平台 (2026版)

## 🎯 项目概述

Data-Agent 是一个功能完整的智能数据助手平台，基于 OpenManus 构建，集成了先进的文档处理能力、语音交互功能和企业级知识库系统。

---

## 🚀 快速开始

### 1. 启动应用

```bash
cd OpenManus
python web_app.py
```

然后在浏览器中访问 `http://localhost:8000`

---

## 🎤 语音输入功能

### 使用方法

1. 在主对话界面的输入框上方，找到 **🎤 语音输入** 按钮
2. 点击按钮开始录音（浏览器会请求麦克风权限）
3. 对着麦克风说话，系统会实时识别并显示在输入框中
4. 说完后再次点击按钮停止，或等待语音识别自动结束
5. 按 Enter 或点击发送按钮发送消息

### 支持的语言

- ✅ **中文** (普通话)
- ✅ **英文** (US/UK)
- ✅ **日文**
- ✅ **韩文**
- ✅ 其他多种语言

### 技术特性

- 使用 **Web Speech API**（浏览器内置，无需额外依赖）
- 支持实时语音识别（interim results）
- 语音朗读功能（Text-to-Speech）
- 音频波形可视化

---

## 📚 知识库功能

### 核心能力

| 功能 | 描述 | 状态 |
|------|------|------|
| 文档上传 | 支持多种格式文件上传 | ✅ |
| 向量检索 | 基于内容相似度搜索 | ✅ |
| 问答系统 | 基于文档内容回答问题 | ✅ |
| 多知识库管理 | 创建和管理多个知识库 | ✅ |
| 文档导入导出 | 支持知识库备份和迁移 | ✅ |

### 支持的文件格式

- 📄 **文本文件** (.txt, .md, .json)
- 📋 **Markdown** (.md)
- 🌐 **HTML** (.html, .htm)
- 📕 **PDF** (.pdf)

### API端点

```
GET    /api/knowledge/bases              # 列出所有知识库
POST   /api/knowledge/bases              # 创建新知识库
DELETE /api/knowledge/bases/{name}       # 删除知识库
POST   /api/knowledge/bases/{name}/files # 上传文件
POST   /api/knowledge/bases/{name}/query # 问答查询
POST   /api/knowledge/bases/{name}/chat  # 对话模式
```

### 使用示例

```python
# 创建知识库
import requests
requests.post('http://localhost:8000/api/knowledge/bases', 
              json={'name': 'my_knowledge'})

# 上传文件
with open('document.pdf', 'rb') as f:
    requests.post('http://localhost:8000/api/knowledge/bases/my_knowledge/files',
                  files={'files': f})

# 查询知识库
result = requests.post('http://localhost:8000/api/knowledge/bases/my_knowledge/query',
                       json={'question': '文档中提到了什么？'})
```

---

## 📖 文档处理模块

### 会议纪要生成
- 📝 支持从会议记录自动提取信息
- ✅ 自动识别参会人员、讨论要点、决议事项
- 📋 生成结构化的会议纪要文档

### 文献摘要提取
- 📄 支持学术论文和普通文档
- 📊 提取关键信息：标题、作者、摘要
- 🔖 支持多种引用格式（APA, MLA, GB7714）

### 多语言翻译
- 🌐 支持中英日韩等多种语言互译
- ✨ 专业术语库
- 📝 保持原文格式和排版

### PPT生成
- 📊 多种专业模板（商业报告、学术报告、会议纪要等）
- 🎨 主题配色方案
- 📈 支持图表和数据可视化

---

## 🤖 智能体系统

### 智能体管理

| 功能 | 描述 |
|------|------|
| 创建智能体 | 自定义智能体名称和角色 |
| 角色定义 | 设置系统提示词和行为规则 |
| 模型配置 | 选择使用的LLM模型 |
| 工具集成 | 配置可用的工具集 |
| 对话历史 | 查看和管理对话记录 |

### 智能体市场

即将推出：
- 📦 预配置的智能体模板
- 🔄 智能体导入导出
- ⭐ 社区分享功能

---

## 🔧 工具集

### 核心工具

| 工具 | 图标 | 描述 |
|------|------|------|
| Python执行 | 🐍 | 在沙箱中运行Python代码 |
| Shell执行 | 💻 | 运行系统命令 |
| 网络搜索 | 🔍 | 实时网络搜索 |
| 计算器 | 🧮 | 数学计算和单位转换 |
| 日期处理 | 📅 | 日期计算和格式化 |
| 待办管理 | ✅ | 任务清单管理 |

### 文档工具

| 工具 | 触发词 |
|------|--------|
| PPT生成 | "生成PPT", "创建演示文稿" |
| 待办提取 | "提取待办", "待办事项" |
| 会议纪要 | "会议纪要", "会议总结" |
| 周报生成 | "写周报", "周报总结" |
| 文献总结 | "总结文献", "摘要提取" |

---

## ⚙️ 模型设置

### 支持的提供商

| 提供商 | 支持状态 | 自定义模型 | 余额查询 |
|--------|----------|------------|----------|
| OpenAI | ✅ | ✅ | ✅ |
| Anthropic | ✅ | ✅ | ✅ |
| Google Gemini | ✅ | ✅ | ⚠️ |
| 阿里云通义千问 | ✅ | ✅ | ⚠️ |
| DeepSeek | ✅ | ✅ | ⚠️ |
| Ollama (本地) | ✅ | ✅ | - |
| 智谱 GLM | ✅ | ✅ | ⚠️ |
| 月之暗面 Kimi | ✅ | ✅ | ⚠️ |

### 连接测试

- ✅ 实时测试API连接
- ✅ 验证模型是否存在
- ✅ 显示详细错误信息
- ✅ 提供解决方案建议

---

## 📊 数据分析

### 数据可视化

- 📈 图表生成（折线图、柱状图、饼图）
- 📊 数据表格展示
- 📉 趋势分析
- 📋 报告生成

### NL2SQL

- ✅ 自然语言转SQL查询
- ✅ 支持多种数据库
- ✅ 查询结果可视化

---

## 🧩 侧边栏功能

### 导航菜单

```
├── 🤖 对话           # 主对话界面
├── 📚 知识库         # 文档管理和查询
├── ⚡ 技能管理       # 自动化工作流
├── 📝 提示词管理     # 提示词模板
├── 🔌 MCP管理       # MCP服务器连接
└── ⚙️ 设置           # 系统配置
```

---

## 🔌 MCP管理

### 功能特性

- 🔗 连接外部MCP服务器
- 🧰 管理可用工具
- 🧪 测试工具调用
- 📊 监控服务器状态

### 支持的工具类型

- Web搜索
- 文件操作
- 代码执行
- API调用
- 数据库查询

---

## 🗂️ 任务管理

### 核心功能

- ✅ 待办清单创建和管理
- ✅ 任务状态追踪
- ✅ 截止日期提醒
- ✅ 任务优先级设置
- ✅ 任务分类和标签

### API端点

```
GET    /api/tasks           # 获取任务列表
POST   /api/tasks           # 创建任务
PUT    /api/tasks/{id}      # 更新任务
DELETE /api/tasks/{id}      # 删除任务
```

---

## 🔧 高级配置

### 配置文件

```toml
[app]
name = "Data-Agent"
version = "2026.1.0"
debug = false

[llm]
default_provider = "openai"
timeout = 60

[knowledge]
persist_dir = "./data/knowledge_base"
chunk_size = 512
overlap = 64

[security]
max_requests_per_minute = 60
allowed_origins = ["*"]
```

---

## 📁 项目结构

```
Data-Agent/
├── OpenManus/
│   ├── main.py              # CLI入口
│   ├── web_app.py           # Web应用入口
│   ├── app/
│   │   ├── agent/           # Agent实现
│   │   ├── tool/            # 工具集
│   │   ├── document/        # 文档处理模块
│   │   │   ├── meeting_minutes.py
│   │   │   ├── summarizer.py
│   │   │   ├── translator.py
│   │   │   └── ppt_generator.py
│   │   ├── knowledge/       # 知识库模块 ⭐
│   │   │   ├── __init__.py
│   │   │   ├── vector_store.py
│   │   │   ├── document_loader.py
│   │   │   ├── knowledge_base.py
│   │   │   └── qa_engine.py
│   │   ├── sandbox/         # 沙箱环境
│   │   └── mcp/             # MCP协议
│   ├── routers/
│   │   ├── settings.py      # 设置路由
│   │   ├── knowledge.py     # 知识库API ⭐
│   │   ├── skills.py        # 技能路由
│   │   ├── mcp.py           # MCP路由
│   │   └── ...
│   ├── services/            # 服务层
│   ├── static/
│   │   ├── js/
│   │   │   ├── app.js
│   │   │   └── voice_input.js  # 语音输入 ⭐
│   │   └── css/
│   └── templates/           # HTML模板
└── README.md                # 使用文档
```

---

## 🌟 特色功能

### ⭐ 智能对话
- 💬 自然语言理解
- 🤖 多模型支持
- 📎 文件上传和分析
- 📊 数据可视化

### ⭐ 语音交互
- 🎤 语音输入（实时识别）
- 🔊 语音朗读（可调节语速）
- 🌐 多语言支持
- ⌨️ 无障碍设计

### ⭐ 知识库系统
- 📚 多格式文档支持
- 🔍 智能检索
- 💬 对话式问答
- 📤 导入导出

### ⭐ 智能体系统
- 🤖 可定制的AI助手
- ⚡ 自动化工作流
- 📚 模板和技能库
- 🔌 扩展集成

---

## 📖 API文档

### 基础URL

```
http://localhost:8000/api/
```

### 完整API列表

| 模块 | 端点 | 方法 | 描述 |
|------|------|------|------|
| 知识库 | /knowledge/bases | GET | 列出知识库 |
| 知识库 | /knowledge/bases | POST | 创建知识库 |
| 知识库 | /knowledge/bases/{name}/query | POST | 问答查询 |
| 设置 | /settings/providers | GET | 获取提供商列表 |
| 设置 | /settings/test-connection | POST | 测试连接 |
| 技能 | /skills/list | GET | 获取技能列表 |
| 技能 | /skills/execute | POST | 执行技能 |
| MCP | /mcp/servers | GET | 获取服务器列表 |
| MCP | /mcp/tools | GET | 获取工具列表 |

---

## 🧪 测试

### 运行测试

```bash
cd OpenManus
python -m pytest tests/
```

### 测试覆盖

- ✅ 文档处理模块
- ✅ 知识库模块
- ✅ 语音输入模块
- ✅ API路由
- ✅ 工具集

---

## 🔧 部署

### 开发环境

```bash
# 安装依赖
pip install -r requirements.txt

# 启动开发服务器
python web_app.py
```

### 生产环境

```bash
# 使用 Gunicorn
pip install gunicorn
gunicorn -w 4 web_app:app
```

---

## 📄 许可证

本项目遵循 Apache 2.0 开源许可证。

---

## 🙏 致谢

感谢所有参与本项目开发的贡献者！

---

**版本**: 2026.1.0  
**更新日期**: 2026年5月  
**文档版本**: v2026.1

---

## 📞 获取帮助

如有问题，请查看：
- 📖 本文档的故障排除部分
- 🔍 浏览器控制台错误信息
- 📝 项目 Issues
