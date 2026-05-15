"""
DataAgent - LLM 调用服务
提供 Python 代码执行、LLM 模型调用、JSON 解析和连接测试功能
所有 LLM 相关调用统一通过此模块
"""

import asyncio
import json
import re
import sys
import os
import tempfile
import base64
import traceback

from config import OPENAI_AVAILABLE


def _create_openai_client(settings):
    """创建 AsyncOpenAI 客户端的辅助函数"""
    from openai import AsyncOpenAI
    return AsyncOpenAI(
        api_key=settings.llm["api_key"],
        base_url=settings.llm["base_url"]
    )


async def execute_python(code: str, timeout: int = 30) -> dict:
    """在沙箱中执行 Python 代码，支持图表生成"""
    sandbox_dir = tempfile.mkdtemp(prefix="dataagent_")
    images = []

    try:
        preamble = f"""
import sys
import os
sys.path.insert(0, '{os.path.dirname(os.path.abspath(__file__))}')

try:
    import numpy as np
except ImportError:
    np = None

try:
    import pandas as pd
except ImportError:
    pd = None

try:
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    plt.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans']
    plt.rcParams['axes.unicode_minus'] = False
except ImportError:
    plt = None

try:
    import seaborn as sns
except ImportError:
    sns = None

try:
    import plotly
    import plotly.graph_objects as go
except ImportError:
    plotly = None

SANDBOX_DIR = '{sandbox_dir}'
os.chdir(SANDBOX_DIR)

def save_plot(filename='chart.png', dpi=150):
    if plt:
        plt.savefig(filename, dpi=dpi, bbox_inches='tight')
        return os.path.join(SANDBOX_DIR, filename)
    return None

def show_plot(title=None, filename=None):
    if plt:
        if title:
            plt.title(title)
        if not filename:
            filename = f'chart_{len(os.listdir(SANDBOX_DIR))}.png'
        plt.savefig(filename, dpi=150, bbox_inches='tight')
        print(f'[CHART] {os.path.join(SANDBOX_DIR, filename)}')
        plt.close()
        return filename
    return None

def pp(obj):
    import pprint
    pprint.pprint(obj)

"""

        full_code = preamble + "\n" + code

        proc = await asyncio.create_subprocess_exec(
            sys.executable, "-c", full_code,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=sandbox_dir,
            env={**os.environ, "MPLBACKEND": "Agg", "PYTHONIOENCODING": "utf-8"},
        )
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)

        stdout_str = stdout.decode('utf-8', errors='replace')
        stderr_str = stderr.decode('utf-8', errors='replace')

        for filename in os.listdir(sandbox_dir):
            if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
                filepath = os.path.join(sandbox_dir, filename)
                try:
                    with open(filepath, 'rb') as f:
                        image_base64 = base64.b64encode(f.read()).decode('utf-8')
                        images.append({
                            'filename': filename,
                            'base64': image_base64,
                            'format': filename.split('.')[-1].upper()
                        })
                except Exception:
                    pass

        return {
            "success": True,
            "stdout": stdout_str,
            "stderr": stderr_str,
            "returncode": proc.returncode,
            "images": images,
            "sandbox_dir": sandbox_dir
        }
    except asyncio.TimeoutError:
        return {"success": False, "error": "执行超时"}
    except Exception as e:
        return {"success": False, "error": str(e), "traceback": traceback.format_exc()}


async def call_llm(prompt: str, settings) -> str:
    """调用 LLM 模型（仅 user 消息）"""
    if not OPENAI_AVAILABLE:
        return "错误: 未安装 openai 库，请运行 pip install openai"
    if not settings.llm.get("api_key"):
        return "请先在设置中配置 API Key"
    try:
        client = _create_openai_client(settings)
        response = await client.chat.completions.create(
            model=settings.llm["model"],
            messages=[{"role": "user", "content": prompt}],
            max_tokens=settings.llm["max_tokens"],
            temperature=settings.llm["temperature"],
            top_p=settings.llm["top_p"]
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"LLM调用失败: {str(e)}"


async def call_llm_with_system(system_prompt: str, user_prompt: str, settings) -> str:
    """调用 LLM 模型（带 system 消息）"""
    if not OPENAI_AVAILABLE:
        return "错误: 未安装 openai 库，请运行 pip install openai"
    if not settings.llm.get("api_key"):
        return "请先在设置中配置 API Key"
    try:
        client = _create_openai_client(settings)
        response = await client.chat.completions.create(
            model=settings.llm["model"],
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            max_tokens=settings.llm["max_tokens"],
            temperature=settings.llm["temperature"],
            top_p=settings.llm["top_p"]
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"LLM调用失败: {str(e)}"


async def call_llm_json(prompt: str, settings, pattern: str = r'\{.*\}|\[.*\]', temperature: float = None) -> dict:
    """调用 LLM 并解析 JSON 响应，用于 skills/agent/nl2sql 等路由"""
    if not OPENAI_AVAILABLE:
        return {"error": "未安装 openai 库，请运行 pip install openai"}
    if not settings.llm.get("api_key"):
        return {"error": "请先在设置中配置 API Key"}
    try:
        client = _create_openai_client(settings)
        response = await client.chat.completions.create(
            model=settings.llm["model"],
            messages=[{"role": "user", "content": prompt}],
            max_tokens=settings.llm.get("max_tokens", 1000),
            temperature=temperature if temperature is not None else settings.llm.get("temperature", 0.3)
        )
        result_text = response.choices[0].message.content.strip()
        # 尝试从响应中提取 JSON
        json_match = re.search(pattern, result_text, re.DOTALL)
        if json_match:
            return json.loads(json_match.group())
        return {"error": "AI返回格式无法解析", "raw": result_text}
    except json.JSONDecodeError as e:
        return {"error": f"JSON解析失败: {str(e)}"}
    except Exception as e:
        return {"error": f"LLM调用失败: {str(e)}"}


async def test_connection(api_key: str, base_url: str = "https://api.openai.com/v1", model: str = "gpt-4o", provider: str = "openai") -> dict:
    """测试 LLM 连接是否正常，提供详细的成功/失败反馈"""
    if not api_key:
        return {
            "success": False,
            "message": "API Key 不能为空",
            "error_type": "missing_api_key",
            "details": "请先配置 API Key"
        }

    if not OPENAI_AVAILABLE:
        return {
            "success": False,
            "message": "未安装 openai 库",
            "error_type": "missing_dependency",
            "details": "请运行: pip install openai"
        }

    try:
        from openai import AsyncOpenAI
        client = AsyncOpenAI(api_key=api_key, base_url=base_url)

        response = await client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": "Hello"}],
            max_tokens=10
        )

        return {
            "success": True,
            "message": f"连接成功！模型 {model} 可用",
            "model": model,
            "provider": provider,
            "response_id": response.id if hasattr(response, 'id') else None,
            "usage": response.usage.model_dump() if hasattr(response, 'usage') and response.usage else None
        }

    except Exception as e:
        error_str = str(e)
        error_type = "unknown_error"
        details = "请检查 API Key、模型名称和网络连接"

        if "401" in error_str or "Incorrect API key" in error_str or "invalid_api_key" in error_str.lower():
            error_type = "invalid_api_key"
            details = "API Key 无效或已过期，请检查或重新获取"
        elif "403" in error_str or "Forbidden" in error_str:
            error_type = "forbidden"
            details = "API Key 权限不足，可能需要充值或升级账户"
        elif "404" in error_str or "does not exist" in error_str or "model_not_found" in error_str.lower():
            error_type = "model_not_found"
            details = f"模型 {model} 不存在，请检查模型名称是否正确"
        elif "429" in error_str or "rate_limit" in error_str.lower() or "quota" in error_str.lower():
            error_type = "rate_limit"
            details = "请求频率超限或账户额度不足"
            balance_info = await _check_balance(api_key, base_url, provider)
            if balance_info:
                details += f"。{balance_info}"
        elif "insufficient_quota" in error_str.lower() or "balance" in error_str.lower():
            error_type = "insufficient_quota"
            details = "账户余额不足，请充值后再试"
            balance_info = await _check_balance(api_key, base_url, provider)
            if balance_info:
                details = balance_info
        elif "timeout" in error_str.lower():
            error_type = "timeout"
            details = "请求超时，请检查网络连接或稍后重试"
        elif "connection" in error_str.lower():
            error_type = "connection_error"
            details = "无法连接到服务器，请检查网络和 base_url 配置"
        elif "authentication" in error_str.lower():
            error_type = "authentication_error"
            details = "认证失败，请确认 API Key 正确"

        return {
            "success": False,
            "message": f"连接失败: {error_str[:100]}",
            "error_type": error_type,
            "details": details,
            "model": model,
            "provider": provider
        }


async def _check_balance(api_key: str, base_url: str, provider: str) -> str:
    """检查账户余额信息"""
    try:
        if provider == "openai":
            from openai import AsyncOpenAI
            client = AsyncOpenAI(api_key=api_key)
            balance = await client.balances.get()
            available = balance.data[0].available if balance.data else "未知"
            return f"账户余额: {available}"
        elif provider == "anthropic":
            return "请访问 https://console.anthropic.com/settings/credits 查看余额"
        elif provider == "azure":
            return "请访问 Azure 门户查看账户余额"
        elif provider in ["qwen", "tongyi", "aliyun"]:
            return "请访问阿里云控制台查看账户余额"
        elif provider == "deepseek":
            return "请访问 https://platform.deepseek.com/balance 查看余额"
        else:
            return f"请访问 {provider} 官网查看账户余额"
    except Exception:
        return None


async def list_available_models(api_key: str, base_url: str, provider: str) -> dict:
    """列出提供商所有可用的模型"""
    if not api_key:
        return {
            "success": False,
            "message": "API Key 不能为空"
        }

    if not OPENAI_AVAILABLE:
        return {
            "success": False,
            "message": "未安装 openai 库"
        }

    try:
        from openai import AsyncOpenAI
        client = AsyncOpenAI(api_key=api_key, base_url=base_url)
        models = await client.models.list()

        model_list = []
        for model in models.data:
            model_list.append({
                "id": model.id,
                "created": getattr(model, 'created', None),
                "object": getattr(model, 'object', None)
            })

        return {
            "success": True,
            "models": model_list,
            "count": len(model_list)
        }

    except Exception as e:
        return {
            "success": False,
            "message": f"获取模型列表失败: {str(e)}",
            "error_type": type(e).__name__
        }


async def verify_model_exists(api_key: str, base_url: str, model: str, provider: str) -> dict:
    """验证指定模型是否存在且可用"""
    if not api_key:
        return {
            "success": False,
            "model_exists": False,
            "message": "API Key 不能为空"
        }

    try:
        result = await test_connection(api_key, base_url, model, provider)

        if result["success"]:
            return {
                "success": True,
                "model_exists": True,
                "model": model,
                "message": f"模型 {model} 可用"
            }
        else:
            return {
                "success": result["success"],
                "model_exists": result["error_type"] != "model_not_found",
                "model": model,
                "message": result["message"],
                "error_type": result.get("error_type"),
                "details": result.get("details")
            }
    except Exception as e:
        return {
            "success": False,
            "model_exists": False,
            "model": model,
            "message": f"验证失败: {str(e)}"
        }


async def get_account_info(api_key: str, base_url: str, provider: str) -> dict:
    """获取账户信息，包括购买渠道"""
    if not api_key:
        return {
            "success": False,
            "message": "API Key 不能为空"
        }

    account_info = {
        "provider": provider,
        "source": _get_provider_source(provider),
        "dashboard_url": _get_provider_dashboard_url(provider),
        "support_url": _get_provider_support_url(provider)
    }

    if provider == "openai":
        try:
            from openai import AsyncOpenAI
            client = AsyncOpenAI(api_key=api_key)
            balance = await client.balances.get()
            if balance.data:
                account_info.update({
                    "balance": balance.data[0].available,
                    "currency": balance.data[0].currency,
                    "total_granted": balance.data[0].total_granted,
                    "total_used": balance.data[0].total_used,
                    "success": True
                })
            return account_info
        except Exception:
            pass

    account_info.update({
        "success": True,
        "message": "请访问对应的控制台查看账户详情"
    })
    return account_info


def _get_provider_source(provider: str) -> str:
    """获取模型提供商来源"""
    sources = {
        "openai": "OpenAI 官方网站 (https://platform.openai.com)",
        "anthropic": "Anthropic 官方网站 (https://www.anthropic.com)",
        "google": "Google AI Studio (https://aistudio.google.com)",
        "azure": "Microsoft Azure (https://azure.microsoft.com)",
        "ollama": "Ollama 本地部署 (https://ollama.com)",
        "qwen": "阿里云通义千问 (https://dashscope.console.aliyun.com)",
        "tongyi": "阿里云通义千问 (https://dashscope.console.aliyun.com)",
        "aliyun": "阿里云 (https://www.aliyun.com)",
        "deepseek": "DeepSeek 官方网站 (https://platform.deepseek.com)",
        "zhipu": "智谱AI (https://open.bigmodel.cn)",
        "minimax": "MiniMax (https://www.minimax.io)",
        "moonshot": "月之暗面 Moonshot (https://platform.moonshot.cn)",
        "spark": "科大讯飞星火 (https://xinghuo.xfyun.cn)"
    }
    return sources.get(provider, f"{provider} 官方网站")


def _get_provider_dashboard_url(provider: str) -> str:
    """获取提供商控制台URL"""
    urls = {
        "openai": "https://platform.openai.com/api-keys",
        "anthropic": "https://console.anthropic.com/settings/keys",
        "google": "https://aistudio.google.com/app/apikey",
        "azure": "https://portal.azure.com/#blade/HubsExtension/BrowseResource/resourceType/Microsoft.CognitiveServices%2Faccounts",
        "ollama": "http://localhost:11434",
        "qwen": "https://dashscope.console.aliyun.com/apiKey",
        "tongyi": "https://dashscope.console.aliyun.com/apiKey",
        "aliyun": "https://console.aliyun.com",
        "deepseek": "https://platform.deepseek.com/api_keys",
        "zhipu": "https://open.bigmodel.cn/usercenter/apikeys",
        "minimax": "https://www.minimax.io/user-center/basic-information/interface-key",
        "moonshot": "https://platform.moonshot.cn/console/api-keys",
        "spark": "https://xinghuo.xfyun.cn/home/dashboard"
    }
    return urls.get(provider, "")


def _get_provider_support_url(provider: str) -> str:
    """获取提供商支持页面URL"""
    urls = {
        "openai": "https://help.openai.com",
        "anthropic": "https://support.anthropic.com",
        "google": "https://ai.google.dev/support",
        "azure": "https://azure.microsoft.com/support",
        "ollama": "https://github.com/ollama/ollama",
        "qwen": "https://help.aliyun.com",
        "tongyi": "https://help.aliyun.com",
        "aliyun": "https://help.aliyun.com",
        "deepseek": "https://platform.deepseek.com/docs",
        "zhipu": "https://open.bigmodel.cn/doc",
        "minimax": "https://www.minimax.io/user-center",
        "moonshot": "https://platform.moonshot.cn/docs",
        "spark": "https://xinghuo.xfyun.cn/doc"
    }
    return urls.get(provider, "")


async def call_llm_with_retry(prompt: str, settings, max_retries: int = 3, base_delay: float = 1.0) -> str:
    """带重试的 LLM 调用"""
    last_error = None

    for attempt in range(max_retries):
        try:
            result = await call_llm(prompt, settings)

            # 检查是否返回了错误信息
            if result.startswith("错误:") or result.startswith("LLM调用失败:"):
                last_error = result
                if attempt < max_retries - 1:
                    delay = base_delay * (2 ** attempt)
                    print(f"[RETRY] LLM call failed (attempt {attempt+1}/{max_retries}), retrying in {delay}s: {result[:100]}")
                    await asyncio.sleep(delay)
                    continue

            return result

        except Exception as e:
            last_error = str(e)
            if attempt < max_retries - 1:
                delay = base_delay * (2 ** attempt)
                print(f"[RETRY] LLM call error (attempt {attempt+1}/{max_retries}), retrying in {delay}s: {last_error[:100]}")
                await asyncio.sleep(delay)
                continue

    return f"LLM调用失败（已重试{max_retries}次）: {last_error}"
