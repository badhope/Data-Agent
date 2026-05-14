/**
 * DATA-AI Application Frontend
 * Architecture inspired by modern open-source projects
 */

// Global state
let appState = {
    ws: null,
    settings: {},
    currentView: 'chat',
    isProcessing: false
};

// Initialize on load
document.addEventListener('DOMContentLoaded', () => {
    initializeApp();
});

/**
 * Initialize the application
 */
async function initializeApp() {
    console.log('🚀 Initializing DATA-AI application...');
    
    // Load settings
    await loadSettings();
    
    // Connect WebSocket
    connectWebSocket();
    
    // Setup event listeners
    setupEventListeners();
    
    // Load initial data
    Promise.all([
        loadKnowledgeBases(),
        loadSkills(),
        loadMcpServers()
    ]);
    
    console.log('✅ Application initialized');
}

/**
 * WebSocket Integration
 */
function connectWebSocket() {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = window.location.host;
    const wsUrl = `${protocol}//${host}/api/v1/chat/ws/default_user`;
    
    console.log('🔌 Connecting to WebSocket:', wsUrl);
    
    appState.ws = new WebSocket(wsUrl);
    
    appState.ws.onopen = () => {
        console.log('✅ WebSocket connected');
    };
    
    appState.ws.onmessage = (event) => {
        try {
            const data = JSON.parse(event.data);
            handleWebSocketMessage(data);
        } catch (e) {
            console.error('❌ WebSocket message error:', e);
        }
    };
    
    appState.ws.onclose = () => {
        console.log('⚠️ WebSocket disconnected, reconnecting in 3s...');
        setTimeout(connectWebSocket, 3000);
    };
    
    appState.ws.onerror = (error) => {
        console.error('❌ WebSocket error:', error);
    };
}

function handleWebSocketMessage(data) {
    const chatArea = document.getElementById('chat-area');
    
    if (data.type === 'thinking') {
        showThinkingPhase(data.title, data.content);
        
    } else if (data.type === 'response') {
        hideThinking();
        addMessage(data.content, 'assistant');
        finishProcessing();
        
    } else if (data.type === 'error') {
        hideThinking();
        showError(data.content);
        finishProcessing();
    }
}

/**
 * Chat Functions
 */
async function sendMessage() {
    const input = document.getElementById('message-input');
    const content = input.value.trim();
    
    if (!content || appState.isProcessing) return;
    
    startProcessing();
    
    // Add user message
    addMessage(content, 'user');
    input.value = '';
    
    // Send via WebSocket if available
    if (appState.ws && appState.ws.readyState === WebSocket.OPEN) {
        appState.ws.send(JSON.stringify({
            content: content,
            timestamp: new Date().toISOString()
        }));
    } else {
        // Fallback to REST API
        await sendMessageViaREST(content);
    }
}

async function sendMessageViaREST(content) {
    try {
        const response = await fetch('/api/v1/chat/send', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ content: content })
        });
        
        const data = await response.json();
        if (data.type === 'response') {
            addMessage(data.content, 'assistant');
        } else if (data.error) {
            showError(data.error);
        }
        finishProcessing();
        
    } catch (error) {
        showError('发送失败: ' + error.message);
        finishProcessing();
    }
}

function addMessage(content, type) {
    const chatArea = document.getElementById('chat-area');
    const messageEl = document.createElement('div');
    messageEl.className = `message ${type}`;
    
    const formattedContent = content.replace(/\n/g, '<br>');
    const time = new Date().toLocaleTimeString('zh-CN', { 
        hour: '2-digit', 
        minute: '2-digit' 
    });
    
    messageEl.innerHTML = `
        <div class="message-content">
            <div class="message-text">${formattedContent}</div>
            <div class="message-actions">
                <button class="message-action-btn" onclick="copyMessage(this)" title="复制">📋</button>
            </div>
        </div>
        <div style="font-size: 11px; color: #6b7280; margin-top: 4px; 
                    ${type === 'user' ? 'text-align: right; padding-right: 8px;' : 'padding-left: 8px;'}">
            ${time}
        </div>
    `;
    
    chatArea.appendChild(messageEl);
    chatArea.scrollTop = chatArea.scrollHeight;
}

function showThinkingPhase(title, content) {
    let container = document.querySelector('.thinking-container');
    if (!container) {
        container = document.createElement('div');
        container.className = 'thinking-container';
        document.getElementById('chat-area').appendChild(container);
    }
    
    const phaseNum = container.querySelectorAll('.thinking-item').length + 1;
    const phaseEl = document.createElement('div');
    phaseEl.className = 'thinking-item';
    phaseEl.innerHTML = `
        <div class="thinking-header">
            <div class="thinking-badge">${phaseNum}</div>
            <div class="thinking-title">${title}</div>
        </div>
        <div class="thinking-content">${content}</div>
    `;
    
    container.appendChild(phaseEl);
    document.getElementById('chat-area').scrollTop = document.getElementById('chat-area').scrollHeight;
}

function hideThinking() {
    document.querySelector('.thinking-container')?.remove();
}

function showError(message) {
    const chatArea = document.getElementById('chat-area');
    const errorEl = document.createElement('div');
    errorEl.className = 'message system error';
    errorEl.innerHTML = `
        <div class="message-content">
            <div style="display: flex; align-items: center; gap: 8px;">
                <span style="font-size: 18px;">❌</span>
                <span style="color: #ef4444;">${message}</span>
            </div>
        </div>
    `;
    chatArea.appendChild(errorEl);
    chatArea.scrollTop = chatArea.scrollHeight;
}

function copyMessage(btn) {
    const text = btn.closest('.message-content').querySelector('.message-text').innerText;
    navigator.clipboard.writeText(text).then(() => {
        showToast('已复制到剪贴板', 'success');
    }).catch(() => {
        showToast('复制失败', 'error');
    });
}

function clearChat() {
    const chatArea = document.getElementById('chat-area');
    chatArea.innerHTML = `
        <div class="message system">
            <div class="message-content">欢迎使用 DATA-AI！我是您的万能智能助手。</div>
        </div>
    `;
    showToast('对话已清空', 'info');
}

function startProcessing() {
    appState.isProcessing = true;
    document.getElementById('send-btn').disabled = true;
    document.getElementById('send-btn').textContent = '⏳ 处理中...';
}

function finishProcessing() {
    appState.isProcessing = false;
    document.getElementById('send-btn').disabled = false;
    document.getElementById('send-btn').textContent = '➤';
}

/**
 * Settings
 */
async function loadSettings() {
    try {
        const response = await fetch('/api/v1/settings');
        appState.settings = await response.json();
        console.log('⚙️ Settings loaded:', appState.settings);
    } catch (error) {
        console.error('❌ Load settings error:', error);
    }
}

async function saveSettings() {
    const form = document.getElementById('settings-form');
    const formData = new FormData(form);
    const settings = {};
    
    for (let [key, value] of formData.entries()) {
        settings[key] = value;
    }
    
    try {
        const response = await fetch('/api/v1/settings', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(settings)
        });
        
        const result = await response.json();
        if (result.success) {
            appState.settings = result.settings;
            showToast('设置已保存', 'success');
        }
    } catch (error) {
        showToast('保存失败: ' + error.message, 'error');
    }
}

/**
 * Knowledge Base
 */
async function loadKnowledgeBases() {
    try {
        const response = await fetch('/api/v1/knowledge/bases');
        const bases = await response.json();
        
        const container = document.getElementById('kb-list');
        if (container) {
            container.innerHTML = bases.map(kb => `
                <div class="kb-item">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <div>
                            <h4 style="color: white; margin: 0;">${kb.name}</h4>
                            <p style="color: #6b7280; margin: 4px 0 0; font-size: 12px;">
                                ${kb.document_count || 0} 文档
                            </p>
                        </div>
                        <button class="btn btn-secondary" style="padding: 4px 12px; font-size: 12px;"
                                onclick="deleteKnowledgeBase('${kb.id}')">删除</button>
                    </div>
                </div>
            `).join('');
        }
    } catch (error) {
        console.error('❌ Load knowledge bases error:', error);
    }
}

async function createKnowledgeBase() {
    const name = document.getElementById('new-kb-name').value;
    if (!name) {
        showToast('请输入知识库名称', 'error');
        return;
    }
    
    try {
        await fetch('/api/v1/knowledge/bases', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name: name })
        });
        
        document.getElementById('new-kb-name').value = '';
        await loadKnowledgeBases();
        showToast('知识库创建成功', 'success');
    } catch (error) {
        showToast('创建失败: ' + error.message, 'error');
    }
}

async function deleteKnowledgeBase(kbId) {
    if (!confirm('确定要删除这个知识库吗？')) return;
    
    try {
        await fetch(`/api/v1/knowledge/bases/${kbId}`, { method: 'DELETE' });
        await loadKnowledgeBases();
        showToast('知识库已删除', 'success');
    } catch (error) {
        showToast('删除失败: ' + error.message, 'error');
    }
}

/**
 * Skills
 */
async function loadSkills() {
    try {
        const response = await fetch('/api/v1/skills');
        const result = await response.json();
        
        const container = document.getElementById('skill-list');
        if (container && result.skills) {
            container.innerHTML = result.skills.map(skill => `
                <div style="background: rgba(30, 41, 59, 0.8); padding: 12px; border-radius: 8px; margin-bottom: 8px; border: 1px solid rgba(255,255,255,0.1);">
                    <div style="display: flex; align-items: center; justify-content: space-between;">
                        <div style="display: flex; align-items: center; gap: 8px;">
                            <span style="font-size: 24px;">${skill.icon || '⚡'}</span>
                            <div>
                                <h4 style="color: white; margin: 0; font-size: 14px;">${skill.name}</h4>
                                <p style="color: #94a3b8; margin: 2px 0 0; font-size: 12px;">${skill.description || ''}</p>
                            </div>
                        </div>
                        <button class="btn btn-secondary" style="padding: 6px 12px; font-size: 12px;"
                                onclick="executeSkill('${skill.id}')">执行</button>
                    </div>
                </div>
            `).join('');
        }
    } catch (error) {
        console.error('❌ Load skills error:', error);
    }
}

async function generateSkillFromPanel() {
    const type = document.getElementById('skill-type-select').value;
    const description = document.getElementById('skill-desc-input').value;
    
    if (!description) {
        showToast('请输入技能描述', 'error');
        return;
    }
    
    showToast('AI 正在生成技能...', 'info');
    
    try {
        const response = await fetch('/api/v1/skills/generate-ai', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                skill_type: type,
                description: description
            })
        });
        
        const result = await response.json();
        if (result.success) {
            showToast('技能生成成功！', 'success');
            document.getElementById('skill-desc-input').value = '';
            await loadSkills();
        }
    } catch (error) {
        showToast('生成失败: ' + error.message, 'error');
    }
}

async function executeSkill(skillId) {
    try {
        const response = await fetch(`/api/v1/skills/${skillId}/execute`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ params: {} })
        });
        
        const result = await response.json();
        showToast('技能执行完成', 'success');
        console.log('Skill result:', result);
    } catch (error) {
        showToast('执行失败: ' + error.message, 'error');
    }
}

/**
 * MCP Servers
 */
async function loadMcpServers() {
    try {
        const response = await fetch('/api/v1/mcp/servers');
        const servers = await response.json();
        
        const container = document.getElementById('mcp-servers-list');
        if (container) {
            container.innerHTML = servers.map(server => `
                <div style="background: rgba(30, 41, 59, 0.8); padding: 12px; border-radius: 8px; margin-bottom: 8px; border: 1px solid rgba(255,255,255,0.1);">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <div style="display: flex; align-items: center; gap: 8px;">
                            <span style="font-size: 20px;">${server.icon || '🔌'}</span>
                            <div>
                                <h4 style="color: white; margin: 0; font-size: 14px;">${server.name}</h4>
                                <span style="color: ${server.enabled ? '#22c55e' : '#6b7280'}; font-size: 11px;">
                                    ${server.enabled ? '✅ 已启用' : '❌ 已禁用'}
                                </span>
                            </div>
                        </div>
                        <div style="display: flex; gap: 6px;">
                            <button class="btn btn-secondary" style="padding: 4px 8px; font-size: 11px;"
                                    onclick="toggleMcpServer('${server.id}')">切换</button>
                        </div>
                    </div>
                </div>
            `).join('');
        }
    } catch (error) {
        console.error('❌ Load MCP servers error:', error);
    }
}

async function toggleMcpServer(serverId) {
    try {
        await fetch(`/api/v1/mcp/servers/${serverId}/toggle`, { method: 'POST' });
        await loadMcpServers();
    } catch (error) {
        showToast('操作失败', 'error');
    }
}

/**
 * Analytics (Competition Features)
 */
async function loadAnalyticsStatus() {
    try {
        const response = await fetch('/api/v1/analytics/status');
        const status = await response.json();
        
        if (status.available) {
            document.getElementById('analytics-status').innerHTML = `
                <span style="color: #22c55e;">✅</span> 分析系统就绪 - 支持: ${status.features.join(', ')}
            `;
        }
    } catch (error) {
        console.error('❌ Load analytics status error:', error);
    }
}

async function executeAnalyticsQuery() {
    const query = document.getElementById('analytics-query-input').value;
    if (!query) {
        showToast('请输入查询内容', 'error');
        return;
    }
    
    showToast('正在执行分析查询...', 'info');
    
    try {
        const response = await fetch('/api/v1/analytics/query', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ query: query })
        });
        
        const result = await response.json();
        const container = document.getElementById('analytics-results');
        
        container.innerHTML = `
            <div style="background: rgba(30, 41, 59, 0.8); padding: 16px; border-radius: 8px; margin-top: 12px;">
                <h4 style="color: white; margin: 0 0 8px;">📊 查询结果</h4>
                <pre style="color: #a0a0a0; white-space: pre-wrap; font-size: 12px;">
                    ${JSON.stringify(result, null, 2)}
                </pre>
            </div>
        `;
        
        showToast('查询完成', 'success');
    } catch (error) {
        showToast('查询失败: ' + error.message, 'error');
    }
}

/**
 * UI Helpers
 */
function setupEventListeners() {
    // Send message on Enter
    const input = document.getElementById('message-input');
    if (input) {
        input.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendMessage();
            }
        });
    }
}

function showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.innerHTML = `
        <span>${type === 'success' ? '✅' : type === 'error' ? '❌' : 'ℹ️'}</span>
        <span>${message}</span>
    `;
    document.body.appendChild(toast);
    
    setTimeout(() => {
        toast.remove();
    }, 3000);
}

/**
 * Modal and Navigation
 */
function openModal(id) {
    document.getElementById(id).classList.add('show');
    
    // Load relevant data when opening modal
    if (id === 'knowledge-modal') loadKnowledgeBases();
    if (id === 'prompt-modal') loadSkills();
    if (id === 'mcp-modal') loadMcpServers();
    if (id === 'tidy-cup-modal') {
        loadAnalyticsStatus();
        loadSkills();
    }
}

function closeModal(id) {
    document.getElementById(id).classList.remove('show');
}

function toggleSidebar() {
    document.getElementById('sidebar').classList.toggle('open');
    document.getElementById('sidebar-overlay').classList.toggle('open');
}

function closeSidebar() {
    document.getElementById('sidebar').classList.remove('open');
    document.getElementById('sidebar-overlay').classList.remove('open');
}

function showMainChat() {
    // Scroll to top of chat
    window.scrollTo(0, 0);
    closeSidebar();
}

function showTidyTab(tab) {
    // Update tabs
    document.querySelectorAll('#tidy-cup-modal .settings-tab').forEach(t => {
        t.classList.remove('active');
        if (t.textContent.includes(tab === 'overview' ? '概览' : 
            tab === 'tasks' ? '竞赛任务' :
            tab === 'query' ? '查询' :
            tab === 'analyze' ? '分析' :
            tab === 'skills' ? 'AI技能' :
            tab === 'mcp' ? 'MCP工具' :
            tab === 'upload' ? '上传' : '数据源')) {
            t.classList.add('active');
        }
    });
    
    // Show selected section
    document.querySelectorAll('#tidy-cup-modal .settings-section').forEach(s => {
        s.classList.remove('active');
    });
    
    const section = document.getElementById(`tidy-${tab}`);
    if (section) {
        section.classList.add('active');
    }
    
    // Load data for specific tabs
    if (tab === 'skills') loadSkills();
}

function loadTidyDemoData() {
    document.getElementById('db-company-count').textContent = '3';
    document.getElementById('db-record-count').textContent = '2';
    showToast('演示数据加载成功', 'success');
}

function quickTidyQuery(query) {
    const queryInput = document.getElementById('tidy-query-input');
    if (queryInput) {
        queryInput.value = query;
    }
    executeTidyQuery();
}

function executeTidyQuery() {
    const queryInput = document.getElementById('tidy-query-input');
    const query = queryInput ? queryInput.value : '';
    
    if (!query) {
        showToast('请输入查询内容', 'error');
        return;
    }
    
    showToast('正在执行查询...', 'info');
    
    // 使用新的API
    fetch('/api/v1/analytics/query', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: query })
    })
    .then(response => response.json())
    .then(data => {
        const resultDiv = document.getElementById('tidy-query-result');
        if (resultDiv) {
            resultDiv.innerHTML = `
                <div style="background: rgba(30,41,59,0.8); padding:16px; border-radius:10px; border:1px solid rgba(255,255,255,0.1);">
                    <h4 style="color:white; margin:0 0 12px 0;">📊 查询结果</h4>
                    <pre style="color:#a0a0a0; font-size:13px; white-space:pre-wrap;">${JSON.stringify(data, null, 2)}</pre>
                </div>
            `;
        }
        showToast('查询完成', 'success');
    })
    .catch(error => {
        showToast('查询失败: ' + error.message, 'error');
    });
}

function clearTidyQuery() {
    const input = document.getElementById('tidy-query-input');
    if (input) input.value = '';
    document.getElementById('tidy-query-result').innerHTML = '';
}

function handleTidyPdfUpload(event) {
    const file = event.target.files[0];
    if (!file) return;
    
    showToast('正在上传文件...', 'info');
    
    const formData = new FormData();
    formData.append('file', file);
    
    fetch('/api/v1/analytics/upload/pdf', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        const resultDiv = document.getElementById('tidy-upload-result');
        if (resultDiv) {
            resultDiv.innerHTML = `
                <div style="background: rgba(34,197,94,0.15); padding:16px; border-radius:10px; border:1px solid rgba(34,197,94,0.3);">
                    <h4 style="color:white; margin:0 0 8px 0;">✅ PDF上传成功</h4>
                    <pre style="color:#a0a0a0; font-size:13px; white-space:pre-wrap;">${JSON.stringify(data, null, 2)}</pre>
                </div>
            `;
        }
        showToast('文件上传成功', 'success');
    })
    .catch(error => {
        showToast('上传失败: ' + error.message, 'error');
    });
}

// 兼容旧版函数
function showSettingsTab(tab) {
    // 简化实现
    console.log('Settings tab:', tab);
}

function showKbTab(tab) {
    console.log('KB tab:', tab);
}

function showSkillTab(tab) {
    console.log('Skill tab:', tab);
}

function toggleSwitch(el) {
    el.classList.toggle('on');
}

function resetSettings() {
    if (confirm('确定要重置所有设置吗？')) {
        showToast('设置已重置', 'success');
    }
}

function createSkill() {
    showToast('功能开发中', 'info');
}

function createKnowledgeBase() {
    showToast('功能开发中', 'info');
}

function createMcpServer() {
    showToast('功能开发中', 'info');
}

function quickAddMcp(type) {
    showToast(`添加${type}中...`, 'info');
}

function toggleWebSearch() {
    showToast('搜索功能开发中', 'info');
}

function handleFileUpload(event) {
    showToast('文件上传中...', 'info');
}
