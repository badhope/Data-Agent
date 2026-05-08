"""Chainlit frontend for Office Assistant Agent.

Official Chainlit + LangChain integration pattern.
https://docs.chainlit.io/integrations/langchain
"""

import chainlit as cl
from typing import Union, Optional
from langchain_openai import ChatOpenAI
from langchain_core.language_models import BaseChatModel
from langchain_core.runnables.config import RunnableConfig
from langchain_core.runnables import Runnable

SYSTEM_PROMPT = """You are a professional office assistant helping users with:

📧 Email Management - Send, search, and manage emails
📅 Calendar & Scheduling - Check schedules and schedule meetings
✅ Task Management - Create and track tasks and todos
📄 Document Handling - Search and summarize documents

Guidelines:
- Always use the available tools to complete tasks
- Ask for clarification when user requests are ambiguous
- Provide clear, structured responses
- Confirm important actions before executing them
"""


def get_agent():
    """Get or create the agent instance."""
    from langchain.agents import create_agent
    from langchain_office_assistant.tools import ALL_OFFICE_TOOLS

    model = ChatOpenAI(
        model="gpt-4",
        temperature=0.7,
        streaming=True
    )

    agent = create_agent(
        model=model,
        tools=ALL_OFFICE_TOOLS,
        system_prompt=SYSTEM_PROMPT,
    )

    return agent


@cl.on_chat_start
async def on_chat_start():
    """Initialize chat session with user."""
    try:
        agent = get_agent()
        cl.user_session.set("runnable", agent)
        await cl.Message(
            content="👋 你好！我是办公助手，可以帮你处理邮件、日程、文档和任务。有什么可以帮你的吗？"
        ).send()
    except Exception as e:
        await cl.Message(
            content=f"❌ 初始化失败: {str(e)}\n\n请确保已设置 OPENAI_API_KEY 环境变量。"
        ).send()


@cl.on_message
async def on_message(message: cl.Message):
    """Handle incoming user message with streaming support."""
    try:
        runnable: Optional[Runnable] = cl.user_session.get("runnable")

        if runnable is None:
            await cl.Message(
                content="❌ Agent 未初始化，请刷新页面重试。"
            ).send()
            return

        msg = cl.Message(content="")

        async for chunk in runnable.astream(
            {"messages": [{"role": "user", "content": message.content}]},
            config=RunnableConfig(callbacks=[cl.LangchainCallbackHandler()]),
        ):
            if hasattr(chunk, "content") and chunk.content:
                await msg.stream_token(chunk.content)

        await msg.send()

    except Exception as e:
        await cl.Message(
            content=f"❌ 处理消息时出错: {str(e)}"
        ).send()
