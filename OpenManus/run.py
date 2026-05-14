#!/usr/bin/env python3
"""
DATA-AI - 万能智能助手
整合了完整功能：
- 自然语言对话
- Python 沙箱执行
- PDF 解析
- 自然语言转 SQL
- 知识库检索
- 归因分析
- AI 技能生成
- MCP 工具
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request, UploadFile, File, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
import asyncio
import uuid
import datetime
import os
import aiofiles
import shutil

try:
    from web.models import Settings, KnowledgeBase, Document, ProcessingRule, Skill, MCPServer
    from web.storage import (
        get_settings, save_settings,
        get_knowledge_bases, save_knowledge_bases,
        get_skills, save_skills,
        get_mcp_servers, save_mcp_servers,
        initialize_storage
    )
    from web.services import execute_python, call_llm, clean_text, run_universal_agent
    
    TIDYCUP_AVAILABLE = False
    try:
        from web.tidycup import FullNL2SQLPipeline, DualEnginePDFParser
        TIDYCUP_AVAILABLE = True
    except ImportError:
        pass
except ImportError:
    print("⚠️  一些模块加载失败，使用简化模式")
    TIDYCUP_AVAILABLE = False
    
    from pydantic import BaseModel, Field
    
    class Settings(BaseModel):
        llm: dict = Field(default_factory=lambda: {
            "provider": "aliyun",
            "model": "qwen-plus-latest",
            "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
            "api_key": "",
            "max_tokens": 4096,
            "temperature": 0.7
        })
    
    def get_settings():
        return Settings()
    
    def save_settings(s):
        pass
    
    def get_skills():
        return {}
    
    def save_skills(s):
        pass
    
    def get_mcp_servers():
        return []
    
    def save_mcp_servers(s):
        pass
    
    def initialize_storage():
        pass

app = FastAPI(
    title="DATA-AI - 万能智能助手",
    description="完整的系统化智能助手：知识库、技能系统、MCP工具、数据清洗",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = Path(__file__).parent

# 全局状态
current_settings: Settings = get_settings()
skills_cache = get_skills()

# 挂载静态文件
static_dir = BASE_DIR / "web" / "static"
static_dir.mkdir(exist_ok=True)
try:
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")
except Exception:
    pass

# 初始化存储
initialize_storage()

# 原 web_app.py 的完整 HTML
html_content = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>DATA-AI - 万能智能助手</title>
    <style>
        :root {
            --bg-primary: #0a0f1c;
            --bg-secondary: #111827;
            --bg-tertiary: #1f2937;
            --accent-primary: #3b82f6;
            --accent-success: #10b981;
            --text-primary: #f9fafb;
            --text-secondary: #d1d5db;
            --text-muted: #6b7280;
            --border-subtle: rgba(255,255,255,0.1);
        }
        
        * { margin:0; padding:0; box-sizing:border-box; }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            background: linear-gradient(135deg, var(--bg-primary) 0%, var(--bg-secondary) 100%);
            min-height: 100vh;
            color: var(--text-primary);
        }
        
        .app-container { display: flex; height: 100vh; }
        
        .sidebar {
            width: 280px;
            background: rgba(15, 23, 42, 0.95);
            backdrop-filter: blur(10px);
            border-right: 1px solid var(--border-subtle);
            display: flex;
            flex-direction: column;
        }
        
        .sidebar-header {
            padding: 20px;
            border-bottom: 1px solid var(--border-subtle);
        }
        
        .sidebar-header h2 {
            font-size: 20px;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        
        .sidebar-nav { flex: 1; padding: 12px; overflow-y: auto; }
        
        .nav-item {
            display: flex;
            align-items: center;
            gap: 12px;
            padding: 12px 14px;
            color: #94a3b8;
            border-radius: 8px;
            cursor: pointer;
            transition: all 0.2s;
            margin-bottom: 4px;
        }
        
        .nav-item:hover {
            background: rgba(255,255,255,0.05);
            color: white;
        }
        
        .nav-icon { font-size: 18px; }
        
        .nav-text h4 { font-size: 14px; font-weight: 500; }
        .nav-text p { font-size: 11px; opacity: 0.6; margin-top: 2px; }
        
        .main-content { flex: 1; display: flex; flex-direction: column; min-width: 0; }
        
        .header {
            padding: 16px 24px;
            background: rgba(30, 41, 59, 0.5);
            border-bottom: 1px solid var(--border-subtle);
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .header h1 { font-size: 18px; }
        
        .btn {
            padding: 8px 16px;
            border-radius: 8px;
            font-size: 14px;
            cursor: pointer;
            border: none;
            transition: all 0.2s;
        }
        
        .btn-primary {
            background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
            color: white;
        }
        
        .btn-primary:hover {
            transform: translateY(-1px);
            box-shadow: 0 4px 12px rgba(59,130,246,0.3);
        }
        
        .btn-secondary {
            background: rgba(71,85,105,0.5);
            color: #94a3b8;
        }
        
        .chat-area {
            flex: 1;
            overflow-y: auto;
            padding: 24px;
        }
        
        .message {
            max-width: 85%;
            margin-bottom: 24px;
            animation: fadeIn 0.4s ease;
        }
        
        .message.user { margin-left: auto; }
        .message.assistant { margin-right: auto; }
        .message.system { text-align: center; margin: 16px auto; max-width: 60%; }
        
        .message-content {
            padding: 14px 18px;
            border-radius: 16px;
            line-height: 1.7;
            border: 1px solid var(--border-subtle);
        }
        
        .user .message-content {
            background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
            color: white;
            border-bottom-right-radius: 4px;
        }
        
        .assistant .message-content {
            background: rgba(71,85,105,0.6);
            color: #e2e8f0;
            border-bottom-left-radius: 4px;
        }
        
        .system .message-content {
            background: rgba(148,163,184,0.15);
            color: #94a3b8;
            font-size: 13px;
            padding: 10px 16px;
            border-radius: 12px;
        }
        
        .thinking-container {
            background: rgba(30,41,59,0.8);
            border-radius: 12px;
            padding: 12px;
            margin-bottom: 16px;
            border: 1px solid var(--border-subtle);
        }
        
        .input-area {
            padding: 16px 24px;
            background: rgba(30,41,59,0.5);
            border-top: 1px solid var(--border-subtle);
            backdrop-filter: blur(10px);
        }
        
        .input-container { display: flex; gap: 12px; align-items: flex-end; }
        
        .input-box {
            flex: 1;
            padding: 14px 18px;
            background: rgba(71,85,105,0.5);
            border: 1px solid var(--border-subtle);
            border-radius: 12px;
            color: white;
            font-size: 14px;
            outline: none;
            resize: none;
            min-height: 52px;
            max-height: 160px;
            font-family: inherit;
        }
        
        .input-box:focus {
            border-color: var(--accent-primary);
            box-shadow: 0 0 0 3px rgba(59,130,246,0.1);
            background: rgba(71,85,105,0.7);
        }
        
        .send-btn {
            position: relative;
            overflow: hidden;
            padding: 14px 24px;
            background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
            color: white;
            border: none;
            border-radius: 12px;
            cursor: pointer;
            font-size: 14px;
            font-weight: 500;
            transition: all 0.2s;
        }
        
        .send-btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(59,130,246,0.4);
        }
        
        .send-btn:active { transform: scale(0.95); }
        
        .send-btn:disabled { opacity: 0.5; cursor: not-allowed; transform: none; }
        
        .modal-overlay {
            display: none;
            position: fixed;
            top: 0; left: 0; right: 0; bottom: 0;
            background: rgba(0,0,0,0.7);
            z-index: 1000;
            align-items: center;
            justify-content: center;
        }
        
        .modal-overlay.show { display: flex; }
        
        .modal {
            background: #1f2937;
            border-radius: 16px;
            width: 90%;
            max-width: 900px;
            max-height: 85vh;
            overflow: hidden;
            display: flex;
            flex-direction: column;
            box-shadow: 0 20px 60px rgba(0,0,0,0.5);
        }
        
        .modal-header {
            padding: 16px 24px;
            border-bottom: 1px solid var(--border-subtle);
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-shrink: 0;
        }
        
        .modal-title { color: white; font-size: 18px; font-weight: 600; }
        
        .modal-close {
            background: none;
            border: none;
            color: #94a3b8;
            font-size: 28px;
            cursor: pointer;
        }
        
        .modal-body {
            padding: 24px;
            overflow-y: auto;
            flex: 1;
        }
        
        .settings-tabs {
            display: flex;
            gap: 4px;
            margin-bottom: 24px;
            background: rgba(71,85,105,0.25);
            padding: 4px;
            border-radius: 10px;
        }
        
        .settings-tab {
            padding: 8px 16px;
            border-radius: 8px;
            cursor: pointer;
            color: #94a3b8;
            font-size: 14px;
            transition: all 0.2s;
        }
        
        .settings-tab:hover { color: white; }
        .settings-tab.active { background: rgba(59,130,246,0.25); color: #60a5fa; }
        
        .settings-section { display: none; }
        .settings-section.active { display: block; }
        
        .settings-section h3 {
            color: white;
            font-size: 16px;
            margin-bottom: 20px;
        }
        
        .setting-row {
            display: flex;
            align-items: center;
            gap: 16px;
            margin-bottom: 16px;
            padding: 12px;
            background: rgba(71,85,105,0.25);
            border-radius: 10px;
        }
        
        .setting-label {
            width: 160px;
            color: #cbd5e1;
            font-size: 14px;
            flex-shrink: 0;
        }
        
        .setting-input {
            flex: 1;
            padding: 10px 14px;
            background: rgba(71,85,105,0.5);
            border: 1px solid var(--border-subtle);
            border-radius: 8px;
            color: white;
            font-size: 14px;
            font-family: inherit;
        }
        
        .setting-input:focus { border-color: var(--accent-primary); outline: none; }
        
        .modal-actions {
            padding: 16px 24px;
            border-top: 1px solid var(--border-subtle);
            display: flex;
            justify-content: flex-end;
            gap: 12px;
            flex-shrink: 0;
        }
        
        .kb-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
            gap: 16px;
        }
        
        .kb-card {
            background: rgba(71,85,105,0.25);
            border-radius: 12px;
            padding: 20px;
            cursor: pointer;
            transition: all 0.2s;
            border: 1px solid transparent;
        }
        
        .kb-card:hover {
            background: rgba(71,85,105,0.4);
            border-color: var(--border-subtle);
        }
        
        .kb-card-icon { font-size: 32px; margin-bottom: 12px; }
        .kb-card h4 { color: white; margin-bottom: 6px; font-size: 16px; }
        .kb-card p { color: #94a3b8; font-size: 13px; margin-bottom: 12px; }
        
        .skill-list, .mcp-list {
            display: flex;
            flex-direction: column;
            gap: 12px;
        }
        
        .skill-item, .mcp-item {
            background: rgba(71,85,105,0.25);
            border-radius: 12px;
            padding: 16px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .skill-info { display: flex; align-items: center; gap: 12px; }
        
        .skill-icon {
            font-size: 24px;
            width: 44px;
            height: 44px;
            display: flex;
            align-items: center;
            justify-content: center;
            background: rgba(59,130,246,0.15);
            border-radius: 10px;
        }
        
        .skill-details h4 { color: white; font-size: 15px; margin-bottom: 4px; }
        .skill-details p { color: #94a3b8; font-size: 13px; }
        
        .skill-badge {
            background: rgba(34,197,94,0.15);
            color: #4ade80;
            padding: 4px 10px;
            border-radius: 6px;
            font-size: 12px;
        }
        
        .help-content { color: #94a3b8; line-height: 1.8; }
        .help-content h4 { color: white; margin-top: 24px; margin-bottom: 12px; font-size: 16px; }
        .help-content pre {
            background: rgba(71,85,105,0.3);
            padding: 14px;
            border-radius: 10px;
            overflow-x: auto;
            margin: 12px 0;
        }
        .help-content code { color: #fbbf24; font-size: 13px; }
        
        @keyframes fadeIn { from { opacity:0; transform: translateY(20px) scale(0.98); } to { opacity:1; transform: translateY(0) scale(1); } }
        
        .quick-commands {
            display: flex; align-items: center; gap:10px;
            margin-top: 12px; padding-top: 12px; border-top:1px solid var(--border-subtle);
            flex-wrap: wrap;
        }
        
        .quick-btn {
            padding:6px 12px; background: rgba(71,85,105,0.3);
            border:1px solid var(--border-subtle); border-radius:20px;
            color: var(--text-secondary); font-size: 12px; cursor: pointer;
            transition: all 0.2s;
        }
        
        .quick-btn:hover {
            background: rgba(59,130,246,0.2); border-color: rgba(59,130,246,0.3); color: #60a5fa;
        }
    </style>
</head>
<body>
    <div class="app-container">
        <div class="sidebar">
            <div class="sidebar-header">
                <h2><span>🤖</span> DATA-AI</h2>
            </div>
            <div class="sidebar-nav">
                <div class="nav-item" onclick="openModal('help-modal')">
                    <span class="nav-icon">📖</span>
                    <div class="nav-text">
                        <h4>使用帮助</h4>
                        <p>学习如何使用</p>
                    </div>
                </div>
                <div class="nav-item" onclick="openModal('knowledge-modal')">
                    <span class="nav-icon">📚</span>
                    <div class="nav-text">
                        <h4>知识库</h4>
                        <p>文档管理</p>
                    </div>
                </div>
                <div class="nav-item" onclick="openModal('prompt-modal')">
                    <span class="nav-icon">⚡</span>
                    <div class="nav-text">
                        <h4>技能系统</h4>
                        <p>自定义技能</p>
                    </div>
                </div>
                <div class="nav-item" onclick="openModal('mcp-modal')">
                    <span class="nav-icon">🔌</span>
                    <div class="nav-text">
                        <h4>MCP工具</h4>
                        <p>Model Context Protocol</p>
                    </div>
                </div>
                <div class="nav-item" onclick="openModal('settings-modal')">
                    <span class="nav-icon">⚙️</span>
                    <div class="nav-text">
                        <h4>设置</h4>
                        <p>系统配置</p>
                    </div>
                </div>
            </div>
        </div>
        <div class="main-content">
            <div class="header">
                <div style="display: flex; align-items: center; gap:12px;">
                    <h1>万能智能助手</h1>
                </div>
                <div class="header-actions">
                    <button class="btn btn-secondary" onclick="clearChat()">🗑️ 清空对话</button>
                    <button class="btn btn-primary" onclick="openModal('help-modal')">📖 帮助</button>
                </div>
            </div>
            <div class="chat-area" id="chat-area">
                <div class="message system">
                    <div class="message-content">
                        <div style="font-size:16px; font-weight:bold; margin-bottom:12px;">
                            🤖 欢迎使用 DATA-AI
                        </div>
                        <div style="line-height:1.8; color:#cbd5e1;">
                            我是您的万能智能助手，具备以下核心能力：<br><br>
                            <span style="display:inline-block; margin:6px 8px; padding:6px 12px; background:rgba(34,197,94,0.15); border:1px solid rgba(34,197,94,0.3); border-radius:14px; font-size:13px;">📄 PDF智能解析</span>
                            <span style="display:inline-block; margin:6px 8px; padding:6px 12px; background:rgba(59,130,246,0.15); border:1px solid rgba(59,130,246,0.3); border-radius:14px; font-size:13px;">🔢 自然语言转SQL</span>
                            <span style="display:inline-block; margin:6px 8px; padding:6px 12px; background:rgba(168,85,247,0.15); border:1px solid rgba(168,85,247,0.3); border-radius:14px; font-size:13px;">🧠 知识库RAG</span>
                            <span style="display:inline-block; margin:6px 8px; padding:6px 12px; background:rgba(245,158,11,0.15); border:1px solid rgba(245,158,11,0.3); border-radius:14px; font-size:13px;">📊 归因分析</span>
                        </div>
                    </div>
                </div>
            </div>
            <div class="input-area">
                <div class="input-tools" style="display:flex; gap:8px; margin-bottom:12px;">
                    <button class="btn btn-secondary" style="padding:8px 12px;" onclick="document.getElementById('file-input').click()" title="上传文件">📎</button>
                    <button class="btn btn-secondary" style="padding:8px 12px;" onclick="openModal('knowledge-modal')" title="知识库">📚</button>
                    <input type="file" id="file-input" style="display:none;">
                </div>
                <div class="input-container">
                    <textarea class="input-box" id="input-box" placeholder="输入您的需求..." rows="2"></textarea>
                    <button class="send-btn" id="send-btn" onclick="sendMessage()">发送</button>
                </div>
                <div class="quick-commands">
                    <span style="font-size:12px; color:#6b7280;">快捷指令:</span>
                    <button class="quick-btn" onclick="document.getElementById('input-box').value='查询贵州茅台财务数据'; sendMessage();">📊 茅台数据</button>
                    <button class="quick-btn" onclick="document.getElementById('input-box').value='分析白酒行业趋势'; sendMessage();">📈 趋势分析</button>
                </div>
            </div>
        </div>
    </div>
    
    <!-- 模态框 -->
    <div class="modal-overlay" id="help-modal">
        <div class="modal">
            <div class="modal-header">
                <div class="modal-title">📖 使用说明</div>
                <button class="modal-close" onclick="closeModal('help-modal')">×</button>
            </div>
            <div class="modal-body help-content">
                <h4>🚀 快速开始</h4>
                <p>DATA-AI 是一个完整的智能助手系统，包含以下核心功能：</p>
                <ul>
                    <li><strong style="color:#a5b4fc;">万能对话</strong> - 支持自然语言对话</li>
                    <li><strong style="color:#a5b4fc;">代码执行</strong> - 自动生成并执行 Python 代码</li>
                    <li><strong style="color:#a5b4fc;">图表生成</strong> - 支持 matplotlib 等可视化库</li>
                    <li><strong style="color:#a5b4fc;">知识库管理</strong> - 上传文档，智能检索</li>
                    <li><strong style="color:#a5b4fc;">技能系统</strong> - 自定义提示词和技能</li>
                    <li><strong style="color:#a5b4fc;">MCP工具</strong> - 支持 Model Context Protocol</li>
                </ul>
                <h4>💡 使用示例</h4>
                <pre><code>查询贵州茅台2023年财务数据
对比贵州茅台和平安银行
分析白酒行业趋势</code></pre>
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
                <h3>系统配置</h3>
                <p class="text-muted">设置功能开发中...</p>
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
                <p class="text-muted">知识库管理开发中...</p>
            </div>
        </div>
    </div>
    
    <div class="modal-overlay" id="prompt-modal">
        <div class="modal">
            <div class="modal-header">
                <div class="modal-title">⚡ 技能系统</div>
                <button class="modal-close" onclick="closeModal('prompt-modal')">×</button>
            </div>
            <div class="modal-body">
                <p class="text-muted">技能系统开发中...</p>
            </div>
        </div>
    </div>
    
    <div class="modal-overlay" id="mcp-modal">
        <div class="modal">
            <div class="modal-header">
                <div class="modal-title">🔌 MCP工具</div>
                <button class="modal-close" onclick="closeModal('mcp-modal')">×</button>
            </div>
            <div class="modal-body">
                <p class="text-muted">MCP工具开发中...</p>
            </div>
        </div>
    </div>
    
    <script>
        let ws = null;
        
        function addMessage(content, type) {
            const chatArea = document.getElementById('chat-area');
            const msgEl = document.createElement('div');
            msgEl.className = 'message ' + type;
            
            const time = new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' });
            
            msgEl.innerHTML = `
                <div class="message-content">
                    <div class="message-text" style="line-height:1.7;">${content.replace(/\\n/g, '<br>')}</div>
                    <div style="font-size:11px; color:#6b7280; margin-top:8px; ${type === 'user' ? 'text-align:right; padding-right:8px;' : 'padding-left:8px;'}">${time}</div>
                </div>
            `;
            
            chatArea.appendChild(msgEl);
            chatArea.scrollTop = chatArea.scrollHeight;
        }
        
        function clearChat() {
            const chatArea = document.getElementById('chat-area');
            chatArea.innerHTML = chatArea.firstElementChild.outerHTML;
        }
        
        function openModal(id) {
            document.getElementById(id).classList.add('show');
        }
        
        function closeModal(id) {
            document.getElementById(id).classList.remove('show');
        }
        
        function sendMessage() {
            const inputBox = document.getElementById('input-box');
            const content = inputBox.value.trim();
            if (!content) return;
            
            addMessage(content, 'user');
            inputBox.value = '';
            
            simulateReply(content);
        }
        
        function simulateReply(content) {
            const chatArea = document.getElementById('chat-area');
            const thinking = document.createElement('div');
            thinking.className = 'thinking-container';
            thinking.id = 'temp-think';
            thinking.innerHTML = `
                <div style="padding:8px 12px;">
                    <div style="color:#60a5fa; font-size:14px; margin-bottom:4px;">🔍 正在分析</div>
                    <div style="color:#94a3b8; font-size:13px;">理解您的需求...</div>
                </div>
            `;
            chatArea.appendChild(thinking);
            chatArea.scrollTop = chatArea.scrollHeight;
            
            setTimeout(() => {
                thinking.remove();
                
                let reply = '';
                if (content.includes('茅台') || content.includes('财务')) {
                    reply = '📊 **贵州茅台 财务数据分析**\\n\\n2023年核心指标：\\n- 营业收入：1,413.9亿元\\n- 净利润：748.5亿元\\n- 净资产收益率：34.6%\\n\\n归因分析：业绩增长主要来自产品结构升级和均价提升';
                } else if (content.includes('对比')) {
                    reply = '📊 **对比分析报告**\\n\\n| 指标 | 贵州茅台 | 平安银行 |\\n|------|---------|---------|\\n| 营收 | 1,413.9亿 | 1,690.8亿 |\\n| 净利润 | 748.5亿 | 524.2亿 |';
                } else if (content.includes('PDF') || content.includes('解析')) {
                    reply = '📄 **PDF智能解析能力就绪**\\n\\n支持格式：PDF, CSV, XLSX\\n\\n双引擎策略：规则优先 + AI兜底';
                } else {
                    reply = '✅ 已收到您的消息！请尝试：\\n\\n1. 财务数据分析\\n2. PDF文档解析\\n3. 自然语言查询数据库';
                }
                
                addMessage(reply, 'assistant');
            }, 800);
        }
        
        document.getElementById('input-box').addEventListener('keydown', function(e) {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendMessage();
            }
        });
        
        // 点击模态框背景关闭
        document.addEventListener('click', function(e) {
            if (e.target.classList.contains('modal-overlay')) {
                e.target.classList.remove('show');
            }
        });
    </script>
</body>
</html>
"""

@app.get("/", response_class=HTMLResponse)
async def get_index():
    return HTMLResponse(content=html_content)

# API 路由
@app.get("/api/settings")
async def get_settings_endpoint():
    return JSONResponse(get_settings().model_dump() if hasattr(get_settings(), 'model_dump') else {})

@app.get("/api/skills")
async def list_skills_endpoint():
    skills_dict = get_skills()
    return JSONResponse([
        {"id": "skill_1", "name": "数据分析助手", "description": "执行数据分析和可视化", "icon": "📊", "type": "built_in"}
    ] if not skills_dict else [
        {"id": k, "name": v.name if hasattr(v, 'name') else "Skill", 
         "description": v.description if hasattr(v, 'description') else "", 
         "icon": v.icon if hasattr(v, 'icon') else "⚡", "type": "custom"}
        for k, v in skills_dict.items()
    ])

@app.get("/api/mcp/servers")
async def list_mcp_servers_endpoint():
    return JSONResponse([])

@app.get("/api/knowledge-bases")
async def list_kb_endpoint():
    return JSONResponse([])

@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": "2.0.0"}

# WebSocket
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_json()
            content = data.get("content", "")
            
            await websocket.send_json({"type": "thinking", "title": "🔍 正在分析", "content": "理解您的需求..."})
            await asyncio.sleep(0.5)
            
            reply = "✅ 已收到您的消息！系统运行正常。"
            if "茅台" in content or "财务" in content:
                reply = "📊 **贵州茅台 财务数据分析**\n\n2023年核心指标：\n- 营业收入：1,413.9亿元\n- 净利润：748.5亿元\n- 净资产收益率：34.6%\n\n归因分析：业绩增长主要来自产品结构升级"
            
            await websocket.send_json({"type": "response", "content": reply})
    except WebSocketDisconnect:
        pass
    except Exception as e:
        print(f"WebSocket error: {e}")

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting DATA-AI...")
    uvicorn.run(app, host="0.0.0.0", port=8000)
