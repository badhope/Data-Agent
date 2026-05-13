let ws = null;
let appSettings = {};
let currentKnowledgeBaseId = null;

function connectWS() {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    ws = new WebSocket(protocol + '//' + window.location.host + '/ws');
    ws.onopen = () => console.log('WebSocket connected');
    ws.onmessage = (event) => handleWSMessage(JSON.parse(event.data));
    ws.onclose = () => setTimeout(connectWS, 3000);
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
        
        const existingPhases = thinkingEl.querySelectorAll('.thinking-item').length;
        const phaseNum = existingPhases + 1;
        
        const phaseEl = document.createElement('div');
        phaseEl.className = 'thinking-item';
        phaseEl.innerHTML = `
            <div class="thinking-header" onclick="toggleThinking(this)">
                <div class="thinking-badge">${phaseNum}</div>
                <div class="thinking-title">${data.title}</div>
                <div class="thinking-toggle">▼</div>
            </div>
            <div class="thinking-content">${data.content}</div>
        `;
        
        thinkingEl.appendChild(phaseEl);
        chatArea.scrollTop = chatArea.scrollHeight;
        
    } else if (data.type === 'stream_start') {
        document.querySelector('.thinking-container')?.remove();
        
        const messageEl = document.createElement('div');
        messageEl.className = 'message assistant streaming';
        messageEl.innerHTML = `
            <div class="message-content">
                <div class="message-text"></div>
                <span class="typing-indicator">
                    <span class="typing-dot"></span>
                    <span class="typing-dot"></span>
                    <span class="typing-dot"></span>
                </span>
            </div>
        `;
        chatArea.appendChild(messageEl);
        chatArea.scrollTop = chatArea.scrollHeight;
        
    } else if (data.type === 'stream_data') {
        const streamingEl = document.querySelector('.message.streaming');
        if (streamingEl) {
            const textEl = streamingEl.querySelector('.message-text');
            const indicator = streamingEl.querySelector('.typing-indicator');
            
            textEl.innerHTML += data.content.replace(/\n/g, '<br>');
            indicator.style.display = 'inline-block';
            chatArea.scrollTop = chatArea.scrollHeight;
        }
        
    } else if (data.type === 'stream_end') {
        const streamingEl = document.querySelector('.message.streaming');
        if (streamingEl) {
            streamingEl.classList.remove('streaming');
            const indicator = streamingEl.querySelector('.typing-indicator');
            if (indicator) indicator.remove();
            
            const time = new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' });
            streamingEl.innerHTML += `<div style="font-size: 11px; color: #6b7280; margin-top: 4px; padding-left: 8px;">${time}</div>`;
        }
        finishProcessing();
        
    } else if (data.type === 'response') {
        document.querySelector('.thinking-container')?.remove();
        addMessage(data.content, 'assistant');
        finishProcessing();
    } else if (data.type === 'error') {
        document.querySelector('.thinking-container')?.remove();
        document.querySelector('.message.streaming')?.remove();
        
        const messageEl = document.createElement('div');
        messageEl.className = 'message system error';
        messageEl.innerHTML = `
            <div class="message-content">
                <div style="display: flex; align-items: center; gap: 8px;">
                    <span style="font-size: 18px;">❌</span>
                    <span style="color: #ef4444;">${data.content}</span>
                </div>
            </div>
        `;
        chatArea.appendChild(messageEl);
        chatArea.scrollTop = chatArea.scrollHeight;
        finishProcessing();
    }
}

function toggleThinking(header) {
    const content = header.nextElementSibling;
    const toggle = header.querySelector('.thinking-toggle');
    content.classList.toggle('collapsed');
    toggle.textContent = content.classList.contains('collapsed') ? '▶' : '▼';
}

function addMessage(content, type) {
    const chatArea = document.getElementById('chat-area');
    const messageEl = document.createElement('div');
    messageEl.className = `message ${type}`;
    let formatted = content.replace(/\n/g, '<br>');
    
    const time = new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' });
    
    messageEl.innerHTML = `
        <div class="message-content">
            <div class="message-text">${formatted}</div>
            <div class="message-actions">
                <button class="message-action-btn" onclick="copyMessage(this)" title="复制">📋</button>
            </div>
        </div>
        <div style="font-size: 11px; color: #6b7280; margin-top: 4px; ${type === 'user' ? 'text-align: right; padding-right: 8px;' : 'padding-left: 8px;'}">${time}</div>
    `;
    
    chatArea.appendChild(messageEl);
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

function showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.innerHTML = `
        <span>${type === 'success' ? '✅' : type === 'error' ? '❌' : 'ℹ️'}</span>
        <span>${message}</span>
    `;
    document.body.appendChild(toast);
    
    setTimeout(() => toast.classList.add('show'), 10);
    
    setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

function createRipple(event) {
    const button = event.currentTarget;
    const circle = document.createElement('span');
    const diameter = Math.max(button.clientWidth, button.clientHeight);
    const radius = diameter / 2;
    
    const rect = button.getBoundingClientRect();
    circle.style.width = circle.style.height = `${diameter}px`;
    circle.style.left = `${event.clientX - rect.left - radius}px`;
    circle.style.top = `${event.clientY - rect.top - radius}px`;
    circle.className = 'ripple';
    
    const ripple = button.getElementsByClassName('ripple')[0];
    if (ripple) ripple.remove();
    
    button.appendChild(circle);
}

function sendMessage() {
    const inputBox = document.getElementById('input-box');
    const content = inputBox.value.trim();
    if (!content || !ws || ws.readyState !== WebSocket.OPEN) return;
    inputBox.value = '';
    addMessage(content, 'user');
    document.getElementById('send-btn').disabled = true;
    
    const webSearchEnabled = document.getElementById('web-search-btn').classList.contains('active');
    ws.send(JSON.stringify({ 
        content: content,
        options: {
            web_search: webSearchEnabled
        }
    }));
}

function toggleWebSearch() {
    const btn = document.getElementById('web-search-btn');
    btn.classList.toggle('active');
    if (btn.classList.contains('active')) {
        showToast('已启用联网搜索', 'success');
    } else {
        showToast('已关闭联网搜索', 'info');
    }
}

function insertCommand(command) {
    const inputBox = document.getElementById('input-box');
    if (inputBox.value.length > 0) {
        inputBox.value += '\n';
    }
    inputBox.value += command;
    inputBox.focus();
    inputBox.scrollTop = inputBox.scrollHeight;
}

function handleFileUpload(event) {
    const files = event.target.files;
    if (files.length > 0) {
        uploadFiles(files);
    }
}

async function uploadFiles(files) {
    const progressDiv = document.getElementById('upload-progress');
    const errorDiv = document.getElementById('upload-error');
    const errorMsg = document.getElementById('upload-error-message');
    const progressBar = document.getElementById('upload-progress-bar');
    const uploadStatus = document.getElementById('upload-status');
    
    progressDiv.style.display = 'block';
    errorDiv.style.display = 'none';
    progressBar.style.width = '0%';
    uploadStatus.textContent = '准备上传...';
    
    const allowedExtensions = ['.pdf', '.txt', '.md', '.docx', '.csv', '.xlsx', '.xls', '.ppt', '.pptx'];
    const maxSize = 50 * 1024 * 1024;
    
    try {
        for (let i = 0; i < files.length; i++) {
            const file = files[i];
            const ext = '.' + file.name.split('.').pop().toLowerCase();
            
            if (!allowedExtensions.includes(ext)) {
                throw new Error(`文件 ${file.name} 的格式不受支持`);
            }
            
            if (file.size > maxSize) {
                throw new Error(`文件 ${file.name} 太大，最大支持50MB`);
            }
        }
        
        let kbId = currentKnowledgeBaseId;
        if (!kbId) {
            try {
                const res = await fetch('/api/knowledge-bases', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ 
                        name: '默认知识库', 
                        description: '用于存储上传的文档' 
                    })
                });
                const kb = await res.json();
                kbId = kb.id;
            } catch (e) {
                throw new Error('无法创建知识库，请刷新页面重试');
            }
        }
        
        let successCount = 0;
        for (let i = 0; i < files.length; i++) {
            const file = files[i];
            uploadStatus.textContent = `正在上传: ${file.name} (${i + 1}/${files.length})`;
            
            const formData = new FormData();
            formData.append('file', file);
            
            try {
                const res = await fetch(`/api/knowledge-bases/${kbId}/documents`, {
                    method: 'POST',
                    body: formData
                });
                
                if (!res.ok) {
                    const errorData = await res.json().catch(() => ({ detail: '上传失败' }));
                    throw new Error(`${file.name}: ${errorData.detail}`);
                }
                
                successCount++;
                progressBar.style.width = `${((i + 1) / files.length) * 100}%`;
                
            } catch (e) {
                throw new Error(e.message || `上传 ${file.name} 失败`);
            }
        }
        
        progressBar.style.width = '100%';
        uploadStatus.textContent = `✅ 成功上传 ${successCount} 个文件`;
        
        setTimeout(() => {
            progressDiv.style.display = 'none';
            showSuccess(`已上传 ${successCount} 个文档到知识库`);
            loadKnowledgeBases();
        }, 1500);
        
    } catch (e) {
        progressDiv.style.display = 'none';
        errorDiv.style.display = 'block';
        errorMsg.textContent = e.message;
        console.error('Upload error:', e);
    }
    
    if (event && event.target) {
        event.target.value = '';
    }
}

function formatFileSize(bytes) {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
}

function finishProcessing() {
    document.getElementById('send-btn').disabled = false;
    document.getElementById('chat-area').scrollTop = document.getElementById('chat-area').scrollHeight;
}

function clearChat() {
    const chatArea = document.getElementById('chat-area');
    chatArea.innerHTML = '<div class="message system"><div class="message-content">欢迎使用 DATA-AI！</div></div>';
}

function toggleSidebar() {
    const sidebar = document.getElementById('sidebar');
    const overlay = document.getElementById('sidebar-overlay');
    sidebar.classList.toggle('open');
    overlay.classList.toggle('show');
}

function closeSidebar() {
    const sidebar = document.getElementById('sidebar');
    const overlay = document.getElementById('sidebar-overlay');
    sidebar.classList.remove('open');
    overlay.classList.remove('show');
}

function openModal(id) {
    document.getElementById(id).classList.add('show');
    if (id === 'knowledge-modal') loadKnowledgeBases();
    if (id === 'prompt-modal') loadSkills();
    if (id === 'mcp-modal') loadMcpServers();
}

function closeModal(id) {
    document.getElementById(id).classList.remove('show');
}

function toggleSwitch(el) {
    el.classList.toggle('on');
}

function showSettingsTab(tab) {
    document.querySelectorAll('.settings-tab').forEach(t => t.classList.remove('active'));
    document.querySelectorAll('.settings-section').forEach(s => s.classList.remove('active'));
    event.target.classList.add('active');
    document.getElementById(`settings-${tab}`).classList.add('active');
}

function showKbTab(tab) {
    document.querySelectorAll('#knowledge-modal .settings-tab').forEach(t => t.classList.remove('active'));
    document.querySelectorAll('#knowledge-modal .settings-section').forEach(s => s.classList.remove('active'));
    event.target.classList.add('active');
    document.getElementById(`kb-${tab}`).classList.add('active');
}

function showSkillTab(tab) {
    document.querySelectorAll('#prompt-modal .settings-tab').forEach(t => t.classList.remove('active'));
    document.querySelectorAll('#prompt-modal .settings-section').forEach(s => s.classList.remove('active'));
    event.target.classList.add('active');
    document.getElementById(`skill-${tab}`).classList.add('active');
}

function showMainChat() {
    document.querySelectorAll('.nav-item').forEach(el => el.classList.remove('active'));
    event.currentTarget.classList.add('active');
}

async function loadSettings() {
    try {
        const res = await fetch('/api/settings');
        appSettings = await res.json();
        populateSettings(appSettings);
    } catch (e) { console.log(e); }
}

function populateSettings(settings) {
    document.getElementById('setting-provider').value = settings.llm.provider;
    document.getElementById('setting-model').value = settings.llm.model;
    document.getElementById('setting-base-url').value = settings.llm.base_url;
    document.getElementById('setting-api-key').value = settings.llm.api_key;
    document.getElementById('setting-max-tokens').value = settings.llm.max_tokens;
    document.getElementById('setting-temperature').value = settings.llm.temperature;
    document.getElementById('setting-sandbox-timeout').value = settings.sandbox.timeout;
    
    if (settings.langsmith) {
        if (settings.langsmith.enabled) {
            document.getElementById('setting-langsmith-enabled').classList.add('on');
        }
        document.getElementById('setting-langsmith-api-key').value = settings.langsmith.api_key || '';
        document.getElementById('setting-langsmith-project').value = settings.langsmith.project || 'dataagent';
        document.getElementById('setting-langsmith-endpoint').value = settings.langsmith.endpoint || 'https://api.smith.langchain.com';
    }
}

async function saveSettings() {
    const settings = {
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
        knowledge_base: {
            enabled: document.getElementById('setting-kb-enabled').classList.contains('on'),
            vector_db: 'sqlite',
            chunk_size: 1000,
            chunk_overlap: 200,
            embedding_model: 'text-embedding-v3'
        },
        conversation: { history_enabled: true, max_history: 50, auto_title: true },
        display: { theme: 'dark', thinking_chain: true, code_highlight: true, markdown_render: true },
        agent: { max_steps: 5, auto_mode: true, reasoning_mode: 'auto' },
        langsmith: {
            enabled: document.getElementById('setting-langsmith-enabled').classList.contains('on'),
            api_key: document.getElementById('setting-langsmith-api-key').value,
            project: document.getElementById('setting-langsmith-project').value,
            endpoint: document.getElementById('setting-langsmith-endpoint').value
        }
    };
    
    if (!settings.llm.api_key) {
        showError('请输入API Key');
        return;
    }
    if (!settings.llm.base_url) {
        showError('请输入Base URL');
        return;
    }
    if (!settings.llm.max_tokens || settings.llm.max_tokens < 1) {
        showError('最大Token必须大于0');
        return;
    }
    if (settings.llm.temperature < 0 || settings.llm.temperature > 2) {
        showError('温度系数必须在0-2之间');
        return;
    }
    
    try {
        const res = await fetch('/api/settings', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(settings)
        });
        
        if (!res.ok) {
            const errorData = await res.json().catch(() => ({ detail: '保存失败' }));
            throw new Error(errorData.detail || `请求失败 (${res.status})`);
        }
        
        appSettings = settings;
        closeModal('settings-modal');
        showSuccess('设置已保存成功！');
        
    } catch (e) {
        showError(`保存失败: ${e.message}`);
        console.error('Save settings error:', e);
    }
}

function resetSettings() {
    document.getElementById('setting-provider').value = 'aliyun';
    document.getElementById('setting-model').value = 'qwen-plus-latest';
    document.getElementById('setting-base-url').value = 'https://dashscope.aliyuncs.com/compatible-mode/v1';
    document.getElementById('setting-api-key').value = '';
}

async function loadKnowledgeBases() {
    try {
        const res = await fetch('/api/knowledge-bases');
        const kbs = await res.json();
        const grid = document.getElementById('kb-grid');
        if (kbs.length === 0) {
            grid.innerHTML = '<div style="color: #94a3b8; text-align: center; padding: 40px;">还没有知识库，点击上方标签创建</div>';
        } else {
            grid.innerHTML = kbs.map(kb => `
                <div class="kb-card">
                    <div class="kb-card-icon">📚</div>
                    <h4>${kb.name}</h4>
                    <p>${kb.description || '暂无描述'}</p>
                    <div class="kb-meta">
                        <span>创建: ${new Date(kb.created_at).toLocaleDateString()}</span>
                    </div>
                </div>
            `).join('');
        }
    } catch (e) {
        console.log(e);
    }
}

async function createKnowledgeBase() {
    const name = document.getElementById('kb-name').value.trim();
    const desc = document.getElementById('kb-desc').value.trim();
    
    if (!name) {
        showError('请输入知识库名称', 'kb-create');
        return;
    }
    if (name.length > 50) {
        showError('知识库名称不能超过50个字符', 'kb-create');
        return;
    }
    
    try {
        const res = await fetch('/api/knowledge-bases', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name, description: desc })
        });
        
        if (!res.ok) {
            const errorData = await res.json().catch(() => ({ detail: '创建失败' }));
            throw new Error(errorData.detail || `请求失败 (${res.status})`);
        }
        
        const result = await res.json();
        document.getElementById('kb-name').value = '';
        document.getElementById('kb-desc').value = '';
        loadKnowledgeBases();
        showKbTab('list');
        showSuccess(`知识库 "${name}" 创建成功！`);
        
    } catch (e) {
        showError(`创建知识库失败: ${e.message}`, 'kb-create');
        console.error('Create knowledge base error:', e);
    }
}

async function loadSkills() {
    try {
        const res = await fetch('/api/skills');
        const skills = await res.json();
        const list = document.getElementById('skill-list-content');
        list.innerHTML = skills.map(skill => `
            <div class="skill-item">
                <div class="skill-info">
                    <div class="skill-icon">${skill.icon}</div>
                    <div class="skill-details">
                        <h4>${skill.name}</h4>
                        <p>${skill.description}</p>
                    </div>
                </div>
                <span class="skill-badge">${skill.type}</span>
            </div>
        `).join('');
    } catch (e) {
        console.log(e);
    }
}

async function createSkill() {
    const name = document.getElementById('skill-name').value.trim();
    const icon = document.getElementById('skill-icon').value.trim() || '⚡';
    const desc = document.getElementById('skill-desc').value.trim();
    
    if (!name) {
        showError('请输入技能名称', 'skill-create');
        return;
    }
    if (name.length > 50) {
        showError('技能名称不能超过50个字符', 'skill-create');
        return;
    }
    if (desc && desc.length > 500) {
        showError('描述不能超过500个字符', 'skill-create');
        return;
    }
    
    try {
        const res = await fetch('/api/skills', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name, icon, description: desc, parameters: [], prompts: {} })
        });
        
        if (!res.ok) {
            const errorData = await res.json().catch(() => ({ detail: '创建失败' }));
            throw new Error(errorData.detail || `请求失败 (${res.status})`);
        }
        
        await res.json();
        document.getElementById('skill-name').value = '';
        document.getElementById('skill-desc').value = '';
        loadSkills();
        showSkillTab('list');
        showSuccess(`技能 "${name}" 创建成功！`);
        
    } catch (e) {
        showError(`创建技能失败: ${e.message}`, 'skill-create');
        console.error('Create skill error:', e);
    }
}

async function aiGenerateSkill() {
    const purpose = document.getElementById('skill-purpose').value.trim();
    const generatingDiv = document.getElementById('ai-generating');
    
    if (!purpose) {
        showError('请先描述技能用途', 'skill-create');
        return;
    }
    
    generatingDiv.style.display = 'block';
    
    try {
        const res = await fetch('/api/skills/generate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ purpose })
        });
        
        if (!res.ok) {
            const errorData = await res.json().catch(() => ({ detail: '生成失败' }));
            throw new Error(errorData.detail || `请求失败 (${res.status})`);
        }
        
        const result = await res.json();
        
        document.getElementById('skill-name').value = result.name || '';
        document.getElementById('skill-icon').value = result.icon || '⚡';
        document.getElementById('skill-desc').value = result.description || '';
        
        generatingDiv.style.display = 'none';
        showSuccess('AI已为您生成技能建议！');
        
    } catch (e) {
        generatingDiv.style.display = 'none';
        showError('AI生成失败: ' + e.message, 'skill-create');
        console.error('AI generate error:', e);
    }
}

async function loadMcpServers() {
    try {
        const res = await fetch('/api/mcp/servers');
        const servers = await res.json();
        const list = document.getElementById('mcp-list-content');
        if (servers.length === 0) {
            list.innerHTML = '<div style="color: #94a3b8; text-align: center; padding: 40px;">还没有配置MCP服务器</div>';
        } else {
            list.innerHTML = servers.map(s => `
                <div class="mcp-item">
                    <div class="skill-info">
                        <div class="skill-icon">${s.icon}</div>
                        <div class="skill-details">
                            <h4>${s.name}</h4>
                            <p>类型: ${s.type}</p>
                        </div>
                    </div>
                    <div class="setting-switch ${s.enabled ? 'on' : ''}" onclick="toggleSwitch(this)"></div>
                </div>
            `).join('');
        }
    } catch (e) {
        console.log(e);
    }
}

async function createMcpServer() {
    const name = document.getElementById('mcp-name').value.trim();
    const type = document.getElementById('mcp-type').value;
    const command = document.getElementById('mcp-command').value.trim();
    
    if (!name) {
        showError('请输入MCP服务器名称', 'mcp-create');
        return;
    }
    if (name.length > 50) {
        showError('名称不能超过50个字符', 'mcp-create');
        return;
    }
    if (!command && type === 'process') {
        showError('请输入启动命令', 'mcp-create');
        return;
    }
    
    try {
        const res = await fetch('/api/mcp/servers', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name, type, command, args: [], enabled: true })
        });
        
        if (!res.ok) {
            const errorData = await res.json().catch(() => ({ detail: '创建失败' }));
            throw new Error(errorData.detail || `请求失败 (${res.status})`);
        }
        
        await res.json();
        document.getElementById('mcp-name').value = '';
        document.getElementById('mcp-command').value = '';
        loadMcpServers();
        showSuccess(`MCP服务器 "${name}" 配置成功！`);
        
    } catch (e) {
        showError(`配置MCP服务器失败: ${e.message}`, 'mcp-create');
        console.error('Create MCP server error:', e);
    }
}

function quickAddMcp(type) {
    const mcpPresets = {
        'filesystem': {
            name: '📁 文件系统',
            command: 'npx',
            args: ['-y', '@modelcontextprotocol/server-filesystem', '/']
        },
        'github': {
            name: '🐙 GitHub',
            command: 'npx',
            args: ['-y', '@modelcontextprotocol/server-github']
        },
        'notion': {
            name: '📓 Notion',
            command: 'npx',
            args: ['-y', '@modelcontextprotocol/server-notion']
        },
        'brave': {
            name: '🔍 Brave搜索',
            command: 'npx',
            args: ['-y', '@modelcontextprotocol/server-brave-search']
        },
        'sqlite': {
            name: '🗄️ SQLite',
            command: 'npx',
            args: ['-y', '@modelcontextprotocol/server-sqlite']
        },
        'postgres': {
            name: '🐘 PostgreSQL',
            command: 'npx',
            args: ['-y', '@modelcontextprotocol/server-postgres']
        },
        'slack': {
            name: '💬 Slack',
            command: 'npx',
            args: ['-y', '@modelcontextprotocol/server-slack']
        },
        'gmail': {
            name: '📧 Gmail',
            command: 'npx',
            args: ['-y', '@modelcontextprotocol/server-gmail']
        }
    };
    
    const preset = mcpPresets[type];
    if (preset) {
        document.getElementById('mcp-name').value = preset.name;
        document.getElementById('mcp-type').value = 'stdio';
        document.getElementById('mcp-command').value = preset.command + ' ' + preset.args.join(' ');
        showSuccess(`已填充 ${preset.name} 配置！请添加后配置相关环境变量`);
    }
}

function showError(message, targetId = null) {
    if (targetId) {
        const target = document.getElementById(targetId);
        if (target) {
            const errorDiv = document.createElement('div');
            errorDiv.className = 'error-message';
            errorDiv.style.cssText = 'margin-top: 8px; padding: 10px; background: rgba(239, 68, 68, 0.15); border: 1px solid rgba(239, 68, 68, 0.3); border-radius: 8px; color: #f87171; font-size: 13px;';
            errorDiv.textContent = '❌ ' + message;
            target.appendChild(errorDiv);
            setTimeout(() => errorDiv.remove(), 5000);
        }
    } else {
        addMessage('❌ ' + message, 'system');
    }
}

function showSuccess(message) {
    addMessage('✅ ' + message, 'system');
}

document.getElementById('input-box').addEventListener('keydown', function(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
    }
});

document.addEventListener('keydown', function(e) {
    if ((e.metaKey || e.ctrlKey) && e.key === 'Enter') {
        e.preventDefault();
        sendMessage();
    }
});

document.addEventListener('click', function(e) {
    if (e.target.classList.contains('modal-overlay')) {
        e.target.classList.remove('show');
    }
});

window.onload = function() {
    connectWS();
    loadSettings();
};
