import click
import asyncio
import os
from langchain_office_assistant.agents import (
    create_office_agent,
    run_office_assistant,
    TraceRecorder,
)
from langchain_office_assistant.utils.config import config
from langchain_office_assistant.utils.model_manager import create_model_manager

@click.group()
def cli():
    pass

@cli.command()
@click.option("--model", default=None, help="指定使用的模型名称")
def chat(model):
    os.chdir('/workspace/langchain_office_assistant')

    click.echo("\n🚀 Office Agent CLI - 输入 'exit' 或 'quit' 退出")
    click.echo("=" * 60)

    model_manager = None
    current_model = model or config.agent_model

    if config.openai_api_key:
        try:
            model_manager = create_model_manager(
                config.openai_api_key,
                config.openai_api_base
            )
            click.echo(f"📡 已连接到阿里百炼平台")
        except Exception as e:
            click.echo(f"⚠️ 无法连接模型管理器: {e}")

    click.echo(f"🤖 当前模型: {current_model}\n")

    config_dict = {
        "agent_model": current_model,
        "openai_api_key": config.openai_api_key,
        "openai_api_base": config.openai_api_base,
        "redis_url": config.redis_url,
    }

    session_id = None

    while True:
        user_input = click.prompt("\n👤 你")

        if user_input.lower() in ["exit", "quit", "bye"]:
            click.echo("\n👋 再见！")
            break

        if user_input.lower() == "help":
            click.echo("""
📖 可用命令:
- help: 显示帮助信息
- exit/quit/bye: 退出程序
- /models: 查看可用模型列表
- /set-model <模型名>: 切换到指定模型
- /test-model <模型名>: 测试模型是否可用
- /current: 查看当前模型
- trace <trace_id>: 查看执行追溯报告
- /tools: 查看可用工具列表
- /clear: 清屏
            """)
            continue

        if user_input.lower() == "/models":
            list_models(model_manager)
            continue

        if user_input.lower().startswith("/set-model "):
            parts = user_input.split(" ", 1)
            if len(parts) > 1:
                new_model = parts[1].strip()
                success = set_model(model_manager, new_model, config_dict)
                if success:
                    current_model = new_model
            continue

        if user_input.lower().startswith("/test-model "):
            parts = user_input.split(" ", 1)
            if len(parts) > 1:
                test_model_name = parts[1].strip()
                test_single_model(model_manager, test_model_name)
            continue

        if user_input.lower() == "/current":
            click.echo(f"\n🔍 当前模型: {current_model}")
            continue

        if user_input.lower() == "/tools":
            show_tools(config_dict)
            continue

        if user_input.lower() == "/clear":
            click.echo("\n" * 50)
            continue

        if user_input.lower().startswith("trace "):
            parts = user_input.split(" ", 1)
            if len(parts) > 1:
                trace_id = parts[1]
                show_trace(trace_id)
            continue

        try:
            result = asyncio.run(run_office_assistant(
                user_input=user_input,
                session_id=session_id,
                config=config_dict
            ))

            session_id = result["session_id"]

            click.echo(f"\n🤖 助手 (模型: {current_model})")
            click.echo("-" * 60)
            click.echo(result["response"])
            click.echo("-" * 60)
            click.echo(f"\n⏱️ 耗时: {result['duration_ms']}ms | 意图: {result['intent']}")
            click.echo(f"📝 Trace ID: {result['trace_id']}")

        except Exception as e:
            click.echo(f"\n❌ 错误: {e}")

@cli.command()
@click.option("--model", default=None, help="指定要测试的模型名称")
def models(model):
    """查看可用模型列表"""
    model_manager = None

    if config.openai_api_key:
        try:
            model_manager = create_model_manager(
                config.openai_api_key,
                config.openai_api_base
            )
        except Exception as e:
            click.echo(f"⚠️ 无法连接模型管理器: {e}")

    list_models(model_manager)

@cli.command()
@click.argument("model_name")
def test_model(model_name):
    """测试指定模型是否可用"""
    model_manager = None

    if config.openai_api_key:
        try:
            model_manager = create_model_manager(
                config.openai_api_key,
                config.openai_api_base
            )
        except Exception as e:
            click.echo(f"⚠️ 无法连接模型管理器: {e}")

    test_single_model(model_manager, model_name)

def list_models(model_manager):
    """列出所有可用模型"""
    click.echo("\n📦 可用模型列表:")
    click.echo("=" * 60)

    if model_manager:
        try:
            models = model_manager.list_models()
            click.echo(f"\n从API获取到 {len(models)} 个模型:\n")

            for i, model in enumerate(models[:20], 1):
                click.echo(f"{i:2d}. {model.name}")
                click.echo(f"    📝 {model.description}")
                click.echo(f"    🏷️  {model.display_name}")
                click.echo()

            if len(models) > 20:
                click.echo(f"... 还有 {len(models) - 20} 个模型")
        except Exception as e:
            click.echo(f"❌ 获取模型列表失败: {e}")
    else:
        click.echo("⚠️ 模型管理器未初始化")

    click.echo("\n" + "=" * 60)
    click.echo("💡 使用 '/set-model <模型名>' 切换模型")

def test_single_model(model_manager, model_name):
    """测试单个模型"""
    click.echo(f"\n🔍 测试模型: {model_name}")
    click.echo("=" * 60)

    if not model_manager:
        click.echo("⚠️ 模型管理器未初始化")
        return

    click.echo("\n⏳ 正在测试...")

    result = model_manager.test_model(model_name)

    if result["success"]:
        click.echo("\n✅ 模型可用!")
        click.echo(f"   响应: {result['response']}")
        click.echo(f"   耗时: {result['duration_ms']}ms")
        if "usage" in result:
            click.echo(f"   Token使用: {result['usage'].get('total_tokens', 0)}")
    else:
        click.echo(f"\n❌ 模型不可用")
        click.echo(f"   错误: {result.get('error')}")
        if "error_detail" in result:
            click.echo(f"   详情: {result.get('error_detail')}")

    click.echo("\n" + "=" * 60)

def set_model(model_manager, new_model, config_dict):
    """设置当前模型"""
    click.echo(f"\n🔄 切换到模型: {new_model}")
    click.echo("=" * 60)

    if model_manager:
        click.echo("\n⏳ 正在验证模型...")

        result = model_manager.test_model(new_model)

        if result["success"]:
            model_manager.current_model = new_model
            config_dict["agent_model"] = new_model

            click.echo("\n✅ 模型切换成功!")
            click.echo(f"   模型: {new_model}")
            click.echo(f"   响应: {result['response']}")
            click.echo(f"   耗时: {result['duration_ms']}ms")
            return True
        else:
            click.echo(f"\n❌ 模型切换失败")
            click.echo(f"   错误: {result.get('error')}")
            if "error_detail" in result:
                click.echo(f"   详情: {result.get('error_detail')}")
            return False
    else:
        config_dict["agent_model"] = new_model
        click.echo(f"\n✅ 模型已设置为: {new_model}")
        return True

    click.echo("\n" + "=" * 60)

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
