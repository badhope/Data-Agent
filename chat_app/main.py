"""Main entry point for the Data Agent chat application with sidebar."""

import chainlit as cl
from app.agents import create_agent
from app.logger import get_logger, log_agent_action, log_error
from app.config import load_config


def get_sidebar_html():
    """Generate sidebar HTML."""
    return """
    <div class="sidebar">
        <div class="sidebar-header">
            <div class="sidebar-logo">🤖 Data</div>
            <div class="sidebar-subtitle">智能助手</div>
        </div>
        
        <div class="sidebar-content">
            <div class="sidebar-section">
                <p class="sidebar-section-title">📋 快捷操作</p>
                
                <div class="sidebar-item" onclick="sendMessage('查看日志')">
                    <span class="sidebar-item-icon">📋</span>
                    <span class="sidebar-item-text">查看日志</span>
                </div>
                
                <div class="sidebar-item" onclick="sendMessage('查看配置')">
                    <span class="sidebar-item-icon">⚙️</span>
                    <span class="sidebar-item-text">查看配置</span>
                </div>
                
                <div class="sidebar-item" onclick="sendMessage('可用工具')">
                    <span class="sidebar-item-icon">📁</span>
                    <span class="sidebar-item-text">可用工具</span>
                </div>
            </div>
            
            <div class="sidebar-section">
                <p class="sidebar-section-title">🛠️ 功能工具</p>
                
                <div class="tool-card">
                    <div class="tool-card-title">🔍 网络搜索</div>
                    <div class="tool-card-desc">搜索网页信息</div>
                </div>
                
                <div class="tool-card">
                    <div class="tool-card-title">📄 文件操作</div>
                    <div class="tool-card-desc">读写文件内容</div>
                </div>
                
                <div class="tool-card">
                    <div class="tool-card-title">📂 目录浏览</div>
                    <div class="tool-card-desc">浏览文件夹</div>
                </div>
            </div>
            
            <div class="sidebar-section">
                <p class="sidebar-section-title">📊 状态信息</p>
                
                <div class="stats-card">
                    <div class="stats-item">
                        <span class="stats-label">运行状态</span>
                        <span class="stats-value">🟢 在线</span>
                    </div>
                    <div class="stats-item">
                        <span class="stats-label">API 模型</span>
                        <span class="stats-value">qwen-turbo</span>
                    </div>
                </div>
            </div>
        </div>
    </div>
    """


@cl.on_chat_start
async def on_chat_start():
    """Initialize chat session when a new user connects."""
    logger = get_logger()
    logger.info("New chat session started")
    
    try:
        agent = create_agent()
        cl.user_session.set("agent", agent)
        logger.info("Agent initialized successfully")
        
        # Send sidebar
        await cl.HTML(
            get_sidebar_html(),
            name="sidebar"
        ).send()
        
        # Send welcome message
        await cl.Message(
            content="""👋 你好！我是 **Data**，您的智能助手。

我可以帮您：
- 🔍 网页搜索
- 📄 文件读写  
- 📂 目录浏览

有什么可以帮您的吗？

💡 **提示**：点击左侧栏可快速访问功能菜单
"""
        ).send()
        
    except Exception as e:
        log_error("Agent initialization failed", e)
        await cl.Message(content="""❌ **系统初始化失败**

请检查：
1. API Key 是否配置正确
2. 网络连接是否正常

详细错误已记录到日志文件。
""").send()


@cl.on_message
async def on_message(message: cl.Message):
    """Handle incoming user messages."""
    logger = get_logger()
    msg_lower = message.content.lower().strip()
    
    # 处理特殊命令
    if msg_lower in ["查看日志", "日志", "logs"]:
        logs = logger.get_recent_logs(20)
        
        if not logs:
            await cl.Message(content="📋 **暂无日志**").send()
            return
        
        log_text = "📋 **最近日志：**\n\n"
        for log in logs:
            level_icon = {"DEBUG": "🔍", "INFO": "ℹ️", "WARNING": "⚠️", "ERROR": "❌"}.get(log["level"], "📝")
            log_text += f"{level_icon} **[{log['level']}]** {log['message']}\n"
            if log.get("details"):
                log_text += f"   详情: `{str(log['details'])[:150]}`\n"
            log_text += "\n"
        
        await cl.Message(content=log_text).send()
        return
    
    elif msg_lower in ["查看配置", "配置", "config"]:
        config = load_config()
        await cl.Message(content=f"""⚙️ **当前配置：**

**LLM 配置：**
- 模型：`{config.model}`
- API 地址：`{config.base_url}`
- Temperature：`{config.temperature}`
- 最大 Token：`{config.max_tokens}`

**API Key：** `{config.api_key[:8] + '...' if config.api_key else '未设置'}`

💡 如需修改配置，请编辑 `app/config.py` 文件
""").send()
        return
    
    elif msg_lower in ["可用工具", "工具", "tools", "help"]:
        await cl.Message(content="""📁 **可用工具列表：**

1. 🔍 **web_search** - 网页搜索
   - 功能：在网上搜索信息
   - 用法：搜索你需要的关键词

2. 📄 **write_file** - 写入文件
   - 功能：创建或修改文件
   - 用法：告诉我要写入的文件名和内容

3. 📄 **read_file** - 读取文件
   - 功能：读取文件内容
   - 用法：告诉我要读取的文件路径

4. 📂 **list_files** - 列出目录
   - 功能：查看文件夹中的内容
   - 用法：告诉我要查看的目录路径

💡 您可以直接用自然语言请求 Data 使用这些工具
""").send()
        return
    
    # 正常消息处理
    try:
        agent = cl.user_session.get("agent")
        
        if agent is None:
            await cl.Message(content="❌ **代理未初始化**，请刷新页面重试。").send()
            return

        log_agent_action(f"User: {message.content[:100]}...")
        
        result = agent.invoke({
            "messages": [{"role": "user", "content": message.content}]
        })
        
        response_content = ""
        if isinstance(result, dict) and "messages" in result:
            messages = result["messages"]
            if messages:
                last_message = messages[-1]
                if isinstance(last_message, dict) and "content" in last_message:
                    response_content = last_message["content"]
                elif hasattr(last_message, "content"):
                    response_content = str(last_message.content)
        
        if response_content:
            log_agent_action("Response sent successfully")
            await cl.Message(content=response_content).send()
        else:
            await cl.Message(content="❌ **未能获取响应**，请稍后重试。").send()

    except Exception as e:
        log_error("Message processing failed", e)
        await cl.Message(content=f"❌ **处理消息时出错**\n\n错误：{str(e)[:150]}\n\n详情已记录到日志。").send()


@cl.on_chat_end
async def on_chat_end():
    """Clean up when chat session ends."""
    logger = get_logger()
    logger.info("Chat session ended")
    cl.user_session.set("agent", None)
