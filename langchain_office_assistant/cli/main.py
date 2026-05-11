import click
import asyncio
from langchain_office_assistant.agents import (
    create_office_agent,
    run_office_assistant,
    TraceRecorder,
)
from langchain_office_assistant.utils.config import config

@click.group()
def cli():
    pass

@cli.command()
@click.option("--model", default=config.agent_model, help="LLM model name")
def chat(model):
    click.echo("🚀 Office Agent CLI - 输入 'exit' 或 'quit' 退出")
    click.echo("=" * 50)
    
    config_dict = {
        "agent_model": model,
        "openai_api_key": config.openai_api_key,
        "redis_url": config.redis_url,
    }
    
    session_id = None
    
    while True:
        user_input = click.prompt("\n👤 你")
        
        if user_input.lower() in ["exit", "quit", "bye"]:
            click.echo("👋 再见！")
            break
        
        if user_input.lower() == "help":
            click.echo("""
可用命令:
- help: 显示帮助信息
- exit/quit/bye: 退出程序
- trace <trace_id>: 查看执行追溯报告
- tools: 查看可用工具列表
            """)
            continue
        
        if user_input.lower().startswith("trace "):
            parts = user_input.split(" ", 1)
            if len(parts) > 1:
                trace_id = parts[1]
                show_trace(trace_id)
            continue
        
        if user_input.lower() == "tools":
            show_tools(config_dict)
            continue
        
        try:
            result = asyncio.run(run_office_assistant(
                user_input=user_input,
                session_id=session_id,
                config=config_dict
            ))
            
            session_id = result["session_id"]
            
            click.echo(f"\n🤖 助手 ({result['intent']}, 置信度: {result['confidence']:.2f})")
            click.echo(result["response"])
            click.echo(f"\n⏱️ 耗时: {result['duration_ms']}ms")
            click.echo(f"📝 Trace ID: {result['trace_id']}")
            
        except Exception as e:
            click.echo(f"❌ 错误: {e}")

@cli.command()
@click.argument("trace_id")
def trace(trace_id):
    show_trace(trace_id)

def show_trace(trace_id):
    try:
        recorder = TraceRecorder()
        report = recorder.visualize_trace(trace_id)
        click.echo("\n" + "=" * 60)
        click.echo(report)
        click.echo("=" * 60)
    except Exception as e:
        click.echo(f"❌ 获取追溯失败: {e}")

@cli.command()
def tools():
    show_tools({})

def show_tools(config):
    try:
        agent = create_office_agent(config)
        tools = agent.get_available_tools()
        
        click.echo("\n📦 可用工具:")
        click.echo("-" * 50)
        
        plugin_tools = {}
        for tool in tools:
            plugin = tool["plugin"]
            if plugin not in plugin_tools:
                plugin_tools[plugin] = []
            plugin_tools[plugin].append(tool)
        
        for plugin, tool_list in plugin_tools.items():
            click.echo(f"\n🔧 {plugin}:")
            for tool in tool_list:
                click.echo(f"  - {tool['name']}: {tool['description']}")
        
        click.echo("\n" + "-" * 50)
    except Exception as e:
        click.echo(f"❌ 获取工具列表失败: {e}")

@cli.command()
@click.option("--host", default="0.0.0.0", help="API host")
@click.option("--port", default=8000, help="API port")
def serve(host, port):
    click.echo(f"🚀 启动 Office Agent API 服务")
    click.echo(f"📍 地址: http://{host}:{port}")
    click.echo(f"📖 文档: http://{host}:{port}/docs")
    
    from langchain_office_assistant.api.main import run_api
    run_api(host, port)

if __name__ == "__main__":
    cli()