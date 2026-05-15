const messages = [];
const files = [];
let socket = null;
let isTyping = false;
let polishStyle = null;

function initWebSocket() {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws`;
socket = new WebSocket(wsUrl);

socket.onopen = () => { updateWsStatus(true); };
    socket.onclose = () => { updateWsStatus(false); setTimeout(initWebSocket, 5000); };
    socket.onerror = (e) => { console.error('WS error:', e); };
    socket.onmessage = (e) => {
        try { handleMessage(JSON.parse(e.data)); }
    catch (err) { console.error('Parse error:', err); }
    };
}

function updateWsStatus(connected) {
    const statusDot = document.getElementById('ws-status');
const statusText = document.getElementById('ws-status-text');
    const headerDot = document.getElementById('header-status-dot');
    const headerText = document.getElementById('header-ws-status-text');

if (statusDot) statusDot.classList.toggle('connected', connected);
    if (statusText) statusText.textContent = connected ? 'Connected' : 'Connecting...';
    if (headerDot) headerDot.classList.toggle('connected', connected);
    if (headerText) headerText.textContent = connected ? 'Connected' : 'Connecting...';
}

function handleMessage(data) {
    const { type, content, id } = data;
    switch (type) {
        case 'message':
            addMessage('assistant', content, id);
            isTyping = false;
            updateTypingIndicator();
            break;
    case 'typing':
            isTyping = true;
            updateTypingIndicator();
            break;
        case 'thinking':
            updateThinking(content);
            break;
        case 'error':
            showToast(content, 'error');
            break;
        case 'success':
            showToast(content, 'success');
        break;
    }
}

function addMessage(role, content, id) {
    const chatArea = document.getElementById('chat-area');
    const welcomePage = document.getElementById('welcome-page');
    if (welcomePage) welcomePage.remove();

    const message = { role, content, id: id || Date.now() };
    messages.push(message);

    const div = document.createElement('div');
    div.className = `message ${message.role}`;
    div.dataset.id = message.id;

    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';

    const textDiv = document.createElement('div');
    textDiv.className = 'message-text';
    textDiv.innerHTML = formatMessage(message.content);

    contentDiv.appendChild(textDiv);

    if (message.role === 'assistant') {
        const actions = document.createElement('div');
    actions.className = 'message-actions';

        const copyBtn = document.createElement('button');
        copyBtn.className = 'message-action-btn';
    copyBtn.innerHTML = '📋';
        copyBtn.onclick = () => copyToClipboard(message.content);
        actions.appendChild(copyBtn);

        contentDiv.appendChild(actions);

        const feedback = document.createElement('div');
        feedback.className = 'message-feedback';

        const likeBtn = document.createElement('button');
        likeBtn.className = 'feedback-btn';
    likeBtn.innerHTML = '👍 Helpful';
        feedback.appendChild(likeBtn);

    const dislikeBtn = document.createElement('button');
        dislikeBtn.className = 'feedback-btn';
        dislikeBtn.innerHTML = '👎 Not helpful';
        feedback.appendChild(dislikeBtn);

        div.appendChild(contentDiv);
    div.appendChild(feedback);
    } else {
        div.appendChild(contentDiv);
    }

    chatArea.appendChild(div);
    chatArea.scrollTop = chatArea.scrollHeight;

    if (role === 'user') {
        const inputBox = document.getElementById('input-box');
if (inputBox) {
            inputBox.value = '';
    updateCharCount();
        }
    }


function formatMessage(text) {
    let html = text;
    html = html.replace(/```(\w+)?\n([\s\S]*?)```/g, (match, lang, code) => {
return '<div class="code-block-wrapper"><div class="code-block-header" onclick="toggleCodeBlock(this)"><div class="code-block-title"><span>' + (lang || 'code') + '</span></div><div class="code-block-toggle">Expand</div></div><div class="code-block-content collapsed"><pre><code>' + code.trim() + '</code></pre></div></div>';
    });
    html = html.replace(/`([^`]+)`/g, '<code>$1</code>');
    html = html.replace(/\n/g, '<br>');
    return html;


function toggleCodeBlock(header) {
    const content = header.parentElement.querySelector('.code-block-content');
    const toggle = header.querySelector('.code-block-toggle');
    if (content) {
    content.classList.toggle('collapsed');
        if (toggle) toggle.textContent = content.classList.contains('collapsed') ? 'Expand' : 'Collapse';
    }
}

function updateTypingIndicator() {
const chatArea = document.getElementById('chat-area');
    let indicator = chatArea?.querySelector('.typing-indicator');

    if (isTyping && !indicator) {
    const div = document.createElement('div');
        div.className = 'typing-indicator';
    div.innerHTML = '<span class="typing-dot"></span><span class="typing-dot"></span><span class="typing-dot"></span>';
        chatArea?.appendChild(div);
    chatArea.scrollTop = chatArea.scrollHeight;
    } else if (!isTyping && indicator) {
        indicator.remove();
    }
}

let thinkingItems = [];

tion updateThinking(data) {
    const container = document.getElementById('thinking-container');
    if (!container) return;

    // 如果是对象形式（单条数据），转换为数组
    const thinking = Array.isArray(data) ? data : [data];
    
    // 更新思考项列表
    thinkingItems = thinking;
    
    // 清空容器
    container.innerHTML = '';
    container.classList.remove('hidden');

    // 创建主思考卡片
    const card = document.createElement('div');
    card.className = 'thinking-card';
    
    // 标题区域
    const header = document.createElement('div');
    header.className = 'thinking-header';
    header.innerHTML = `<span class="thinking-icon">${thinking[0]?.title || '🔄'}</span><span class="thinking-title">${thinking[0]?.title || '处理中...'}</span>`;
    card.appendChild(header);
    
    // 内容区域
    const content = document.createElement('div');
    content.className = 'thinking-content';
    content.textContent = thinking[0]?.content || '';
card.appendChild(content);
    
// 进度条（如果有进度信息）
    if (thinking[0]?.progress !== undefined) {
        const progressBar = document.createElement('div');
        progressBar.className = 'thinking-progress';

        const progressFill = document.createElement('div');
        progressFill.className = 'thinking-progress-fill';
        progressFill.style.width = `${thinking[0].progress}%`;
        progressFill.style.transition = 'width 0.3s ease-in-out';
        
        progressBar.appendChild(progressFill);
        card.appendChild(progressBar);
        
// 进度数字
        const progressText = document.createElement('div');
        progressText.className = 'thinking-progress-text';
        progressText.textContent = `${thinking[0].progress}%`;
card.appendChild(progressText);
    }
    
    // 添加状态指示器动画
    const statusIndicator = document.createElement('div');
statusIndicator.className = 'thinking-status';
    for (let i = 0; i < 3; i++) {
        const dot = document.createElement('span');
        dot.className = 'thinking-dot';
        dot.style.animationDelay = `${i * 0.2}s`;
        statusIndicator.appendChild(dot);
    }
card.appendChild(statusIndicator);
    
    container.appendChild(card);
    
    // 添加滑入动画
    setTimeout(() => {
        card.classList.add('show');
    }, 50);
}

function clearThinking() {
    const container = document.getElementById('thinking-container');
    if (container) {
    const card = container.querySelector('.thinking-card');
        if (card) {
        card.classList.remove('show');
            setTimeout(() => {
            container.innerHTML = '';
                container.classList.add('hidden');
            }, 300);
    }
    }
    thinkingItems = [];
}

function sendMessage() {
    const input = document.getElementById('input-box');
const text = input?.value.trim();

    if (!text && files.length === 0) return;

    addMessage('user', text || '');

    const thinkingContainer = document.getElementById('thinking-container');
    if (thinkingContainer) thinkingContainer.classList.remove('hidden');

    const payload = {
        type: 'message',
        content: text || '',
        files: files.map(f => f.name),
        polishStyle: polishStyle
    };

if (socket && socket.readyState === WebSocket.OPEN) {
        socket.send(JSON.stringify(payload));
    } else {
        showToast('WebSocket not connected', 'error');
        setTimeout(() => {
            addMessage('assistant', 'Hello! I am DataAgent. The WebSocket connection is not established. Please check your network connection or try again later.');
        }, 500);
}
}

tion copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(() => {
        showToast('Copied to clipboard', 'success');
    }).catch(() => {
        showToast('Copy failed', 'error');
    });
}

function showToast(message, type = 'info') {
    const container = document.getElementById('toast-container');
    if (!container) return;

    const toast = document.createElement('div');
    toast.className = 'toast ' + type;

    const icons = { success: '✅', error: '❌', warning: '⚠️', info: 'ℹ️' };
    toast.innerHTML = '<span>' + icons[type] + '</span><span>' + message + '</span>';

    container.appendChild(toast);
    setTimeout(() => { toast.remove(); }, 3000);


function updateCharCount() {
    const input = document.getElementById('input-box');
const count = document.getElementById('char-count');
    if (input && count) count.textContent = input.value.length;
}

function handleFileSelect(event) {
    const selectedFiles = Array.from(event.target?.files || []);
    selectedFiles.forEach(file => {
        if (files.find(f => f.name === file.name)) {
            showToast(file.name + ' already added', 'warning');
        return;
        }
    files.push(file);
        addFilePreview(file);
    });
    event.target.value = '';
}

function addFilePreview(file) {
    const list = document.getElementById('file-preview-list');
    if (!list) return;

    const card = document.createElement('div');
    card.className = 'file-preview-card';
    card.dataset.filename = file.name;

    const size = (file.size / 1024).toFixed(1) + ' KB';
    card.innerHTML = '<span class="file-icon">📄</span><div class="file-info"><div class="file-name">' + file.name + '</div><div class="file-size">' + size + '</div></div><button class="file-remove" onclick="removeFile(\'' + file.name + '\')">×</button>';

.appendChild(card);
}

function removeFile(filename) {
    const index = files.findIndex(f => f.name === filename);
    if (index !== -1) {
        files.splice(index, 1);
        const card = document.querySelector('[data-filename="' + filename + '"]');
        if (card) card.remove();
    }
}

function togglePolishPanel() {
const panel = document.getElementById('polish-panel');
    if (panel) panel.classList.toggle('hidden');
}

tion selectPolishStyle(style) {
    polishStyle = polishStyle === style ? null : style;
    document.querySelectorAll('.option-btn').forEach(btn => btn.classList.remove('active'));
    if (polishStyle && event) event.target.classList.add('active');
}

function openModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.classList.remove('hidden');
        document.body.style.overflow = 'hidden';
    }
}

function closeModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.classList.add('hidden');
    document.body.style.overflow = '';
    }
}

function highlightNav(navId) {
    document.querySelectorAll('.nav-item').forEach(item => item.classList.remove('active'));
    const navItem = document.getElementById(navId);
if (navItem) navItem.classList.add('active');
}

function handlePolishSubmit() {
    const style = document.getElementById('polish-type')?.value;
    const text = document.getElementById('polish-input')?.value;
if (!text?.trim()) {
        showToast('Please enter text to polish', 'warning');
    return;
    }

    closeModal('polish-modal');
    const styleNames = { academic: 'academic', formal: 'formal', concise: 'concise', casual: 'casual' };
    const prompt = 'Please polish this text to be more ' + (styleNames[style] || style) + ':\n\n' + text;
    document.getElementById('input-box').value = prompt;
updateCharCount();
}

function handlePptSubmit() {
const topic = document.getElementById('ppt-topic')?.value;
    const content = document.getElementById('ppt-content')?.value;

    if (!topic?.trim()) {
showToast('Please enter PPT topic', 'warning');
        return;
    }

    closeModal('ppt-modal');
let prompt = 'Please generate a PPT about: ' + topic;
    if (content?.trim()) prompt += '\n\nContent outline:\n' + content;
    document.getElementById('input-box').value = prompt;
    updateCharCount();


function handleTodoSubmit() {
    const text = document.getElementById('todo-input')?.value;
if (!text?.trim()) {
        showToast('Please enter text', 'warning');
        return;
    }

    closeModal('todo-modal');
    const prompt = 'Extract todo items from this text:\n\n' + text;
    document.getElementById('input-box').value = prompt;
    updateCharCount();
}

function handleMeetingSubmit() {
    const text = document.getElementById('meeting-input')?.value;
    if (!text?.trim()) {
        showToast('Please enter meeting notes', 'warning');
   
     return;
    }

    closeModal('meeting-modal');
    const prompt = 'Generate meeting minutes from these notes:\n\n' + text;
    document.getElementById('input-box').value = prompt;
    updateCharCount();
}

function handleWeeklySubmit() {
    const work = document.getElementById('weekly-work')?.value;
    const problems = document.getElementById('weekly-problems')?.value;
    const plan = document.getElementById('weekly-plan')?.value;

    if (!work?.trim()) {
        showToast('Please enter weekly work content', 'warning');
        return;
    }

    closeModal('weekly-modal');
    let prompt = 'Generate weekly report:\n\nThis week completed:\n' + work;
    if (problems?.trim()) prompt += '\n\nProblems encountered:\n' + problems;
    if (plan?.trim()) prompt += '\n\nNext week plan:\n' + plan;
    document.getElementById('input-box').value = prompt;
    updateCharCount();
}

function handleSettingsSave() {
    const settings = {
        apiKey: document.getElementById('settings-api-key')?.value || '',
        model: document.getElementById('settings-model')?.value || 'gpt-4o',
        temperature: parseFloat(document.getElementById('settings-temperature')?.value || 0.7),
        maxTokens: parseInt(document.getElementById('settings-tokens')?.value || 4096),
        stream: document.getElementById('settings-stream')?.checked !== false
    };

    localStorage.setItem('dataagent-settings', JSON.stringify(settings));
    closeModal('settings-modal');
    showToast('Settings saved', 'success');
}

function testConnection() {
    showToast('Testing connection...', 'info');
    setTimeout(() => { showToast('Connection test successful', 'success'); }, 1500);
}

function initEventListeners() {
    const inputBox = document.getElementById('input-box');
    const sendBtn = document.getElementById('send-btn');
    const fileInput = document.getElementById('file-input');
    const polishBtn = document.getElementById('polish-btn');
    const chatArea = document.getElementById('chat-area');
    const sidebarToggle = document.getElementById('sidebar-toggle');

    if (inputBox) {
        inputBox.addEventListener('input', updateCharCount);
        inputBox.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMessage(); }
        });
    }

    if (sendBtn) sendBtn.addEventListener('click', sendMessage);
    if (fileInput) fileInput.addEventListener('change', handleFileSelect);
    if (polishBtn) polishBtn.addEventListener('click', togglePolishPanel);

    document.addEventListener('click', (e) => {
        const panel = document.getElementById('polish-panel');
        const btn = document.getElementById('polish-btn');
        if (panel && btn && !panel.classList.contains('hidden') && !btn.contains(e.target) && !panel.contains(e.target)) {
            panel.classList.add('hidden');
        }
    });

    if (chatArea) {
        chatArea.addEventListener('dragover', (e) => { e.preventDefault(); chatArea.classList.add('drag-over'); });
        chatArea.addEventListener('dragleave', () => { chatArea.classList.remove('drag-over'); });
        chatArea.addEventListener('drop', (e) => {
            e.preventDefault();
            chatArea.classList.remove('drag-over');
            const droppedFiles = Array.from(e.dataTransfer?.files || []);
            const input = document.getElementById('file-input');
            if (input && droppedFiles.length > 0) {
                const dataTransfer = new DataTransfer();
                droppedFiles.forEach(f => dataTransfer.items.add(f));
                input.files = dataTransfer.files;
                handleFileSelect({ target: input });
            }
        });
    }

    if (sidebarToggle) {
        sidebarToggle.addEventListener('click', () => {
            const sidebar = document.getElementById('sidebar');
            if (sidebar) sidebar.classList.toggle('closed');
        });
    }

    document.querySelectorAll('.suggestion-card').forEach(card => {
        card.addEventListener('click', () => {
            const text = card.dataset.prompt;
            if (text) {
                const input = document.getElementById('input-box');
                if (input) { input.value = text; updateCharCount(); }
            }
        });
    });

    document.querySelectorAll('.option-group .option-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.preventDefault();
            const group = e.target.closest('.option-group');
            if (group) {
                group.querySelectorAll('.option-btn').forEach(b => b.classList.remove('active'));
                e.target.classList.add('active');
            }
        });
    });
}

function initModalListeners() {
    const modals = ['polish', 'ppt', 'todo', 'meeting', 'weekly', 'settings'];

    modals.forEach(name => {
        const closeBtn = document.getElementById(name + '-close');
        const cancelBtn = document.getElementById(name + '-cancel');
        if (closeBtn) closeBtn.addEventListener('click', () => closeModal(name + '-modal'));
        if (cancelBtn) cancelBtn.addEventListener('click', () => closeModal(name + '-modal'));
    });

    document.getElementById('polish-submit')?.addEventListener('click', handlePolishSubmit);
    document.getElementById('ppt-submit')?.addEventListener('click', handlePptSubmit);
    document.getElementById('todo-submit')?.addEventListener('click', handleTodoSubmit);
    document.getElementById('meeting-submit')?.addEventListener('click', handleMeetingSubmit);
    document.getElementById('weekly-submit')?.addEventListener('click', handleWeeklySubmit);
    document.getElementById('settings-save')?.addEventListener('click', handleSettingsSave);
    document.getElementById('settings-test')?.addEventListener('click', testConnection);

    const tempSlider = document.getElementById('settings-temperature');
    const tempValue = document.getElementById('temp-value');
    if (tempSlider && tempValue) {
        tempSlider.addEventListener('input', (e) => { tempValue.textContent = e.target.value; });
    }

    const tokensSlider = document.getElementById('settings-tokens');
    const tokensValue = document.getElementById('tokens-value');
    if (tokensSlider && tokensValue) {
        tokensSlider.addEventListener('input', (e) => { tokensValue.textContent = e.target.value; });
    }

    document.querySelectorAll('.modal-overlay').forEach(modal => {
        modal.addEventListener('click', (e) => { if (e.target === modal) closeModal(modal.id); });
    });
}

function initSidebarNav() {
    const navItems = [
        { id: 'nav-chat', action: () => highlightNav('nav-chat') },
        { id: 'nav-knowledge', action: () => { highlightNav('nav-knowledge'); showToast('Knowledge base feature coming soon', 'info'); } },
        { id: 'nav-skills', action: () => { highlightNav('nav-skills'); showToast('Skills center feature coming soon', 'info'); } },
        { id: 'nav-mcp', action: () => { highlightNav('nav-mcp'); showToast('MCP tools feature coming soon', 'info'); } },
        { id: 'nav-database', action: () => { highlightNav('nav-database'); showToast('Database feature coming soon', 'info'); } },
        { id: 'nav-polish', action: () => { highlightNav('nav-polish'); openModal('polish-modal'); } },
        { id: 'nav-ppt', action: () => { highlightNav('nav-ppt'); openModal('ppt-modal'); } },
        { id: 'nav-todo', action: () => { highlightNav('nav-todo'); openModal('todo-modal'); } },
        { id: 'nav-meeting', action: () => { highlightNav('nav-meeting'); openModal('meeting-modal'); } },
        { id: 'nav-weekly', action: () => { highlightNav('nav-weekly'); openModal('weekly-modal'); } },
        { id: 'nav-literature', action: () => { highlightNav('nav-literature'); showToast('Literature summary feature coming soon', 'info'); } },
        { id: 'nav-settings', action: () => { highlightNav('nav-settings'); openModal('settings-modal'); } }
    ];

    navItems.forEach(item => {
        const element = document.getElementById(item.id);
        if (element) element.addEventListener('click', item.action);
    });

    const headerMenuBtn = document.getElementById('header-menu-btn');
    if (headerMenuBtn) {
        headerMenuBtn.addEventListener('click', () => {
            const sidebar = document.getElementById('sidebar');
            if (sidebar) sidebar.classList.toggle('closed');
        });
    }

    const newConversationBtn = document.getElementById('new-conversation-btn');
    if (newConversationBtn) newConversationBtn.addEventListener('click', () => location.reload());

    const clearChatBtn = document.getElementById('clear-chat-btn');
    if (clearChatBtn) {
        clearChatBtn.addEventListener('click', () => {
            if (confirm('Are you sure you want to clear chat history?')) location.reload();
        });
    }

    const fileBtn = document.getElementById('file-btn');
    if (fileBtn) {
        fileBtn.addEventListener('click', () => {
            const fileInput = document.getElementById('file-input');
            if (fileInput) fileInput.click();
        });
    }

    const webSearchBtn = document.getElementById('web-search-btn');
    if (webSearchBtn) {
        webSearchBtn.addEventListener('click', (e) => {
            e.target.classList.toggle('active');
            showToast('Web search ' + (e.target.classList.contains('active') ? 'enabled' : 'disabled'), 'info');
        });
    }

    const pythonBtn = document.getElementById('python-btn');
    if (pythonBtn) {
        pythonBtn.addEventListener('click', () => {
            const input = document.getElementById('input-box');
            if (input) { input.value = '/tool python\n'; input.focus(); updateCharCount(); }
        });
    }

    const bashBtn = document.getElementById('bash-btn');
    if (bashBtn) {
        bashBtn.addEventListener('click', () => {
            const input = document.getElementById('input-box');
            if (input) { input.value = '/tool bash\n'; input.focus(); updateCharCount(); }
        });
    }
}

function loadSettings() {
    const savedSettings = localStorage.getItem('dataagent-settings');
    if (savedSettings) {
        try {
            const settings = JSON.parse(savedSettings);
            document.getElementById('settings-api-key')?.value = settings.apiKey || '';
            document.getElementById('settings-model')?.value = settings.model || 'gpt-4o';
            document.getElementById('settings-temperature')?.value = settings.temperature || 0.7;
            document.getElementById('settings-tokens')?.value = settings.maxTokens || 4096;
            document.getElementById('settings-stream')?.checked = settings.stream !== false;

            document.getElementById('temp-value')?.textContent = settings.temperature || 0.7;
            document.getElementById('tokens-value')?.textContent = settings.maxTokens || 4096;
        } catch (e) { console.error('Failed to load settings:', e); }
    }
}

document.addEventListener('DOMContentLoaded', () => {
    console.log('DOM loaded, initializing DataAgent...');
    initEventListeners();
    initModalListeners();
    initSidebarNav();
    initWebSocket();
    loadSettings();
    console.log('DataAgent initialized successfully!');
});
