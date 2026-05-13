"""DataAgent Web Interface - Simplified Testing Version"""

from fastapi import FastAPI, WebSocket, Request
from fastapi.responses import HTMLResponse, JSONResponse
import asyncio
import json
import tempfile
import os
import sys
from typing import Dict
from pathlib import Path

try:
    from openai import AsyncOpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

app = FastAPI(title="Data Agent", description="DataAgent Universal AI Assistant")

CONFIG_PATH = Path(__file__).parent / "config" / "web_config.json"

def load_settings():
    if CONFIG_PATH.exists():
        try:
            with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            pass
    return get_default_settings()

def save_settings(settings):
    CONFIG_PATH.parent.mkdir(exist_ok=True)
    with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
        json.dump(settings, f, ensure_ascii=False, indent=2)

def get_default_settings():
    return {
        "llm": {
            "provider": "aliyun",
            "model": "qwen-plus-latest",
            "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
            "api_key": "",
            "max_tokens": 4096,
            "temperature": 0.7,
            "top_p": 0.9,
            "stream": False
        },
        "sandbox": {
            "enabled": True,
            "timeout": 60,
            "allow_network": False
        },
        "conversation": {
            "history_enabled": True,
            "max_history": 50
        },
        "agent": {
            "max_steps": 5,
            "auto_mode": True
        }
    }

current_settings = load_settings()

async def execute_python(code: str, timeout: int = 30) -> dict:
    try:
        proc = await asyncio.create_subprocess_exec(
            sys.executable, "-c", code,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=str(Path(tempfile.mkdtemp(prefix="dataagent_"))),
            env={**os.environ, "MPLBACKEND": "Agg", "PYTHONIOENCODING": "utf-8"},
        )
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
        return {
            "success": True,
            "stdout": stdout.decode('utf-8', errors='replace'),
            "stderr": stderr.decode('utf-8', errors='replace'),
            "returncode": proc.returncode
        }
    except asyncio.TimeoutError:
        return {"success": False, "error": "执行超时"}
    except Exception as e:
        return {"success": False, "error": str(e)}

async def call_llm(prompt: str, settings: dict):
    if not OPENAI_AVAILABLE:
        return "错误: 未安装 openai 库"
    
    try:
        client = AsyncOpenAI(
            api_key=settings["llm"]["api_key"],
            base_url=settings["llm"]["base_url"]
        )
        
        response = await client.chat.completions.create(
            model=settings["llm"]["model"],
            messages=[{"role": "user", "content": prompt}],
            max_tokens=settings["llm"]["max_tokens"],
            temperature=settings["llm"]["temperature"],
            top_p=settings["llm"]["top_p"]
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"LLM调用失败: {str(e)}"

async def run_universal_agent(websocket, message):
    try:
        await websocket.send_json({
            "type": "thinking",
            "phase": "init",
            "title": "🤔 理解需求",
            "content": f"正在分析: {message[:100]}..."
        })

        settings = current_settings
        
        if "python" in message.lower() or "代码" in message.lower() or "图表" in message.lower() or "matplotlib" in message.lower() or "plot" in message.lower():
            await websocket.send_json({
                "type": "thinking",
                "phase": "tool_select",
                "title": "🛠️ 代码执行",
                "content": "检测到代码需求，准备执行Python代码"
            })
            
            code_prompt = f"""根据用户需求生成Python代码：
用户需求：{message}

请直接输出可执行的Python代码，不需要解释，代码中如果需要生成图像，请保存为PNG文件。"""
            
            code = await call_llm(code_prompt, settings)
            
            import re
            code = re.sub(r'^```python\s*\n?', '', code.strip(), flags=re.MULTILINE)
            code = re.sub(r'\n?```$', '', code.strip(), flags=re.MULTILINE)
            code = code.strip()
            
            await websocket.send_json({
                "type": "thinking",
                "phase": "tool_result",
                "title": "📋 生成代码",
                "content": f"```python\n{code}\n```"
            })
            
            result = await execute_python(code, timeout=settings["sandbox"]["timeout"])
            
            if result["success"]:
                response = f"✅ 执行成功!\n\n**标准输出:**\n{result['stdout']}\n\n**代码:**\n```python\n{code}\n```"
                if result["stderr"]:
                    response += f"\n\n**警告:**\n{result['stderr']}"
            else:
                response = f"❌ 执行失败: {result['error']}\n\n**代码:**\n```python\n{code}\n```"
        else:
            await websocket.send_json({
                "type": "thinking",
                "phase": "analyze",
                "title": "🧠 智能分析",
                "content": "直接进行对话响应"
            })
            
            response = await call_llm(message, settings)

        await websocket.send_json({"type": "response", "content": response})
        
    except Exception as e:
        await websocket.send_json({"type": "error", "content": f"❌ 处理失败: {str(e)[:300]}"})
        import traceback
        traceback.print_exc()

@app.get("/api/settings")
async def get_settings_endpoint():
    return JSONResponse(current_settings)

@app.post("/api/settings")
async def update_settings_endpoint(request: Request):
    global current_settings
    new_settings = await request.json()
    current_settings = new_settings
    save_settings(current_settings)
    return JSONResponse({"success": True, "settings": current_settings})

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_json()
            message = data.get("content", "")
            await run_universal_agent(websocket, message)
    except Exception:
        pass

@app.get("/")
async def get():
    html_content = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Data Agent - 万能智能助手</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: linear-gradient(135deg, #0F172A 0%, #1E293B 100%); min-height: 100vh; }
        .app-container { display: flex; height: 100vh; }
        .sidebar { width: 260px; background: rgba(30, 41, 59, 0.8); backdrop-filter: blur(10px); border-right: 1px solid rgba(255,255,255,0.1); display: flex; flex-direction: column; }
        .sidebar-header { padding: 20px; border-bottom: 1px solid rgba(255,255,255,0.1); }
        .sidebar-header h2 { color: #fff; font-size: 18px; display: flex; align-items: center; gap: 10px; }
        .sidebar-nav { flex: 1; padding: 10px; }
        .nav-item { display: flex; align-items: center; gap: 12px; padding: 12px 16px; color: #94A3B8; border-radius: 8px; cursor: pointer; transition: all 0.2s; margin-bottom: 4px; }
        .nav-item:hover { background: rgba(255,255,255,0.05); color: #fff; }
        .nav-item.active { background: rgba(59, 130, 246, 0.2); color: #3B82F6; }
        .nav-icon { font-size: 18px; }
        .nav-text h4 { font-size: 14px; font-weight: 500; }
        .nav-text p { font-size: 12px; opacity: 0.6; }
        .nav-divider { height: 1px; background: rgba(255,255,255,0.1); margin: 12px 0; }
        .main-content { flex: 1; display: flex; flex-direction: column; }
        .header { padding: 16px 24px; background: rgba(30, 41, 59, 0.5); border-bottom: 1px solid rgba(255,255,255,0.1); display: flex; justify-content: space-between; align-items: center; }
        .header h1 { color: #fff; font-size: 20px; }
        .new-chat-btn { padding: 8px 16px; background: #3B82F6; color: white; border: none; border-radius: 6px; cursor: pointer; font-size: 14px; }
        .chat-area { flex: 1; overflow-y: auto; padding: 20px; }
        .message { max-width: 80%; margin-bottom: 20px; }
        .message.user { margin-left: auto; }
        .message.assistant { margin-right: auto; }
        .message.system { text-align: center; margin: 10px auto; max-width: 60%; }
        .message-content { padding: 12px 16px; border-radius: 16px; }
        .user .message-content { background: #3B82F6; color: white; border-bottom-right-radius: 4px; }
        .assistant .message-content { background: rgba(71, 85, 105, 0.5); color: #E2E8F0; border-bottom-left-radius: 4px; }
        .system .message-content { background: rgba(148, 163, 184, 0.2); color: #94A3B8; font-size: 12px; padding: 8px 12px; border-radius: 8px; }
        .thinking-container { background: rgba(71, 85, 105, 0.3); border-radius: 12px; padding: 16px; margin-bottom: 16px; }
        .thinking-phase { display: flex; align-items: center; gap: 12px; margin-bottom: 8px; }
        .thinking-dot { width: 8px; height: 8px; background: #3B82F6; border-radius: 50%; animation: pulse 1s infinite; }
        .thinking-title { color: #3B82F6; font-weight: 500; }
        .thinking-content { color: #94A3B8; font-size: 14px; padding-left: 20px; }
        .thinking-tools { margin-top: 8px; padding-left: 20px; }
        .tool-tag { display: inline-block; background: rgba(59, 130, 246, 0.2); color: #60A5FA; padding: 4px 8px; border-radius: 4px; font-size: 12px; margin-right: 6px; }
        @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.5; } }
        .input-area { padding: 16px 24px; background: rgba(30, 41, 59, 0.5); border-top: 1px solid rgba(255,255,255,0.1); }
        .input-container { display: flex; gap: 12px; }
        .input-box { flex: 1; padding: 14px 18px; background: rgba(71, 85, 105, 0.5); border: 1px solid rgba(255,255,255,0.1); border-radius: 12px; color: #fff; font-size: 14px; outline: none; resize: none; }
        .input-box:focus { border-color: #3B82F6; }
        .send-btn { padding: 14px 24px; background: #3B82F6; color: white; border: none; border-radius: 12px; cursor: pointer; font-size: 14px; }
        .send-btn:hover { background: #2563EB; }
        .modal-overlay { display: none; position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: rgba(0,0,0,0.7); z-index: 1000; }
        .modal-overlay.show { display: flex; align-items: center; justify-content: center; }
        .modal { background: #1E293B; border-radius: 16px; width: 90%; max-width: 800px; max-height: 80vh; overflow-y: auto; }
        .modal-header { padding: 20px; border-bottom: 1px solid rgba(255,255,255,0.1); display: flex; justify-content: space-between; align-items: center; }
        .modal-title { color: #fff; font-size: 18px; }
        .modal-close { background: none; border: none; color: #94A3B8; font-size: 24px; cursor: pointer; }
        .modal-body { padding: 20px; }
        .settings-section { margin-bottom: 24px; }
        .settings-section h3 { color: #fff; font-size: 16px; margin-bottom: 16px; }
        .setting-row { display: flex; align-items: center; gap: 16px; margin-bottom: 16px; }
        .setting-label { width: 140px; color: #94A3B8; font-size: 14px; }
        .setting-input { flex: 1; padding: 10px 14px; background: rgba(71, 85, 105, 0.5); border: 1px solid rgba(255,255,255,0.1); border-radius: 8px; color: #fff; font-size: 14px; }
        .setting-input:focus { border-color: #3B82F6; outline: none; }
        .setting-select { flex: 1; padding: 10px 14px; background: rgba(71, 85, 105, 0.5); border: 1px solid rgba(255,255,255,0.1); border-radius: 8px; color: #fff; font-size: 14px; }
        .setting-switch { width: 48px; height: 26px; background: rgba(71, 85, 105, 0.5); border-radius: 13px; position: relative; cursor: pointer; }
        .setting-switch.on { background: #3B82F6; }
        .setting-switch::after { content: ''; position: absolute; top: 3px; left: 3px; width: 20px; height: 20px; background: #fff; border-radius: 50%; transition: left 0.2s; }
        .setting-switch.on::after { left: 25px; }
        .modal-actions { padding: 20px; border-top: 1px solid rgba(255,255,255,0.1); display: flex; justify-content: flex-end; gap: 12px; }
        .btn { padding: 10px 20px; border-radius: 8px; font-size: 14px; cursor: pointer; }
        .btn-primary { background: #3B82F6; color: white; border: none; }
        .btn-secondary { background: rgba(71, 85, 105, 0.5); color: #94A3B8; border: none; }
        .help-content { color: #94A3B8; line-height: 1.8; }
        .help-content h4 { color: #fff; margin-top: 20px; margin-bottom: 10px; }
        .help-content ul { padding-left: 20px; }
        .help-content li { margin-bottom: 8px; }
        pre { background: rgba(71, 85, 105, 0.3); padding: 12px; border-radius: 8px; overflow-x: auto; }
        code { color: #FBBF24; font-size: 13px; }
        .knowledge-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 16px; }
        .knowledge-card { background: rgba(71, 85, 105, 0.3); border-radius: 12px; padding: 16px; cursor: pointer; transition: background 0.2s; }
        .knowledge-card:hover { background: rgba(71, 85, 105, 0.5); }
        .knowledge-card h4 { color: #fff; margin-bottom: 8px; }
        .knowledge-card p { color: #94A3B8; font-size: 13px; }
        .prompt-list { display: flex; flex-direction: column; gap: 12px; }
        .prompt-item { background: rgba(71, 85, 105, 0.3); border-radius: 12px; padding: 16px; }
        .prompt-item h4 { color: #fff; margin-bottom: 8px; }
        .prompt-item p { color: #94A3B8; font-size: 13px; margin-bottom: 8px; }
        .prompt-apply { padding: 6px 12px; background: rgba(59, 130, 246, 0.2); color: #60A5FA; border: none; border-radius: 4px; font-size: 12px; cursor: pointer; }
        .skill-list { display: grid; grid-template-columns: repeat(auto-fill, minmax(180px, 1fr)); gap: 16px; }
        .skill-card { background: rgba(71, 85, 105, 0.3); border-radius: 12px; padding: 16px; text-align: center; }
        .skill-card .icon { font-size: 32px; margin-bottom: 8px; }
        .skill-card h4 { color: #fff; margin-bottom: 4px; }
        .skill-card p { color: #94A3B8; font-size: 12px; }
        .mcp-list { display: flex; flex-direction: column; gap: 12px; }
        .mcp-item { background: rgba(71, 85, 105, 0.3); border-radius: 12px; padding: 16px; display: flex; justify-content: space-between; align-items: center; }
        .mcp-item .info h4 { color: #fff; margin-bottom: 4px; }
        .mcp-item .info p { color: #94A3B8; font-size: 13px; }
        .mcp-toggle { width: 48px; height: 26px; background: rgba(71, 85, 105, 0.5); border-radius: 13px; position: relative; cursor: pointer; }
        .mcp-toggle.on { background: #10B981; }
        .mcp-toggle::after { content: ''; position: absolute; top: 3px; left: 3px; width: 20px; height: 20px; background: #fff; border-radius: 50%; transition: left 0.2s; }
        .mcp-toggle.on::after { left: 25px; }
        .code-block { background: rgba(71, 85, 105, 0.3); padding: 12px; border-radius: 8px; overflow-x: auto; }
        .code-block pre { margin: 0; }
    </style>
</head>
<body>
    <div class="app-container">
        <div class="sidebar">
            <div class="sidebar-header">
                <h2>🤖 Data Agent</h2>
            </div>
            <div class="sidebar-nav">
                <div class="nav-item active" onclick="showMainChat()">
                    <span class="nav-icon">💬</span>
                    <div class="nav-text">
                        <h4>对话</h4>
                        <p>开始智能对话</p>
                    </div>
                </div>
                <div class="nav-divider"></div>
                <div class="nav-item" onclick="openModal('knowledge-modal')">📚 知识库</div>
                <div class="nav-item" onclick="openModal('prompt-modal')">💡 提示词市场</div>
                <div class="nav-item" onclick="openModal('skill-modal')">🛠️ Skill 市场</div>
                <div class="nav-item" onclick="openModal('mcp-modal')">🔌 MCP 工具服务</div>
                <div class="nav-divider"></div>
                <div class="nav-item" onclick="openModal('settings-modal')">⚙️ 设置</div>
                <div class="nav-item" onclick="openModal('help-modal')">❓ 使用说明</div>
            </div>
        </div>
        <div class="main-content">
            <div class="header">
                <h1>Data Agent</h1>
                <button class="new-chat-btn" onclick="clearChat()">✨ 新建对话</button>
            </div>
            <div class="chat-area" id="chat-area">
                <div class="message system">
                    <div class="message-content">欢迎使用 Data Agent！我是您的万能智能助手，支持代码执行、数据分析、图表生成等功能。</div>
                </div>
            </div>
            <div class="input-area">
                <div class="input-container">
                    <textarea class="input-box" id="input-box" placeholder="输入您的需求... (Enter 发送, Shift+Enter 换行)" rows="2"></textarea>
                    <button class="send-btn" onclick="sendMessage()">发送</button>
                </div>
            </div>
        </div>
    </div>

    <div class="modal-overlay" id="settings-modal">
        <div class="modal">
            <div class="modal-header">
                <div class="modal-title">⚙️ 设置</div>
                <button class="modal-close" onclick="closeModal('settings-modal')">×</button>
            </div>
            <div class="modal-body">
                <div class="settings-section">
                    <h3>🤖 模型配置</h3>
                    <div class="setting-row">
                        <span class="setting-label">模型提供商</span>
                        <select class="setting-select" id="setting-provider">
                            <optgroup label="🇨🇳 国内模型">
                                <option value="aliyun">阿里云 - 通义千问 (Qwen3.6/Qwen2.5)</option>
                                <option value="baidu">百度 - 文心一言 (ERNIE 5.0/4.0)</option>
                                <option value="doubao">字节跳动 - 豆包 (Doubao 5.0/1.5)</option>
                                <option value="tencent">腾讯 - 混元 (Hunyuan 3.0)</option>
                                <option value="deepseek">深度求索 - DeepSeek (V4/R1)</option>
                                <option value="zhipu">智谱AI - GLM (GLM-5/4)</option>
                                <option value="kimi">月之暗面 - Kimi (K2.6/K2)</option>
                            </optgroup>
                            <optgroup label="🌍 国际模型">
                                <option value="openai">OpenAI - GPT (GPT-5.5/5.4/4o)</option>
                                <option value="anthropic">Anthropic - Claude (Opus 4.7/Sonnet 4.7)</option>
                                <option value="google">Google - Gemini (Gemini 3.1/3.0)</option>
                                <option value="xai">xAI - Grok (Grok 4.2)</option>
                            </optgroup>
                        </select>
                    </div>
                    <div class="setting-row">
                        <span class="setting-label">模型名称</span>
                        <select class="setting-select" id="setting-model">
                            <option value="qwen-plus-latest">qwen-plus-latest (通义千问Plus)</option>
                            <option value="qwen-max">qwen-max (通义千问Max)</option>
                            <option value="qwen-turbo-latest">qwen-turbo-latest (通义千问Turbo)</option>
                        </select>
                    </div>
                    <div class="setting-row">
                        <span class="setting-label">API Base URL</span>
                        <input type="text" class="setting-input" id="setting-base-url" placeholder="https://...">
                    </div>
                    <div class="setting-row">
                        <span class="setting-label">API Key</span>
                        <input type="password" class="setting-input" id="setting-api-key" placeholder="sk-...">
                    </div>
                    <div class="setting-row">
                        <span class="setting-label">最大 Token</span>
                        <input type="number" class="setting-input" id="setting-max-tokens" value="4096">
                    </div>
                    <div class="setting-row">
                        <span class="setting-label">温度系数</span>
                        <input type="number" step="0.1" class="setting-input" id="setting-temperature" value="0.7">
                    </div>
                </div>
                <div class="settings-section">
                    <h3>🏖️ 沙箱环境</h3>
                    <div class="setting-row">
                        <span class="setting-label">启用沙箱</span>
                        <div class="setting-switch on" id="setting-sandbox-enabled" onclick="toggleSwitch(this)"></div>
                    </div>
                    <div class="setting-row">
                        <span class="setting-label">执行超时(秒)</span>
                        <input type="number" class="setting-input" id="setting-sandbox-timeout" value="60">
                    </div>
                </div>
                <div class="settings-section">
                    <h3>🤖 智能体配置</h3>
                    <div class="setting-row">
                        <span class="setting-label">最大步骤</span>
                        <input type="number" class="setting-input" id="setting-max-steps" value="5">
                    </div>
                </div>
            </div>
            <div class="modal-actions">
                <button class="btn btn-secondary" onclick="resetSettings()">重置默认</button>
                <button class="btn btn-primary" onclick="saveSettings()">保存设置</button>
            </div>
        </div>
    </div>

    <div class="modal-overlay" id="help-modal">
        <div class="modal">
            <div class="modal-header">
                <div class="modal-title">❓ 使用说明</div>
                <button class="modal-close" onclick="closeModal('help-modal')">×</button>
            </div>
            <div class="modal-body help-content">
                <h4>📖 关于 Data Agent</h4>
                <p>Data Agent 是一个万能智能助手，具备以下核心能力：</p>
                <ul>
                    <li><strong>智能对话</strong> - 支持自然语言对话，理解复杂需求</li>
                    <li><strong>代码执行</strong> - 自动生成并执行 Python 代码</li>
                    <li><strong>图表生成</strong> - 支持 matplotlib、plotly 图表生成</li>
                    <li><strong>数据分析</strong> - 处理 CSV、Excel 数据</li>
                    <li><strong>文档处理</strong> - 支持 Markdown、PDF 等格式</li>
                </ul>
                <h4>💡 使用示例</h4>
                <ul>
                    <li><strong>代码生成:</strong> <code>帮我写一个 Python 程序来计算斐波那契数列</code></li>
                    <li><strong>图表生成:</strong> <code>生成一个正弦函数的折线图</code></li>
                    <li><strong>数据分析:</strong> <code>分析这个数据：[1,2,3,4,5,6,7,8,9,10]，计算平均值和标准差</code></li>
                    <li><strong>日常对话:</strong> <code>今天天气怎么样？</code></li>
                </ul>
                <h4>⚙️ 设置说明</h4>
                <p>在设置中您可以配置：</p>
                <ul>
                    <li>模型提供商和具体模型</li>
                    <li>API Key 和访问地址</li>
                    <li>沙箱环境配置</li>
                    <li>智能体行为参数</li>
                </ul>
                <h4>🔗 知识库</h4>
                <p>知识库功能允许您上传文档，让智能助手基于文档内容进行回答。</p>
                <h4>💬 提示词市场</h4>
                <p>提供精选的提示词模板，帮助您更好地与 AI 交互。</p>
                <h4>🛠️ Skill 市场</h4>
                <p>扩展智能助手的能力，添加各种专业技能。</p>
                <h4>🔌 MCP 工具服务</h4>
                <p>管理和配置外部工具服务，扩展智能助手的功能边界。</p>
            </div>
        </div>
    </div>

    <div class="modal-overlay" id="knowledge-modal">
        <div class="modal">
            <div class="modal-header">
                <div class="modal-title">📚 知识库</div>
                <button class="modal-close" onclick="closeModal('knowledge-modal')">×</button>
            </div>
            <div class="modal-body">
                <div class="knowledge-grid">
                    <div class="knowledge-card">
                        <h4>📁 产品手册</h4>
                        <p>产品使用说明和功能介绍</p>
                    </div>
                    <div class="knowledge-card">
                        <h4>📁 API 文档</h4>
                        <p>接口说明和调用示例</p>
                    </div>
                    <div class="knowledge-card">
                        <h4>📁 技术白皮书</h4>
                        <p>技术架构和实现原理</p>
                    </div>
                    <div class="knowledge-card">
                        <h4>📁 常见问题</h4>
                        <p>FAQ 和故障排除</p>
                    </div>
                </div>
                <button class="btn btn-primary" style="margin-top: 16px; width: 100%;">📤 上传文档</button>
            </div>
        </div>
    </div>

    <div class="modal-overlay" id="prompt-modal">
        <div class="modal">
            <div class="modal-header">
                <div class="modal-title">💡 提示词市场</div>
                <button class="modal-close" onclick="closeModal('prompt-modal')">×</button>
            </div>
            <div class="modal-body">
                <div class="prompt-list">
                    <div class="prompt-item">
                        <h4>🎯 代码审查专家</h4>
                        <p>帮我审查这段代码，找出潜在的bug和性能问题...</p>
                        <button class="prompt-apply" onclick="applyPrompt('代码审查')">应用</button>
                    </div>
                    <div class="prompt-item">
                        <h4>📝 文案润色</h4>
                        <p>帮我优化这段文字，使其更加专业和流畅...</p>
                        <button class="prompt-apply" onclick="applyPrompt('文案润色')">应用</button>
                    </div>
                    <div class="prompt-item">
                        <h4>📊 数据分析助手</h4>
                        <p>帮我分析这份数据，提取关键洞察和趋势...</p>
                        <button class="prompt-apply" onclick="applyPrompt('数据分析')">应用</button>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <div class="modal-overlay" id="skill-modal">
        <div class="modal">
            <div class="modal-header">
                <div class="modal-title">🛠️ Skill 市场</div>
                <button class="modal-close" onclick="closeModal('skill-modal')">×</button>
            </div>
            <div class="modal-body">
                <div class="skill-list">
                    <div class="skill-card">
                        <div class="icon">📈</div>
                        <h4>数据分析</h4>
                        <p>数据处理和可视化</p>
                    </div>
                    <div class="skill-card">
                        <div class="icon">🤖</div>
                        <h4>代码生成</h4>
                        <p>自动代码编写</p>
                    </div>
                    <div class="skill-card">
                        <div class="icon">📊</div>
                        <h4>图表制作</h4>
                        <p>专业图表生成</p>
                    </div>
                    <div class="skill-card">
                        <div class="icon">📝</div>
                        <h4>文档处理</h4>
                        <p>文档分析和生成</p>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <div class="modal-overlay" id="mcp-modal">
        <div class="modal">
            <div class="modal-header">
                <div class="modal-title">🔌 MCP 工具服务</div>
                <button class="modal-close" onclick="closeModal('mcp-modal')">×</button>
            </div>
            <div class="modal-body">
                <div class="mcp-list">
                    <div class="mcp-item">
                        <div class="info">
                            <h4>🌐 Web 搜索</h4>
                            <p>实时网络搜索服务</p>
                        </div>
                        <div class="mcp-toggle on" onclick="toggleSwitch(this)"></div>
                    </div>
                    <div class="mcp-item">
                        <div class="info">
                            <h4>📁 文件操作</h4>
                            <p>文件读写和管理</p>
                        </div>
                        <div class="mcp-toggle on" onclick="toggleSwitch(this)"></div>
                    </div>
                    <div class="mcp-item">
                        <div class="info">
                            <h4>🧮 计算器</h4>
                            <p>数学计算服务</p>
                        </div>
                        <div class="mcp-toggle on" onclick="toggleSwitch(this)"></div>
                    </div>
                    <div class="mcp-item">
                        <div class="info">
                            <h4>🌤️ 天气查询</h4>
                            <p>实时天气信息</p>
                        </div>
                        <div class="mcp-toggle" onclick="toggleSwitch(this)"></div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script>
        let ws = null;
        let appSettings = {};

        function connectWS() {
            ws = new WebSocket('ws://' + window.location.host + '/ws');
            ws.onmessage = function(event) {
                const data = JSON.parse(event.data);
                handleWSMessage(data);
            };
            ws.onclose = function() {
                setTimeout(connectWS, 3000);
            };
        }

        function handleWSMessage(data) {
            const chatArea = document.getElementById('chat-area');
            if (data.type === 'thinking') {
                let thinkingEl = document.querySelector('.thinking-container');
                if (!thinkingEl) {
                    thinkingEl = document.createElement('div');
                    thinkingEl.className = 'thinking-container';
                    chatArea.appendChild(thinkingEl);
                }
                thinkingEl.innerHTML = `
                    <div class="thinking-phase">
                        <div class="thinking-dot"></div>
                        <div class="thinking-title">${data.title}</div>
                    </div>
                    <div class="thinking-content">${data.content}</div>
                    ${data.tools ? '<div class="thinking-tools">' + data.tools.map(t => `<span class="tool-tag">${t.name}</span>`).join('') + '</div>' : ''}
                `;
            } else if (data.type === 'response') {
                document.querySelector('.thinking-container')?.remove();
                addMessage(data.content, 'assistant');
                finishProcessing();
            } else if (data.type === 'error') {
                document.querySelector('.thinking-container')?.remove();
                addMessage(data.content, 'system');
                finishProcessing();
            }
        }

        function addMessage(content, type) {
            const chatArea = document.getElementById('chat-area');
            const messageEl = document.createElement('div');
            messageEl.className = `message ${type}`;
            messageEl.innerHTML = `<div class="message-content">${formatMessage(content)}</div>`;
            chatArea.appendChild(messageEl);
            chatArea.scrollTop = chatArea.scrollHeight;
        }

        function formatMessage(content) {
            return content
                .replace(/```(\w+)?\n([\s\S]*?)```/g, '<pre><code>$2</code></pre>')
                .replace(/`([^`]+)`/g, '<code>$1</code>')
                .replace(/\n/g, '<br>');
        }

        function sendMessage() {
            const inputBox = document.getElementById('input-box');
            const content = inputBox.value.trim();
            if (!content || !ws) return;
            
            inputBox.value = '';
            addMessage(content, 'user');
            
            const thinkingEl = document.createElement('div');
            thinkingEl.className = 'thinking-container';
            thinkingEl.innerHTML = '<div class="thinking-phase"><div class="thinking-dot"></div><div class="thinking-title">🤔 思考中...</div></div>';
            document.getElementById('chat-area').appendChild(thinkingEl);
            
            ws.send(JSON.stringify({ content: content }));
        }

        function finishProcessing() {
            document.getElementById('chat-area').scrollTop = document.getElementById('chat-area').scrollHeight;
        }

        function clearChat() {
            const chatArea = document.getElementById('chat-area');
            chatArea.innerHTML = '<div class="message system"><div class="message-content">欢迎使用 Data Agent！我是您的万能智能助手，支持代码执行、数据分析、图表生成等功能。</div></div>';
        }

        function openModal(modalId) {
            document.getElementById(modalId).classList.add('show');
        }

        function closeModal(modalId) {
            document.getElementById(modalId).classList.remove('show');
        }

        function toggleSwitch(el) {
            el.classList.toggle('on');
        }

        async function loadSettings() {
            try {
                const response = await fetch('/api/settings');
                appSettings = await response.json();
                populateSettings(appSettings);
            } catch(e) {
                console.log('使用默认设置');
            }
        }

        function populateSettings(settings) {
            document.getElementById('setting-provider').value = settings.llm.provider || 'aliyun';
            document.getElementById('setting-model').value = settings.llm.model;
            document.getElementById('setting-base-url').value = settings.llm.base_url;
            document.getElementById('setting-api-key').value = settings.llm.api_key;
            document.getElementById('setting-max-tokens').value = settings.llm.max_tokens;
            document.getElementById('setting-temperature').value = settings.llm.temperature;
            document.getElementById('setting-sandbox-enabled').classList.toggle('on', settings.sandbox.enabled);
            document.getElementById('setting-sandbox-timeout').value = settings.sandbox.timeout;
            document.getElementById('setting-max-steps').value = settings.agent.max_steps;
        }

        async function saveSettings() {
            const newSettings = {
                llm: {
                    provider: document.getElementById('setting-provider').value,
                    model: document.getElementById('setting-model').value,
                    base_url: document.getElementById('setting-base-url').value,
                    api_key: document.getElementById('setting-api-key').value,
                    max_tokens: parseInt(document.getElementById('setting-max-tokens').value),
                    temperature: parseFloat(document.getElementById('setting-temperature').value),
                    top_p: 0.9,
                    stream: false
                },
                sandbox: {
                    enabled: document.getElementById('setting-sandbox-enabled').classList.contains('on'),
                    timeout: parseInt(document.getElementById('setting-sandbox-timeout').value),
                    allow_network: false
                },
                conversation: { history_enabled: true, max_history: 50 },
                agent: { max_steps: parseInt(document.getElementById('setting-max-steps').value), auto_mode: true }
            };
            try {
                await fetch('/api/settings', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(newSettings)
                });
                appSettings = newSettings;
                closeModal('settings-modal');
                addMessage('✅ 设置已保存', 'system');
            } catch(e) {
                addMessage('❌ 保存设置失败: ' + e.message, 'system');
            }
        }

        function resetSettings() {
            document.getElementById('setting-provider').value = 'aliyun';
            document.getElementById('setting-model').value = 'qwen-plus-latest';
            document.getElementById('setting-base-url').value = 'https://dashscope.aliyuncs.com/compatible-mode/v1';
            document.getElementById('setting-api-key').value = '';
            document.getElementById('setting-max-tokens').value = '4096';
            document.getElementById('setting-temperature').value = '0.7';
            document.getElementById('setting-sandbox-enabled').classList.add('on');
            document.getElementById('setting-sandbox-timeout').value = '60';
            document.getElementById('setting-max-steps').value = '5';
        }

        function applyPrompt(name) {
            document.getElementById('input-box').value = `使用${name}功能：`;
            closeModal('prompt-modal');
        }

        function showMainChat() {
            document.querySelectorAll('.nav-item').forEach(el => el.classList.remove('active'));
            event.target.classList.add('active');
        }

        document.getElementById('input-box').addEventListener('keydown', function(e) {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendMessage();
            }
        });

        window.addEventListener('load', function() {
            connectWS();
            loadSettings();
        });

        document.addEventListener('click', function(e) {
            if (e.target.classList.contains('modal-overlay')) {
                e.target.classList.remove('show');
            }
        });
    </script>
</body>
</html>
    """
    return HTMLResponse(content=html_content)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
