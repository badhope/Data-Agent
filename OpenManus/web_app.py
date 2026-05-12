"""DataAgent Web Interface with Sandbox & Thinking Chain Visualization"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
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
        agent.max_steps = 5

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


HTML_TEMPLATE = """
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

        /* ===== Sidebar Btn ===== */
        .sidebar-btn {
            width: 100%;
            padding: 8px 12px;
            background: #334155;
            border: 1px solid #475569;
            border-radius: 7px;
            color: #F1F5F9;
            font-size: 12px;
            cursor: pointer;
            text-align: left;
            margin-bottom: 5px;
            transition: all 0.2s;
            display: flex;
            align-items: center;
            gap: 6px;
        }
        .sidebar-btn:hover { background: #4F46E5; border-color: #4F46E5; }

        /* ===== Tool Card ===== */
        .tool-card {
            background: #1E293B;
            border: 1px solid #334155;
            border-radius: 7px;
            padding: 8px 12px;
            margin-bottom: 5px;
            cursor: pointer;
            transition: all 0.2s;
            display: flex;
            align-items: center;
            gap: 8px;
        }
        .tool-card:hover { border-color: #4F46E5; }
        .tool-card .tool-icon { font-size: 16px; flex-shrink: 0; }
        .tool-card .tool-info h5 { color: white; font-size: 12px; font-weight: 500; }
        .tool-card .tool-info p { color: #94A3B8; font-size: 10px; }

        .status-badge {
            display: inline-block;
            padding: 2px 8px;
            background: #10B981;
            border-radius: 10px;
            font-size: 10px;
            color: white;
            margin-top: 6px;
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
                    <span>📋 快捷操作</span><span class="arrow">▶</span>
                </div>
                <div class="collapse-body"><div class="collapse-body-inner">
                    <button class="sidebar-btn" onclick="showConfig()">⚙️ 查看配置</button>
                    <button class="sidebar-btn" onclick="showTools()">🛠️ 查看所有工具</button>
                    <button class="sidebar-btn" onclick="showSandboxInfo()">📦 沙箱环境</button>
                </div></div>
            </div>
            <div class="collapse-section">
                <div class="collapse-header" onclick="toggleSection(this)">
                    <span>🌐 网页工具</span><span class="arrow">▶</span>
                </div>
                <div class="collapse-body"><div class="collapse-body-inner">
                    <div class="tool-card" onclick="useSearch('web')">
                        <span class="tool-icon">🔍</span>
                        <div class="tool-info"><h5>网络搜索</h5><p>百度 / DuckDuckGo</p></div>
                    </div>
                    <div class="tool-card" onclick="useBrowser()">
                        <span class="tool-icon">🌐</span>
                        <div class="tool-info"><h5>浏览器自动化</h5><p>Browser Use</p></div>
                    </div>
                </div></div>
            </div>
            <div class="collapse-section">
                <div class="collapse-header" onclick="toggleSection(this)">
                    <span>💻 终端工具</span><span class="arrow">▶</span>
                </div>
                <div class="collapse-body"><div class="collapse-body-inner">
                    <div class="tool-card" onclick="useTerminal('bash')">
                        <span class="tool-icon">⚡</span>
                        <div class="tool-info"><h5>Bash 命令</h5><p>执行 Shell 命令</p></div>
                    </div>
                    <div class="tool-card" onclick="useTerminal('python')">
                        <span class="tool-icon">🐍</span>
                        <div class="tool-info"><h5>Python 执行</h5><p>运行 Python 代码</p></div>
                    </div>
                </div></div>
            </div>
            <div class="collapse-section">
                <div class="collapse-header" onclick="toggleSection(this)">
                    <span>🚀 高级工具</span><span class="arrow">▶</span>
                </div>
                <div class="collapse-body"><div class="collapse-body-inner">
                    <div class="tool-card" onclick="useAdvanced('chart')">
                        <span class="tool-icon">📈</span>
                        <div class="tool-info"><h5>图表可视化</h5><p>数据图表生成</p></div>
                    </div>
                    <div class="tool-card" onclick="useAdvanced('planning')">
                        <span class="tool-icon">🧠</span>
                        <div class="tool-info"><h5>任务规划</h5><p>多步骤任务规划</p></div>
                    </div>
                </div></div>
            </div>
            <div class="collapse-section">
                <div class="collapse-header" onclick="toggleSection(this)">
                    <span>📊 系统信息</span><span class="arrow">▶</span>
                </div>
                <div class="collapse-body"><div class="collapse-body-inner" style="color:#94A3B8;font-size:11px;line-height:1.8;">
                    <p>模型: qwen-plus-latest</p>
                    <p>API: 阿里百炼</p>
                    <p>沙箱: 已启用</p>
                    <p>Python: 已配置</p>
                    <p>状态: <span id="sys-status">正常运行</span></p>
                </div></div>
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
                        请输入您的需求开始体验！
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
            addMessage('👋 你好！我是 <strong>Data</strong>，您的智能助手。请描述您的需求！', 'assistant');
        }

        // ===== Sidebar =====
        function toggleSidebar() {
            document.getElementById('sidebar').classList.toggle('open');
            document.getElementById('overlay').classList.toggle('show');
        }

        function toggleSection(headerEl) {
            headerEl.parentElement.classList.toggle('open');
        }

        function selectAgent(agent) {
            currentAgent = agent;
            const names = { 'data': 'Data 通用代理', 'browser': '浏览器代理', 'swe': 'SWE 软件工程代理', 'analysis': '数据分析代理' };
            currentAgentSpan.textContent = names[agent];
            document.querySelectorAll('.agent-card').forEach(c => c.classList.remove('active'));
            const el = document.getElementById('agent-' + agent);
            if (el) el.classList.add('active');
            addMessage('已切换到 <strong>' + names[agent] + '</strong>', 'system');
        }

        // ===== Quick Actions =====
        function showConfig() {
            addMessage('⚙️ <strong>当前配置：</strong><br><br>• 模型: qwen-plus-latest<br>• API: 阿里百炼<br>• 代理: ' + currentAgent + '<br>• 沙箱: 已启用<br>• 思维链: 可视化', 'assistant');
        }

        function showTools() {
            addMessage('🛠️ <strong>可用工具：</strong><br><br>🌐 <strong>网页：</strong>网络搜索 / 浏览器自动化 / 网页爬取<br>📁 <strong>文件：</strong>读取 / 写入 / 浏览 / 编辑<br>💻 <strong>终端：</strong>Bash / Python<br>🚀 <strong>高级：</strong>图表 / 规划 / 沙箱 / MCP', 'assistant');
        }

        function showSandboxInfo() {
            addMessage('📦 <strong>沙箱环境信息：</strong><br><br>• Python 环境: 已配置 (matplotlib, pandas, numpy)<br>• 工作目录: /tmp/dataagent_sandbox_<br>• 超时限制: 30秒<br>• 图表输出: 支持 PNG<br>• 安全隔离: 子进程执行', 'assistant');
        }

        function useSearch(engine) {
            inputEl.value = '帮我搜索 ';
            inputEl.focus();
        }

        function useBrowser() {
            addMessage('🌐 浏览器自动化已就绪！请输入网页操作指令。', 'assistant');
        }

        function useTerminal(type) {
            if (type === 'python') {
                inputEl.value = '运行 Python 代码: ';
            } else {
                inputEl.value = '执行命令: ';
            }
            inputEl.focus();
        }

        function useAdvanced(tool) {
            const msgs = {
                'chart': '📈 请提供数据，我将为您生成图表！例如："用Python画一个折线图"',
                'planning': '🧠 请描述您的复杂任务，我将规划执行步骤。',
            };
            addMessage(msgs[tool] || '工具已就绪', 'assistant');
        }

        selectAgent('data');
    </script>
</body>
</html>
"""


@app.get("/", response_class=HTMLResponse)
async def get_index():
    return HTMLResponse(content=HTML_TEMPLATE)


@app.get("/api/sandbox/python")
async def sandbox_python(code: str = ""):
    if not code:
        return JSONResponse({"error": "No code provided"}, status_code=400)
    result = await sandbox.execute_python(code)
    return JSONResponse({"result": result})


@app.get("/api/sandbox/bash")
async def sandbox_bash(command: str = ""):
    if not command:
        return JSONResponse({"error": "No command provided"}, status_code=400)
    result = await sandbox.execute_bash(command)
    return JSONResponse({"result": result})


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()

    client_id = f"client_{id(websocket)}"
    active_connections[client_id] = websocket

    try:
        while True:
            data = await websocket.receive_json()
            content = data.get('content', '')
            agent_type = data.get('agent', 'data')

            await run_agent_with_thinking(websocket, content, agent_type)

    except WebSocketDisconnect:
        del active_connections[client_id]


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
