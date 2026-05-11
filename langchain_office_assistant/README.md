# Office Agent - 办公智能体

一个基于 LangChain 构建的专业办公智能体框架，提供邮件管理、日历调度、任务管理、文档处理、PPT生成、知识库检索、图表报告和计算工具等功能。

## 功能特性

### 📧 邮件管理
- 发送邮件
- 搜索邮件
- 阅读邮件详情

### 📅 日历管理
- 创建会议/事件
- 查询日程安排
- 设置提醒

### ✅ 任务管理
- 创建任务
- 任务列表
- 更新任务状态

### 📄 文档处理
- Word/Excel/PDF读写
- 文档格式转换

### 📊 PPT生成
- 演示文稿创建
- 幻灯片管理
- 图表嵌入

### 📚 知识库
- 向量检索
- 文档问答
- 多模态支持

### 📈 图表报告
- 折线图、柱状图、饼图
- 雷达图、散点图
- 数据可视化

### 🧮 计算工具
- 公式计算
- 统计分析
- 单位转换

### 🔍 意图识别
- 上下文理解
- 多轮对话支持

### 📝 计算追溯
- 完整思考过程记录
- 执行步骤可视化

## 技术栈

- **核心框架**: LangChain + LangGraph
- **API框架**: FastAPI
- **向量数据库**: FAISS
- **会话存储**: Redis
- **文档处理**: python-docx, openpyxl, PyPDF2
- **PPT生成**: python-pptx
- **图表生成**: matplotlib, plotly

## 安装

```bash
pip install -e .
```

## 配置

创建 `.env` 文件：

```env
OPENAI_API_KEY=your-api-key
REDIS_URL=redis://localhost:6379
AGENT_MODEL=gpt-3.5-turbo
```

## 使用方式

### CLI 模式

```bash
office-agent chat
```

### API 服务

```bash
office-agent serve --host 0.0.0.0 --port 8000
```

### Python API

```python
from langchain_office_assistant import create_office_agent

agent = create_office_agent({
    "agent_model": "gpt-3.5-turbo",
    "openai_api_key": "your-api-key",
})

result = await agent.run("帮我发送一封邮件给张三")
print(result["response"])
```

## API 接口

### POST /chat
发送消息给智能体

```json
{
  "message": "帮我计算 2 + 3",
  "session_id": "optional-session-id"
}
```

### GET /trace/{trace_id}
获取执行追溯报告

### GET /tools
获取可用工具列表

## 项目结构

```
langchain_office_assistant/
├── agents/                    # 智能体核心模块
│   ├── core.py               # 主智能体类
│   ├── intent_recognizer.py  # 意图识别器
│   ├── memory_manager.py     # 记忆管理器
│   └── trace_recorder.py     # 追溯记录器
├── plugins/                  # 功能插件
│   ├── email/                # 邮件插件
│   ├── calendar/             # 日历插件
│   ├── task/                 # 任务插件
│   ├── document/             # 文档插件
│   ├── ppt/                  # PPT插件
│   ├── knowledge/            # 知识库插件
│   ├── chart/                # 图表插件
│   └── calc/                 # 计算插件
├── api/                      # API服务
│   └── main.py
├── cli/                      # 命令行接口
│   └── main.py
├── utils/                    # 工具函数
│   ├── config.py
│   ├── logger.py
│   └── helpers.py
└── tests/                    # 测试模块
    ├── test_agents.py
    └── test_plugins.py
```

## 测试

```bash
pytest tests/ -v
```

## Docker 部署

```bash
cd docker
docker-compose up -d
```

## 许可证

MIT License