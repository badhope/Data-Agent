"""Simple Web Interface for DataAgent using FastAPI"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
import asyncio
from typing import Dict

app = FastAPI(title="Data Agent", description="DataAgent Web Interface")

active_connections: Dict[str, WebSocket] = {}

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
            left: 0;
            top: 0;
            z-index: 100;
            transition: transform 0.3s ease;
        }

        .sidebar-header {
            padding: 16px 18px;
            border-bottom: 1px solid #334155;
            flex-shrink: 0;
        }

        .sidebar-header h2 {
            color: white;
            font-size: 17px;
            margin-bottom: 4px;
        }

        .sidebar-header p {
            color: #94A3B8;
            font-size: 11px;
        }

        .sidebar-body {
            flex: 1;
            overflow-y: auto;
            padding: 12px 14px;
        }

        .sidebar-body::-webkit-scrollbar { width: 3px; }
        .sidebar-body::-webkit-scrollbar-thumb { background: #475569; border-radius: 2px; }

        /* ===== Collapsible Section ===== */
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

        .collapse-header:hover {
            background: rgba(79,70,229,0.15);
        }

        .collapse-header .arrow {
            transition: transform 0.25s;
            font-size: 10px;
            color: #94A3B8;
        }

        .collapse-section.open .collapse-header .arrow {
            transform: rotate(90deg);
        }

        .collapse-body {
            max-height: 0;
            overflow: hidden;
            transition: max-height 0.3s ease;
        }

        .collapse-section.open .collapse-body {
            max-height: 600px;
        }

        .collapse-body-inner {
            padding: 6px 10px 10px;
        }

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

        /* ===== Sidebar Button ===== */
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

        /* ===== Status Badge ===== */
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

        /* ===== Header ===== */
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
            max-width: 75%;
            padding: 10px 14px;
            border-radius: 14px;
            line-height: 1.6;
            font-size: 13px;
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

        /* ===== Input Area - FIXED at bottom ===== */
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

        .send-btn:disabled {
            background: #334155;
            color: #64748B;
            cursor: not-allowed;
        }

        /* ===== Status Bar ===== */
        .status-bar {
            flex-shrink: 0;
            text-align: center;
            padding: 5px;
            font-size: 10px;
            color: #64748B;
            background: #0F172A;
            border-top: 1px solid #1E293B;
        }

        /* ===== Typing Indicator ===== */
        .typing-indicator {
            display: none;
            padding: 8px 14px;
            color: #94A3B8;
            font-size: 12px;
        }

        .typing-indicator.show { display: flex; align-items: center; gap: 6px; }

        .typing-dots span {
            display: inline-block;
            width: 6px;
            height: 6px;
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

        /* ===== Animations ===== */
        @keyframes slideIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }

        /* ===== Mobile ===== */
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

    <!-- ===== Sidebar ===== -->
    <div class="sidebar" id="sidebar">
        <div class="sidebar-header">
            <h2>🤖 Data Agent</h2>
            <p>智能助手控制面板</p>
            <span class="status-badge" id="ws-status">🟢 在线</span>
        </div>

        <div class="sidebar-body">
            <!-- Agent Types -->
            <div class="collapse-section open">
                <div class="collapse-header" onclick="toggleSection(this)">
                    <span>🤖 代理模式</span>
                    <span class="arrow">▶</span>
                </div>
                <div class="collapse-body">
                    <div class="collapse-body-inner">
                        <div class="agent-card active" onclick="selectAgent('data')" id="agent-data">
                            <h4>📋 Data 通用代理</h4>
                            <p>多工具协同处理复杂任务</p>
                        </div>
                        <div class="agent-card" onclick="selectAgent('browser')" id="agent-browser">
                            <h4>🌐 浏览器代理</h4>
                            <p>自动化网页操作</p>
                        </div>
                        <div class="agent-card" onclick="selectAgent('swe')" id="agent-swe">
                            <h4>💻 SWE 软件工程代理</h4>
                            <p>代码开发与调试</p>
                        </div>
                        <div class="agent-card" onclick="selectAgent('analysis')" id="agent-analysis">
                            <h4>📊 数据分析代理</h4>
                            <p>数据处理与可视化</p>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Quick Actions -->
            <div class="collapse-section">
                <div class="collapse-header" onclick="toggleSection(this)">
                    <span>📋 快捷操作</span>
                    <span class="arrow">▶</span>
                </div>
                <div class="collapse-body">
                    <div class="collapse-body-inner">
                        <button class="sidebar-btn" onclick="showLogs()">📊 查看日志</button>
                        <button class="sidebar-btn" onclick="showConfig()">⚙️ 查看配置</button>
                        <button class="sidebar-btn" onclick="showTools()">🛠️ 查看所有工具</button>
                        <button class="sidebar-btn" onclick="showHistory()">📜 对话历史</button>
                    </div>
                </div>
            </div>

            <!-- Web Tools -->
            <div class="collapse-section">
                <div class="collapse-header" onclick="toggleSection(this)">
                    <span>🌐 网页工具</span>
                    <span class="arrow">▶</span>
                </div>
                <div class="collapse-body">
                    <div class="collapse-body-inner">
                        <div class="tool-card" onclick="useSearch('web')">
                            <span class="tool-icon">🔍</span>
                            <div class="tool-info"><h5>网络搜索</h5><p>百度 / DuckDuckGo</p></div>
                        </div>
                        <div class="tool-card" onclick="useBrowser('auto')">
                            <span class="tool-icon">🌐</span>
                            <div class="tool-info"><h5>浏览器自动化</h5><p>Browser Use</p></div>
                        </div>
                        <div class="tool-card" onclick="useSearch('baidu')">
                            <span class="tool-icon">📝</span>
                            <div class="tool-info"><h5>百度搜索</h5><p>中文搜索引擎</p></div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- File Tools -->
            <div class="collapse-section">
                <div class="collapse-header" onclick="toggleSection(this)">
                    <span>📁 文件工具</span>
                    <span class="arrow">▶</span>
                </div>
                <div class="collapse-body">
                    <div class="collapse-body-inner">
                        <div class="tool-card" onclick="useFile('read')">
                            <span class="tool-icon">📖</span>
                            <div class="tool-info"><h5>读取文件</h5><p>读取文件内容</p></div>
                        </div>
                        <div class="tool-card" onclick="useFile('write')">
                            <span class="tool-icon">✏️</span>
                            <div class="tool-info"><h5>写入文件</h5><p>创建或编辑文件</p></div>
                        </div>
                        <div class="tool-card" onclick="useFile('browse')">
                            <span class="tool-icon">📂</span>
                            <div class="tool-info"><h5>浏览目录</h5><p>查看目录结构</p></div>
                        </div>
                        <div class="tool-card" onclick="useFile('edit')">
                            <span class="tool-icon">🔧</span>
                            <div class="tool-info"><h5>编辑文件</h5><p>代码编辑器</p></div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Terminal Tools -->
            <div class="collapse-section">
                <div class="collapse-header" onclick="toggleSection(this)">
                    <span>💻 终端工具</span>
                    <span class="arrow">▶</span>
                </div>
                <div class="collapse-body">
                    <div class="collapse-body-inner">
                        <div class="tool-card" onclick="useTerminal('bash')">
                            <span class="tool-icon">⚡</span>
                            <div class="tool-info"><h5>Bash 命令</h5><p>执行 Shell 命令</p></div>
                        </div>
                        <div class="tool-card" onclick="useTerminal('python')">
                            <span class="tool-icon">🐍</span>
                            <div class="tool-info"><h5>Python 执行</h5><p>运行 Python 代码</p></div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Advanced Tools -->
            <div class="collapse-section">
                <div class="collapse-header" onclick="toggleSection(this)">
                    <span>🚀 高级工具</span>
                    <span class="arrow">▶</span>
                </div>
                <div class="collapse-body">
                    <div class="collapse-body-inner">
                        <div class="tool-card" onclick="useAdvanced('chart')">
                            <span class="tool-icon">📈</span>
                            <div class="tool-info"><h5>图表可视化</h5><p>数据图表生成</p></div>
                        </div>
                        <div class="tool-card" onclick="useAdvanced('planning')">
                            <span class="tool-icon">🧠</span>
                            <div class="tool-info"><h5>任务规划</h5><p>多步骤任务规划</p></div>
                        </div>
                        <div class="tool-card" onclick="useAdvanced('sandbox')">
                            <span class="tool-icon">🔒</span>
                            <div class="tool-info"><h5>沙箱环境</h5><p>安全隔离执行</p></div>
                        </div>
                        <div class="tool-card" onclick="useAdvanced('mcp')">
                            <span class="tool-icon">🔌</span>
                            <div class="tool-info"><h5>MCP 服务</h5><p>模型上下文协议</p></div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- System Info -->
            <div class="collapse-section">
                <div class="collapse-header" onclick="toggleSection(this)">
                    <span>📊 系统信息</span>
                    <span class="arrow">▶</span>
                </div>
                <div class="collapse-body">
                    <div class="collapse-body-inner" style="color:#94A3B8;font-size:11px;line-height:1.8;">
                        <p>模型: qwen-plus-latest</p>
                        <p>API: 阿里百炼</p>
                        <p>工具数: 14+</p>
                        <p>状态: <span id="sys-status">正常运行</span></p>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <!-- ===== Main Content ===== -->
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
                        我有多种代理模式和丰富的工具可以帮助您：<br><br>
                        <strong>🤖 代理模式：</strong><br>
                        • 📋 Data 通用代理 - 多工具协同<br>
                        • 🌐 浏览器代理 - 网页自动化<br>
                        • 💻 SWE 代理 - 软件工程<br>
                        • 📊 数据分析代理 - 数据处理<br><br>
                        请从左侧选择功能或直接输入您的需求！
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
            🟢 在线 | WebSocket | 14+ 工具 | Data Agent v1.0
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

        // ===== WebSocket =====
        function connectWS() {
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            ws = new WebSocket(protocol + '//' + window.location.host + '/ws');

            ws.onopen = function() {
                console.log('WS connected');
                document.getElementById('ws-status').textContent = '🟢 在线';
                document.getElementById('sys-status').textContent = '正常运行';
            };

            ws.onmessage = function(event) {
                try {
                    const data = JSON.parse(event.data);
                    hideTyping();
                    isProcessing = false;
                    sendBtn.disabled = false;
                    addMessage(data.content, data.sender || 'assistant');
                } catch(e) {
                    hideTyping();
                    isProcessing = false;
                    sendBtn.disabled = false;
                    addMessage(event.data, 'assistant');
                }
            };

            ws.onerror = function(err) {
                console.error('WS error', err);
                hideTyping();
                isProcessing = false;
                sendBtn.disabled = false;
            };

            ws.onclose = function() {
                console.log('WS closed, reconnecting...');
                document.getElementById('ws-status').textContent = '🔴 重连中';
                document.getElementById('sys-status').textContent = '重连中...';
                setTimeout(connectWS, 3000);
            };
        }

        connectWS();

        // ===== Sidebar Toggle =====
        function toggleSidebar() {
            const sidebar = document.getElementById('sidebar');
            const overlay = document.getElementById('overlay');
            sidebar.classList.toggle('open');
            overlay.classList.toggle('show');
        }

        // ===== Collapsible Sections =====
        function toggleSection(headerEl) {
            const section = headerEl.parentElement;
            section.classList.toggle('open');
        }

        // ===== Agent Selection =====
        function selectAgent(agent) {
            currentAgent = agent;
            const names = {
                'data': 'Data 通用代理',
                'browser': '浏览器代理',
                'swe': 'SWE 软件工程代理',
                'analysis': '数据分析代理'
            };
            currentAgentSpan.textContent = names[agent];
            document.querySelectorAll('.agent-card').forEach(c => c.classList.remove('active'));
            const el = document.getElementById('agent-' + agent);
            if (el) el.classList.add('active');
            addMessage('已切换到 <strong>' + names[agent] + '</strong>，请描述您的任务。', 'system');
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

        function hideTyping() {
            typingEl.classList.remove('show');
        }

        // ===== Send Message =====
        function sendMessage() {
            const content = inputEl.value.trim();
            if (!content) return;

            if (!ws || ws.readyState !== WebSocket.OPEN) {
                addMessage('⚠️ 未连接到服务器，正在尝试重连...', 'system');
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
            showTyping();

            try {
                ws.send(JSON.stringify({
                    content: content,
                    agent: currentAgent
                }));
            } catch(e) {
                hideTyping();
                isProcessing = false;
                sendBtn.disabled = false;
                addMessage('❌ 发送失败: ' + e.message, 'system');
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
            addMessage('👋 你好！我是 <strong>Data</strong>，您的智能助手。请描述您的需求！', 'assistant');
        }

        // ===== Quick Actions =====
        function showLogs() {
            addMessage('📊 <strong>最近操作日志：</strong><br><br>• 系统启动成功<br>• WebSocket 连接建立<br>• 代理已就绪<br>• 等待用户输入...', 'assistant');
        }

        function showConfig() {
            addMessage('⚙️ <strong>当前配置：</strong><br><br>• 模型: qwen-plus-latest<br>• API: 阿里百炼<br>• 代理模式: ' + currentAgent + '<br>• 工具数: 14+', 'assistant');
        }

        function showTools() {
            addMessage('🛠️ <strong>可用工具列表：</strong><br><br><strong>🌐 网页工具：</strong><br>• 🔍 网络搜索 - 百度/DuckDuckGo<br>• 🌐 浏览器自动化 - Browser Use<br>• 📝 网页爬取 - Crawl4AI<br><br><strong>📁 文件工具：</strong><br>• 📖 读取文件<br>• ✏️ 写入文件<br>• 📂 浏览目录<br>• 🔧 编辑文件<br><br><strong>💻 终端工具：</strong><br>• ⚡ Bash 命令<br>• 🐍 Python 执行<br><br><strong>🚀 高级工具：</strong><br>• 📈 图表可视化<br>• 🧠 任务规划<br>• 🔒 沙箱环境<br>• 🔌 MCP 服务', 'assistant');
        }

        function showHistory() {
            addMessage('📜 <strong>对话历史：</strong><br><br>当前会话暂无历史记录。', 'assistant');
        }

        // ===== Tool Shortcuts =====
        function useSearch(engine) {
            const labels = { 'web': '帮我搜索 ', 'baidu': '用百度搜索 ' };
            inputEl.value = labels[engine] || '搜索 ';
            inputEl.focus();
        }

        function useBrowser(mode) {
            addMessage('🌐 <strong>浏览器自动化工具已就绪！</strong><br><br>请输入指令，例如：<br>• "打开网页 https://example.com"<br>• "搜索 Python 教程"', 'assistant');
        }

        function useFile(action) {
            const templates = {
                'read': '读取文件 /workspace/test.txt',
                'write': '创建文件 test.txt，内容：Hello Data',
                'browse': '浏览目录 /workspace',
                'edit': '编辑文件 /workspace/test.txt'
            };
            inputEl.value = templates[action] || '';
            inputEl.focus();
        }

        function useTerminal(type) {
            const templates = {
                'bash': '执行命令 ls -la',
                'python': '运行 Python 代码 print("Hello Data")'
            };
            inputEl.value = templates[type] || '';
            inputEl.focus();
        }

        function useAdvanced(tool) {
            const msgs = {
                'chart': '📈 <strong>图表可视化工具已就绪！</strong><br><br>请提供数据，我可以为您生成折线图、柱状图、饼图、散点图等。',
                'planning': '🧠 <strong>任务规划工具已就绪！</strong><br><br>请描述您的复杂任务，我会为您规划执行步骤。',
                'sandbox': '🔒 <strong>沙箱环境已就绪！</strong><br><br>您可以在隔离环境中安全执行操作。',
                'mcp': '🔌 <strong>MCP 服务已就绪！</strong><br><br>支持连接多种 MCP 服务器进行扩展功能。'
            };
            addMessage(msgs[tool], 'assistant');
        }

        // Init
        selectAgent('data');
    </script>
</body>
</html>
"""


@app.get("/", response_class=HTMLResponse)
async def get_index():
    return HTMLResponse(content=HTML_TEMPLATE)


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

            response = await process_message(content, agent_type)

            await websocket.send_json({
                'sender': 'assistant',
                'content': response
            })

    except WebSocketDisconnect:
        del active_connections[client_id]


async def process_message(message: str, agent_type: str = 'data') -> str:
    try:
        from app.agent.data import Data
        from app.agent.browser import BrowserAgent
        from app.agent.swe import SWEAgent
        from app.agent.data_analysis import DataAnalysis

        agent_map = {
            'data': Data,
            'browser': BrowserAgent,
            'swe': SWEAgent,
            'analysis': DataAnalysis
        }

        agent_class = agent_map.get(agent_type, Data)

        agent = await agent_class.create()

        try:
            await agent.run(message)

            if agent.memory and agent.memory.messages:
                last_msg = agent.memory.messages[-1]
                if hasattr(last_msg, 'content') and last_msg.content:
                    return str(last_msg.content)
                return "✅ 任务已完成！"
            return "✅ 任务已完成！"

        finally:
            await agent.cleanup()

    except Exception as e:
        return f"❌ 处理失败：{str(e)[:300]}"


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
