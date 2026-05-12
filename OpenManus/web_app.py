"""DataAgent Web Interface with Sandbox & Thinking Chain Visualization"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.responses import HTMLResponse, JSONResponse
import asyncio
import json
import subprocess
import tempfile
import os
import base64
import sys
from typing import Dict, Optional
from pathlib import Path

app = FastAPI(title="Data Agent", description="DataAgent Web Interface")

active_connections: Dict[str, WebSocket] = {}

SANDBOX_DIR = Path(tempfile.mkdtemp(prefix="dataagent_sandbox_"))
SANDBOX_DIR.mkdir(parents=True, exist_ok=True)

# Config Management
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
        "search": {
            "engine": "Google",
            "lang": "zh",
            "country": "cn"
        },
        "browser": {
            "headless": False,
            "max_content_length": 2000
        },
        "sandbox": {
            "use_sandbox": False,
            "timeout": 300,
            "network_enabled": False
        },
        "prompts": {
            "data_agent": "",
            "browser_agent": "",
            "swe_agent": "",
            "analysis_agent": ""
        },
        "agent": {
            "max_steps": 5
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
            return {"success": False, "stdout": "", "stderr": "Execution timed out", "returncode": -1, "images": []}
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
            return {"success": False, "stdout": "", "stderr": "Execution timed out", "returncode": -1}
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


async def run_agent_with_thinking(websocket: WebSocket, message: str, agent_type: str = "data"):
    try:
        from app.agent.data import Data
        from app.agent.browser import BrowserAgent
        from app.agent.swe import SWEAgent
        from app.agent.data_analysis import DataAnalysis

        agent_map = {
            "data": Data,
            "browser": BrowserAgent,
            "swe": SWEAgent,
            "analysis": DataAnalysis,
        }

        agent_class = agent_map.get(agent_type, Data)

        await ws_send(websocket, "thinking", {
            "phase": "init",
            "title": "🤔 理解问题",
            "content": message[:200],
        })

        agent = await agent_class.create()
        agent.max_steps = current_settings.get("agent", {}).get("max_steps", 5)

        if message:
            agent.update_memory("user", message)

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
                "title": "🛠️ 使用工具",
                "content": ", ".join(tool_names),
                "tools": [{"name": n, "args": a} for n, a in zip(tool_names, tool_args)],
            })

            act_result = await agent.act()

            await ws_send(websocket, "thinking", {
                "phase": "tool_result",
                "title": "📋 执行结果",
                "content": act_result[:300] if act_result else "完成",
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
                        "title": f"🛠️ 继续使用工具",
                        "content": ", ".join(names),
                    })
                act_result = await agent.act()
                await ws_send(websocket, "thinking", {
                    "phase": "tool_result",
                    "title": "📋 执行结果",
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


async def ws_send(websocket: WebSocket, msg_type: str, data: dict):
    try:
        await websocket.send_json({"type": msg_type, **data})
    except Exception:
        pass


# Settings API Endpoints
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


# WebSocket Endpoint
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_json()
            message = data.get("content", "")
            agent_type = data.get("agent", "data")
            await run_agent_with_thinking(websocket, message, agent_type)
    except WebSocketDisconnect:
        pass
    except Exception as e:
        pass


# HTML Endpoint
@app.get("/")
async def get():
    html_content = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>Data Agent - DataAgent</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        html, body { height: 100%; overflow: hidden; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #0F172A 0%, #1E293B 100%);
            display: flex;
            height: 100vh;
        }

        /* ===== Sidebar ===== */
        .sidebar {
            width: 280px;
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
            padding: 16px 18px;
            border-bottom: 1px solid #334155;
            flex-shrink: 0;
        }
        .sidebar-header h2 { color: white; font-size: 17px; margin-bottom: 4px; }
        .sidebar-header p { color: #94A3B8; font-size: 11px; }
        .sidebar-body {
            flex: 1;
            overflow-y: auto;
            padding: 12px 14px;
        }
        .sidebar-body::-webkit-scrollbar { width: 3px; }
        .sidebar-body::-webkit-scrollbar-thumb { background: #475569; border-radius: 2px; }

        /* ===== Collapsible ===== */
        .collapse-section {
            margin-bottom: 6px;
            border: 1px solid #334155;
            border-radius: 10px;
            overflow: hidden;
            background: rgba(30,41,59,0.5);
        }
        .collapse-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 10px 14px;
            cursor: pointer;
            user-select: none;
            color: #E2E8F0;
            font-size: 13px;
            font-weight: 600;
            transition: background 0.2s;
        }
        .collapse-header:hover { background: rgba(79,70,229,0.15); }
        .collapse-header .arrow {
            transition: transform 0.25s;
            font-size: 10px;
            color: #94A3B8;
        }
        .collapse-section.open .collapse-header .arrow { transform: rotate(90deg); }
        .collapse-body {
            max-height: 0;
            overflow: hidden;
            transition: max-height 0.3s ease;
        }
        .collapse-section.open .collapse-body { max-height: 600px; }
        .collapse-body-inner { padding: 6px 10px 10px; }

        /* ===== Agent Card ===== */
        .agent-card {
            background: linear-gradient(135deg, #334155 0%, #1E293B 100%);
            border: 1px solid #475569;
            border-radius: 8px;
            padding: 9px 12px;
            margin-bottom: 6px;
            cursor: pointer;
            transition: all 0.2s;
        }
        .agent-card:hover { border-color: #4F46E5; }
        .agent-card.active {
            border-color: #4F46E5;
            background: linear-gradient(135deg, #4F46E5 0%, #4338CA 100%);
        }
        .agent-card h4 { color: white; font-size: 12px; margin-bottom: 2px; }
        .agent-card p { color: #94A3B8; font-size: 10px; }

        .status-badge {
            display: inline-block;
            padding: 2px 8px;
            background: #10B981;
            border-radius: 10px;
            font-size: 10px;
            color: white;
            margin-top: 6px;
        }

        /* ===== Settings Button ===== */
        .settings-btn-sidebar {
            width: 100%;
            padding: 12px;
            border: none;
            border-radius: 10px;
            background: linear-gradient(135deg, #4F46E5 0%, #4338CA 100%);
            color: white;
            font-weight: 600;
            font-size: 14px;
            cursor: pointer;
            transition: all 0.2s;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 8px;
        }
        .settings-btn-sidebar:hover {
            transform: scale(1.02);
            box-shadow: 0 4px 12px rgba(79,70,229,0.4);
        }

        /* ===== Main Content ===== */
        .main-content {
            flex: 1;
            margin-left: 280px;
            display: flex;
            flex-direction: column;
            height: 100vh;
        }

        .header {
            background: linear-gradient(135deg, #4F46E5 0%, #4338CA 100%);
            color: white;
            padding: 12px 20px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.2);
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-shrink: 0;
        }
        .header-left { display: flex; align-items: center; gap: 10px; }
        .menu-btn {
            background: rgba(255,255,255,0.2);
            border: none;
            color: white;
            padding: 5px 10px;
            border-radius: 6px;
            cursor: pointer;
            font-size: 16px;
        }
        .menu-btn:hover { background: rgba(255,255,255,0.3); }
        .header h1 { font-size: 17px; font-weight: 600; }
        .new-chat-btn {
            background: white;
            color: #4F46E5;
            border: none;
            padding: 6px 14px;
            border-radius: 6px;
            cursor: pointer;
            font-size: 12px;
            font-weight: 600;
        }
        .new-chat-btn:hover { background: #F1F5F9; }

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
            padding: 20px;
        }
        .messages::-webkit-scrollbar { width: 5px; }
        .messages::-webkit-scrollbar-thumb { background: #475569; border-radius: 3px; }

        .message { margin-bottom: 14px; animation: slideIn 0.3s ease-out; }
        .message.user { text-align: right; }
        .message-content {
            display: inline-block;
            max-width: 80%;
            padding: 10px 14px;
            border-radius: 14px;
            line-height: 1.6;
            font-size: 13px;
            text-align: left;
        }
        .message.user .message-content {
            background: linear-gradient(135deg, #4F46E5, #4338CA);
            color: white;
            border-bottom-right-radius: 4px;
        }
        .message.assistant .message-content {
            background: #1E293B;
            border: 1px solid #334155;
            color: #F1F5F9;
            border-bottom-left-radius: 4px;
        }
        .message.system .message-content {
            background: #334155;
            color: #94A3B8;
            font-size: 12px;
            border-radius: 8px;
        }

        /* ===== Thinking Chain ===== */
        .thinking-chain {
            margin-bottom: 14px;
            animation: slideIn 0.3s ease-out;
        }
        .thinking-chain-header {
            display: flex;
            align-items: center;
            gap: 8px;
            padding: 8px 14px;
            background: linear-gradient(135deg, #312E81 0%, #1E1B4B 100%);
            border: 1px solid #4338CA;
            border-radius: 10px 10px 0 0;
            cursor: pointer;
            user-select: none;
        }
        .thinking-chain-header:hover { background: linear-gradient(135deg, #3730A3 0%, #312E81 100%); }
        .thinking-chain-header .chain-icon { font-size: 14px; }
        .thinking-chain-header .chain-title { color: #C7D2FE; font-size: 12px; font-weight: 600; flex: 1; }
        .thinking-chain-header .chain-toggle { color: #818CF8; font-size: 10px; }
        .thinking-chain.open .thinking-chain-header { border-radius: 10px 10px 0 0; }
        .thinking-chain:not(.open) .thinking-chain-header { border-radius: 10px; }

        .thinking-chain-body {
            max-height: 0;
            overflow: hidden;
            transition: max-height 0.4s ease;
            background: #0F172A;
            border: 1px solid #334155;
            border-top: none;
            border-radius: 0 0 10px 10px;
        }
        .thinking-chain.open .thinking-chain-body { max-height: 2000px; }

        .thinking-step {
            padding: 8px 14px;
            border-bottom: 1px solid #1E293B;
            animation: fadeIn 0.3s ease;
        }
        .thinking-step:last-child { border-bottom: none; }

        .step-header {
            display: flex;
            align-items: center;
            gap: 6px;
            margin-bottom: 4px;
        }
        .step-phase {
            display: inline-block;
            padding: 1px 6px;
            border-radius: 4px;
            font-size: 9px;
            font-weight: 700;
            text-transform: uppercase;
        }
        .step-phase.init { background: #4338CA; color: #C7D2FE; }
        .step-phase.tool_select { background: #B45309; color: #FDE68A; }
        .step-phase.tool_result { background: #047857; color: #A7F3D0; }

        .step-title { color: #E2E8F0; font-size: 11px; font-weight: 600; }
        .step-content {
            color: #94A3B8;
            font-size: 11px;
            line-height: 1.5;
            margin-top: 3px;
            white-space: pre-wrap;
            word-break: break-all;
        }

        .step-tools {
            margin-top: 6px;
            display: flex;
            flex-wrap: wrap;
            gap: 4px;
        }
        .step-tool-tag {
            display: inline-flex;
            align-items: center;
            gap: 3px;
            padding: 2px 8px;
            background: #1E293B;
            border: 1px solid #475569;
            border-radius: 5px;
            color: #FCD34D;
            font-size: 10px;
        }
        .step-tool-args {
            color: #94A3B8;
            font-size: 9px;
            max-width: 200px;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }

        /* ===== Sandbox Output ===== */
        .sandbox-output {
            margin-top: 8px;
            background: #0D1117;
            border: 1px solid #30363D;
            border-radius: 8px;
            overflow: hidden;
        }
        .sandbox-header {
            padding: 6px 10px;
            background: #161B22;
            border-bottom: 1px solid #30363D;
            font-size: 10px;
            color: #8B949E;
            display: flex;
            align-items: center;
            gap: 6px;
        }
        .sandbox-header .dot { width: 8px; height: 8px; border-radius: 50%; }
        .sandbox-header .dot.red { background: #FF5F56; }
        .sandbox-header .dot.yellow { background: #FFBD2E; }
        .sandbox-header .dot.green { background: #27C93F; }
        .sandbox-body {
            padding: 10px;
            font-family: 'SF Mono', 'Fira Code', monospace;
            font-size: 11px;
            line-height: 1.5;
            color: #C9D1D9;
            white-space: pre-wrap;
            word-break: break-all;
            max-height: 300px;
            overflow-y: auto;
        }
        .sandbox-body.success { border-left: 3px solid #10B981; }
        .sandbox-body.error { border-left: 3px solid #EF4444; }
        .sandbox-image {
            padding: 10px;
            text-align: center;
        }
        .sandbox-image img {
            max-width: 100%;
            border-radius: 6px;
            border: 1px solid #334155;
        }

        /* ===== Input Area ===== */
        .input-area {
            flex-shrink: 0;
            background: #0F172A;
            border-top: 1px solid #334155;
            padding: 14px 20px;
            display: flex;
            gap: 10px;
            align-items: flex-end;
        }
        .input-area textarea {
            flex: 1;
            background: #1E293B;
            border: 1px solid #475569;
            border-radius: 12px;
            padding: 10px 14px;
            font-size: 13px;
            color: #F1F5F9;
            resize: none;
            min-height: 42px;
            max-height: 120px;
            font-family: inherit;
            line-height: 1.5;
        }
        .input-area textarea:focus {
            outline: none;
            border-color: #4F46E5;
            box-shadow: 0 0 0 2px rgba(79,70,229,0.2);
        }
        .input-area textarea::placeholder { color: #64748B; }
        .send-btn {
            background: #4F46E5;
            color: white;
            border: none;
            padding: 10px 22px;
            border-radius: 12px;
            cursor: pointer;
            font-size: 13px;
            font-weight: 600;
            transition: all 0.2s;
            flex-shrink: 0;
            height: 42px;
        }
        .send-btn:hover { background: #4338CA; }
        .send-btn:disabled { background: #334155; color: #64748B; cursor: not-allowed; }

        .status-bar {
            flex-shrink: 0;
            text-align: center;
            padding: 5px;
            font-size: 10px;
            color: #64748B;
            background: #0F172A;
            border-top: 1px solid #1E293B;
        }

        /* ===== Typing ===== */
        .typing-indicator {
            display: none;
            padding: 8px 14px;
            color: #94A3B8;
            font-size: 12px;
        }
        .typing-indicator.show { display: flex; align-items: center; gap: 6px; }
        .typing-dots span {
            display: inline-block;
            width: 6px; height: 6px;
            background: #4F46E5;
            border-radius: 50%;
            animation: typing 1.4s infinite;
        }
        .typing-dots span:nth-child(2) { animation-delay: 0.2s; }
        .typing-dots span:nth-child(3) { animation-delay: 0.4s; }
        @keyframes typing {
            0%, 60%, 100% { transform: translateY(0); opacity: 0.4; }
            30% { transform: translateY(-6px); opacity: 1; }
        }
        @keyframes slideIn {
            from { opacity: 0; transform: translateY(10px); }
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
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: rgba(0, 0, 0, 0.7);
            z-index: 1000;
            justify-content: center;
            align-items: center;
        }
        .settings-modal-overlay.show { display: flex; }
        
        .settings-modal {
            background: #1E293B;
            border-radius: 16px;
            width: 90%;
            max-width: 700px;
            max-height: 85vh;
            display: flex;
            flex-direction: column;
            overflow: hidden;
            box-shadow: 0 20px 60px rgba(0,0,0,0.4);
            border: 1px solid #334155;
        }
        
        .settings-modal-header {
            padding: 20px 24px;
            border-bottom: 1px solid #334155;
            display: flex;
            justify-content: space-between;
            align-items: center;
            background: linear-gradient(135deg, #0F172A 0%, #1E293B 100%);
        }
        .settings-modal-title {
            color: #E2E8F0;
            font-size: 20px;
            font-weight: 700;
        }
        .settings-modal-close {
            background: none;
            border: none;
            color: #94A3B8;
            font-size: 28px;
            cursor: pointer;
            line-height: 1;
            transition: color 0.2s;
        }
        .settings-modal-close:hover { color: #E2E8F0; }
        
        .settings-tabs {
            display: flex;
            gap: 4px;
            padding: 12px 16px;
            background: #0F172A;
            border-bottom: 1px solid #334155;
            overflow-x: auto;
        }
        .settings-tab {
            padding: 8px 16px;
            background: transparent;
            border: none;
            color: #94A3B8;
            border-radius: 8px;
            cursor: pointer;
            font-size: 13px;
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
            padding: 20px 24px;
        }
        
        .settings-tab-content {
            display: none;
        }
        .settings-tab-content.active {
            display: block;
            animation: fadeIn 0.2s ease;
        }
        
        .setting-group {
            margin-bottom: 20px;
        }
        .setting-row {
            display: flex;
            gap: 16px;
        }
        .setting-row .setting-group { flex: 1; }
        .flex-1 { flex: 1; }
        
        .setting-label {
            color: #E2E8F0;
            font-size: 14px;
            font-weight: 600;
            margin-bottom: 6px;
        }
        .setting-desc {
            color: #64748B;
            font-size: 12px;
            margin-bottom: 8px;
        }
        .setting-input {
            width: 100%;
            padding: 10px 14px;
            background: #0F172A;
            border: 1px solid #334155;
            border-radius: 10px;
            color: #E2E8F0;
            font-size: 14px;
            transition: border-color 0.2s, box-shadow 0.2s;
        }
        .setting-input:focus {
            outline: none;
            border-color: #4F46E5;
            box-shadow: 0 0 0 3px rgba(79,70,229,0.2);
        }
        .setting-textarea {
            min-height: 120px;
            resize: vertical;
            font-family: inherit;
        }
        
        .setting-checkbox-group {
            background: rgba(79,70,229,0.05);
            padding: 14px;
            border-radius: 10px;
            border: 1px solid rgba(79,70,229,0.2);
        }
        .setting-checkbox-label {
            display: flex;
            align-items: center;
            gap: 10px;
            cursor: pointer;
        }
        .setting-checkbox-label input[type="checkbox"] {
            width: 18px;
            height: 18px;
            accent-color: #4F46E5;
            cursor: pointer;
        }
        .setting-checkbox-label span {
            color: #E2E8F0;
            font-size: 14px;
        }
        
        .settings-modal-footer {
            padding: 16px 24px;
            border-top: 1px solid #334155;
            display: flex;
            justify-content: flex-end;
            gap: 12px;
            background: #0F172A;
        }
        .settings-btn {
            padding: 10px 24px;
            border-radius: 10px;
            font-size: 14px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s;
            border: none;
        }
        .settings-btn-primary {
            background: #4F46E5;
            color: white;
        }
        .settings-btn-primary:hover { background: #4338CA; }
        .settings-btn-secondary {
            background: #334155;
            color: #E2E8F0;
        }
        .settings-btn-secondary:hover { background: #475569; }

        @media (max-width: 768px) {
            .sidebar { transform: translateX(-100%); }
            .sidebar.open { transform: translateX(0); }
            .main-content { margin-left: 0; }
            .message-content { max-width: 90%; }
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
            <p>智能助手控制面板</p>
            <span class="status-badge" id="ws-status">🟢 在线</span>
        </div>
        <div class="sidebar-body">
            <div class="collapse-section open">
                <div class="collapse-header" onclick="toggleSection(this)">
                    <span>🤖 代理模式</span><span class="arrow">▶</span>
                </div>
                <div class="collapse-body"><div class="collapse-body-inner">
                    <div class="agent-card active" onclick="selectAgent('data')" id="agent-data">
                        <h4>📋 Data 通用代理</h4><p>多工具协同处理复杂任务</p>
                    </div>
                    <div class="agent-card" onclick="selectAgent('browser')" id="agent-browser">
                        <h4>🌐 浏览器代理</h4><p>自动化网页操作</p>
                    </div>
                    <div class="agent-card" onclick="selectAgent('swe')" id="agent-swe">
                        <h4>💻 SWE 软件工程代理</h4><p>代码开发与调试</p>
                    </div>
                    <div class="agent-card" onclick="selectAgent('analysis')" id="agent-analysis">
                        <h4>📊 数据分析代理</h4><p>数据处理与可视化</p>
                    </div>
                </div></div>
            </div>
            <div class="collapse-section">
                <div class="collapse-header" onclick="toggleSection(this)">
                    <span>📊 系统信息</span><span class="arrow">▶</span>
                </div>
                <div class="collapse-body"><div class="collapse-body-inner" style="color:#94A3B8;font-size:11px;line-height:1.8;">
                    <p>模型: <span id="setting-model">qwen-plus-latest</span></p>
                    <p>API: 阿里百炼</p>
                    <p>沙箱: 已启用</p>
                    <p>Python: 已配置</p>
                    <p>状态: <span id="sys-status">正常运行</span></p>
                </div></div>
            </div>
            
            <div style="padding-top: 12px;">
                <button class="settings-btn-sidebar" onclick="openSettings()">
                    ⚙️ 设置
                </button>
            </div>
        </div>
    </div>
    
    <!-- Settings Modal -->
    <div class="settings-modal-overlay" id="settings-modal">
        <div class="settings-modal">
            <div class="settings-modal-header">
                <div class="settings-modal-title">⚙️ 设置</div>
                <button class="settings-modal-close" onclick="closeSettings()">×</button>
            </div>
            
            <div class="settings-tabs">
                <button class="settings-tab active" onclick="switchSettingTab('llm')" data-tab="llm">模型配置</button>
                <button class="settings-tab" onclick="switchSettingTab('prompts')" data-tab="prompts">提示词</button>
                <button class="settings-tab" onclick="switchSettingTab('search')" data-tab="search">搜索配置</button>
                <button class="settings-tab" onclick="switchSettingTab('browser')" data-tab="browser">浏览器</button>
                <button class="settings-tab" onclick="switchSettingTab('sandbox')" data-tab="sandbox">沙箱</button>
                <button class="settings-tab" onclick="switchSettingTab('agent')" data-tab="agent">智能体</button>
            </div>
            
            <div class="settings-content" id="settings-content">
                <!-- LLM Settings Tab -->
                <div class="settings-tab-content active" data-tab="llm">
                    <div class="setting-group">
                        <div class="setting-label">模型名称</div>
                        <div class="setting-desc">选择要使用的 LLM 模型</div>
                        <select class="setting-input" id="setting-llm-model">
                            <option value="qwen-plus-latest">qwen-plus-latest (阿里百炼)</option>
                            <option value="qwen-turbo-latest">qwen-turbo-latest (阿里百炼)</option>
                            <option value="gpt-4o">gpt-4o (OpenAI)</option>
                            <option value="gpt-4">gpt-4 (OpenAI)</option>
                            <option value="gpt-3.5-turbo">gpt-3.5-turbo (OpenAI)</option>
                            <option value="claude-3-opus">claude-3-opus (Anthropic)</option>
                            <option value="claude-3-sonnet">claude-3-sonnet (Anthropic)</option>
                        </select>
                    </div>
                    
                    <div class="setting-group">
                        <div class="setting-label">API Base URL</div>
                        <div class="setting-desc">API 端点地址</div>
                        <input type="text" class="setting-input" id="setting-llm-base-url" placeholder="https://api.example.com/v1">
                    </div>
                    
                    <div class="setting-group">
                        <div class="setting-label">API Key</div>
                        <div class="setting-desc">您的 API 密钥（将安全存储）</div>
                        <input type="password" class="setting-input" id="setting-llm-api-key" placeholder="sk-...">
                    </div>
                    
                    <div class="setting-row">
                        <div class="setting-group flex-1">
                            <div class="setting-label">最大 Token 数</div>
                            <input type="number" class="setting-input" id="setting-llm-max-tokens" value="4096" min="256" max="128000">
                        </div>
                        <div class="setting-group flex-1">
                            <div class="setting-label">温度</div>
                            <input type="number" class="setting-input" id="setting-llm-temperature" value="0.7" min="0" max="2" step="0.1">
                        </div>
                    </div>
                    
                    <div class="setting-group">
                        <div class="setting-label">API 类型</div>
                        <select class="setting-input" id="setting-llm-api-type">
                            <option value="Openai">OpenAI 兼容</option>
                            <option value="Azure">Azure OpenAI</option>
                            <option value="Ollama">Ollama (本地)</option>
                        </select>
                    </div>
                </div>
                
                <!-- Prompts Settings Tab -->
                <div class="settings-tab-content" data-tab="prompts">
                    <div class="setting-group">
                        <div class="setting-label">Data 通用代理提示词</div>
                        <div class="setting-desc">自定义 Data 代理的系统提示词</div>
                        <textarea class="setting-input setting-textarea" id="setting-prompt-data" placeholder="输入自定义系统提示词..."></textarea>
                    </div>
                    
                    <div class="setting-group">
                        <div class="setting-label">浏览器代理提示词</div>
                        <div class="setting-desc">自定义浏览器代理的系统提示词</div>
                        <textarea class="setting-input setting-textarea" id="setting-prompt-browser" placeholder="输入自定义系统提示词..."></textarea>
                    </div>
                    
                    <div class="setting-group">
                        <div class="setting-label">SWE 软件工程代理提示词</div>
                        <div class="setting-desc">自定义 SWE 代理的系统提示词</div>
                        <textarea class="setting-input setting-textarea" id="setting-prompt-swe" placeholder="输入自定义系统提示词..."></textarea>
                    </div>
                    
                    <div class="setting-group">
                        <div class="setting-label">数据分析代理提示词</div>
                        <div class="setting-desc">自定义数据分析代理的系统提示词</div>
                        <textarea class="setting-input setting-textarea" id="setting-prompt-analysis" placeholder="输入自定义系统提示词..."></textarea>
                    </div>
                </div>
                
                <!-- Search Settings Tab -->
                <div class="settings-tab-content" data-tab="search">
                    <div class="setting-group">
                        <div class="setting-label">默认搜索引擎</div>
                        <select class="setting-input" id="setting-search-engine">
                            <option value="Google">Google</option>
                            <option value="DuckDuckGo">DuckDuckGo</option>
                            <option value="Baidu">百度</option>
                            <option value="Bing">Bing</option>
                        </select>
                    </div>
                    
                    <div class="setting-row">
                        <div class="setting-group flex-1">
                            <div class="setting-label">搜索语言</div>
                            <select class="setting-input" id="setting-search-lang">
                                <option value="zh">中文</option>
                                <option value="en">English</option>
                                <option value="ja">日本語</option>
                                <option value="ko">한국어</option>
                            </select>
                        </div>
                        <div class="setting-group flex-1">
                            <div class="setting-label">搜索地区</div>
                            <select class="setting-input" id="setting-search-country">
                                <option value="cn">中国</option>
                                <option value="us">美国</option>
                                <option value="jp">日本</option>
                                <option value="kr">韩国</option>
                            </select>
                        </div>
                    </div>
                </div>
                
                <!-- Browser Settings Tab -->
                <div class="settings-tab-content" data-tab="browser">
                    <div class="setting-group setting-checkbox-group">
                        <label class="setting-checkbox-label">
                            <input type="checkbox" id="setting-browser-headless">
                            <span>无头模式（不显示浏览器窗口）</span>
                        </label>
                    </div>
                    
                    <div class="setting-group">
                        <div class="setting-label">最大内容长度</div>
                        <div class="setting-desc">单次获取网页内容的最大字符数</div>
                        <input type="number" class="setting-input" id="setting-browser-max-content" value="2000" min="500" max="10000">
                    </div>
                </div>
                
                <!-- Sandbox Settings Tab -->
                <div class="settings-tab-content" data-tab="sandbox">
                    <div class="setting-group setting-checkbox-group">
                        <label class="setting-checkbox-label">
                            <input type="checkbox" id="setting-sandbox-enabled">
                            <span>启用沙箱环境</span>
                        </label>
                    </div>
                    
                    <div class="setting-group">
                        <div class="setting-label">执行超时（秒）</div>
                        <div class="setting-desc">沙箱命令执行的超时时间</div>
                        <input type="number" class="setting-input" id="setting-sandbox-timeout" value="300" min="10" max="3600">
                    </div>
                    
                    <div class="setting-group setting-checkbox-group">
                        <label class="setting-checkbox-label">
                            <input type="checkbox" id="setting-sandbox-network">
                            <span>允许网络访问（谨慎开启）</span>
                        </label>
                    </div>
                </div>
                
                <!-- Agent Settings Tab -->
                <div class="settings-tab-content" data-tab="agent">
                    <div class="setting-group">
                        <div class="setting-label">最大执行步数</div>
                        <div class="setting-desc">智能体执行的最大循环步数</div>
                        <input type="number" class="setting-input" id="setting-agent-max-steps" value="5" min="1" max="50">
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
                <span id="current-agent" style="font-size:12px;opacity:0.8;margin-left:8px;">Data 通用代理</span>
            </div>
            <div>
                <button class="new-chat-btn" onclick="newChat()">+ 新建对话</button>
            </div>
        </div>

        <div class="chat-area">
            <div class="messages" id="messages">
                <div class="message assistant">
                    <div class="message-content">
                        👋 你好！我是 <strong>Data</strong>，您的智能助手。<br><br>
                        我运行在<strong>沙箱环境</strong>中，您可以清楚地看到我的<strong>思维链</strong>——每一步的思考、推理、工具选择和执行结果。<br><br>
                        <strong>🧠 思维链可视化：</strong><br>
                        • 🎯 意图识别 — 理解您的需求<br>
                        • 💭 思考推理 — 分析决策过程<br>
                        • 🛠️ 工具选择 — 选择合适的工具<br>
                        • 🎯 执行结果 — 查看工具输出<br><br>
                        <strong>📦 沙箱环境：</strong><br>
                        • Python 代码安全执行<br>
                        • 图表可视化输出<br>
                        • Bash 命令执行<br><br>
                        点击侧边栏的 <strong>⚙️ 设置</strong> 按钮来配置 API 和其他选项！
                    </div>
                </div>
            </div>

            <div class="typing-indicator" id="typing">
                <div class="typing-dots"><span></span><span></span><span></span></div>
                <span>正在思考...</span>
            </div>

            <div class="input-area">
                <textarea id="input" placeholder="输入您的消息... (Enter 发送, Shift+Enter 换行)" rows="1" oninput="autoResize(this)" onkeydown="handleKeyDown(event)"></textarea>
                <button class="send-btn" id="send-btn" onclick="sendMessage()">发送</button>
            </div>
        </div>

        <div class="status-bar">
            🟢 在线 | WebSocket | 沙箱已启用 | 思维链可视化 | Data Agent v2.0
        </div>
    </div>

    <script>
        const messagesDiv = document.getElementById('messages');
        const inputEl = document.getElementById('input');
        const sendBtn = document.getElementById('send-btn');
        const typingEl = document.getElementById('typing');
        const currentAgentSpan = document.getElementById('current-agent');
        let ws = null;
        let currentAgent = 'data';
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
                document.getElementById('sys-status').textContent = '正常运行';
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

            ws.onerror = function() { finishProcessing(); };

            ws.onclose = function() {
                document.getElementById('ws-status').textContent = '🔴 重连中';
                document.getElementById('sys-status').textContent = '重连中...';
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

            if (phase === 'init') {
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
                currentThinkingChain = createThinkingChain('📦 沙箱执行结果');
            }

            let html = '';
            if (result.stdout) {
                html += '<div class="sandbox-output">';
                html += '<div class="sandbox-header"><span class="dot red"></span><span class="dot yellow"></span><span class="dot green"></span> 终端输出</div>';
                html += '<div class="sandbox-body ' + (result.success ? 'success' : 'error') + '">' + escapeHtml(result.stdout) + '</div>';
                html += '</div>';
            }
            if (result.stderr && !result.success) {
                html += '<div class="sandbox-output">';
                html += '<div class="sandbox-header"><span class="dot red"></span><span class="dot yellow"></span><span class="dot green"></span> 错误输出</div>';
                html += '<div class="sandbox-body error">' + escapeHtml(result.stderr) + '</div>';
                html += '</div>';
            }
            if (result.images && result.images.length > 0) {
                for (const img of result.images) {
                    html += '<div class="sandbox-output">';
                    html += '<div class="sandbox-header"><span class="dot red"></span><span class="dot yellow"></span><span class="dot green"></span> 📊 图表输出: ' + escapeHtml(img.name) + '</div>';
                    html += '<div class="sandbox-image"><img src="data:image/png;base64,' + img.data + '" alt="' + escapeHtml(img.name) + '"></div>';
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
                    const argsStr = JSON.stringify(tool.args).substring(0, 80);
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

        function showTyping() { typingEl.classList.add('show'); messagesDiv.scrollTop = messagesDiv.scrollHeight; }
        function hideTyping() { typingEl.classList.remove('show'); }
        function finishProcessing() { isProcessing = false; sendBtn.disabled = false; hideTyping(); }

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
                ws.send(JSON.stringify({ content: content, agent: currentAgent }));
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
            el.style.height = Math.min(el.scrollHeight, 120) + 'px';
        }

        function newChat() {
            messagesDiv.innerHTML = '';
            currentThinkingChain = null;
            addMessage('👋 你好！我是 <strong>Data</strong>，您的智能助手。', 'assistant');
        }

        // ===== Sidebar =====
        function toggleSidebar() {
            const sidebar = document.getElementById('sidebar');
            const overlay = document.getElementById('overlay');
            sidebar.classList.toggle('open');
            overlay.classList.toggle('show');
        }

        function toggleSection(header) {
            const section = header.parentElement;
            section.classList.toggle('open');
        }

        function selectAgent(agent) {
            currentAgent = agent;
            document.querySelectorAll('.agent-card').forEach(card => {
                card.classList.remove('active');
            });
            document.getElementById('agent-' + agent).classList.add('active');
            
            const agentNames = {
                'data': 'Data 通用代理',
                'browser': '浏览器代理',
                'swe': 'SWE 软件工程代理',
                'analysis': '数据分析代理'
            };
            currentAgentSpan.textContent = agentNames[agent];
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
                console.error('Failed to load settings:', e);
            }
        }

        function populateSettings(settings) {
            // LLM
            document.getElementById('setting-llm-model').value = settings.llm.model;
            document.getElementById('setting-llm-base-url').value = settings.llm.base_url;
            document.getElementById('setting-llm-api-key').value = settings.llm.api_key;
            document.getElementById('setting-llm-max-tokens').value = settings.llm.max_tokens;
            document.getElementById('setting-llm-temperature').value = settings.llm.temperature;
            document.getElementById('setting-llm-api-type').value = settings.llm.api_type;
            
            // Prompts
            document.getElementById('setting-prompt-data').value = settings.prompts.data_agent;
            document.getElementById('setting-prompt-browser').value = settings.prompts.browser_agent;
            document.getElementById('setting-prompt-swe').value = settings.prompts.swe_agent;
            document.getElementById('setting-prompt-analysis').value = settings.prompts.analysis_agent;
            
            // Search
            document.getElementById('setting-search-engine').value = settings.search.engine;
            document.getElementById('setting-search-lang').value = settings.search.lang;
            document.getElementById('setting-search-country').value = settings.search.country;
            
            // Browser
            document.getElementById('setting-browser-headless').checked = settings.browser.headless;
            document.getElementById('setting-browser-max-content').value = settings.browser.max_content_length;
            
            // Sandbox
            document.getElementById('setting-sandbox-enabled').checked = settings.sandbox.use_sandbox;
            document.getElementById('setting-sandbox-timeout').value = settings.sandbox.timeout;
            document.getElementById('setting-sandbox-network').checked = settings.sandbox.network_enabled;
            
            // Agent
            document.getElementById('setting-agent-max-steps').value = settings.agent.max_steps;
            
            // Update UI
            document.getElementById('setting-model').textContent = settings.llm.model;
        }

        async function saveSettings() {
            const newSettings = {
                llm: {
                    model: document.getElementById('setting-llm-model').value,
                    base_url: document.getElementById('setting-llm-base-url').value,
                    api_key: document.getElementById('setting-llm-api-key').value,
                    max_tokens: parseInt(document.getElementById('setting-llm-max-tokens').value),
                    temperature: parseFloat(document.getElementById('setting-llm-temperature').value),
                    api_type: document.getElementById('setting-llm-api-type').value
                },
                search: {
                    engine: document.getElementById('setting-search-engine').value,
                    lang: document.getElementById('setting-search-lang').value,
                    country: document.getElementById('setting-search-country').value
                },
                browser: {
                    headless: document.getElementById('setting-browser-headless').checked,
                    max_content_length: parseInt(document.getElementById('setting-browser-max-content').value)
                },
                sandbox: {
                    use_sandbox: document.getElementById('setting-sandbox-enabled').checked,
                    timeout: parseInt(document.getElementById('setting-sandbox-timeout').value),
                    network_enabled: document.getElementById('setting-sandbox-network').checked
                },
                prompts: {
                    data_agent: document.getElementById('setting-prompt-data').value,
                    browser_agent: document.getElementById('setting-prompt-browser').value,
                    swe_agent: document.getElementById('setting-prompt-swe').value,
                    analysis_agent: document.getElementById('setting-prompt-analysis').value
                },
                agent: {
                    max_steps: parseInt(document.getElementById('setting-agent-max-steps').value)
                }
            };
            
            try {
                await fetch('/api/settings', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(newSettings)
                });
                appSettings = newSettings;
                document.getElementById('setting-model').textContent = newSettings.llm.model;
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
                        search: {
                            engine: "Google",
                            lang: "zh",
                            country: "cn"
                        },
                        browser: {
                            headless: false,
                            max_content_length: 2000
                        },
                        sandbox: {
                            use_sandbox: false,
                            timeout: 300,
                            network_enabled: false
                        },
                        prompts: {
                            data_agent: "",
                            browser_agent: "",
                            swe_agent: "",
                            analysis_agent: ""
                        },
                        agent: {
                            max_steps: 5
                        }
                    };
                    
                    await fetch('/api/settings', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify(defaultSettings)
                    });
                    
                    populateSettings(defaultSettings);
                    document.getElementById('setting-model').textContent = defaultSettings.llm.model;
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
