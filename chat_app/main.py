"""Main entry point for the Chainlit chat application.

This file serves as the frontend interface layer that connects to the backend modules.
"""

import chainlit as cl
from typing import Optional
from app.agents import create_agent
from app.logger import get_logger, log_agent_action, log_error
from app.config import load_config


@cl.on_chat_start
async def on_chat_start():
    """Initialize chat session when a new user connects."""
    logger = get_logger()
    logger.info("New chat session started")
    
    try:
        agent = create_agent()
        cl.user_session.set("agent", agent)
        logger.info("Agent initialized successfully")
        
        await cl.Message(
            content="""👋 你好！我是 **Data**，您的智能助手。

我可以帮您：
- 🔍 网页搜索
- 📄 文件读写
- 📂 目录浏览

有什么可以帮您的吗？

💡 **提示**：
- 输入 "查看日志" 可查看最近的操作记录
- 输入 "查看配置" 可查看当前设置
- 输入 "可用工具" 可查看所有功能
"""
        ).send()
        
    except Exception as e:
        log_error("Agent initialization failed", e)
        error_msg = """❌ **系统初始化失败**

请检查：
1. API Key 是否配置正确
2. 网络连接是否正常

详细错误信息已记录到日志文件。
"""
        await cl.Message(content=error_msg).send()


@cl.on_message
async def on_message(message: cl.Message):
    """Handle incoming user messages."""
    logger = get_logger()
    
    # 检查特殊命令
    msg_lower = message.content.lower().strip()
    
    # 处理特殊命令
    if msg_lower in ["查看日志", "日志", "logs"]:
        logs = logger.get_recent_logs(20)
        
        if not logs:
            await cl.Message(content="📋 **暂无日志**").send()
            return
        
        log_text = "📋 **最近日志：**\n\n"
        
        for log in logs:
            level_icon = {
                "DEBUG": "🔍",
                "INFO": "ℹ️",
                "WARNING": "⚠️",
                "ERROR": "❌"
            }.get(log["level"], "📝")
            
            log_text += f"{level_icon} **[{log['level']}]** {log['message']}\n"
            
            if log.get("details"):
                details_str = str(log['details'])[:150]
                log_text += f"   详情: `{details_str}`\n"
            
            log_text += "\n"
        
        await cl.Message(content=log_text).send()
        return
    
    elif msg_lower in ["查看配置", "配置", "config"]:
        config = load_config()
        
        config_text = f"""⚙️ **当前配置：**

**LLM 配置：**
- 模型：`{config.model}`
- API 地址：`{config.base_url}`
- Temperature：`{config.temperature}`
- 最大 Token：`{config.max_tokens}`

**API Key：** `{config.api_key[:8] + '...' if config.api_key else '未设置'}`

💡 如需修改配置，请编辑 `app/config.py` 文件
"""
        
        await cl.Message(content=config_text).send()
        return
    
    elif msg_lower in ["可用工具", "工具", "tools", "help"]:
        tools_text = """📁 **可用工具列表：**

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
"""
        
        await cl.Message(content=tools_text).send()
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
        error_msg = f"❌ **处理消息时出错**\n\n错误信息：{str(e)[:150]}\n\n详情已记录到日志。"
        await cl.Message(content=error_msg).send()


@cl.on_chat_end
async def on_chat_end():
    """Clean up when chat session ends."""
    logger = get_logger()
    logger.info("Chat session ended")
    cl.user_session.set("agent", None)
