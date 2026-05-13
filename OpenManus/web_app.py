"""DataAgent Web Interface - Unified Universal Agent"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.responses import HTMLResponse, JSONResponse
import asyncio
import json
import tempfile
import os
import base64
import sys
from typing import Dict
from pathlib import Path

app = FastAPI(title="Data Agent", description="DataAgent Universal AI Assistant")

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
        "knowledge_base": {
            "enabled": False,
            "vector_db": "sqlite",
            "chunk_size": 500,
            "overlap": 50,
            "embedding_model": "text-embedding-v3"
        },
        "conversation": {
            "history_enabled": True,
            "max_history": 50,
            "auto_title": True
        },
        "display": {
            "theme": "dark",
            "thinking_chain": True,
            "code_highlight": True,
            "markdown_render": True
        },
        "agent": {
            "max_steps": 5,
            "auto_mode": True,
            "reasoning_mode": "auto"
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
    try:
        from app.agent.data import Data

        await ws_send(websocket, "thinking", {
            "phase": "init",
            "title": "🤔 理解需求",
            "content": f"正在分析: {message[:100]}...",
        })

        agent = await Data.create()
        agent.max_steps = current_settings.get("agent", {}).get("max_steps", 5)

        if message:
            agent.update_memory("user", message)

        await ws_send(websocket, "thinking", {
            "phase": "analyze",
            "title": "🧠 智能分析",
            "content": "自动识别任务类型，调度最佳工具",
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
            padding: 24px 20px;
            border-bottom: 1px solid #334155;
            text-align: center;
        }
        .sidebar-header h2 { color: white; font-size: 22px; margin-bottom: 6px; }
        .sidebar-header p { color: #94A3B8; font-size: 12px; }

        .sidebar-nav {
            flex: 1;
            overflow-y: auto;
            padding: 12px;
        }
        .sidebar-nav::-webkit-scrollbar { width: 4px; }
        .sidebar-nav::-webkit-scrollbar-thumb { background: #475569; border-radius: 2px; }

        .nav-item {
            display: flex;
            align-items: center;
            gap: 12px;
            padding: 14px 16px;
            border-radius: 10px;
            margin-bottom: 6px;
            cursor: pointer;
            transition: all 0.2s;
            border: 1px solid transparent;
        }
        .nav-item:hover {
            background: rgba(79,70,229,0.15);
            border-color: #4F46E5;
        }
        .nav-item.active {
            background: linear-gradient(135deg, #4F46E5 0%, #4338CA 100%);
            border-color: #4F46E5;
        }
        .nav-icon { font-size: 20px; }
        .nav-text { flex: 1; }
        .nav-text h4 { color: #E2E8F0; font-size: 14px; font-weight: 600; margin-bottom: 2px; }
        .nav-text p { color: #64748B; font-size: 11px; }
        .nav-item.active .nav-text h4 { color: white; }
        .nav-item.active .nav-text p { color: rgba(255,255,255,0.8); }

        .nav-divider {
            height: 1px;
            background: #334155;
            margin: 12px 0;
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

        /* ===== Modal Base ===== */
        .modal-overlay {
            display: none;
            position: fixed;
            top: 0; left: 0; right: 0; bottom: 0;
            background: rgba(0, 0, 0, 0.7);
            z-index: 1000;
            justify-content: center;
            align-items: center;
        }
        .modal-overlay.show { display: flex; }
        
        .modal {
            background: #1E293B;
            border-radius: 16px;
            width: 92%;
            max-width: 800px;
            max-height: 88vh;
            display: flex;
            flex-direction: column;
            overflow: hidden;
            box-shadow: 0 25px 80px rgba(0,0,0,0.5);
            border: 1px solid #334155;
        }
        
        .modal-header {
            padding: 20px 24px;
            border-bottom: 1px solid #334155;
            display: flex;
            justify-content: space-between;
            align-items: center;
            background: linear-gradient(135deg, #0F172A 0%, #1E293B 100%);
        }
        .modal-title {
            color: #E2E8F0;
            font-size: 20px;
            font-weight: 700;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        .modal-close {
            background: none;
            border: none;
            color: #94A3B8;
            font-size: 28px;
            cursor: pointer;
            line-height: 1;
            transition: color 0.2s;
        }
        .modal-close:hover { color: #E2E8F0; }
        
        .modal-content {
            flex: 1;
            overflow-y: auto;
            padding: 24px;
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
            padding: 16px 24px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.3);
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-shrink: 0;
        }
        .header-left { display: flex; align-items: center; gap: 12px; }
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
        .header h1 { font-size: 20px; font-weight: 700; }
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
        .new-chat-btn:hover { transform: scale(1.05); box-shadow: 0 4px 12px rgba(0,0,0,0.2); }

        .chat-area { flex: 1; display: flex; flex-direction: column; overflow: hidden; }
        .messages { flex: 1; overflow-y: auto; padding: 24px; }
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
        .thinking-chain { margin-bottom: 20px; animation: slideIn 0.3s ease-out; }
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

        .step-tools { margin-top: 10px; display: flex; flex-wrap: wrap; gap: 6px; }
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
        .sandbox-header .dots { display: flex; gap: 6px; }
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
        
        .sandbox-image { padding: 14px; text-align: center; background: #161B22; }
        .sandbox-image img {
            max-width: 100%;
            border-radius: 8px;
            border: 2px solid #30363D;
            cursor: pointer;
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

        .typing-indicator { display: none; padding: 12px 18px; color: #94A3B8; font-size: 13px; }
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
        .settings-tabs {
            display: flex;
            gap: 6px;
            padding: 16px 20px;
            background: #0F172A;
            border-bottom: 1px solid #334155;
            overflow-x: auto;
        }
        .settings-tab {
            padding: 10px 18px;
            background: transparent;
            border: none;
            color: #94A3B8;
            border-radius: 10px;
            cursor: pointer;
            font-size: 13px;
            font-weight: 600;
            transition: all 0.2s;
            white-space: nowrap;
        }
        .settings-tab:hover { background: rgba(79,70,229,0.15); color: #E2E8F0; }
        .settings-tab.active { background: #4F46E5; color: white; }
        
        .settings-content { flex: 1; overflow-y: auto; padding: 24px; }
        
        .settings-tab-content { display: none; }
        .settings-tab-content.active { display: block; animation: fadeIn 0.2s ease; }
        
        .setting-group { margin-bottom: 24px; }
        .setting-row { display: flex; gap: 20px; }
        .setting-row .setting-group { flex: 1; }
        
        .setting-label { color: #E2E8F0; font-size: 15px; font-weight: 600; margin-bottom: 8px; }
        .setting-desc { color: #64748B; font-size: 13px; margin-bottom: 10px; }
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
        .setting-checkbox-label span { color: #E2E8F0; font-size: 15px; }
        
        .settings-modal-footer {
            padding: 20px 24px;
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
        .settings-btn-primary { background: #4F46E5; color: white; }
        .settings-btn-primary:hover { background: #4338CA; transform: translateY(-2px); }
        .settings-btn-secondary { background: #334155; color: #E2E8F0; }
        .settings-btn-secondary:hover { background: #475569; }

        .info-banner {
            background: linear-gradient(135deg, rgba(79,70,229,0.1), rgba(67,56,202,0.1));
            border: 1px solid rgba(79,70,229,0.3);
            border-radius: 12px;
            padding: 16px;
            margin-bottom: 20px;
        }
        .info-banner h3 { color: #C7D2FE; font-size: 14px; margin-bottom: 8px; }
        .info-banner p { color: #94A3B8; font-size: 12px; line-height: 1.6; }

        /* ===== Knowledge Base Modal ===== */
        .knowledge-tabs {
            display: flex;
            gap: 8px;
            margin-bottom: 20px;
        }
        .knowledge-tab {
            padding: 10px 20px;
            background: #334155;
            border: none;
            color: #E2E8F0;
            border-radius: 8px;
            cursor: pointer;
            font-size: 14px;
            font-weight: 600;
            transition: all 0.2s;
        }
        .knowledge-tab:hover { background: #475569; }
        .knowledge-tab.active { background: #4F46E5; }

        .knowledge-content { display: none; }
        .knowledge-content.active { display: block; }

        .file-upload-area {
            border: 2px dashed #475569;
            border-radius: 12px;
            padding: 40px;
            text-align: center;
            cursor: pointer;
            transition: all 0.2s;
        }
        .file-upload-area:hover { border-color: #4F46E5; background: rgba(79,70,229,0.05); }
        .file-upload-area .icon { font-size: 48px; margin-bottom: 16px; }
        .file-upload-area h3 { color: #E2E8F0; font-size: 18px; margin-bottom: 8px; }
        .file-upload-area p { color: #64748B; font-size: 13px; }

        .knowledge-list {
            background: #0F172A;
            border: 1px solid #334155;
            border-radius: 12px;
            overflow: hidden;
        }
        .knowledge-item {
            padding: 16px;
            border-bottom: 1px solid #334155;
            display: flex;
            align-items: center;
            gap: 12px;
        }
        .knowledge-item:last-child { border-bottom: none; }
        .knowledge-item .icon { font-size: 24px; }
        .knowledge-item .info { flex: 1; }
        .knowledge-item .info h4 { color: #E2E8F0; font-size: 14px; margin-bottom: 4px; }
        .knowledge-item .info p { color: #64748B; font-size: 12px; }
        .knowledge-item .actions { display: flex; gap: 8px; }
        .knowledge-item .actions button {
            padding: 6px 12px;
            border: none;
            border-radius: 6px;
            cursor: pointer;
            font-size: 12px;
            transition: all 0.2s;
        }
        .knowledge-item .actions .edit { background: #334155; color: #E2E8F0; }
        .knowledge-item .actions .delete { background: #DC2626; color: white; }

        /* ===== Prompt Market Modal ===== */
        .prompt-card {
            background: #0F172A;
            border: 1px solid #334155;
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 16px;
            cursor: pointer;
            transition: all 0.2s;
        }
        .prompt-card:hover { border-color: #4F46E5; transform: translateY(-2px); }
        .prompt-card h3 { color: #E2E8F0; font-size: 16px; margin-bottom: 8px; display: flex; align-items: center; gap: 8px; }
        .prompt-card p { color: #94A3B8; font-size: 13px; margin-bottom: 12px; }
        .prompt-card .tags { display: flex; flex-wrap: wrap; gap: 6px; }
        .prompt-card .tag {
            padding: 4px 10px;
            background: rgba(79,70,229,0.2);
            color: #C7D2FE;
            border-radius: 6px;
            font-size: 11px;
        }

        /* ===== Skill Market Modal ===== */
        .skill-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
            gap: 16px;
        }
        .skill-card {
            background: #0F172A;
            border: 1px solid #334155;
            border-radius: 12px;
            padding: 20px;
            transition: all 0.2s;
        }
        .skill-card:hover { border-color: #4F46E5; transform: translateY(-4px); box-shadow: 0 8px 20px rgba(79,70,229,0.2); }
        .skill-card .header { display: flex; align-items: center; gap: 12px; margin-bottom: 12px; }
        .skill-card .header .icon { font-size: 32px; }
        .skill-card .header h3 { color: #E2E8F0; font-size: 16px; flex: 1; }
        .skill-card .header .badge {
            padding: 4px 8px;
            background: #10B981;
            color: white;
            border-radius: 6px;
            font-size: 10px;
        }
        .skill-card p { color: #94A3B8; font-size: 13px; margin-bottom: 12px; line-height: 1.6; }
        .skill-card .footer { display: flex; justify-content: space-between; align-items: center; }
        .skill-card .author { color: #64748B; font-size: 12px; }
        .skill-card .install-btn {
            padding: 8px 16px;
            background: #4F46E5;
            color: white;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            font-size: 13px;
            font-weight: 600;
            transition: all 0.2s;
        }
        .skill-card .install-btn:hover { background: #4338CA; }

        /* ===== MCP Tools Modal ===== */
        .mcp-service {
            background: #0F172A;
            border: 1px solid #334155;
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 16px;
        }
        .mcp-service h3 { color: #E2E8F0; font-size: 16px; margin-bottom: 8px; display: flex; align-items: center; gap: 8px; }
        .mcp-service p { color: #94A3B8; font-size: 13px; margin-bottom: 16px; }
        .mcp-service .config { display: flex; gap: 12px; margin-bottom: 12px; }
        .mcp-service .config input { flex: 1; }

        /* ===== Help Modal ===== */
        .help-section {
            margin-bottom: 32px;
        }
        .help-section h2 {
            color: #E2E8F0;
            font-size: 22px;
            margin-bottom: 16px;
            padding-bottom: 8px;
            border-bottom: 2px solid #4F46E5;
        }
        .help-section h3 { color: #C7D2FE; font-size: 16px; margin: 16px 0 8px; }
        .help-section p { color: #94A3B8; font-size: 14px; line-height: 1.8; margin-bottom: 12px; }
        .help-section ul { color: #94A3B8; font-size: 14px; line-height: 2; margin-left: 24px; margin-bottom: 12px; }
        .help-section code {
            background: #334155;
            padding: 2px 8px;
            border-radius: 4px;
            color: #FCD34D;
            font-size: 13px;
        }
        .help-section pre {
            background: #0D1117;
            border: 1px solid #30363D;
            border-radius: 8px;
            padding: 16px;
            margin: 12px 0;
            overflow-x: auto;
        }
        .help-section pre code {
            background: none;
            padding: 0;
            color: #C9D1D9;
            font-size: 13px;
            line-height: 1.6;
        }

        .feature-list {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
            gap: 16px;
            margin: 20px 0;
        }
        .feature-item {
            background: rgba(79,70,229,0.1);
            border: 1px solid rgba(79,70,229,0.3);
            border-radius: 12px;
            padding: 20px;
            text-align: center;
        }
        .feature-item .icon { font-size: 36px; margin-bottom: 12px; }
        .feature-item h4 { color: #E2E8F0; font-size: 15px; margin-bottom: 8px; }
        .feature-item p { color: #94A3B8; font-size: 12px; line-height: 1.6; }

        @media (max-width: 768px) {
            .sidebar { transform: translateX(-100%); }
            .sidebar.open { transform: translateX(0); }
            .main-content { margin-left: 0; }
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
        
        <div class="sidebar-nav">
            <!-- Main Navigation -->
            <div class="nav-item active" onclick="showMainChat()">
                <span class="nav-icon">💬</span>
                <div class="nav-text">
                    <h4>对话</h4>
                    <p>开始智能对话</p>
                </div>
            </div>

            <div class="nav-divider"></div>

            <!-- Feature Modules -->
            <div class="nav-item" onclick="openModal('knowledge-modal')">
                <span class="nav-icon">📚</span>
                <div class="nav-text">
                    <h4>知识库</h4>
                    <p>文档管理与检索</p>
                </div>
            </div>

            <div class="nav-item" onclick="openModal('prompt-modal')">
                <span class="nav-icon">💡</span>
                <div class="nav-text">
                    <h4>提示词市场</h4>
                    <p>精选提示词模板</p>
                </div>
            </div>

            <div class="nav-item" onclick="openModal('skill-modal')">
                <span class="nav-icon">🛠️</span>
                <div class="nav-text">
                    <h4>Skill 市场</h4>
                    <p>扩展技能与插件</p>
                </div>
            </div>

            <div class="nav-item" onclick="openModal('mcp-modal')">
                <span class="nav-icon">🔌</span>
                <div class="nav-text">
                    <h4>MCP 工具服务</h4>
                    <p>模型上下文协议</p>
                </div>
            </div>

            <div class="nav-divider"></div>

            <!-- Settings -->
            <div class="nav-item" onclick="openModal('settings-modal')">
                <span class="nav-icon">⚙️</span>
                <div class="nav-text">
                    <h4>设置</h4>
                    <p>系统配置与管理</p>
                </div>
            </div>

            <div class="nav-item" onclick="openModal('help-modal')">
                <span class="nav-icon">❓</span>
                <div class="nav-text">
                    <h4>使用说明</h4>
                    <p>功能介绍与教程</p>
                </div>
            </div>
        </div>
    </div>
    
    <!-- Settings Modal -->
    <div class="modal-overlay" id="settings-modal">
        <div class="modal">
            <div class="modal-header">
                <div class="modal-title">⚙️ 系统设置</div>
                <button class="modal-close" onclick="closeModal('settings-modal')">×</button>
            </div>
            
            <div class="settings-tabs">
                <button class="settings-tab active" onclick="switchSettingTab('model')" data-tab="model">🤖 模型配置</button>
                <button class="settings-tab" onclick="switchSettingTab('sandbox')" data-tab="sandbox">📦 沙箱环境</button>
                <button class="settings-tab" onclick="switchSettingTab('knowledge')" data-tab="knowledge">📚 知识库</button>
                <button class="settings-tab" onclick="switchSettingTab('conversation')" data-tab="conversation">💬 对话设置</button>
                <button class="settings-tab" onclick="switchSettingTab('display')" data-tab="display">🎨 显示设置</button>
            </div>
            
            <div class="settings-content" id="settings-content">
                <!-- Model Settings -->
                <div class="settings-tab-content active" data-tab="model">
                    <div class="info-banner">
                        <h3>💡 模型配置提示</h3>
                        <p>Data Agent 支持国内外主流大模型，包括阿里通义千问、百度文心、字节豆包、OpenAI GPT、Anthropic Claude、Google Gemini 等。支持 API 调用和本地部署（Ollama）。</p>
                    </div>
                    
                    <div class="setting-group">
                        <div class="setting-label">模型供应商</div>
                        <select class="setting-input" id="setting-provider">
                            <optgroup label="🇨🇳 国内模型">
                                <option value="aliyun">阿里云 - 通义千问 (Qwen3.6/Qwen2.5)</option>
                                <option value="baidu">百度 - 文心一言 (ERNIE 5.0/4.0)</option>
                                <option value="doubao">字节跳动 - 豆包 (Doubao 5.0/1.5)</option>
                                <option value="tencent">腾讯 - 混元 (Hunyuan 3.0)</option>
                                <option value="deepseek">深度求索 - DeepSeek (V4/R1)</option>
                                <option value="zhipu">智谱AI - GLM (GLM-5/4)</option>
                                <option value="kimi">月之暗面 - Kimi (K2.6/K2)</option>
                                <option value="minimax">MiniMax - M2.7/M2</option>
                                <option value="xiaomi">小米 - MiMo</option>
                                <option value="iflytek">科大讯飞 - 星火</option>
                            </optgroup>
                            <optgroup label="🌍 国际模型">
                                <option value="openai">OpenAI - GPT (GPT-5.5/5.4/4o)</option>
                                <option value="anthropic">Anthropic - Claude (Opus 4.7/Sonnet 4.7)</option>
                                <option value="google">Google - Gemini (Gemini 3.1/3.0)</option>
                                <option value="xai">xAI - Grok (Grok 4.2)</option>
                                <option value="meta">Meta - Llama (Llama 4/3)</option>
                                <option value="mistral">Mistral AI - Mistral (Large 2/Small 4)</option>
                            </optgroup>
                            <optgroup label="💻 本地部署">
                                <option value="ollama">Ollama - 本地模型</option>
                                <option value="lmstudio">LM Studio - 本地模型</option>
                                <option value="llamafile">LLaMAfile - 本地模型</option>
                            </optgroup>
                        </select>
                    </div>
                    
                    <div class="setting-group">
                        <div class="setting-label">具体模型</div>
                        <div class="setting-desc">根据选择的供应商显示可用模型列表</div>
                        <select class="setting-input" id="setting-model">
                            <option value="qwen-plus-latest">qwen-plus-latest (通义千问Plus)</option>
                            <option value="qwen-max">qwen-max (通义千问Max)</option>
                            <option value="qwen-turbo-latest">qwen-turbo-latest (通义千问Turbo)</option>
                            <option value="qwen2.5-72b-instruct">qwen2.5-72b-instruct (开源)</option>
                            <option value="qwen2.5-coder-32b-instruct">qwen2.5-coder-32b-instruct (编程)</option>
                        </select>
                    </div>
                    
                    <div class="setting-group">
                        <div class="setting-label">API Base URL</div>
                        <div class="setting-desc">API 端点地址（不同供应商地址不同）</div>
                        <input type="text" class="setting-input" id="setting-base-url" placeholder="https://api.example.com/v1">
                    </div>
                    
                    <div class="setting-group">
                        <div class="setting-label">API Key</div>
                        <div class="setting-desc">您的 API 密钥（将安全存储在本地）</div>
                        <input type="password" class="setting-input" id="setting-api-key" placeholder="sk-...">
                    </div>
                    
                    <div class="setting-row">
                        <div class="setting-group">
                            <div class="setting-label">最大 Token 数</div>
                            <input type="number" class="setting-input" id="setting-max-tokens" value="4096" min="256" max="128000">
                        </div>
                        <div class="setting-group">
                            <div class="setting-label">温度参数</div>
                            <input type="number" class="setting-input" id="setting-temperature" value="0.7" min="0" max="2" step="0.1">
                        </div>
                        <div class="setting-group">
                            <div class="setting-label">Top P</div>
                            <input type="number" class="setting-input" id="setting-top-p" value="0.9" min="0" max="1" step="0.1">
                        </div>
                    </div>
                </div>
                
                <!-- Sandbox Settings -->
                <div class="settings-tab-content" data-tab="sandbox">
                    <div class="info-banner">
                        <h3>📦 沙箱环境说明</h3>
                        <p>沙箱环境提供安全的代码执行空间。启用后可以在隔离环境中执行 Python 代码、生成图表、运行命令等操作。</p>
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
                            <span style="background:#334155;padding:6px 12px;border-radius:8px;font-size:12px;">🔷 Seaborn</span>
                            <span style="background:#334155;padding:6px 12px;border-radius:8px;font-size:12px;">📉 Plotly</span>
                        </div>
                    </div>
                </div>
                
                <!-- Knowledge Base Settings -->
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
                        <select class="setting-input" id="setting-vector-db">
                            <option value="sqlite">SQLite (轻量级，无需额外服务)</option>
                            <option value="chroma">Chroma (推荐，生产环境)</option>
                            <option value="milvus">Milvus (大规模部署)</option>
                            <option value="qdrant">Qdrant (高性能向量搜索)</option>
                        </select>
                    </div>
                    
                    <div class="setting-row">
                        <div class="setting-group">
                            <div class="setting-label">文档分块大小</div>
                            <input type="number" class="setting-input" id="setting-chunk-size" value="500" min="100" max="2000">
                        </div>
                        <div class="setting-group">
                            <div class="setting-label">重叠大小</div>
                            <input type="number" class="setting-input" id="setting-overlap" value="50" min="0" max="500">
                        </div>
                    </div>

                    <div class="setting-group">
                        <div class="setting-label">嵌入模型</div>
                        <div class="setting-desc">用于将文档向量化的模型</div>
                        <select class="setting-input" id="setting-embedding-model">
                            <option value="text-embedding-v3">text-embedding-v3 (阿里)</option>
                            <option value="text-embedding-3-small">text-embedding-3-small (OpenAI)</option>
                            <option value="bge-m3">BGE-M3 (智源，开源)</option>
                            <option value="m3e-base">M3E-Base (开源)</option>
                        </select>
                    </div>
                </div>
                
                <!-- Conversation Settings -->
                <div class="settings-tab-content" data-tab="conversation">
                    <div class="info-banner">
                        <h3>💬 对话设置</h3>
                        <p>配置对话历史管理和自动优化功能。</p>
                    </div>
                    
                    <div class="setting-group setting-checkbox-group">
                        <label class="setting-checkbox-label">
                            <input type="checkbox" id="setting-history-enabled" checked>
                            <span>启用对话历史</span>
                        </label>
                    </div>
                    
                    <div class="setting-group">
                        <div class="setting-label">最大历史记录数</div>
                        <div class="setting-desc">保存的对话历史条数</div>
                        <input type="number" class="setting-input" id="setting-max-history" value="50" min="10" max="200">
                    </div>
                    
                    <div class="setting-group setting-checkbox-group">
                        <label class="setting-checkbox-label">
                            <input type="checkbox" id="setting-auto-title" checked>
                            <span>自动生成对话标题</span>
                        </label>
                    </div>
                    
                    <div class="setting-group">
                        <div class="setting-label">智能体设置</div>
                        <div class="setting-desc">配置 Agent 的行为模式</div>
                        <input type="number" class="setting-input" id="setting-max-steps" value="5" min="1" max="20" style="margin-top:8px;">
                        <div class="setting-desc" style="margin-top:8px;">最大执行步数：Agent 自动执行的最大循环次数</div>
                    </div>
                </div>
                
                <!-- Display Settings -->
                <div class="settings-tab-content" data-tab="display">
                    <div class="info-banner">
                        <h3>🎨 界面显示设置</h3>
                        <p>自定义 Data Agent 的界面外观和行为。</p>
                    </div>
                    
                    <div class="setting-group">
                        <div class="setting-label">主题模式</div>
                        <select class="setting-input" id="setting-theme">
                            <option value="dark">🌙 深色主题（当前）</option>
                            <option value="light">☀️ 浅色主题</option>
                            <option value="auto">🔄 跟随系统</option>
                        </select>
                    </div>
                    
                    <div class="setting-group setting-checkbox-group">
                        <label class="setting-checkbox-label">
                            <input type="checkbox" id="setting-thinking-chain" checked>
                            <span>显示思维链（推荐开启）</span>
                        </label>
                    </div>
                    
                    <div class="setting-group setting-checkbox-group">
                        <label class="setting-checkbox-label">
                            <input type="checkbox" id="setting-code-highlight" checked>
                            <span>代码语法高亮</span>
                        </label>
                    </div>
                    
                    <div class="setting-group setting-checkbox-group">
                        <label class="setting-checkbox-label">
                            <input type="checkbox" id="setting-markdown-render" checked>
                            <span>Markdown 渲染</span>
                        </label>
                    </div>
                </div>
            </div>
            
            <div class="settings-modal-footer">
                <button class="settings-btn settings-btn-secondary" onclick="resetSettings()">重置默认</button>
                <button class="settings-btn settings-btn-primary" onclick="saveSettings()">保存设置</button>
            </div>
        </div>
    </div>

    <!-- Knowledge Base Modal -->
    <div class="modal-overlay" id="knowledge-modal">
        <div class="modal" style="max-width:900px;">
            <div class="modal-header">
                <div class="modal-title">📚 知识库管理</div>
                <button class="modal-close" onclick="closeModal('knowledge-modal')">×</button>
            </div>
            
            <div class="modal-content">
                <div class="knowledge-tabs">
                    <button class="knowledge-tab active" onclick="switchKnowledgeTab('documents')">📄 文档管理</button>
                    <button class="knowledge-tab" onclick="switchKnowledgeTab('collections')">📁 知识集合</button>
                    <button class="knowledge-tab" onclick="switchKnowledgeTab('config')">⚙️ 配置</button>
                </div>
                
                <div class="knowledge-content active" data-tab="documents">
                    <div class="file-upload-area" onclick="document.getElementById('file-input').click()">
                        <div class="icon">📤</div>
                        <h3>点击上传文档</h3>
                        <p>支持 PDF、Word、TXT、Markdown 等格式</p>
                        <input type="file" id="file-input" style="display:none;" multiple accept=".pdf,.doc,.docx,.txt,.md">
                    </div>
                    
                    <div class="knowledge-list" style="margin-top:24px;">
                        <div class="knowledge-item">
                            <span class="icon">📄</span>
                            <div class="info">
                                <h4>产品手册.pdf</h4>
                                <p>上传于 2026-05-10 | 2.3MB | 已分块 156 段</p>
                            </div>
                            <div class="actions">
                                <button class="edit">编辑</button>
                                <button class="delete">删除</button>
                            </div>
                        </div>
                        <div class="knowledge-item">
                            <span class="icon">📝</span>
                            <div class="info">
                                <h4>技术文档.md</h4>
                                <p>上传于 2026-05-09 | 156KB | 已分块 42 段</p>
                            </div>
                            <div class="actions">
                                <button class="edit">编辑</button>
                                <button class="delete">删除</button>
                            </div>
                        </div>
                    </div>
                </div>
                
                <div class="knowledge-content" data-tab="collections">
                    <div style="padding:40px;text-align:center;color:#64748B;">
                        <div style="font-size:48px;margin-bottom:16px;">📁</div>
                        <p>创建知识集合来组织您的文档</p>
                        <button class="settings-btn settings-btn-primary" style="margin-top:16px;" onclick="alert('创建知识集合功能开发中...')">+ 创建集合</button>
                    </div>
                </div>
                
                <div class="knowledge-content" data-tab="config">
                    <div class="info-banner">
                        <h3>⚙️ 知识库配置</h3>
                        <p>配置知识库的索引和检索参数</p>
                    </div>
                    <div class="setting-group">
                        <div class="setting-label">检索模式</div>
                        <select class="setting-input">
                            <option>混合检索（向量 + 关键词）</option>
                            <option>向量检索（语义相似度）</option>
                            <option>关键词检索（BM25）</option>
                        </select>
                    </div>
                    <div class="setting-group">
                        <div class="setting-label">返回数量</div>
                        <input type="number" class="setting-input" value="5" min="1" max="20">
                    </div>
                </div>
            </div>
        </div>
    </div>

    <!-- Prompt Market Modal -->
    <div class="modal-overlay" id="prompt-modal">
        <div class="modal" style="max-width:900px;">
            <div class="modal-header">
                <div class="modal-title">💡 提示词市场</div>
                <button class="modal-close" onclick="closeModal('prompt-modal')">×</button>
            </div>
            
            <div class="modal-content">
                <div class="prompt-card" onclick="usePrompt(this)">
                    <h3>🎯 精确代码生成器</h3>
                    <p>优化代码生成的提示词模板，生成更高质量的代码</p>
                    <div class="tags">
                        <span class="tag">编程</span>
                        <span class="tag">代码优化</span>
                        <span class="tag">高质量</span>
                    </div>
                </div>
                
                <div class="prompt-card" onclick="usePrompt(this)">
                    <h3>📊 数据分析专家</h3>
                    <p>专业的可视化数据分析提示词，支持多种图表类型</p>
                    <div class="tags">
                        <span class="tag">数据分析</span>
                        <span class="tag">可视化</span>
                        <span class="tag">图表</span>
                    </div>
                </div>
                
                <div class="prompt-card" onclick="usePrompt(this)">
                    <h3>📝 技术文档撰写</h3>
                    <p>生成结构清晰、技术规范的技术文档</p>
                    <div class="tags">
                        <span class="tag">文档</span>
                        <span class="tag">技术写作</span>
                        <span class="tag">Markdown</span>
                    </div>
                </div>
                
                <div class="prompt-card" onclick="usePrompt(this)">
                    <h3>🔍 深度研究助手</h3>
                    <p>进行深入研究和分析，提供全面的研究报告</p>
                    <div class="tags">
                        <span class="tag">研究</span>
                        <span class="tag">分析</span>
                        <span class="tag">报告</span>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <!-- Skill Market Modal -->
    <div class="modal-overlay" id="skill-modal">
        <div class="modal" style="max-width:1000px;">
            <div class="modal-header">
                <div class="modal-title">🛠️ Skill 市场</div>
                <button class="modal-close" onclick="closeModal('skill-modal')">×</button>
            </div>
            
            <div class="modal-content">
                <div class="skill-grid">
                    <div class="skill-card">
                        <div class="header">
                            <span class="icon">🔍</span>
                            <h3>网络搜索</h3>
                            <span class="badge">官方</span>
                        </div>
                        <p>实时网络搜索能力，支持 Google、Bing、DuckDuckGo 等搜索引擎</p>
                        <div class="footer">
                            <span class="author">DataAgent</span>
                            <button class="install-btn" onclick="alert('已安装')">已安装</button>
                        </div>
                    </div>
                    
                    <div class="skill-card">
                        <div class="header">
                            <span class="icon">📊</span>
                            <h3>数据可视化</h3>
                            <span class="badge">官方</span>
                        </div>
                        <p>专业的数据可视化技能，支持 Matplotlib、Seaborn、Plotly 等库</p>
                        <div class="footer">
                            <span class="author">DataAgent</span>
                            <button class="install-btn" onclick="alert('已安装')">已安装</button>
                        </div>
                    </div>
                    
                    <div class="skill-card">
                        <div class="header">
                            <span class="icon">📁</span>
                            <h3>文件操作</h3>
                            <span class="badge">官方</span>
                        </div>
                        <p>文件和目录的读取、编辑、管理操作</p>
                        <div class="footer">
                            <span class="author">DataAgent</span>
                            <button class="install-btn" onclick="alert('已安装')">已安装</button>
                        </div>
                    </div>
                    
                    <div class="skill-card">
                        <div class="header">
                            <span class="icon">💻</span>
                            <h3>代码执行</h3>
                            <span class="badge">官方</span>
                        </div>
                        <p>Python 代码的安全执行环境</p>
                        <div class="footer">
                            <span class="author">DataAgent</span>
                            <button class="install-btn" onclick="alert('已安装')">已安装</button>
                        </div>
                    </div>
                    
                    <div class="skill-card">
                        <div class="header">
                            <span class="icon">🌐</span>
                            <h3>浏览器自动化</h3>
                            <span class="badge">官方</span>
                        </div>
                        <p>网页浏览和自动化操作能力</p>
                        <div class="footer">
                            <span class="author">DataAgent</span>
                            <button class="install-btn" onclick="alert('已安装')">已安装</button>
                        </div>
                    </div>
                    
                    <div class="skill-card">
                        <div class="header">
                            <span class="icon">📝</span>
                            <h3>文档处理</h3>
                            <span class="badge">官方</span>
                        </div>
                        <p>PDF、Word、Excel 等文档的读取和处理</p>
                        <div class="footer">
                            <span class="author">DataAgent</span>
                            <button class="install-btn" onclick="alert('已安装')">已安装</button>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <!-- MCP Tools Modal -->
    <div class="modal-overlay" id="mcp-modal">
        <div class="modal" style="max-width:900px;">
            <div class="modal-header">
                <div class="modal-title">🔌 MCP 工具服务</div>
                <button class="modal-close" onclick="closeModal('mcp-modal')">×</button>
            </div>
            
            <div class="modal-content">
                <div class="info-banner">
                    <h3>🔌 MCP (Model Context Protocol)</h3>
                    <p>MCP 是一种开放协议，让 AI 模型能够安全地与外部工具和数据源连接。配置您的 MCP 服务器来扩展 Data Agent 的能力。</p>
                </div>
                
                <div class="mcp-service">
                    <h3>🌤️ 天气查询服务</h3>
                    <p>获取实时天气信息和预报</p>
                    <div class="config">
                        <input type="text" class="setting-input" placeholder="服务器地址" value="https://mcp.weather.com">
                        <button class="settings-btn settings-btn-primary">连接</button>
                    </div>
                </div>
                
                <div class="mcp-service">
                    <h3>🗺️ 地图位置服务</h3>
                    <p>地理位置查询和地图相关功能</p>
                    <div class="config">
                        <input type="text" class="setting-input" placeholder="服务器地址">
                        <button class="settings-btn settings-btn-primary">连接</button>
                    </div>
                </div>
                
                <div class="mcp-service">
                    <h3>📧 邮件服务</h3>
                    <p>邮件发送和接收功能</p>
                    <div class="config">
                        <input type="text" class="setting-input" placeholder="SMTP 服务器地址">
                        <button class="settings-btn settings-btn-primary">连接</button>
                    </div>
                </div>
                
                <button class="settings-btn settings-btn-primary" style="width:100%;margin-top:20px;" onclick="alert('添加自定义 MCP 服务器功能开发中...')">+ 添加自定义 MCP 服务器</button>
            </div>
        </div>
    </div>

    <!-- Help Modal -->
    <div class="modal-overlay" id="help-modal">
        <div class="modal" style="max-width:1000px;">
            <div class="modal-header">
                <div class="modal-title">❓ 使用说明</div>
                <button class="modal-close" onclick="closeModal('help-modal')">×</button>
            </div>
            
            <div class="modal-content" style="padding:32px;">
                <div class="help-section">
                    <h2>🤖 Data Agent - 万能智能助手</h2>
                    <p>Data Agent 是一款功能强大的万能智能助手，能够自动识别您的需求并调用合适的工具来完成各种任务。</p>
                    
                    <div class="feature-list">
                        <div class="feature-item">
                            <div class="icon">🧠</div>
                            <h4>智能意图识别</h4>
                            <p>自动分析需求类型</p>
                        </div>
                        <div class="feature-item">
                            <div class="icon">🐍</div>
                            <h4>Python 执行</h4>
                            <p>代码编写与运行</p>
                        </div>
                        <div class="feature-item">
                            <div class="icon">📊</div>
                            <h4>图表生成</h4>
                            <p>数据可视化</p>
                        </div>
                        <div class="feature-item">
                            <div class="icon">🔍</div>
                            <h4>网络搜索</h4>
                            <p>实时信息检索</p>
                        </div>
                        <div class="feature-item">
                            <div class="icon">📝</div>
                            <h4>文档处理</h4>
                            <p>PDF/Word/TXT</p>
                        </div>
                        <div class="feature-item">
                            <div class="icon">💻</div>
                            <h4>代码执行</h4>
                            <p>安全沙箱环境</p>
                        </div>
                    </div>
                </div>
                
                <div class="help-section">
                    <h2>🚀 快速开始</h2>
                    
                    <h3>1. 配置模型</h3>
                    <p>点击侧边栏的「⚙️ 设置」按钮，进入「🤖 模型配置」标签页，选择您想要使用的 AI 模型和 API。</p>
                    <p>支持的模型包括：</p>
                    <ul>
                        <li><strong>🇨🇳 国内模型：</strong>阿里通义千问、百度文心一言、字节豆包、腾讯混元、DeepSeek、智谱GLM、月之暗面Kimi 等</li>
                        <li><strong>🌍 国际模型：</strong>OpenAI GPT、Anthropic Claude、Google Gemini、xAI Grok、Meta Llama 等</li>
                        <li><strong>💻 本地部署：</strong>Ollama、LM Studio、LLaMAfile 等</li>
                    </ul>
                    
                    <h3>2. 开始对话</h3>
                    <p>直接在对话框中输入您的需求，Data Agent 会自动识别意图并处理。例如：</p>
                    <pre><code>帮我分析这份销售数据并生成图表
写一个排序算法并可视化执行过程
搜索最新的 AI 技术发展趋势
帮我整理会议记录为 Markdown 格式</code></pre>
                    
                    <h3>3. 查看思维链</h3>
                    <p>Data Agent 会实时展示思维链，让您清楚看到 AI 是如何分析问题、选择工具和执行操作的。点击思维链卡片可以展开查看详细信息。</p>
                </div>
                
                <div class="help-section">
                    <h2>📚 功能模块</h2>
                    
                    <h3>💬 对话</h3>
                    <p>主要的对话界面，支持多轮对话和上下文记忆。</p>
                    
                    <h3>📚 知识库</h3>
                    <p>上传和管理您的文档，Data Agent 可以基于这些文档回答问题。</p>
                    <ul>
                        <li>支持 PDF、Word、TXT、Markdown 等格式</li>
                        <li>自动分块和向量化</li>
                        <li>智能检索和问答</li>
                    </ul>
                    
                    <h3>💡 提示词市场</h3>
                    <p>精选的提示词模板，帮助您更好地使用 AI。</p>
                    
                    <h3>🛠️ Skill 市场</h3>
                    <p>扩展 Data Agent 的技能，包括：</p>
                    <ul>
                        <li>网络搜索 - 实时信息检索</li>
                        <li>数据可视化 - 专业图表生成</li>
                        <li>文件操作 - 读写管理文件</li>
                        <li>代码执行 - Python 安全运行环境</li>
                        <li>浏览器自动化 - 网页操作</li>
                        <li>文档处理 - PDF/Word/Excel</li>
                    </ul>
                    
                    <h3>🔌 MCP 工具服务</h3>
                    <p>通过 MCP (Model Context Protocol) 连接外部工具和数据源。</p>
                </div>
                
                <div class="help-section">
                    <h2>💡 使用技巧</h2>
                    
                    <h3>清晰描述需求</h3>
                    <p>越详细的需求描述，AI 越能准确理解并给出满意的结果。</p>
                    
                    <h3>分步骤处理复杂任务</h3>
                    <p>对于复杂任务，可以分步骤进行，每一步给出明确的指示。</p>
                    
                    <h3>利用沙箱环境</h3>
                    <p>需要数据处理或生成图表时，可以直接让 AI 执行 Python 代码，结果会直接显示在界面中。</p>
                    
                    <h3>使用提示词模板</h3>
                    <p>在「提示词市场」中找到适合的模板，可以快速获得高质量的输出。</p>
                </div>
                
                <div class="help-section">
                    <h2>⚙️ 设置选项</h2>
                    
                    <h3>沙箱环境</h3>
                    <p>配置代码执行环境，包括超时时间和网络访问权限。建议保持默认设置以确保安全性。</p>
                    
                    <h3>知识库</h3>
                    <p>配置向量数据库和嵌入模型，以获得更好的文档检索效果。</p>
                    
                    <h3>对话设置</h3>
                    <p>管理对话历史和 Agent 的行为参数。</p>
                    
                    <h3>显示设置</h3>
                    <p>自定义界面外观，包括主题模式和思维链显示等。</p>
                </div>
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
                        我是您的<strong>万能智能助手</strong>，能够自动识别您的需求并调用合适的工具来完成各种任务。<br><br>
                        
                        <strong>🧠 智能自动化：</strong><br>
                        • 自动识别意图，无需手动选择模式<br>
                        • 智能调度最佳工具组合<br><br>
                        
                        <strong>📦 强大能力：</strong><br>
                        • Python 编程与执行<br>
                        • 图表生成与下载<br>
                        • 网络搜索<br>
                        • 文档处理<br>
                        • 等等...<br><br>
                        
                        <strong>💡 使用方式：</strong><br>
                        直接输入您的需求即可！<br>
                        例如："帮我分析数据并生成图表"<br><br>
                        
                        点击左侧菜单探索更多功能！🎯
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
            🟢 在线 | WebSocket 连接 | 沙箱已启用 | 思维链可视化 | Data Agent v2.0
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
            };

            ws.onclose = function() {
                document.getElementById('ws-status').textContent = '🔴 重连中';
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
                currentThinkingChain = createThinkingChain(title);
            }

            if (currentThinkingChain) {
                addThinkingStep(currentThinkingChain, {
                    phase: phase,
                    title: title,
                    content: content,
                    tools: data.tools || null,
                });
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
            if (result.images && result.images.length > 0) {
                for (const img of result.images) {
                    html += '<div class="sandbox-output">';
                    html += '<div class="sandbox-header"><div class="dots"><span class="dot red"></span><span class="dot yellow"></span><span class="dot green"></span></div><span>📊 ' + escapeHtml(img.name) + '</span></div>';
                    html += '<div class="sandbox-image">';
                    html += '<img src="data:image/png;base64,' + img.data + '" alt="' + escapeHtml(img.name) + '">';
                    html += '<a href="data:image/png;base64,' + img.data + '" download="' + escapeHtml(img.name) + '" class="download-btn">⬇️ 下载图表</a>';
                    html += '</div></div>';
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
                    toolsHtml += '<span class="step-tool-tag">🔧 ' + escapeHtml(tool.name) + '</span>';
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

        function showMainChat() {
            document.querySelectorAll('.nav-item').forEach(item => item.classList.remove('active'));
            event.currentTarget.classList.add('active');
            toggleSidebar();
        }

        // ===== Modals =====
        function openModal(modalId) {
            document.getElementById(modalId).classList.add('show');
            toggleSidebar();
        }

        function closeModal(modalId) {
            document.getElementById(modalId).classList.remove('show');
        }

        // ===== Settings Functions =====
        function switchSettingTab(tabName) {
            document.querySelectorAll('.settings-tab').forEach(tab => tab.classList.remove('active'));
            document.querySelectorAll('.settings-tab-content').forEach(content => content.classList.remove('active'));
            
            document.querySelector('.settings-tab[data-tab="' + tabName + '"]').classList.add('active');
            document.querySelector('.settings-tab-content[data-tab="' + tabName + '"]').classList.add('active');
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
            document.getElementById('setting-top-p').value = settings.llm.top_p;
            
            document.getElementById('setting-sandbox-enabled').checked = settings.sandbox.enabled;
            document.getElementById('setting-sandbox-timeout').value = settings.sandbox.timeout;
            document.getElementById('setting-sandbox-network').checked = settings.sandbox.allow_network;
            
            document.getElementById('setting-knowledge-enabled').checked = settings.knowledge_base.enabled;
            document.getElementById('setting-vector-db').value = settings.knowledge_base.vector_db;
            document.getElementById('setting-chunk-size').value = settings.knowledge_base.chunk_size;
            document.getElementById('setting-overlap').value = settings.knowledge_base.overlap;
            document.getElementById('setting-embedding-model').value = settings.knowledge_base.embedding_model;
            
            document.getElementById('setting-history-enabled').checked = settings.conversation.history_enabled;
            document.getElementById('setting-max-history').value = settings.conversation.max_history;
            document.getElementById('setting-auto-title').checked = settings.conversation.auto_title;
            document.getElementById('setting-max-steps').value = settings.agent.max_steps;
            
            document.getElementById('setting-theme').value = settings.display.theme;
            document.getElementById('setting-thinking-chain').checked = settings.display.thinking_chain;
            document.getElementById('setting-code-highlight').checked = settings.display.code_highlight;
            document.getElementById('setting-markdown-render').checked = settings.display.markdown_render;
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
                    top_p: parseFloat(document.getElementById('setting-top-p').value),
                    stream: false
                },
                sandbox: {
                    enabled: document.getElementById('setting-sandbox-enabled').checked,
                    timeout: parseInt(document.getElementById('setting-sandbox-timeout').value),
                    allow_network: document.getElementById('setting-sandbox-network').checked
                },
                knowledge_base: {
                    enabled: document.getElementById('setting-knowledge-enabled').checked,
                    vector_db: document.getElementById('setting-vector-db').value,
                    chunk_size: parseInt(document.getElementById('setting-chunk-size').value),
                    overlap: parseInt(document.getElementById('setting-overlap').value),
                    embedding_model: document.getElementById('setting-embedding-model').value
                },
                conversation: {
                    history_enabled: document.getElementById('setting-history-enabled').checked,
                    max_history: parseInt(document.getElementById('setting-max-history').value),
                    auto_title: document.getElementById('setting-auto-title').checked
                },
                display: {
                    theme: document.getElementById('setting-theme').value,
                    thinking_chain: document.getElementById('setting-thinking-chain').checked,
                    code_highlight: document.getElementById('setting-code-highlight').checked,
                    markdown_render: document.getElementById('setting-markdown-render').checked
                },
                agent: {
                    max_steps: parseInt(document.getElementById('setting-max-steps').value),
                    auto_mode: true,
                    reasoning_mode: "auto"
                }
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

        async function resetSettings() {
            if (confirm('确定要重置为默认设置吗？')) {
                const defaultSettings = {
                    llm: { provider: "aliyun", model: "qwen-plus-latest", base_url: "https://dashscope.aliyuncs.com/compatible-mode/v1", api_key: "", max_tokens: 4096, temperature: 0.7, top_p: 0.9, stream: false },
                    sandbox: { enabled: true, timeout: 60, allow_network: false },
                    knowledge_base: { enabled: false, vector_db: "sqlite", chunk_size: 500, overlap: 50, embedding_model: "text-embedding-v3" },
                    conversation: { history_enabled: true, max_history: 50, auto_title: true },
                    display: { theme: "dark", thinking_chain: true, code_highlight: true, markdown_render: true },
                    agent: { max_steps: 5, auto_mode: true, reasoning_mode: "auto" }
                };
                
                await fetch('/api/settings', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(defaultSettings)
                });
                
                populateSettings(defaultSettings);
                addMessage('✅ 设置已重置为默认', 'system');
            }
        }

        // ===== Knowledge Base Functions =====
        function switchKnowledgeTab(tabName) {
            document.querySelectorAll('.knowledge-tab').forEach(tab => tab.classList.remove('active'));
            document.querySelectorAll('.knowledge-content').forEach(content => content.classList.remove('active'));
            
            event.currentTarget.classList.add('active');
            document.querySelector('.knowledge-content[data-tab="' + tabName + '"]').classList.add('active');
        }

        // ===== Prompt Market Functions =====
        function usePrompt(card) {
            const title = card.querySelector('h3').textContent;
            addMessage('我想使用"' + title + '"提示词模板', 'user');
            closeModal('prompt-modal');
        }

        // Load settings on page load
        window.addEventListener('DOMContentLoaded', function() {
            loadSettings();
        });

        // Close modals on escape key
        document.addEventListener('keydown', function(e) {
            if (e.key === 'Escape') {
                document.querySelectorAll('.modal-overlay.show').forEach(modal => {
                    modal.classList.remove('show');
                });
            }
        });
    </script>
</body>
</html>
    """
    return HTMLResponse(html_content)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
