"""Main entry point for the Chainlit chat application.

This file serves as the frontend interface layer that connects to the backend modules.
"""

import chainlit as cl
from typing import Optional
from app.agents import create_agent


@cl.on_chat_start
async def on_chat_start():
    """Initialize chat session when a new user connects."""
    try:
        agent = create_agent()
        cl.user_session.set("agent", agent)
        
        await cl.Message(
            content="👋 你好！我是 Data，您的智能助手。\n\n我可以帮您：\n- 🔍 网页搜索\n- 📄 文件读写\n- 📂 目录浏览\n\n有什么可以帮您的吗？"
        ).send()
        
    except Exception as e:
        error_msg = f"❌ 初始化失败: {str(e)}"
        await cl.Message(content=error_msg).send()
        cl.logger.error(f"Agent initialization failed: {e}")


@cl.on_message
async def on_message(message: cl.Message):
    """Handle incoming user messages."""
    try:
        agent = cl.user_session.get("agent")
        
        if agent is None:
            await cl.Message(
                content="❌ 代理未初始化，请刷新页面重试。"
            ).send()
            return

        # Run the agent with the user's message using LangGraph format
        result = agent.invoke({
            "messages": [{"role": "user", "content": message.content}]
        })
        
        # Extract the response content
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
            await cl.Message(content=response_content).send()
        else:
            await cl.Message(content="❌ 未能获取响应内容").send()

    except Exception as e:
        error_msg = f"❌ 处理消息时出错: {str(e)}"
        await cl.Message(content=error_msg).send()
        cl.logger.error(f"Message processing failed: {e}")


@cl.on_chat_end
async def on_chat_end():
    """Clean up when chat session ends."""
    try:
        cl.user_session.set("agent", None)
        cl.logger.info("Chat session ended")
    except Exception as e:
        cl.logger.error(f"Cleanup failed: {e}")