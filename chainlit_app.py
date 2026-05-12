"""Chainlit frontend for OpenManus AI Agent.

Official Chainlit + LangChain integration pattern.
https://docs.chainlit.io/integrations/langchain
"""

import chainlit as cl
from typing import Union, Optional
from langchain_openai import ChatOpenAI
from langchain_core.language_models import BaseChatModel
from langchain_core.runnables.config import RunnableConfig
from langchain_core.runnables import Runnable
import os

SYSTEM_PROMPT = """You are OpenManus, a versatile AI assistant that can help users with various tasks.

Capabilities:
- Web browsing and information retrieval
- File operations and document processing
- Python code execution
- Text editing and search
- And much more!

Guidelines:
- Always use the available tools to complete tasks
- Ask for clarification when user requests are ambiguous
- Provide clear, structured responses
- Confirm important actions before executing them
"""


def get_agent():
    """Get or create the agent instance using 阿里百炼 API."""
    from langchain.tools import tool
    from langchain.agents import initialize_agent, AgentType
    from typing import Dict, Any

    # 使用阿里百炼 API
    model = ChatOpenAI(
        model="qwen-turbo",
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        api_key="sk-b8669932bc524dd191a14fc417079e8e",
        temperature=0.7,
        streaming=True
    )

    @tool
    def web_search(query: str) -> str:
        """Search the web for information about a topic."""
        from duckduckgo_search import DDGS
        results = DDGS().text(query, max_results=5)
        return "\n\n".join([f"- {r['title']}: {r['body']}" for r in results])

    @tool
    def write_file(file_path: str, content: str) -> str:
        """Write content to a file."""
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return f"Successfully wrote to {file_path}"

    @tool
    def read_file(file_path: str) -> str:
        """Read content from a file."""
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()

    @tool
    def list_files(directory: str = ".") -> str:
        """List files in a directory."""
        import os
        return "\n".join(os.listdir(directory))

    tools = [web_search, write_file, read_file, list_files]

    agent = initialize_agent(
        tools,
        model,
        agent=AgentType.CHAT_CONVERSATIONAL_REACT_DESCRIPTION,
        verbose=True
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
