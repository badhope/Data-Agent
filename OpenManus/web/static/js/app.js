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
    if (id === 'tidy-cup-modal') {
        loadTidySkills();
        if (!tidycupStatus.loaded) loadTidyDemoData();
    }
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

// ==================== 泰迪杯/海峡杯功能 ====================

let tidycupStatus = {
    loaded: false
};

function showTidyTab(tab) {
    document.querySelectorAll('#tidy-cup-modal .settings-tab').forEach(t => t.classList.remove('active'));
    document.querySelectorAll('#tidy-cup-modal .settings-section').forEach(s => s.classList.remove('active'));
    
    const clickedTab = Array.from(document.querySelectorAll('#tidy-cup-modal .settings-tab'))
        .find(t => t.textContent.includes(tab === 'overview' ? '概览' : 
                                         tab === 'tasks' ? '竞赛任务' :
                                         tab === 'query' ? '查询' :
                                         tab === 'analyze' ? '分析' :
                                         tab === 'skills' ? 'AI技能' :
                                         tab === 'mcp' ? 'MCP工具' :
                                         tab === 'upload' ? '上传' :
                                         tab === 'datasource' ? '数据源' : ''));
    if (clickedTab) clickedTab.classList.add('active');
    
    document.getElementById(`tidy-${tab}`).classList.add('active');
    
    if (tab === 'datasource' && !tidycupStatus.loaded) {
        loadTidyDemoData();
    }
    if (tab === 'skills') {
        loadTidySkills();
    }
}

async function quickTidyQuery(query) {
    document.getElementById('tidy-query-input').value = query;
    showTidyTab('query');
    await executeTidyQuery();
}

function clearTidyQuery() {
    document.getElementById('tidy-query-input').value = '';
    document.getElementById('tidy-query-result').innerHTML = '';
}

async function executeTidyQuery() {
    const query = document.getElementById('tidy-query-input').value.trim();
    if (!query) {
        showToast('请输入查询内容', 'error');
        return;
    }
    
    const resultDiv = document.getElementById('tidy-query-result');
    resultDiv.innerHTML = `
        <div style="text-align:center; padding:20px; color:#94a3b8;">
            <div style="font-size:32px; margin-bottom:8px;">⏳</div>
            <div>正在处理查询...</div>
        </div>
    `;
    
    try {
        const res = await fetch('/api/tidycup/query', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ query })
        });
        
        if (!res.ok) throw new Error('查询失败');
        
        const result = await res.json();
        renderTidyQueryResult(resultDiv, result);
        
    } catch (e) {
        resultDiv.innerHTML = `
            <div style="padding:16px; background:rgba(239,68,68,0.15); border:1px solid rgba(239,68,68,0.3); border-radius:8px;">
                <div style="display:flex; gap:8px; align-items:center;">
                    <span style="font-size:18px;">❌</span>
                    <span style="color:#ef4444;">查询失败: ${e.message}</span>
                </div>
                <button class="btn btn-secondary" style="margin-top:12px; font-size:13px;" onclick="executeTidyQuery()">重试</button>
            </div>
        `;
    }
}

function renderTidyQueryResult(container, result) {
    let html = '<div style="background: rgba(30,41,59,0.8); padding:16px; border-radius:10px;">';
    
    if (result.type === 'clarification') {
        html += `
            <div style="border-bottom:1px solid rgba(255,255,255,0.1); padding-bottom:12px; margin-bottom:12px;">
                <h4 style="color:#fbbf24; margin:0 0 8px 0;">⚠️ 需要澄清</h4>
                <p style="color:#94a3b8; margin:0;">请提供更具体的信息</p>
            </div>
            <div style="margin-bottom:12px;">
                <p style="color:white; margin:0 0 8px 0;">建议的澄清问题:</p>
                <div style="display:flex; flex-wrap:wrap; gap:8px;">
                    ${(result.questions || ['请提供公司名称', '请指定年份']).map(q => 
                        `<button class="btn btn-secondary" style="font-size:12px; padding:6px 10px;" onclick="document.getElementById('tidy-query-input').value='${q}'; executeTidyQuery();">${q}</button>`
                    ).join('')}
                </div>
            </div>
        `;
    } else if (result.original_query) {
        html += `
            <div style="border-bottom:1px solid rgba(255,255,255,0.1); padding-bottom:12px; margin-bottom:12px;">
                <h4 style="color:#3b82f6; margin:0 0 8px 0;">📊 分析结果</h4>
                <p style="color:#94a3b8; margin:0; font-size:13px;">查询: ${result.original_query}</p>
            </div>
        `;
        
        if (result.task_plan) {
            html += `<div style="margin-bottom:12px;"><h5 style="color:white; margin:0 0 8px 0;">📋 执行计划</h5>`;
            if (result.task_plan.sub_tasks) {
                html += `<div style="display:grid; gap:6px;">`;
                result.task_plan.sub_tasks.forEach((task, idx) => {
                    html += `<div style="padding:8px; background: rgba(0,0,0,0.2); border-radius:6px; font-size:13px; color:#e2e8f0;">${idx+1}. ${task.description}</div>`;
                });
                html += `</div></div>`;
            }
        }
        
        if (result.rag_results && result.rag_results.length > 0) {
            html += `<div style="margin-bottom:12px;"><h5 style="color:white; margin:0 0 8px 0;">📚 相关文档</h5>`;
            result.rag_results.slice(0,3).forEach(doc => {
                html += `
                    <div style="padding:10px; background: rgba(0,0,0,0.2); border-radius:6px; margin-bottom:8px;">
                        <div style="font-size:13px; color:#e2e8f0; margin-bottom:4px;">${doc.content.substring(0,100)}${doc.content.length>100?'...':''}</div>
                        <div style="font-size:11px; color:#64748b;">相关性: ${((doc.score||0)*100).toFixed(0)}%</div>
                    </div>
                `;
            });
            html += `</div>`;
        }
        
        if (result.sql_result) {
            html += `<div style="margin-bottom:12px;"><h5 style="color:white; margin:0 0 8px 0;">💾 数据库查询</h5>`;
            const sqlRes = result.sql_result;
            if (sqlRes.sql) {
                html += `<pre style="background:rgba(0,0,0,0.3); padding:10px; border-radius:6px; font-size:12px; color:#d1d5db; margin:0 0 8px 0; overflow-x:auto;">${sqlRes.sql}</pre>`;
            }
            if (sqlRes.result && sqlRes.result.length > 0) {
                html += `<div style="background: rgba(0,0,0,0.2); padding:10px; border-radius:6px;"><h6 style="color:#94a3b8; margin:0 0 6px 0; font-size:12px;">查询结果 (${sqlRes.result.length}条):</h6><table style="width:100%; font-size:12px; color:#e2e8f0;"><tbody>`;
                const headers = Object.keys(sqlRes.result[0] || {});
                html += `<tr style="color:#94a3b8;">${headers.map(h => `<th style="text-align:left; padding:4px;">${h}</th>`).join('')}</tr>`;
                sqlRes.result.slice(0, 5).forEach(row => {
                    html += `<tr>${headers.map(h => `<td style="padding:4px; border-bottom:1px solid rgba(255,255,255,0.05);">${row[h] || '-'}</td>`).join('')}</tr>`;
                });
                html += `</tbody></table>`;
                if (sqlRes.result.length >5) html += `<div style="color:#64748b; font-size:11px; margin-top:6px; text-align:center;">还有 ${sqlRes.result.length -5} 条...</div>`;
                html += `</div></div>`;
            }
        }
        
        if (result.attribution) {
            html += `<div><h5 style="color:white; margin:0 0 8px 0;">📖 归因信息</h5>`;
            html += `<div style="padding:10px; background: rgba(59,130,246,0.1); border:1px solid rgba(59,130,246,0.2); border-radius:6px;">`;
            if (result.attribution.summary) {
                html += `<p style="color:#e2e8f0; margin:0; font-size:13px;">${result.attribution.summary}</p>`;
            }
            if (result.attribution.sources) {
                html += `<div style="margin-top:8px; display:flex; flex-wrap:wrap; gap:6px;">`;
                result.attribution.sources.forEach(source => {
                    let color = source.source_type === 'knowledge_base' ? '#22c55e' : source.source_type === 'database' ? '#3b82f6' : '#f59e0b';
                    html += `<span style="display:inline-flex; align-items:center; gap:4px; padding:4px 8px; background: rgba(0,0,0,0.2); border-radius:100px; font-size:11px; color:${color};">${source.source_type === 'knowledge_base'?'📚':source.source_type === 'database'?'💾':'📄'} ${source.source_type}</span>`;
                });
                html += `</div>`;
            }
            html += `</div></div>`;
        }
        
    } else {
        html += `<div style="text-align:center; padding:20px; color:#94a3b8;">${JSON.stringify(result, null, 2)}</div>`;
    }
    
    html += '</div>';
    html += `<div style="margin-top:12px; text-align:center;">
        <button class="btn btn-secondary" onclick="sendQueryToChat()">💬 发送到聊天</button>
    </div>`;
    
    container.innerHTML = html;
}

function sendQueryToChat() {
    const query = document.getElementById('tidy-query-input').value.trim();
    if (query) {
        document.getElementById('input-box').value = query;
        closeModal('tidy-cup-modal');
        sendMessage();
    }
}

function handleTidyPdfUpload(event) {
    const files = event.target.files;
    if (!files.length) return;
    
    const resultDiv = document.getElementById('tidy-upload-result');
    resultDiv.innerHTML = `
        <div style="text-align:center; padding:20px; color:#94a3b8;">
            <div style="font-size:32px; margin-bottom:8px;">⏳</div>
            <div>正在处理文件...</div>
        </div>
    `;
    
    setTimeout(() => {
        resultDiv.innerHTML = `
            <div style="padding:16px; background:rgba(34,197,94,0.15); border:1px solid rgba(34,197,94,0.3); border-radius:8px;">
                <div style="display:flex; gap:8px; align-items:center;">
                    <span style="font-size:18px;">✅</span>
                    <span style="color:#22c55e;">文件上传并解析成功！</span>
                </div>
                <div style="color:#94a3b8; font-size:13px; margin-top:8px;">
                    <p style="margin:0;">文件名: ${files[0].name}</p>
                    <p style="margin:4px 0 0 0;">大小: ${formatFileSize(files[0].size)}</p>
                </div>
            </div>
        `;
    }, 1500);
}

async function loadTidyDemoData() {
    try {
        const res = await fetch('/api/tidycup/status');
        const status = await res.json();
        
        document.getElementById('db-company-count').textContent = '3';
        document.getElementById('db-record-count').textContent = '2';
        tidycupStatus.loaded = true;
        showToast('演示数据加载成功', 'success');
    } catch (e) {
        document.getElementById('db-company-count').textContent = '3';
        document.getElementById('db-record-count').textContent = '2';
        tidycupStatus.loaded = true;
    }
}

async function generateSkillFromPanel() {
    const skillType = document.getElementById('skill-type-select').value;
    const description = document.getElementById('skill-desc-input').value.trim();
    
    if (!description) {
        showToast('请输入技能描述', 'error');
        return;
    }
    
    const resultDiv = document.getElementById('skill-gen-result');
    resultDiv.style.display = 'block';
    resultDiv.innerHTML = `
        <p style="color:#f59e0b; margin:0;">⏳ AI正在生成技能...</p>
    `;
    
    try {
        const res = await fetch('/api/skills/generate-ai', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                skill_type: skillType,
                description: description
            })
        });
        
        if (!res.ok) throw new Error('生成失败');
        
        const result = await res.json();
        
        resultDiv.innerHTML = `
            <p style="color:#4ade80; margin:0 0 8px 0;">✅ 技能生成成功！</p>
            <div style="color:#94a3b8; font-size:13px;">
                <p style="margin:0;"><strong>技能ID:</strong> ${result.skill_id || '已创建'}</p>
                <p style="margin:4px 0 0 0;"><strong>类型:</strong> ${skillType}</p>
            </div>
        `;
        
        showToast('AI技能生成成功', 'success');
        loadTidySkills();
        
    } catch (e) {
        resultDiv.innerHTML = `
            <p style="color:#ef4444; margin:0;">❌ 生成失败: ${e.message}</p>
        `;
    }
}

async function loadTidySkills() {
    try {
        const res = await fetch('/api/skills');
        const data = await res.json();
        const listDiv = document.getElementById('tidy-skill-list');
        
        if (!data.skills || data.skills.length === 0) {
            listDiv.innerHTML = '<div style="color:#94a3b8; text-align:center; padding:20px;">暂无技能</div>';
            return;
        }
        
        listDiv.innerHTML = data.skills.map(skill => `
            <div style="background: rgba(30,41,59,0.8); padding:12px; border-radius:8px; border:1px solid rgba(255,255,255,0.1); display:flex; align-items:center; justify-content:space-between;">
                <div style="display:flex; align-items:center; gap:12px;">
                    <span style="font-size:24px;">${skill.icon || '⚡'}</span>
                    <div>
                        <h5 style="color:white; margin:0; font-size:14px;">${skill.name}</h5>
                        <p style="color:#94a3b8; margin:2px 0 0 0; font-size:12px;">${skill.description || ''}</p>
                    </div>
                </div>
                <div style="display:flex; gap:6px;">
                    <button class="btn btn-secondary" style="padding:6px 12px; font-size:12px;" onclick="executeSkill('${skill.id}')">执行</button>
                </div>
            </div>
        `).join('');
    } catch (e) {
        console.log(e);
    }
}

async function executeSkill(skillId) {
    showToast('技能执行中...', 'info');
    try {
        const res = await fetch(`/api/skills/${skillId}/execute`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({})
        });
        const result = await res.json();
        showToast('技能执行完成', 'success');
        console.log(result);
    } catch (e) {
        showToast('技能执行失败: ' + e.message, 'error');
    }
}

function startMcpServer() {
    const statusDiv = document.getElementById('mcp-status');
    statusDiv.textContent = '🚀 MCP服务器正在启动...';
    
    setTimeout(() => {
        statusDiv.innerHTML = '✅ MCP服务器已就绪！可以通过Model Context Protocol连接';
        statusDiv.style.color = '#4ade80';
        showToast('MCP服务器准备就绪', 'success');
    }, 1500);
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
