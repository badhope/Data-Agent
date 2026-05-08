"""Office Agent - Built on LangGraph prebuilt ReAct agent."""

from typing import Optional, Union
from langchain_core.language_models import BaseChatModel
from langchain_core.tools import BaseTool

from langchain_office_assistant.tools import ALL_OFFICE_TOOLS


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
- Be proactive in identifying automation opportunities

Remember to use tools effectively and provide helpful, actionable responses."""


def create_office_agent(
    model: Union[str, BaseChatModel] = "gpt-4",
    tools: Optional[list[BaseTool]] = None,
    system_prompt: Optional[str] = None,
    **kwargs
):
    """Create an office assistant agent using LangGraph prebuilt ReAct agent.

    This function wraps LangGraph's create_react_agent with office-specific configuration.

    Args:
        model: A chat model instance or model name string (default: "gpt-4")
        tools: List of tools to use (defaults to ALL_OFFICE_TOOLS)
        system_prompt: Custom system prompt (defaults to office assistant prompt)
        **kwargs: Additional arguments passed to create_react_agent()

    Returns:
        A compiled LangGraph agent graph

    Example:
        ```python
        from langchain_office_assistant.agents import create_office_agent
        from langchain_openai import ChatOpenAI

        model = ChatOpenAI(model="gpt-4", temperature=0.7)
        agent = create_office_agent(model=model)

        result = agent.invoke({"messages": [{"role": "user", "content": "Schedule a meeting"}]})
        ```
    """
    from langgraph.prebuilt import create_react_agent

    agent_tools = tools if tools is not None else ALL_OFFICE_TOOLS
    prompt = system_prompt if system_prompt is not None else SYSTEM_PROMPT

    if isinstance(model, str):
        from langchain_openai import ChatOpenAI
        model = ChatOpenAI(model=model, temperature=0.7)

    agent = create_react_agent(
        model=model,
        tools=agent_tools,
        state_modifier=prompt,
        **kwargs
    )

    return agent


def run_office_assistant(
    user_input: str,
    model: Union[str, BaseChatModel] = "gpt-4",
    tools: Optional[list[BaseTool]] = None,
    stream: bool = True,
):
    """Run the office assistant with a single user input.

    Args:
        user_input: The user's message
        model: A chat model instance or model name
        tools: Optional list of tools
        stream: Whether to stream the response

    Returns:
        The agent's response (if stream=False)
    """
    agent = create_office_agent(model=model, tools=tools)

    if stream:
        for chunk in agent.stream(
            {"messages": [{"role": "user", "content": user_input}]},
            stream_mode="values"
        ):
            if "messages" in chunk:
                last_msg = chunk["messages"][-1]
                if hasattr(last_msg, "content") and last_msg.content:
                    print(last_msg.content, end="", flush=True)
        print()  # Add newline after streaming completes
    else:
        result = agent.invoke(
            {"messages": [{"role": "user", "content": user_input}]}
        )
        return result


__all__ = [
    "create_office_agent",
    "run_office_assistant",
    "SYSTEM_PROMPT",
]
