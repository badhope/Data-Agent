"""Simple Web Interface for DataAgent using FastAPI"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
import asyncio
from typing import Dict

app = FastAPI(title="Data Agent", description="DataAgent Web Interface")

active_connections: Dict[str, WebSocket] = {}

# HTML Template with All Backend Features
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Data Agent - DataAgent</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #0F172A 0%, #1E293B 100%);
            min-height: 100vh;
            display: flex;
        }
        
        /* Sidebar */
        .sidebar {
            width: 300px;
            background: linear-gradient(180deg, #1E293B 0%, #0F172A 100%);
            border-right: 1px solid #334155;
            padding: 20px;
            overflow-y: auto;
            height: 100vh;
            position: fixed;
            left: 0;
            top: 0;
            z-index: 100;
            transition: transform 0.3s ease;
        }
        
        .sidebar::-webkit-scrollbar {
            width: 4px;
        }
        
        .sidebar::-webkit-scrollbar-thumb {
            background: #475569;
            border-radius: 2px;
        }
        
        .sidebar-header {
            color: white;
            margin-bottom: 20px;
            padding-bottom: 15px;
            border-bottom: 1px solid #334155;
        }
        
        .sidebar-header h2 {
            font-size: 18px;
            margin-bottom: 5px;
        }
        
        .sidebar-section {
            margin-bottom: 20px;
        }
        
        .sidebar-section-title {
            color: #94A3B8;
            font-size: 11px;
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-bottom: 10px;
        }
        
        .sidebar-btn {
            width: 100%;
            padding: 10px 12px;
            background: #334155;
            border: 1px solid #475569;
            border-radius: 8px;
            color: #F1F5F9;
            font-size: 13px;
            cursor: pointer;
            text-align: left;
            margin-bottom: 6px;
            transition: all 0.2s;
            display: flex;
            align-items: center;
            gap: 8px;
        }
        
        .sidebar-btn:hover {
            background: #4F46E5;
            border-color: #4F46E5;
        }
        
        .sidebar-tool-card {
            background: #1E293B;
            border: 1px solid #334155;
            border-radius: 8px;
            padding: 12px;
            margin-bottom: 8px;
            cursor: pointer;
            transition: all 0.2s;
        }
        
        .sidebar-tool-card:hover {
            border-color: #4F46E5;
            transform: translateX(5px);
        }
        
        .sidebar-tool-card h4 {
            color: white;
            font-size: 13px;
            margin-bottom: 4px;
            display: flex;
            align-items: center;
            gap: 6px;
        }
        
        .sidebar-tool-card p {
            color: #94A3B8;
            font-size: 11px;
        }
        
        .status-badge {
            display: inline-block;
            padding: 3px 8px;
            background: #10B981;
            border-radius: 12px;
            font-size: 11px;
            color: white;
            margin-top: 8px;
        }
        
        /* Agent Types */
        .agent-card {
            background: linear-gradient(135deg, #334155 0%, #1E293B 100%);
            border: 1px solid #475569;
            border-radius: 8px;
            padding: 10px;
            margin-bottom: 8px;
            cursor: pointer;
            transition: all 0.2s;
        }
        
        .agent-card:hover {
            border-color: #4F46E5;
            transform: scale(1.02);
        }
        
        .agent-card h4 {
            color: white;
            font-size: 13px;
            margin-bottom: 3px;
        }
        
        .agent-card p {
            color: #94A3B8;
            font-size: 10px;
        }
        
        .agent-card.active {
            border-color: #4F46E5;
            background: linear-gradient(135deg, #4F46E5 0%, #4338CA 100%);
        }
        
        /* Main Content */
        .main-content {
            flex: 1;
            margin-left: 300px;
            display: flex;
            flex-direction: column;
            min-height: 100vh;
        }
        
        /* Header */
        .header {
            background: linear-gradient(135deg, #4F46E5 0%, #4338CA 100%);
            color: white;
            padding: 14px 20px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.2);
            display: flex;
            justify-content: space-between;
            align-items: center;
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
            padding: 6px 10px;
            border-radius: 6px;
            cursor: pointer;
            font-size: 16px;
        }
        
        .menu-btn:hover {
            background: rgba(255,255,255,0.3);
        }
        
        .header h1 {
            font-size: 18px;
            font-weight: 600;
        }
        
        .header-right {
            display: flex;
            gap: 8px;
        }
        
        .new-chat-btn {
            background: white;
            color: #4F46E5;
            border: none;
            padding: 6px 14px;
            border-radius: 6px;
            cursor: pointer;
            font-size: 13px;
            font-weight: 600;
        }
        
        .new-chat-btn:hover {
            background: #F1F5F9;
        }
        
        /* Chat Container */
        .chat-container {
            flex: 1;
            display: flex;
            flex-direction: column;
            max-width: 1000px;
            margin: 0 auto;
            width: 100%;
            padding: 20px;
        }
        
        .messages { flex: 1; overflow-y: auto; padding-bottom: 20px; }
        
        .message { margin-bottom: 14px; animation: slideIn 0.3s ease-out; }
        .message.user { text-align: right; }
        
        .message-content {
            display: inline-block;
            max-width: 75%;
            padding: 10px 14px;
            border-radius: 14px;
            line-height: 1.6;
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
        
        /* Input Area */
        .input-area {
            background: #1E293B;
            padding: 14px;
            border-radius: 14px;
            display: flex;
            gap: 10px;
            box-shadow: 0 -2px 10px rgba(0,0,0,0.1);
        }
        
        .input-area textarea {
            flex: 1;
            background: #334155;
            border: 1px solid #475569;
            border-radius: 10px;
            padding: 12px 16px;
            font-size: 13px;
            color: #F1F5F9;
            resize: none;
            min-height: 44px;
            max-height: 100px;
            font-family: inherit;
        }
        
        .input-area textarea:focus {
            outline: none;
            border-color: #4F46E5;
            box-shadow: 0 0 0 2px rgba(79,70,229,0.2);
        }
        
        .input-area button {
            background: #4F46E5;
            color: white;
            border: none;
            padding: 12px 20px;
            border-radius: 10px;
            cursor: pointer;
            font-size: 13px;
            font-weight: 600;
            transition: background 0.2s;
        }
        
        .input-area button:hover { background: #4338CA; }
        
        /* Status Bar */
        .status-bar {
            text-align: center;
            padding: 6px;
            font-size: 11px;
            color: #94A3B8;
            background: #0F172A;
        }
        
        /* Animations */
        @keyframes slideIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }
        
        ::-webkit-scrollbar { width: 6px; }
        ::-webkit-scrollbar-track { background: transparent; }
        ::-webkit-scrollbar-thumb { background: #475569; border-radius: 3px; }
        
        /* Mobile Responsive */
        @media (max-width: 768px) {
            .sidebar {
                transform: translateX(-100%);
            }
            
            .sidebar.open {
                transform: translateX(0);
            }
            
            .main-content {
                margin-left: 0;
            }
            
            .message-content {
                max-width: 90%;
            }
            
            .overlay {
                display: none;
                position: fixed;
                top: 0;
                left: 0;
                right: 0;
                bottom: 0;
                background: rgba(0,0,0,0.5);
                z-index: 99;
            }
            
            .overlay.show {
                display: block;
            }
        }
        
        @media (min-width: 769px) {
            .overlay {
                display: none;
            }
        }
    </style>
</head>
<body>
    <!-- Overlay for mobile -->
    <div class="overlay" id="overlay" onclick="toggleSidebar()"></div>
    
    <!-- Sidebar -->
    <div class="sidebar" id="sidebar">
        <div class="sidebar-header">
            <h2>🤖 Data Agent</h2>
            <p style="color: #94A3B8; font-size: 11px;">智能助手控制面板</p>
            <span class="status-badge">🟢 在线</span>
        </div>
        
        <!-- Agent Types -->
        <div class="sidebar-section">
            <div class="sidebar-section-title">🤖 代理类型</div>
            <div class="agent-card" onclick="selectAgent('data')" id="agent-data">
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
        
        <!-- Quick Actions -->
        <div class="sidebar-section">
            <div class="sidebar-section-title">📋 快捷操作</div>
            <button class="sidebar-btn" onclick="showLogs()">📊 查看日志</button>
            <button class="sidebar-btn" onclick="showConfig()">⚙️ 查看配置</button>
            <button class="sidebar-btn" onclick="showTools()">📁 查看所有工具</button>
            <button class="sidebar-btn" onclick="showHistory()">📜 对话历史</button>
        </div>
        
        <!-- Web Tools -->
        <div class="sidebar-section">
            <div class="sidebar-section-title">🌐 网页工具</div>
            <div class="sidebar-tool-card" onclick="useSearch('web')">
                <h4>🔍 网络搜索</h4>
                <p>DuckDuckGo / 百度 / Google</p>
            </div>
            <div class="sidebar-tool-card" onclick="useBrowser('auto')">
                <h4>🌐 浏览器自动化</h4>
                <p>Browser Use / Crawl4AI</p>
            </div>
            <div class="sidebar-tool-card" onclick="useSearch('baidu')">
                <h4>📝 百度搜索</h4>
                <p>百度搜索引擎</p>
            </div>
        </div>
        
        <!-- File Tools -->
        <div class="sidebar-section">
            <div class="sidebar-section-title">📁 文件工具</div>
            <div class="sidebar-tool-card" onclick="useFile('read')">
                <h4>📖 读取文件</h4>
                <p>读取文件内容</p>
            </div>
            <div class="sidebar-tool-card" onclick="useFile('write')">
                <h4>✏️ 写入文件</h4>
                <p>创建或编辑文件</p>
            </div>
            <div class="sidebar-tool-card" onclick="useFile('browse')">
                <h4>📂 浏览目录</h4>
                <p>查看目录结构</p>
            </div>
            <div class="sidebar-tool-card" onclick="useFile('edit')">
                <h4>🔧 编辑文件</h4>
                <p>代码编辑器工具</p>
            </div>
        </div>
        
        <!-- Terminal Tools -->
        <div class="sidebar-section">
            <div class="sidebar-section-title">💻 终端工具</div>
            <div class="sidebar-tool-card" onclick="useTerminal('bash')">
                <h4>⚡ Bash 命令</h4>
                <p>执行 Shell 命令</p>
            </div>
            <div class="sidebar-tool-card" onclick="useTerminal('python')">
                <h4>🐍 Python 执行</h4>
                <p>运行 Python 代码</p>
            </div>
        </div>
        
        <!-- Advanced Tools -->
        <div class="sidebar-section">
            <div class="sidebar-section-title">🚀 高级工具</div>
            <div class="sidebar-tool-card" onclick="useAdvanced('chart')">
                <h4>📈 图表可视化</h4>
                <p>数据图表生成</p>
            </div>
            <div class="sidebar-tool-card" onclick="useAdvanced('planning')">
                <h4>🧠 任务规划</h4>
                <p>多步骤任务规划</p>
            </div>
            <div class="sidebar-tool-card" onclick="useAdvanced('sandbox')">
                <h4>🔒 沙箱环境</h4>
                <p>安全隔离执行</p>
            </div>
            <div class="sidebar-tool-card" onclick="useAdvanced('mcp')">
                <h4>🔌 MCP 服务</h4>
                <p>模型上下文协议</p>
            </div>
        </div>
        
        <!-- System Info -->
        <div class="sidebar-section">
            <div class="sidebar-section-title">📊 系统信息</div>
            <div style="color: #94A3B8; font-size: 11px;">
                <p>模型: qwen-plus-latest</p>
                <p>API: 阿里百炼</p>
                <p>工具数: 14+</p>
                <p>状态: 正常运行</p>
            </div>
        </div>
    </div>
    
    <!-- Main Content -->
    <div class="main-content">
        <div class="header">
            <div class="header-left">
                <button class="menu-btn" onclick="toggleSidebar()">☰</button>
                <h1>Data Agent</h1>
                <span id="current-agent" style="font-size: 12px; opacity: 0.8; margin-left: 10px;">Data 通用代理</span>
            </div>
            <div class="header-right">
                <button class="new-chat-btn" onclick="newChat()">+ 新建对话</button>
            </div>
        </div>
        
        <div class="chat-container">
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
                        <strong>🛠️ 核心工具：</strong><br>
                        • 🔍 网络搜索（支持多个搜索引擎）<br>
                        • 🌐 浏览器自动化操作<br>
                        • 📁 文件读写和管理<br>
                        • 💻 终端和代码执行<br>
                        • 📈 数据可视化图表<br><br>
                        请从左侧选择功能或直接输入您的需求！
                    </div>
                </div>
            </div>
            
            <div class="input-area">
                <textarea id="input" placeholder="输入您的消息..." onkeydown="handleKeyDown(event)"></textarea>
                <button onclick="sendMessage()">发送</button>
            </div>
        </div>
        
        <div class="status-bar">
            🟢 在线 | WebSocket 连接 | 已加载 14+ 工具 | Data Agent v1.0
        </div>
    </div>
    
    <script>
        const messagesDiv = document.getElementById('messages');
        const inputTextarea = document.getElementById('input');
        const currentAgentSpan = document.getElementById('current-agent');
        let ws = null;
        let currentAgent = 'data';
        
        // Connect WebSocket
        function connectWS() {
            ws = new WebSocket('ws://' + window.location.host + '/ws');
            
            ws.onopen = function() {
                console.log('Connected to server');
            };
            
            ws.onmessage = function(event) {
                const data = JSON.parse(event.data);
                addMessage(data.content, data.sender);
            };
            
            ws.onclose = function() {
                console.log('Disconnected, reconnecting...');
                setTimeout(connectWS, 2000);
            };
        }
        
        connectWS();
        
        function toggleSidebar() {
            const sidebar = document.getElementById('sidebar');
            const overlay = document.getElementById('overlay');
            sidebar.classList.toggle('open');
            overlay.classList.toggle('show');
        }
        
        function selectAgent(agent) {
            currentAgent = agent;
            const agentNames = {
                'data': 'Data 通用代理',
                'browser': '浏览器代理',
                'swe': 'SWE 软件工程代理',
                'analysis': '数据分析代理'
            };
            currentAgentSpan.textContent = agentNames[agent];
            
            // Update active state
            document.querySelectorAll('.agent-card').forEach(card => {
                card.classList.remove('active');
            });
            document.getElementById('agent-' + agent).classList.add('active');
            
            addMessage('已切换到 <strong>' + agentNames[agent] + '</strong>，请描述您的任务。', 'assistant');
        }
        
        function addMessage(content, sender) {
            const messageDiv = document.createElement('div');
            messageDiv.className = 'message ' + sender;
            
            const contentDiv = document.createElement('div');
            contentDiv.className = 'message-content';
            contentDiv.innerHTML = content.replace(new RegExp('\\\\n', 'g'), '<br>');
            
            messageDiv.appendChild(contentDiv);
            messagesDiv.appendChild(messageDiv);
            messagesDiv.scrollTop = messagesDiv.scrollHeight;
        }
        
        function sendMessage() {
            const content = inputTextarea.value.trim();
            if (!content || !ws) return;
            
            addMessage(content, 'user');
            ws.send(JSON.stringify({ 
                content: content,
                agent: currentAgent
            }));
            inputTextarea.value = '';
        }
        
        function handleKeyDown(event) {
            if (event.key === 'Enter' && !event.shiftKey) {
                event.preventDefault();
                sendMessage();
            }
        }
        
        function newChat() {
            messagesDiv.innerHTML = '';
            addMessage('👋 你好！我是 <strong>Data</strong>，您的智能助手。请描述您的需求或从左侧选择功能！', 'assistant');
        }
        
        // Quick Actions
        function showLogs() {
            addMessage('📊 <strong>最近操作日志：</strong><br><br>• 系统启动成功<br>• WebSocket 连接建立<br>• 代理已就绪<br>• 等待用户输入...', 'assistant');
        }
        
        function showConfig() {
            addMessage('⚙️ <strong>当前配置：</strong><br><br>• 模型: qwen-plus-latest<br>• API: 阿里百炼<br>• 代理模式: ' + currentAgent + '<br>• 工具数: 14+<br>• 侧边栏: 已启用<br>• 移动端适配: 已启用', 'assistant');
        }
        
        function showTools() {
            addMessage('📁 <strong>可用工具列表：</strong><br><br><strong>🌐 网页工具：</strong><br>• 🔍 网络搜索 - DuckDuckGo/百度/Google<br>• 🌐 浏览器自动化 - Browser Use<br>• 📝 网页爬取 - Crawl4AI<br><br><strong>📁 文件工具：</strong><br>• 📖 读取文件 - 读取文件内容<br>• ✏️ 写入文件 - 创建/编辑文件<br>• 📂 浏览目录 - 查看目录结构<br>• 🔧 编辑文件 - 代码编辑<br><br><strong>💻 终端工具：</strong><br>• ⚡ Bash - 执行 Shell 命令<br>• 🐍 Python - 运行 Python 代码<br><br><strong>🚀 高级工具：</strong><br>• 📈 图表可视化 - 生成数据图表<br>• 🧠 任务规划 - 多步骤规划<br>• 🔒 沙箱环境 - 安全隔离<br>• 🔌 MCP 服务 - 模型上下文协议', 'assistant');
        }
        
        function showHistory() {
            addMessage('📜 <strong>对话历史：</strong><br><br>当前会话暂无历史记录。<br>开始对话后，历史记录将显示在这里。', 'assistant');
        }
        
        // Web Tools
        function useSearch(engine) {
            const engines = {
                'web': '帮我搜索',
                'baidu': '用百度搜索'
            };
            inputTextarea.value = engines[engine] + ' ';
            inputTextarea.focus();
        }
        
        function useBrowser(mode) {
            addMessage('🌐 <strong>浏览器自动化工具已准备就绪！</strong><br><br>支持的指令：<br>• "打开网页 https://example.com"<br>• "搜索 Python 教程"<br>• "点击登录按钮"<br>• "填写表单：用户名=xxx，密码=xxx"<br>• "截取当前页面"', 'assistant');
        }
        
        // File Tools
        function useFile(action) {
            const actions = {
                'read': '读取文件 /workspace/test.txt',
                'write': '创建文件 test.txt，内容：Hello Data',
                'browse': '浏览目录 /workspace',
                'edit': '编辑文件 /workspace/test.txt'
            };
            inputTextarea.value = actions[action] || '';
            inputTextarea.focus();
        }
        
        // Terminal Tools
        function useTerminal(type) {
            const types = {
                'bash': '执行命令 ls -la',
                'python': '运行 Python 代码 print("Hello Data")'
            };
            addMessage('💻 <strong>' + (type === 'bash' ? 'Bash' : 'Python') + ' 执行器已就绪！</strong><br><br>请描述您想要执行的操作，例如：<br>• "列出当前目录文件"<br>• "创建新文件夹 test"<br>• "运行 Python 代码计算 1+1"', 'assistant');
        }
        
        // Advanced Tools
        function useAdvanced(tool) {
            const tools = {
                'chart': '📈 <strong>图表可视化工具已就绪！</strong><br><br>请提供数据，我可以为您生成：<br>• 折线图<br>• 柱状图<br>• 饼图<br>• 散点图',
                'planning': '🧠 <strong>任务规划工具已就绪！</strong><br><br>请描述您的复杂任务，我会为您规划执行步骤。',
                'sandbox': '🔒 <strong>沙箱环境已就绪！</strong><br><br>您可以在隔离环境中安全执行危险操作。',
                'mcp': '🔌 <strong>MCP 服务已就绪！</strong><br><br>支持连接多种 MCP 服务器进行扩展功能。'
            };
            addMessage(tools[tool], 'assistant');
        }
        
        // Initialize first agent as active
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
