"""DataAgent Web Interface - Unified Universal Agent with Sandbox"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.responses import HTMLResponse, JSONResponse
import asyncio
import json
import subprocess
import tempfile
import os
import base64
import sys
from typing import Dict
from pathlib import Path

app = FastAPI(title="Data Agent", description="DataAgent Universal Agent")

active_connections: Dict[str, WebSocket] = {}

SANDBOX_DIR = Path(tempfile.mkdtemp(prefix="dataagent_sandbox_"))
SANDBOX_DIR.mkdir(parents=True, exist_ok=True)

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
            "model": "qwen-plus-latest",
            "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
            "api_key": "",
            "max_tokens": 4096,
            "temperature": 0.7,
            "api_type": "Openai"
        },
        "sandbox": {
            "enabled": True,
            "timeout": 60,
            "allow_network": False
        },
        "knowledge_base": {
            "enabled": False,
            "vector_db": "sqlite",
            "chunk_size": 500,
            "overlap": 50
        },
        "display": {
            "theme": "dark",
            "thinking_chain": True,
            "code_highlight": True
        },
        "agent": {
            "max_steps": 5,
            "auto_mode": True
        }
    }


current_settings = load_settings()


class SandboxExecutor:
    def __init__(self, work_dir: str = None):
        self.work_dir = work_dir or str(SANDBOX_DIR)

    async def execute_python(self, code: str, timeout: int = 30) -> dict:
        try:
            proc = await asyncio.create_subprocess_exec(
                sys.executable, "-c", code,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=self.work_dir,
                env={**os.environ, "MPLBACKEND": "Agg", "PYTHONIOENCODING": "utf-8"},
            )
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
            result = {
                "success": proc.returncode == 0,
                "stdout": stdout.decode("utf-8", errors="replace"),
                "stderr": stderr.decode("utf-8", errors="replace"),
                "returncode": proc.returncode,
                "images": self._collect_images(),
            }
            return result
        except asyncio.TimeoutError:
            proc.kill()
            return {"success": False, "stdout": "", "stderr": "执行超时", "returncode": -1, "images": []}
        except Exception as e:
            return {"success": False, "stdout": "", "stderr": str(e), "returncode": -1, "images": []}

    async def execute_bash(self, command: str, timeout: int = 30) -> dict:
        try:
            proc = await asyncio.create_subprocess_exec(
                "bash", "-c", command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=self.work_dir,
            )
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
            return {
                "success": proc.returncode == 0,
                "stdout": stdout.decode("utf-8", errors="replace"),
                "stderr": stderr.decode("utf-8", errors="replace"),
                "returncode": proc.returncode,
            }
        except asyncio.TimeoutError:
            proc.kill()
            return {"success": False, "stdout": "", "stderr": "执行超时", "returncode": -1}
        except Exception as e:
            return {"success": False, "stdout": "", "stderr": str(e), "returncode": -1}

    def _collect_images(self) -> list:
        images = []
        for f in Path(self.work_dir).glob("*.png"):
            try:
                data = base64.b64encode(f.read_bytes()).decode()
                images.append({"name": f.name, "data": data})
                f.unlink()
            except Exception:
                pass
        return images


sandbox = SandboxExecutor()


async def run_universal_agent(websocket: WebSocket, message: str):
    """万能智能体 - 自动识别意图，调度工具"""
    try:
        from app.agent.data import Data

        await ws_send(websocket, "thinking", {
            "phase": "init",
            "title": "🤔 理解需求",
            "content": f"正在分析您的问题: {message[:100]}...",
        })

        agent = await Data.create()
        agent.max_steps = current_settings.get("agent", {}).get("max_steps", 5)

        if message:
            agent.update_memory("user", message)

        await ws_send(websocket, "thinking", {
            "phase": "analyze",
            "title": "🧠 智能分析",
            "content": "自动识别任务类型，调度最佳工具组合",
        })

        should_act = await agent.think()

        if agent.tool_calls:
            tool_names = [tc.function.name for tc in agent.tool_calls]
            tool_args = []
            for tc in agent.tool_calls:
                try:
                    args = json.loads(tc.function.arguments or "{}")
                    tool_args.append(args)
                except Exception:
                    tool_args.append({})

            await ws_send(websocket, "thinking", {
                "phase": "tool_select",
                "title": "🛠️ 自动选择工具",
                "content": f"智能选择: {', '.join(tool_names)}",
                "tools": [{"name": n, "args": a} for n, a in zip(tool_names, tool_args)],
            })

            act_result = await agent.act()

            await ws_send(websocket, "thinking", {
                "phase": "tool_result",
                "title": "📋 执行完成",
                "content": act_result[:300] if act_result else "处理完成",
            })

            step_count = 1
            while step_count < agent.max_steps and agent.state.value != "FINISHED":
                step_count += 1
                should_act = await agent.think()
                if not should_act:
                    break
                if agent.tool_calls:
                    names = [tc.function.name for tc in agent.tool_calls]
                    await ws_send(websocket, "thinking", {
                        "phase": "tool_select",
                        "title": f"🛠️ 继续处理",
                        "content": f"使用工具: {', '.join(names)}",
                    })
                act_result = await agent.act()
                await ws_send(websocket, "thinking", {
                    "phase": "tool_result",
                    "title": "📋 处理中",
                    "content": act_result[:300] if act_result else "完成",
                })

        final_response = ""
        if agent.memory and agent.memory.messages:
            for msg in reversed(agent.memory.messages):
                if msg.role == "assistant" and msg.content:
                    final_response = msg.content
                    break

        if not final_response:
            final_response = "✅ 任务已完成！"

        await ws_send(websocket, "response", {"content": final_response})

        await agent.cleanup()

    except Exception as e:
        await ws_send(websocket, "error", {"content": f"❌ 处理失败: {str(e)[:300]}"})
        import traceback
        traceback.print_exc()


async def ws_send(websocket: WebSocket, msg_type: str, data: dict):
    try:
        await websocket.send_json({"type": msg_type, **data})
    except Exception:
        pass


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
    except WebSocketDisconnect:
        pass
    except Exception as e:
        pass


@app.get("/")
async def get():
    html_content = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>Data Agent - 万能智能助手</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        html, body { height: 100%; overflow: hidden; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #0F172A 0%, #1E293B 100%);
            display: flex;
            height: 100vh;
            color: #E2E8F0;
        }

        /* ===== Sidebar ===== */
        .sidebar {
            width: 300px;
            background: linear-gradient(180deg, #1E293B 0%, #0F172A 100%);
            border-right: 1px solid #334155;
            display: flex;
            flex-direction: column;
            height: 100vh;
            position: fixed;
            left: 0; top: 0;
            z-index: 100;
            transition: transform 0.3s ease;
        }
        .sidebar-header {
            padding: 24px 20px;
            border-bottom: 1px solid #334155;
            text-align: center;
        }
        .sidebar-header h2 {
            color: white;
            font-size: 20px;
            margin-bottom: 8px;
        }
        .sidebar-header p {
            color: #94A3B8;
            font-size: 12px;
        }

        .sidebar-body {
            flex: 1;
            overflow-y: auto;
            padding: 16px;
        }
        .sidebar-body::-webkit-scrollbar { width: 4px; }
        .sidebar-body::-webkit-scrollbar-thumb { background: #475569; border-radius: 2px; }

        .capability-section {
            margin-bottom: 16px;
        }
        .capability-title {
            color: #94A3B8;
            font-size: 11px;
            font-weight: 600;
            text-transform: uppercase;
            margin-bottom: 8px;
            letter-spacing: 0.5px;
        }

        .capability-item {
            display: flex;
            align-items: center;
            gap: 10px;
            padding: 10px 12px;
            background: rgba(30,41,59,0.6);
            border: 1px solid #334155;
            border-radius: 8px;
            margin-bottom: 6px;
            transition: all 0.2s;
        }
        .capability-item:hover {
            background: rgba(79,70,229,0.15);
            border-color: #4F46E5;
        }
        .capability-icon {
            font-size: 18px;
        }
        .capability-info h4 {
            color: #E2E8F0;
            font-size: 13px;
            font-weight: 600;
            margin-bottom: 2px;
        }
        .capability-info p {
            color: #64748B;
            font-size: 10px;
        }

        .status-badge {
            display: inline-block;
            padding: 4px 12px;
            background: #10B981;
            border-radius: 12px;
            font-size: 11px;
            color: white;
            margin-top: 12px;
        }

        .settings-btn {
            width: 100%;
            padding: 14px;
            border: none;
            border-radius: 12px;
            background: linear-gradient(135deg, #4F46E5 0%, #4338CA 100%);
            color: white;
            font-weight: 600;
            font-size: 15px;
            cursor: pointer;
            transition: all 0.2s;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 8px;
            margin-top: 16px;
        }
        .settings-btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 20px rgba(79,70,229,0.4);
        }

        /* ===== Main Content ===== */
        .main-content {
            flex: 1;
            margin-left: 300px;
            display: flex;
            flex-direction: column;
            height: 100vh;
        }

        .header {
            background: linear-gradient(135deg, #4F46E5 0%, #4338CA 100%);
            color: white;
            padding: 16px 24px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.3);
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-shrink: 0;
        }
        .header-left {
            display: flex;
            align-items: center;
            gap: 12px;
        }
        .menu-btn {
            background: rgba(255,255,255,0.2);
            border: none;
            color: white;
            padding: 8px 12px;
            border-radius: 8px;
            cursor: pointer;
            font-size: 18px;
        }
        .menu-btn:hover { background: rgba(255,255,255,0.3); }
        .header h1 {
            font-size: 20px;
            font-weight: 700;
        }
        .new-chat-btn {
            background: white;
            color: #4F46E5;
            border: none;
            padding: 10px 20px;
            border-radius: 10px;
            cursor: pointer;
            font-size: 14px;
            font-weight: 600;
            transition: all 0.2s;
        }
        .new-chat-btn:hover {
            transform: scale(1.05);
            box-shadow: 0 4px 12px rgba(0,0,0,0.2);
        }

        /* ===== Chat Area ===== */
        .chat-area {
            flex: 1;
            display: flex;
            flex-direction: column;
            overflow: hidden;
        }
        .messages {
            flex: 1;
            overflow-y: auto;
            padding: 24px;
        }
        .messages::-webkit-scrollbar { width: 6px; }
        .messages::-webkit-scrollbar-thumb { background: #475569; border-radius: 3px; }

        .message { margin-bottom: 20px; animation: slideIn 0.3s ease-out; }
        .message.user { text-align: right; }
        .message-content {
            display: inline-block;
            max-width: 85%;
            padding: 14px 18px;
            border-radius: 16px;
            line-height: 1.7;
            font-size: 14px;
            text-align: left;
        }
        .message.user .message-content {
            background: linear-gradient(135deg, #4F46E5, #4338CA);
            color: white;
            border-bottom-right-radius: 6px;
        }
        .message.assistant .message-content {
            background: #1E293B;
            border: 1px solid #334155;
            color: #F1F5F9;
            border-bottom-left-radius: 6px;
        }
        .message.system .message-content {
            background: #334155;
            color: #94A3B8;
            font-size: 13px;
            border-radius: 10px;
        }

        /* ===== Thinking Chain ===== */
        .thinking-chain {
            margin-bottom: 20px;
            animation: slideIn 0.3s ease-out;
        }
        .thinking-chain-header {
            display: flex;
            align-items: center;
            gap: 10px;
            padding: 12px 18px;
            background: linear-gradient(135deg, #312E81 0%, #1E1B4B 100%);
            border: 1px solid #4338CA;
            border-radius: 12px 12px 0 0;
            cursor: pointer;
            user-select: none;
        }
        .thinking-chain-header:hover { background: linear-gradient(135deg, #3730A3 0%, #3120E0 100%); }
        .thinking-chain-header .chain-icon { font-size: 16px; }
        .thinking-chain-header .chain-title { color: #C7D2FE; font-size: 14px; font-weight: 600; flex: 1; }
        .thinking-chain-header .chain-toggle { color: #818CF8; font-size: 12px; }
        .thinking-chain.open .thinking-chain-header { border-radius: 12px 12px 0 0; }
        .thinking-chain:not(.open) .thinking-chain-header { border-radius: 12px; }

        .thinking-chain-body {
            max-height: 0;
            overflow: hidden;
            transition: max-height 0.4s ease;
            background: #0F172A;
            border: 1px solid #334155;
            border-top: none;
            border-radius: 0 0 12px 12px;
        }
        .thinking-chain.open .thinking-chain-body { max-height: 3000px; }

        .thinking-step {
            padding: 12px 18px;
            border-bottom: 1px solid #1E293B;
            animation: fadeIn 0.3s ease;
        }
        .thinking-step:last-child { border-bottom: none; }

        .step-header {
            display: flex;
            align-items: center;
            gap: 8px;
            margin-bottom: 6px;
        }
        .step-phase {
            display: inline-block;
            padding: 2px 8px;
            border-radius: 6px;
            font-size: 10px;
            font-weight: 700;
            text-transform: uppercase;
        }
        .step-phase.init { background: #4338CA; color: #C7D2FE; }
        .step-phase.analyze { background: #7C3AED; color: #E9D5FF; }
        .step-phase.tool_select { background: #B45309; color: #FDE68A; }
        .step-phase.tool_result { background: #047857; color: #A7F3D0; }

        .step-title { color: #E2E8F0; font-size: 13px; font-weight: 600; }
        .step-content {
            color: #94A3B8;
            font-size: 12px;
            line-height: 1.6;
            margin-top: 4px;
            white-space: pre-wrap;
            word-break: break-all;
        }

        .step-tools {
            margin-top: 10px;
            display: flex;
            flex-wrap: wrap;
            gap: 6px;
        }
        .step-tool-tag {
            display: inline-flex;
            align-items: center;
            gap: 4px;
            padding: 4px 12px;
            background: #1E293B;
            border: 1px solid #475569;
            border-radius: 8px;
            color: #FCD34D;
            font-size: 12px;
        }
        .step-tool-args {
            color: #94A3B8;
            font-size: 10px;
            max-width: 250px;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }

        /* ===== Sandbox Output ===== */
        .sandbox-output {
            margin-top: 12px;
            background: #0D1117;
            border: 1px solid #30363D;
            border-radius: 10px;
            overflow: hidden;
        }
        .sandbox-header {
            padding: 8px 14px;
            background: #161B22;
            border-bottom: 1px solid #30363D;
            font-size: 11px;
            color: #8B949E;
            display: flex;
            align-items: center;
            justify-content: space-between;
        }
        .sandbox-header .dots {
            display: flex;
            gap: 6px;
        }
        .sandbox-header .dot { width: 10px; height: 10px; border-radius: 50%; }
        .sandbox-header .dot.red { background: #FF5F56; }
        .sandbox-header .dot.yellow { background: #FFBD2E; }
        .sandbox-header .dot.green { background: #27C93F; }
        
        .sandbox-body {
            padding: 14px;
            font-family: 'SF Mono', 'Fira Code', monospace;
            font-size: 12px;
            line-height: 1.6;
            color: #C9D1D9;
            white-space: pre-wrap;
            word-break: break-all;
            max-height: 400px;
            overflow-y: auto;
        }
        .sandbox-body.success { border-left: 4px solid #10B981; }
        .sandbox-body.error { border-left: 4px solid #EF4444; }
        
        .sandbox-image {
            padding: 14px;
            text-align: center;
            background: #161B22;
        }
        .sandbox-image img {
            max-width: 100%;
            border-radius: 8px;
            border: 2px solid #30363D;
            cursor: pointer;
            transition: transform 0.2s;
        }
        .sandbox-image img:hover {
            transform: scale(1.02);
        }
        
        .download-btn {
            display: inline-block;
            margin-top: 8px;
            padding: 8px 16px;
            background: #238636;
            color: white;
            border: none;
            border-radius: 6px;
            font-size: 12px;
            cursor: pointer;
            text-decoration: none;
            transition: background 0.2s;
        }
        .download-btn:hover { background: #2EA043; }

        /* ===== Input Area ===== */
        .input-area {
            flex-shrink: 0;
            background: #0F172A;
            border-top: 1px solid #334155;
            padding: 20px 24px;
            display: flex;
            gap: 12px;
            align-items: flex-end;
        }
        .input-area textarea {
            flex: 1;
            background: #1E293B;
            border: 1px solid #475569;
            border-radius: 14px;
            padding: 12px 16px;
            font-size: 14px;
            color: #F1F5F9;
            resize: none;
            min-height: 48px;
            max-height: 150px;
            font-family: inherit;
            line-height: 1.6;
        }
        .input-area textarea:focus {
            outline: none;
            border-color: #4F46E5;
            box-shadow: 0 0 0 3px rgba(79,70,229,0.2);
        }
        .input-area textarea::placeholder { color: #64748B; }
        .send-btn {
            background: #4F46E5;
            color: white;
            border: none;
            padding: 12px 28px;
            border-radius: 14px;
            cursor: pointer;
            font-size: 15px;
            font-weight: 600;
            transition: all 0.2s;
            flex-shrink: 0;
            height: 48px;
        }
        .send-btn:hover { background: #4338CA; transform: translateY(-2px); }
        .send-btn:disabled { background: #334155; color: #64748B; cursor: not-allowed; transform: none; }

        .status-bar {
            flex-shrink: 0;
            text-align: center;
            padding: 8px;
            font-size: 11px;
            color: #64748B;
            background: #0F172A;
            border-top: 1px solid #1E293B;
        }

        /* ===== Typing ===== */
        .typing-indicator {
            display: none;
            padding: 12px 18px;
            color: #94A3B8;
            font-size: 13px;
        }
        .typing-indicator.show { display: flex; align-items: center; gap: 8px; }
        .typing-dots span {
            display: inline-block;
            width: 8px; height: 8px;
            background: #4F46E5;
            border-radius: 50%;
            animation: typing 1.4s infinite;
        }
        .typing-dots span:nth-child(2) { animation-delay: 0.2s; }
        .typing-dots span:nth-child(3) { animation-delay: 0.4s; }
        @keyframes typing {
            0%, 60%, 100% { transform: translateY(0); opacity: 0.4; }
            30% { transform: translateY(-8px); opacity: 1; }
        }
        @keyframes slideIn {
            from { opacity: 0; transform: translateY(15px); }
            to { opacity: 1; transform: translateY(0); }
        }
        @keyframes fadeIn {
            from { opacity: 0; }
            to { opacity: 1; }
        }

        .overlay {
            display: none;
            position: fixed;
            top: 0; left: 0; right: 0; bottom: 0;
            background: rgba(0,0,0,0.5);
            z-index: 99;
        }
        .overlay.show { display: block; }

        /* ===== Settings Modal ===== */
        .settings-modal-overlay {
            display: none;
            position: fixed;
            top: 0; left: 0; right: 0; bottom: 0;
            background: rgba(0, 0, 0, 0.7);
            z-index: 1000;
            justify-content: center;
            align-items: center;
        }
        .settings-modal-overlay.show { display: flex; }
        
        .settings-modal {
            background: #1E293B;
            border-radius: 20px;
            width: 92%;
            max-width: 750px;
            max-height: 88vh;
            display: flex;
            flex-direction: column;
            overflow: hidden;
            box-shadow: 0 25px 80px rgba(0,0,0,0.5);
            border: 1px solid #334155;
        }
        
        .settings-modal-header {
            padding: 24px 28px;
            border-bottom: 1px solid #334155;
            display: flex;
            justify-content: space-between;
            align-items: center;
            background: linear-gradient(135deg, #0F172A 0%, #1E293B 100%);
        }
        .settings-modal-title {
            color: #E2E8F0;
            font-size: 22px;
            font-weight: 700;
        }
        .settings-modal-close {
            background: none;
            border: none;
            color: #94A3B8;
            font-size: 32px;
            cursor: pointer;
            line-height: 1;
            transition: color 0.2s;
        }
        .settings-modal-close:hover { color: #E2E8F0; }
        
        .settings-tabs {
            display: flex;
            gap: 6px;
            padding: 16px 20px;
            background: #0F172A;
            border-bottom: 1px solid #334155;
            overflow-x: auto;
        }
        .settings-tab {
            padding: 10px 20px;
            background: transparent;
            border: none;
            color: #94A3B8;
            border-radius: 10px;
            cursor: pointer;
            font-size: 14px;
            font-weight: 600;
            transition: all 0.2s;
            white-space: nowrap;
        }
        .settings-tab:hover {
            background: rgba(79,70,229,0.15);
            color: #E2E8F0;
        }
        .settings-tab.active {
            background: #4F46E5;
            color: white;
        }
        
        .settings-content {
            flex: 1;
            overflow-y: auto;
            padding: 24px 28px;
        }
        
        .settings-tab-content {
            display: none;
        }
        .settings-tab-content.active {
            display: block;
            animation: fadeIn 0.2s ease;
        }
        
        .setting-group {
            margin-bottom: 24px;
        }
        .setting-row {
            display: flex;
            gap: 20px;
        }
        .setting-row .setting-group { flex: 1; }
        .flex-1 { flex: 1; }
        
        .setting-label {
            color: #E2E8F0;
            font-size: 15px;
            font-weight: 600;
            margin-bottom: 8px;
        }
        .setting-desc {
            color: #64748B;
            font-size: 13px;
            margin-bottom: 10px;
        }
        .setting-input {
            width: 100%;
            padding: 12px 16px;
            background: #0F172A;
            border: 1px solid #334155;
            border-radius: 12px;
            color: #E2E8F0;
            font-size: 15px;
            transition: border-color 0.2s, box-shadow 0.2s;
        }
        .setting-input:focus {
            outline: none;
            border-color: #4F46E5;
            box-shadow: 0 0 0 4px rgba(79,70,229,0.2);
        }
        .setting-textarea {
            min-height: 140px;
            resize: vertical;
            font-family: inherit;
        }
        
        .setting-checkbox-group {
            background: rgba(79,70,229,0.05);
            padding: 16px;
            border-radius: 12px;
            border: 1px solid rgba(79,70,229,0.2);
        }
        .setting-checkbox-label {
            display: flex;
            align-items: center;
            gap: 12px;
            cursor: pointer;
        }
        .setting-checkbox-label input[type="checkbox"] {
            width: 20px;
            height: 20px;
            accent-color: #4F46E5;
            cursor: pointer;
        }
        .setting-checkbox-label span {
            color: #E2E8F0;
            font-size: 15px;
        }
        
        .settings-modal-footer {
            padding: 20px 28px;
            border-top: 1px solid #334155;
            display: flex;
            justify-content: flex-end;
            gap: 14px;
            background: #0F172A;
        }
        .settings-btn {
            padding: 12px 28px;
            border-radius: 12px;
            font-size: 15px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s;
            border: none;
        }
        .settings-btn-primary {
            background: #4F46E5;
            color: white;
        }
        .settings-btn-primary:hover { background: #4338CA; transform: translateY(-2px); }
        .settings-btn-secondary {
            background: #334155;
            color: #E2E8F0;
        }
        .settings-btn-secondary:hover { background: #475569; }

        /* ===== Info Banner ===== */
        .info-banner {
            background: linear-gradient(135deg, rgba(79,70,229,0.1), rgba(67,56,202,0.1));
            border: 1px solid rgba(79,70,229,0.3);
            border-radius: 12px;
            padding: 16px;
            margin-bottom: 20px;
        }
        .info-banner h3 {
            color: #C7D2FE;
            font-size: 14px;
            margin-bottom: 8px;
        }
        .info-banner p {
            color: #94A3B8;
            font-size: 12px;
            line-height: 1.6;
        }

        @media (max-width: 768px) {
            .sidebar { transform: translateX(-100%); }
            .sidebar.open { transform: translateX(0); }
            .main-content { margin-left: 0; }
            .message-content { max-width: 95%; }
        }
        @media (min-width: 769px) {
            .overlay { display: none !important; }
        }
    </style>
</head>
<body>
    <div class="overlay" id="overlay" onclick="toggleSidebar()"></div>

    <!-- Sidebar -->
    <div class="sidebar" id="sidebar">
        <div class="sidebar-header">
            <h2>🤖 Data Agent</h2>
            <p>万能智能助手</p>
            <span class="status-badge" id="ws-status">🟢 在线</span>
        </div>
        
        <div class="sidebar-body">
            <div class="capability-section">
                <div class="capability-title">🧠 核心能力</div>
                
                <div class="capability-item">
                    <span class="capability-icon">🧠</span>
                    <div class="capability-info">
                        <h4>智能意图识别</h4>
                        <p>自动分析任务类型</p>
                    </div>
                </div>
                
                <div class="capability-item">
                    <span class="capability-icon">🐍</span>
                    <div class="capability-info">
                        <h4>Python 执行</h4>
                        <p>代码编写与运行</p>
                    </div>
                </div>
                
                <div class="capability-item">
                    <span class="capability-icon">📊</span>
                    <div class="capability-info">
                        <h4>图表生成</h4>
                        <p>数据可视化与下载</p>
                    </div>
                </div>
                
                <div class="capability-item">
                    <span class="capability-icon">🔍</span>
                    <div class="capability-info">
                        <h4>网络搜索</h4>
                        <p>实时信息检索</p>
                    </div>
                </div>
                
                <div class="capability-item">
                    <span class="capability-icon">📝</span>
                    <div class="capability-info">
                        <h4>Markdown 文档</h4>
                        <p>文档编写与格式化</p>
                    </div>
                </div>
                
                <div class="capability-item">
                    <span class="capability-icon">📁</span>
                    <div class="capability-info">
                        <h4>文件操作</h4>
                        <p>读取、编辑、管理</p>
                    </div>
                </div>
                
                <div class="capability-item">
                    <span class="capability-icon">💻</span>
                    <div class="capability-info">
                        <h4>终端命令</h4>
                        <p>系统命令执行</p>
                    </div>
                </div>
            </div>
            
            <div class="capability-section">
                <div class="capability-title">⚙️ 环境状态</div>
                <div style="color:#94A3B8;font-size:12px;line-height:2;" id="env-status">
                    <p>🤖 模型: <span id="setting-model">qwen-plus-latest</span></p>
                    <p>📦 沙箱: <span id="setting-sandbox">已启用</span></p>
                    <p>📚 知识库: <span id="setting-knowledge">未启用</span></p>
                </div>
            </div>
            
            <button class="settings-btn" onclick="openSettings()">
                ⚙️ 系统设置
            </button>
        </div>
    </div>
    
    <!-- Settings Modal -->
    <div class="settings-modal-overlay" id="settings-modal">
        <div class="settings-modal">
            <div class="settings-modal-header">
                <div class="settings-modal-title">⚙️ 系统设置</div>
                <button class="settings-modal-close" onclick="closeSettings()">×</button>
            </div>
            
            <div class="settings-tabs">
                <button class="settings-tab active" onclick="switchSettingTab('llm')" data-tab="llm">🤖 模型配置</button>
                <button class="settings-tab" onclick="switchSettingTab('sandbox')" data-tab="sandbox">📦 沙箱环境</button>
                <button class="settings-tab" onclick="switchSettingTab('knowledge')" data-tab="knowledge">📚 知识库</button>
                <button class="settings-tab" onclick="switchSettingTab('display')" data-tab="display">🎨 显示设置</button>
            </div>
            
            <div class="settings-content" id="settings-content">
                <!-- LLM Settings Tab -->
                <div class="settings-tab-content active" data-tab="llm">
                    <div class="info-banner">
                        <h3>💡 模型配置提示</h3>
                        <p>配置您要使用的 AI 模型。Data Agent 会根据任务自动选择合适的工具组合，无需手动切换。</p>
                    </div>
                    
                    <div class="setting-group">
                        <div class="setting-label">模型选择</div>
                        <div class="setting-desc">选择 AI 模型供应商和版本</div>
                        <select class="setting-input" id="setting-llm-model">
                            <option value="qwen-plus-latest">通义千问 Plus (阿里百炼)</option>
                            <option value="qwen-turbo-latest">通义千问 Turbo (阿里百炼)</option>
                            <option value="gpt-4o">GPT-4o (OpenAI)</option>
                            <option value="gpt-4-turbo">GPT-4 Turbo (OpenAI)</option>
                            <option value="claude-3-5-sonnet">Claude 3.5 Sonnet (Anthropic)</option>
                        </select>
                    </div>
                    
                    <div class="setting-group">
                        <div class="setting-label">API Base URL</div>
                        <div class="setting-desc">API 端点地址</div>
                        <input type="text" class="setting-input" id="setting-llm-base-url" placeholder="https://api.example.com/v1">
                    </div>
                    
                    <div class="setting-group">
                        <div class="setting-label">API Key</div>
                        <div class="setting-desc">您的 API 密钥（将安全存储在本地）</div>
                        <input type="password" class="setting-input" id="setting-llm-api-key" placeholder="sk-...">
                    </div>
                    
                    <div class="setting-row">
                        <div class="setting-group flex-1">
                            <div class="setting-label">最大 Token 数</div>
                            <input type="number" class="setting-input" id="setting-llm-max-tokens" value="4096" min="256" max="128000">
                        </div>
                        <div class="setting-group flex-1">
                            <div class="setting-label">温度参数</div>
                            <input type="number" class="setting-input" id="setting-llm-temperature" value="0.7" min="0" max="2" step="0.1">
                        </div>
                    </div>
                </div>
                
                <!-- Sandbox Settings Tab -->
                <div class="settings-tab-content" data-tab="sandbox">
                    <div class="info-banner">
                        <h3>📦 沙箱环境说明</h3>
                        <p>沙箱环境提供安全的代码执行空间。启用后，Data Agent 可以在隔离环境中执行 Python 代码、生成图表、运行命令等操作。</p>
                    </div>
                    
                    <div class="setting-group setting-checkbox-group">
                        <label class="setting-checkbox-label">
                            <input type="checkbox" id="setting-sandbox-enabled" checked>
                            <span>启用沙箱环境（推荐开启）</span>
                        </label>
                    </div>
                    
                    <div class="setting-group">
                        <div class="setting-label">执行超时时间（秒）</div>
                        <div class="setting-desc">代码和命令的最大执行时间</div>
                        <input type="number" class="setting-input" id="setting-sandbox-timeout" value="60" min="10" max="600">
                    </div>
                    
                    <div class="setting-group setting-checkbox-group">
                        <label class="setting-checkbox-label">
                            <input type="checkbox" id="setting-sandbox-network">
                            <span>允许网络访问（谨慎开启，可能有安全风险）</span>
                        </label>
                    </div>
                    
                    <div class="setting-group">
                        <div class="setting-label">沙箱内置环境</div>
                        <div class="setting-desc">已预装的工具和库</div>
                        <div style="display:flex;flex-wrap:wrap;gap:8px;margin-top:8px;">
                            <span style="background:#334155;padding:6px 12px;border-radius:8px;font-size:12px;">🐍 Python 3.x</span>
                            <span style="background:#334155;padding:6px 12px;border-radius:8px;font-size:12px;">📊 Matplotlib</span>
                            <span style="background:#334155;padding:6px 12px;border-radius:8px;font-size:12px;">📈 Pandas</span>
                            <span style="background:#334155;padding:6px 12px;border-radius:8px;font-size:12px;">🔢 NumPy</span>
                            <span style="background:#334155;padding:6px 12px;border-radius:8px;font-size:12px;">📝 Markdown</span>
                            <span style="background:#334155;padding:6px 12px;border-radius:8px;font-size:12px;">💻 Bash</span>
                        </div>
                    </div>
                </div>
                
                <!-- Knowledge Base Settings Tab -->
                <div class="settings-tab-content" data-tab="knowledge">
                    <div class="info-banner">
                        <h3>📚 知识库配置</h3>
                        <p>启用知识库可以让 Data Agent 基于您的文档进行问答，提供更精准的领域知识支持。</p>
                    </div>
                    
                    <div class="setting-group setting-checkbox-group">
                        <label class="setting-checkbox-label">
                            <input type="checkbox" id="setting-knowledge-enabled">
                            <span>启用知识库功能</span>
                        </label>
                    </div>
                    
                    <div class="setting-group">
                        <div class="setting-label">向量数据库</div>
                        <div class="setting-desc">选择知识库的存储方式</div>
                        <select class="setting-input" id="setting-knowledge-vector-db">
                            <option value="sqlite">SQLite (轻量级)</option>
                            <option value="chroma">Chroma (推荐)</option>
                            <option value="milvus">Milvus (大规模)</option>
                        </select>
                    </div>
                    
                    <div class="setting-row">
                        <div class="setting-group flex-1">
                            <div class="setting-label">文档分块大小</div>
                            <input type="number" class="setting-input" id="setting-knowledge-chunk-size" value="500" min="100" max="2000">
                        </div>
                        <div class="setting-group flex-1">
                            <div class="setting-label">重叠大小</div>
                            <input type="number" class="setting-input" id="setting-knowledge-overlap" value="50" min="0" max="500">
                        </div>
                    </div>
                </div>
                
                <!-- Display Settings Tab -->
                <div class="settings-tab-content" data-tab="display">
                    <div class="info-banner">
                        <h3>🎨 界面显示设置</h3>
                        <p>自定义 Data Agent 的界面外观和行为，提升使用体验。</p>
                    </div>
                    
                    <div class="setting-group">
                        <div class="setting-label">主题模式</div>
                        <select class="setting-input" id="setting-display-theme">
                            <option value="dark">🌙 深色主题（当前）</option>
                            <option value="light">☀️ 浅色主题</option>
                            <option value="auto">🔄 跟随系统</option>
                        </select>
                    </div>
                    
                    <div class="setting-group setting-checkbox-group">
                        <label class="setting-checkbox-label">
                            <input type="checkbox" id="setting-display-thinking" checked>
                            <span>显示思维链（推荐开启）</span>
                        </label>
                    </div>
                    
                    <div class="setting-group setting-checkbox-group">
                        <label class="setting-checkbox-label">
                            <input type="checkbox" id="setting-display-highlight" checked>
                            <span>代码语法高亮</span>
                        </label>
                    </div>
                    
                    <div class="setting-group">
                        <div class="setting-label">最大执行步数</div>
                        <div class="setting-desc">Agent 自动执行的最大循环次数</div>
                        <input type="number" class="setting-input" id="setting-agent-max-steps" value="5" min="1" max="20">
                    </div>
                </div>
            </div>
            
            <div class="settings-modal-footer">
                <button class="settings-btn settings-btn-secondary" onclick="resetSettings()">重置默认</button>
                <button class="settings-btn settings-btn-primary" onclick="saveSettings()">保存设置</button>
            </div>
        </div>
    </div>

    <!-- Main Content -->
    <div class="main-content">
        <div class="header">
            <div class="header-left">
                <button class="menu-btn" onclick="toggleSidebar()">☰</button>
                <h1>Data Agent</h1>
                <span style="font-size:13px;opacity:0.9;margin-left:10px;">万能智能助手</span>
            </div>
            <div>
                <button class="new-chat-btn" onclick="newChat()">✨ 新建对话</button>
            </div>
        </div>

        <div class="chat-area">
            <div class="messages" id="messages">
                <div class="message assistant">
                    <div class="message-content">
                        👋 <strong>欢迎使用 Data Agent！</strong><br><br>
                        我是您的<strong>万能智能助手</strong>，具备以下核心能力：<br><br>
                        
                        <strong>🧠 智能自动化：</strong><br>
                        • 自动识别您的需求意图<br>
                        • 智能调度最佳工具组合<br>
                        • 无需手动选择模式<br><br>
                        
                        <strong>📦 强大的沙箱环境：</strong><br>
                        • <strong>Python 编程</strong> - 数据分析、算法实现<br>
                        • <strong>图表生成</strong> - Matplotlib、Seaborn，可视化下载<br>
                        • <strong>Markdown 文档</strong> - 格式化输出<br>
                        • <strong>网络搜索</strong> - 实时信息检索<br>
                        • <strong>文件操作</strong> - 读取、编辑、管理<br>
                        • <strong>终端命令</strong> - Bash 命令执行<br><br>
                        
                        <strong>💡 使用示例：</strong><br>
                        • "帮我分析这份 CSV 数据并生成图表"<br>
                        • "搜索最新的 AI 技术趋势"<br>
                        • "写一个排序算法并可视化"<br>
                        • "帮我整理会议记录为 Markdown"<br><br>
                        
                        直接输入您的需求，我会自动处理！🎯
                    </div>
                </div>
            </div>

            <div class="typing-indicator" id="typing">
                <div class="typing-dots"><span></span><span></span><span></span></div>
                <span>正在智能分析...</span>
            </div>

            <div class="input-area">
                <textarea id="input" placeholder="输入您的需求... (Enter 发送, Shift+Enter 换行)" rows="1" oninput="autoResize(this)" onkeydown="handleKeyDown(event)"></textarea>
                <button class="send-btn" id="send-btn" onclick="sendMessage()">发送</button>
            </div>
        </div>

        <div class="status-bar">
            🟢 在线 | WebSocket 连接 | 沙箱已启用 | 思维链可视化 | Data Agent v2.0 - 万能智能助手
        </div>
    </div>

    <script>
        const messagesDiv = document.getElementById('messages');
        const inputEl = document.getElementById('input');
        const sendBtn = document.getElementById('send-btn');
        const typingEl = document.getElementById('typing');
        let ws = null;
        let isProcessing = false;
        let currentThinkingChain = null;
        let thinkingStepCount = 0;
        let appSettings = null;

        // ===== WebSocket =====
        function connectWS() {
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            ws = new WebSocket(protocol + '//' + window.location.host + '/ws');

            ws.onopen = function() {
                document.getElementById('ws-status').textContent = '🟢 在线';
                document.getElementById('ws-status').style.background = '#10B981';
            };

            ws.onmessage = function(event) {
                try {
                    const data = JSON.parse(event.data);
                    handleWSMessage(data);
                } catch(e) {
                    addMessage(event.data, 'assistant');
                    finishProcessing();
                }
            };

            ws.onerror = function() { 
                finishProcessing();
                document.getElementById('ws-status').textContent = '🔴 连接错误';
                document.getElementById('ws-status').style.background = '#EF4444';
            };

            ws.onclose = function() {
                document.getElementById('ws-status').textContent = '🔴 重连中';
                document.getElementById('ws-status').style.background = '#EF4444';
                setTimeout(connectWS, 3000);
            };
        }

        connectWS();

        function handleWSMessage(data) {
            const type = data.type;

            if (type === 'thinking') {
                handleThinkingMessage(data);
            } else if (type === 'response') {
                hideTyping();
                addMessage(data.content, 'assistant');
                if (currentThinkingChain) {
                    currentThinkingChain.classList.add('open');
                }
                finishProcessing();
            } else if (type === 'sandbox_result') {
                handleSandboxResult(data);
            } else if (type === 'error') {
                hideTyping();
                addMessage(data.content, 'system');
                finishProcessing();
            }
        }

        function handleThinkingMessage(data) {
            const phase = data.phase;
            const title = data.title;
            const content = data.content;

            if (phase === 'init' || phase === 'analyze') {
                thinkingStepCount = 0;
                currentThinkingChain = createThinkingChain(title);
            }

            if (currentThinkingChain) {
                thinkingStepCount++;
                addThinkingStep(currentThinkingChain, {
                    phase: phase,
                    title: title,
                    content: content,
                    tools: data.tools || null,
                    stepNum: thinkingStepCount,
                });

                if (phase === 'complete') {
                    currentThinkingChain.classList.add('open');
                    currentThinkingChain = null;
                }
            }

            messagesDiv.scrollTop = messagesDiv.scrollHeight;
        }

        function handleSandboxResult(data) {
            const result = data.result;
            if (!currentThinkingChain) {
                currentThinkingChain = createThinkingChain('📦 执行结果');
            }

            let html = '';
            if (result.stdout) {
                html += '<div class="sandbox-output">';
                html += '<div class="sandbox-header"><div class="dots"><span class="dot red"></span><span class="dot yellow"></span><span class="dot green"></span></div><span>终端输出</span></div>';
                html += '<div class="sandbox-body ' + (result.success ? 'success' : 'error') + '">' + escapeHtml(result.stdout) + '</div>';
                html += '</div>';
            }
            if (result.stderr && !result.success) {
                html += '<div class="sandbox-output">';
                html += '<div class="sandbox-header"><div class="dots"><span class="dot red"></span><span class="dot yellow"></span><span class="dot green"></span></div><span>错误信息</span></div>';
                html += '<div class="sandbox-body error">' + escapeHtml(result.stderr) + '</div>';
                html += '</div>';
            }
            if (result.images && result.images.length > 0) {
                for (const img of result.images) {
                    html += '<div class="sandbox-output">';
                    html += '<div class="sandbox-header"><div class="dots"><span class="dot red"></span><span class="dot yellow"></span><span class="dot green"></span></div><span>📊 图表: ' + escapeHtml(img.name) + '</span></div>';
                    html += '<div class="sandbox-image">';
                    html += '<img src="data:image/png;base64,' + img.data + '" alt="' + escapeHtml(img.name) + '" onclick="downloadImage(this)">';
                    html += '<a href="data:image/png;base64,' + img.data + '" download="' + escapeHtml(img.name) + '" class="download-btn">⬇️ 下载图表</a>';
                    html += '</div>';
                    html += '</div>';
                }
            }

            if (html) {
                const body = currentThinkingChain.querySelector('.thinking-chain-body');
                const stepDiv = document.createElement('div');
                stepDiv.className = 'thinking-step';
                stepDiv.innerHTML = html;
                body.appendChild(stepDiv);
            }

            currentThinkingChain.classList.add('open');
            messagesDiv.scrollTop = messagesDiv.scrollHeight;
        }

        function downloadImage(imgElement) {
            const link = document.createElement('a');
            link.href = imgElement.src;
            link.download = 'chart_' + Date.now() + '.png';
            link.click();
        }

        // ===== Thinking Chain UI =====
        function createThinkingChain(title) {
            const chain = document.createElement('div');
            chain.className = 'thinking-chain open';

            const header = document.createElement('div');
            header.className = 'thinking-chain-header';
            header.onclick = function() { chain.classList.toggle('open'); };
            header.innerHTML = '<span class="chain-icon">🧠</span><span class="chain-title">' + title + '</span><span class="chain-toggle">▼</span>';

            const body = document.createElement('div');
            body.className = 'thinking-chain-body';

            chain.appendChild(header);
            chain.appendChild(body);
            messagesDiv.appendChild(chain);
            return chain;
        }

        function addThinkingStep(chain, step) {
            const body = chain.querySelector('.thinking-chain-body');
            const stepDiv = document.createElement('div');
            stepDiv.className = 'thinking-step';

            let toolsHtml = '';
            if (step.tools && step.tools.length > 0) {
                toolsHtml = '<div class="step-tools">';
                for (const tool of step.tools) {
                    const argsStr = JSON.stringify(tool.args).substring(0, 100);
                    toolsHtml += '<span class="step-tool-tag">🔧 ' + escapeHtml(tool.name) + ' <span class="step-tool-args">' + escapeHtml(argsStr) + '</span></span>';
                }
                toolsHtml += '</div>';
            }

            stepDiv.innerHTML =
                '<div class="step-header">' +
                    '<span class="step-phase ' + step.phase + '">' + step.phase.replace('_', ' ') + '</span>' +
                    '<span class="step-title">' + escapeHtml(step.title) + '</span>' +
                '</div>' +
                '<div class="step-content">' + escapeHtml(step.content) + '</div>' +
                toolsHtml;

            body.appendChild(stepDiv);
        }

        function escapeHtml(text) {
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        }

        // ===== Messages =====
        function addMessage(content, sender) {
            const div = document.createElement('div');
            div.className = 'message ' + sender;
            const inner = document.createElement('div');
            inner.className = 'message-content';
            inner.innerHTML = content.replace(/\\n/g, '<br>');
            div.appendChild(inner);
            messagesDiv.appendChild(div);
            messagesDiv.scrollTop = messagesDiv.scrollHeight;
        }

        function showTyping() { 
            typingEl.classList.add('show'); 
            messagesDiv.scrollTop = messagesDiv.scrollHeight; 
        }
        function hideTyping() { typingEl.classList.remove('show'); }
        function finishProcessing() { 
            isProcessing = false; 
            sendBtn.disabled = false; 
            hideTyping(); 
        }

        // ===== Send =====
        function sendMessage() {
            const content = inputEl.value.trim();
            if (!content) return;
            if (!ws || ws.readyState !== WebSocket.OPEN) {
                addMessage('⚠️ 未连接到服务器，正在重连...', 'system');
                connectWS();
                return;
            }
            if (isProcessing) {
                addMessage('⚠️ 请等待当前任务完成...', 'system');
                return;
            }

            addMessage(content, 'user');
            isProcessing = true;
            sendBtn.disabled = true;
            currentThinkingChain = null;
            thinkingStepCount = 0;
            showTyping();

            try {
                ws.send(JSON.stringify({ content: content }));
            } catch(e) {
                addMessage('❌ 发送失败: ' + e.message, 'system');
                finishProcessing();
            }

            inputEl.value = '';
            inputEl.style.height = 'auto';
        }

        function handleKeyDown(event) {
            if (event.key === 'Enter' && !event.shiftKey) {
                event.preventDefault();
                sendMessage();
            }
        }

        function autoResize(el) {
            el.style.height = 'auto';
            el.style.height = Math.min(el.scrollHeight, 150) + 'px';
        }

        function newChat() {
            messagesDiv.innerHTML = '';
            currentThinkingChain = null;
            addMessage('👋 <strong>欢迎使用 Data Agent！</strong><br><br>请输入您的需求，我会自动识别意图并处理！', 'assistant');
        }

        // ===== Sidebar =====
        function toggleSidebar() {
            const sidebar = document.getElementById('sidebar');
            const overlay = document.getElementById('overlay');
            sidebar.classList.toggle('open');
            overlay.classList.toggle('show');
        }

        // ===== Settings =====
        function openSettings() {
            document.getElementById('settings-modal').classList.add('show');
            loadSettings();
        }

        function closeSettings() {
            document.getElementById('settings-modal').classList.remove('show');
        }

        function switchSettingTab(tabName) {
            document.querySelectorAll('.settings-tab').forEach(tab => {
                tab.classList.remove('active');
            });
            document.querySelectorAll('.settings-tab-content').forEach(content => {
                content.classList.remove('active');
            });
            
            document.querySelector('.settings-tab[data-tab="' + tabName + '"]').classList.add('active');
            document.querySelector('.settings-tab-content[data-tab="' + tabName + '"]').classList.add('active');
        }

        async function loadSettings() {
            try {
                const response = await fetch('/api/settings');
                appSettings = await response.json();
                populateSettings(appSettings);
            } catch(e) {
                console.error('加载设置失败:', e);
            }
        }

        function populateSettings(settings) {
            // LLM
            document.getElementById('setting-llm-model').value = settings.llm.model;
            document.getElementById('setting-llm-base-url').value = settings.llm.base_url;
            document.getElementById('setting-llm-api-key').value = settings.llm.api_key;
            document.getElementById('setting-llm-max-tokens').value = settings.llm.max_tokens;
            document.getElementById('setting-llm-temperature').value = settings.llm.temperature;
            
            // Sandbox
            document.getElementById('setting-sandbox-enabled').checked = settings.sandbox.enabled;
            document.getElementById('setting-sandbox-timeout').value = settings.sandbox.timeout;
            document.getElementById('setting-sandbox-network').checked = settings.sandbox.allow_network;
            
            // Knowledge Base
            document.getElementById('setting-knowledge-enabled').checked = settings.knowledge_base.enabled;
            document.getElementById('setting-knowledge-vector-db').value = settings.knowledge_base.vector_db;
            document.getElementById('setting-knowledge-chunk-size').value = settings.knowledge_base.chunk_size;
            document.getElementById('setting-knowledge-overlap').value = settings.knowledge_base.overlap;
            
            // Display
            document.getElementById('setting-display-theme').value = settings.display.theme;
            document.getElementById('setting-display-thinking').checked = settings.display.thinking_chain;
            document.getElementById('setting-display-highlight').checked = settings.display.code_highlight;
            document.getElementById('setting-agent-max-steps').value = settings.agent.max_steps;
            
            // Update Sidebar
            document.getElementById('setting-model').textContent = settings.llm.model;
            document.getElementById('setting-sandbox').textContent = settings.sandbox.enabled ? '已启用' : '已禁用';
            document.getElementById('setting-knowledge').textContent = settings.knowledge_base.enabled ? '已启用' : '未启用';
        }

        async function saveSettings() {
            const newSettings = {
                llm: {
                    model: document.getElementById('setting-llm-model').value,
                    base_url: document.getElementById('setting-llm-base-url').value,
                    api_key: document.getElementById('setting-llm-api-key').value,
                    max_tokens: parseInt(document.getElementById('setting-llm-max-tokens').value),
                    temperature: parseFloat(document.getElementById('setting-llm-temperature').value),
                    api_type: "Openai"
                },
                sandbox: {
                    enabled: document.getElementById('setting-sandbox-enabled').checked,
                    timeout: parseInt(document.getElementById('setting-sandbox-timeout').value),
                    allow_network: document.getElementById('setting-sandbox-network').checked
                },
                knowledge_base: {
                    enabled: document.getElementById('setting-knowledge-enabled').checked,
                    vector_db: document.getElementById('setting-knowledge-vector-db').value,
                    chunk_size: parseInt(document.getElementById('setting-knowledge-chunk-size').value),
                    overlap: parseInt(document.getElementById('setting-knowledge-overlap').value)
                },
                display: {
                    theme: document.getElementById('setting-display-theme').value,
                    thinking_chain: document.getElementById('setting-display-thinking').checked,
                    code_highlight: document.getElementById('setting-display-highlight').checked
                },
                agent: {
                    max_steps: parseInt(document.getElementById('setting-agent-max-steps').value),
                    auto_mode: true
                }
            };
            
            try {
                await fetch('/api/settings', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(newSettings)
                });
                appSettings = newSettings;
                populateSettings(newSettings);
                closeSettings();
                addMessage('✅ 设置已保存', 'system');
            } catch(e) {
                addMessage('❌ 保存设置失败: ' + e.message, 'system');
            }
        }

        async function resetSettings() {
            if (confirm('确定要重置为默认设置吗？')) {
                try {
                    const defaultSettings = {
                        llm: {
                            model: "qwen-plus-latest",
                            base_url: "https://dashscope.aliyuncs.com/compatible-mode/v1",
                            api_key: "",
                            max_tokens: 4096,
                            temperature: 0.7,
                            api_type: "Openai"
                        },
                        sandbox: {
                            enabled: true,
                            timeout: 60,
                            allow_network: false
                        },
                        knowledge_base: {
                            enabled: false,
                            vector_db: "sqlite",
                            chunk_size: 500,
                            overlap: 50
                        },
                        display: {
                            theme: "dark",
                            thinking_chain: true,
                            code_highlight: true
                        },
                        agent: {
                            max_steps: 5,
                            auto_mode: true
                        }
                    };
                    
                    await fetch('/api/settings', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify(defaultSettings)
                    });
                    
                    populateSettings(defaultSettings);
                    addMessage('✅ 设置已重置为默认', 'system');
                } catch(e) {
                    addMessage('❌ 重置设置失败: ' + e.message, 'system');
                }
            }
        }

        // Load settings on page load
        window.addEventListener('DOMContentLoaded', function() {
            loadSettings();
        });
    </script>
</body>
</html>
    """
    return HTMLResponse(html_content)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
