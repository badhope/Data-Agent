import click
import asyncio
import os
from langchain_office_assistant.agents import (
    create_office_agent,
    run_office_assistant,
    TraceRecorder,
)
from langchain_office_assistant.utils.config import config
from langchain_office_assistant.utils.multi_platform_manager import (
    get_model_manager,
    setup_platform,
    switch_platform,
    list_platforms,
)
from langchain_office_assistant.adapters import PlatformType

@click.group()
def cli():
    pass

@cli.command()
@click.option("--model", default=None, help="指定使用的模型名称")
@click.option("--platform", default=None, help="指定使用的平台 (dashscope/openai/anthropic/gemini)")
def chat(model, platform):
    os.chdir('/workspace/langchain_office_assistant')

    click.echo("\n🚀 Office Agent CLI - 输入 'exit' 或 'quit' 退出")
    click.echo("=" * 60)

    manager = get_model_manager()
    current_platform = platform or "dashscope"
    current_model = model or config.agent_model

    if config.openai_api_key:
        try:
            manager.setup_platform(
                current_platform,
                config.openai_api_key
            )
            click.echo(f"📡 已连接到 {manager.get_current_platform()} 平台")
        except Exception as e:
            click.echo(f"⚠️ 无法连接模型管理器: {e}")

    click.echo(f"🤖 当前平台: {current_platform}")
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
- /platforms: 查看所有支持的平台
- /setup <平台> <API密钥>: 配置新平台
- /switch <平台>: 切换到指定平台
- /models: 查看当前平台可用模型
- /set-model <模型名>: 切换到指定模型
- /test-model <模型名>: 测试模型是否可用
- /current: 查看当前平台和模型
- trace <trace_id>: 查看执行追溯报告
- /tools: 查看可用工具列表
- /clear: 清屏
            """)
            continue

        if user_input.lower() == "/platforms":
            list_all_platforms()
            continue

        if user_input.lower().startswith("/setup "):
            parts = user_input.split(" ", 2)
            if len(parts) >= 3:
                setup_platform_cmd(parts[1], parts[2])
            elif len(parts) == 2:
                click.echo("⚠️ 请提供API密钥: /setup <平台> <API密钥>")
                click.echo("   例如: /setup openai sk-xxxx")
            continue

        if user_input.lower().startswith("/switch "):
            parts = user_input.split(" ", 1)
            if len(parts) > 1:
                new_platform = parts[1].strip()
                if switch_platform(new_platform):
                    click.echo(f"✅ 已切换到 {new_platform} 平台")
                    current_platform = new_platform
                else:
                    click.echo(f"❌ 切换失败，请先使用 /setup 配置该平台")
            continue

        if user_input.lower() == "/models":
            list_platform_models(manager)
            continue

        if user_input.lower().startswith("/set-model "):
            parts = user_input.split(" ", 1)
            if len(parts) > 1:
                new_model = parts[1].strip()
                success = set_model(manager, new_model, config_dict)
                if success:
                    current_model = new_model
            continue

        if user_input.lower().startswith("/test-model "):
            parts = user_input.split(" ", 1)
            if len(parts) > 1:
                test_model_name = parts[1].strip()
                test_single_model(manager, test_model_name)
            continue

        if user_input.lower() == "/current":
            click.echo(f"\n🔍 当前平台: {current_platform}")
            click.echo(f"🔍 当前模型: {current_model}")
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

            click.echo(f"\n🤖 助手 (平台: {current_platform}, 模型: {current_model})")
            click.echo("-" * 60)
            click.echo(result["response"])
            click.echo("-" * 60)
            click.echo(f"\n⏱️ 耗时: {result['duration_ms']}ms | 意图: {result['intent']}")
            click.echo(f"📝 Trace ID: {result['trace_id']}")

        except Exception as e:
            click.echo(f"\n❌ 错误: {e}")

@cli.command()
@click.option("--platform", default=None, help="指定平台")
def models(platform):
    """查看可用模型列表"""
    manager = get_model_manager()
    platform = platform or manager.get_current_platform() or "dashscope"

    list_platform_models(manager, platform)

@cli.command()
def platforms():
    """查看所有支持的平台"""
    list_all_platforms()

@cli.command()
@click.argument("platform")
@click.argument("api_key")
@click.option("--api-base", default=None, help="自定义API基础URL")
def setup(platform, api_key, api_base):
    """配置新平台"""
    setup_platform_cmd(platform, api_key, api_base)

@cli.command()
@click.argument("platform")
def switch(platform):
    """切换到指定平台"""
    if switch_platform(platform):
        click.echo(f"✅ 已切换到 {platform} 平台")
    else:
        click.echo(f"❌ 切换失败，请先使用 /setup 配置该平台")
        click.echo(f"   命令: /setup {platform} <API密钥>")

@cli.command()
@click.argument("model_name")
def test_model(model_name):
    """测试指定模型是否可用"""
    manager = get_model_manager()
    test_single_model(manager, model_name)

def list_all_platforms():
    """列出所有支持的平台"""
    platforms = list_platforms()

    click.echo("\n📦 支持的AI平台:")
    click.echo("=" * 60)

    for p in platforms:
        status = "✅ 已配置" if p.get("is_configured") else "⚪ 未配置"
        current = " ◀ 当前" if p.get("is_active") else ""

        click.echo(f"\n🏷️ {p['name']} ({p['id']}) {status}{current}")
        click.echo(f"   📝 {p['description']}")
        click.echo(f"   🔗 {p['website']}")
        click.echo(f"   ✨ 功能: {', '.join(p['features'])}")

    click.echo("\n" + "=" * 60)
    click.echo("💡 使用 /setup <平台> <API密钥> 配置新平台")
    click.echo("💡 使用 /switch <平台> 切换平台")

def setup_platform_cmd(platform, api_key, api_base=None):
    """配置平台"""
    click.echo(f"\n🔧 配置平台: {platform}")
    click.echo("=" * 60)

    kwargs = {}
    if api_base:
        kwargs["api_base"] = api_base

    success = setup_platform(platform, api_key, **kwargs)

    if success:
        click.echo("\n✅ 平台配置成功!")
        click.echo(f"   平台: {platform}")

        manager = get_model_manager()
        if manager.get_current_adapter():
            models = manager.get_current_adapter().get_recommended_models()[:5]
            click.echo(f"   推荐模型: {', '.join(models)}")
    else:
        click.echo(f"\n❌ 平台配置失败")
        click.echo(f"   可用平台: dashscope, openai, anthropic, gemini, azure")

    click.echo("\n" + "=" * 60)

def list_platform_models(manager, platform=None):
    """列出平台模型"""
    click.echo("\n📦 可用模型列表:")
    click.echo("=" * 60)

    try:
        if platform and platform != manager.get_current_platform():
            models = manager.get_platform_models(platform)
        else:
            models = manager.list_models()

        if models:
            click.echo(f"\n从API获取到 {len(models)} 个模型:\n")

            for i, m in enumerate(models[:20], 1):
                click.echo(f"{i:2d}. {m.name}")
                click.echo(f"    📝 {m.description[:80]}...")
                click.echo(f"    🏷️  {m.display_name}")
                click.echo()

            if len(models) > 20:
                click.echo(f"... 还有 {len(models) - 20} 个模型 (使用 /search <关键词> 搜索)")
        else:
            click.echo("⚠️ 获取模型列表失败或平台未配置")

    except Exception as e:
        click.echo(f"❌ 获取模型列表失败: {e}")

    click.echo("\n" + "=" * 60)
    click.echo("💡 使用 '/set-model <模型名>' 切换模型")

def test_single_model(manager, model_name):
    """测试单个模型"""
    click.echo(f"\n🔍 测试模型: {model_name}")
    click.echo("=" * 60)

    click.echo("\n⏳ 正在测试...")

    result = manager.test_model(model_name)

    if result.get("success"):
        click.echo("\n✅ 模型可用!")
        click.echo(f"   平台: {result.get('platform', 'unknown')}")
        click.echo(f"   响应: {result.get('response')}")
        click.echo(f"   耗时: {result.get('duration_ms')}ms")
    else:
        click.echo(f"\n❌ 模型不可用")
        click.echo(f"   错误: {result.get('error')}")
        if "error_detail" in result:
            click.echo(f"   详情: {result.get('error_detail')}")

    click.echo("\n" + "=" * 60)

def set_model(manager, new_model, config_dict):
    """设置当前模型"""
    click.echo(f"\n🔄 切换到模型: {new_model}")
    click.echo("=" * 60)

    click.echo("\n⏳ 正在验证模型...")

    result = manager.test_model(new_model)

    if result.get("success"):
        manager.set_model(new_model)
        config_dict["agent_model"] = new_model

        click.echo("\n✅ 模型切换成功!")
        click.echo(f"   模型: {new_model}")
        click.echo(f"   响应: {result.get('response')}")
        click.echo(f"   耗时: {result.get('duration_ms')}ms")
        return True
    else:
        click.echo(f"\n❌ 模型切换失败")
        click.echo(f"   错误: {result.get('error')}")
        if "error_detail" in result:
            click.echo(f"   详情: {result.get('error_detail')}")
        return False

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
