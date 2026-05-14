// 主应用逻辑

// ==================== 代码块折叠功能 ====================

function renderMarkdownWithCodeFolding(text) {
    if (!window.marked) {
        return text.replace(/\n/g, '<br>');
    }
    
    let html = marked.parse(text);
    
    // 处理代码块，添加折叠功能
    html = html.replace(/<pre><code([^>]*)>([\s\S]*?)<\/code><\/pre>/g, 
        function(match, attrs, code) {
            // 提取语言类型
            let lang = 'text';
            const langMatch = attrs.match(/class="[^"]*language-(\w+)/);
            if (langMatch) lang = langMatch[1];
            
            const codeId = 'code-' + Date.now() + '-' + Math.random().toString(36).substr(2, 9);
            
            return `
                <div class="code-block-wrapper">
                    <div class="code-block-header" onclick="toggleCodeBlock('${codeId}')">
                        <div class="code-block-title">
                            <span>📝</span>
                            <span class="code-block-lang">${lang}</span>
                        </div>
                        <div class="code-block-toggle" id="${codeId}-toggle">▼</div>
                    </div>
                    <div class="code-block-content" id="${codeId}">
                        <pre><code${attrs}>${code}</code></pre>
                    </div>
                </div>
            `;
        });
    
    return html;
}

function toggleCodeBlock(id) {
    const content = document.getElementById(id);
    const toggle = document.getElementById(id + '-toggle');
    
    if (content) {
        content.classList.toggle('collapsed');
        toggle.textContent = content.classList.contains('collapsed') ? '▶' : '▼';
    }
}

function autoScrollChat() {
    const chatArea = document.getElementById('chat-area');
    if (chatArea) {
        chatArea.scrollTop = chatArea.scrollHeight;
    }
}

// ==================== 欢迎页面控制 ====================

function hideWelcomePage() {
    const wp = document.getElementById('welcome-page');
    if (wp) wp.style.display = 'none';
}

function showWelcomePage() {
    const wp = document.getElementById('welcome-page');
    if (wp) wp.style.display = 'flex';
}

// ==================== WebSocket 连接 ====================

let wsReconnectAttempts = 0;
const WS_MAX_RETRIES = 10;
const WS_BASE_DELAY = 1000;

function connectWS() {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = protocol + '//' + window.location.host + '/ws';
    console.log('Connecting to WebSocket:', wsUrl);
    
    ws = new WebSocket(wsUrl);

    ws.onopen = () => {
        console.log('WebSocket connected successfully');
        wsReconnectAttempts = 0;
        updateWSStatus('connected', '已连接');
        showToast('连接成功，可以开始对话', 'success');
    };

    ws.onmessage = (event) => {
        console.log('WebSocket message received');
        handleWSMessage(JSON.parse(event.data));
    };

    ws.onclose = (event) => {
        console.log('WebSocket closed:', event.code, event.reason);
        updateWSStatus('error', '已断开');
        if (wsReconnectAttempts < WS_MAX_RETRIES) {
            const delay = Math.min(WS_BASE_DELAY * Math.pow(2, wsReconnectAttempts), 30000);
            wsReconnectAttempts++;
            console.log(`WebSocket reconnecting in ${delay}ms (attempt ${wsReconnectAttempts}/${WS_MAX_RETRIES})`);
            setTimeout(connectWS, delay);
        } else {
            updateWSStatus('error', '连接失败');
            showToast('WebSocket连接已断开，请刷新页面重试', 'error');
        }
    };

    ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        updateWSStatus('error', '连接失败');
        showToast('WebSocket连接出错，请检查服务器状态', 'error');
    };
}

function updateWSStatus(status, text) {
    // 更新欢迎页状态点
    const dot = document.getElementById('ws-status');
    const statusText = document.getElementById('ws-status-text');
    if (dot) {
        dot.className = 'status-dot ' + status;
    }
    if (statusText) {
        statusText.textContent = text;
    }
    // 更新头部状态
    const headerDot = document.querySelector('.header-status .status-dot');
    const headerText = document.getElementById('header-ws-status-text');
    if (headerDot) headerDot.className = 'status-dot ' + status;
    if (headerText) headerText.textContent = text;
}

// ==================== 消息处理 ====================

function handleWSMessage(data) {
    const chatArea = document.getElementById('chat-area');

    if (data.type === 'thinking') {
        hideWelcomePage();
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
                <div class="thinking-title">${escapeHtml(data.title)}</div>
                <div class="thinking-toggle">\u25bc</div>
            </div>
            <div class="thinking-content">${escapeHtml(data.content)}</div>
        `;

        thinkingEl.appendChild(phaseEl);
        chatArea.scrollTop = chatArea.scrollHeight;

    } else if (data.type === 'stream_start') {
        hideWelcomePage();
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

            const rawText = (textEl.getAttribute('data-raw') || '') + data.content;
            textEl.setAttribute('data-raw', rawText);
            if (!textEl._rafPending) {
                textEl._rafPending = true;
                requestAnimationFrame(() => {
                    textEl.innerHTML = renderMarkdownWithCodeFolding(rawText);
                    textEl.querySelectorAll('pre code').forEach(block => {
                        if (window.hljs) hljs.highlightElement(block);
                    });
                    textEl._rafPending = false;
                });
            }
            indicator.style.display = 'inline-block';
            autoScrollChat();
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
        // 自动保存对话
        saveCurrentConversation();

    } else if (data.type === 'response') {
        hideWelcomePage();
        document.querySelector('.thinking-container')?.remove();
        addMessage(data.content, 'assistant');
        finishProcessing();
        // 自动保存对话
        saveCurrentConversation();
    } else if (data.type === 'error') {
        document.querySelector('.thinking-container')?.remove();
        document.querySelector('.message.streaming')?.remove();

        const messageEl = document.createElement('div');
        messageEl.className = 'message system error';
        messageEl.innerHTML = `
            <div class="message-content">
                <div style="display: flex; align-items: center; gap: 8px;">
                    <span style="font-size: 18px;">\u274c</span>
                    <span style="color: #ef4444;">${data.content}</span>
                </div>
                <button onclick="retryLastMessage()" style="margin-top: 8px; padding: 4px 12px; background: rgba(239,68,68,0.15); border: 1px solid rgba(239,68,68,0.3); border-radius: 6px; color: #f87171; cursor: pointer; font-size: 12px;">\ud83d\udd04 重试</button>
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
    toggle.textContent = content.classList.contains('collapsed') ? '\u25b6' : '\u25bc';
}

function addMessage(content, type) {
    const chatArea = document.getElementById('chat-area');
    const messageEl = document.createElement('div');
    messageEl.className = `message ${type}`;
    let formatted;
    if (type === 'user') {
        formatted = escapeHtml(content).replace(/\n/g, '<br>');
    } else {
        formatted = renderMarkdownWithCodeFolding(content);
    }

    const time = new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' });

    messageEl.innerHTML = `
        <div class="message-content">
            <div class="message-text">${formatted}</div>
            <div class="message-actions">
                <button class="message-action-btn" onclick="copyMessage(this)" title="复制">\ud83d\udccb</button>
            </div>
            ${type === 'assistant' ? `
            <div class="message-feedback" style="display: flex; gap: 4px; margin-top: 4px;">
                <button class="feedback-btn" onclick="submitFeedback(this, 'up')" title="有帮助" style="background: none; border: 1px solid rgba(255,255,255,0.1); border-radius: 6px; padding: 2px 8px; color: #64748b; cursor: pointer; font-size: 12px; transition: all 0.2s;">\ud83d\udc4d</button>
                <button class="feedback-btn" onclick="submitFeedback(this, 'down')" title="需改进" style="background: none; border: 1px solid rgba(255,255,255,0.1); border-radius: 6px; padding: 2px 8px; color: #64748b; cursor: pointer; font-size: 12px; transition: all 0.2s;">\ud83d\udc4e</button>
            </div>` : ''}
        </div>
        <div style="font-size: 11px; color: #6b7280; margin-top: 4px; ${type === 'user' ? 'text-align: right; padding-right: 8px;' : 'padding-left: 8px;'}">${time}</div>
    `;

    chatArea.appendChild(messageEl);
    // Highlight code blocks in the new message
    messageEl.querySelectorAll('pre code').forEach(block => {
        if (window.hljs) hljs.highlightElement(block);
    });
    addCodeCopyButtons();
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

async function submitFeedback(btn, rating) {
    const messageEl = btn.closest('.message');
    const content = messageEl.querySelector('.message-text')?.textContent || '';

    // Determine category from content
    let category = 'general';
    if (/代码|python|function|class|import/.test(content)) category = 'code';
    else if (/数据|分析|统计|图表|plot|chart/.test(content)) category = 'analysis';
    else if (/写|文章|文案|翻译/.test(content)) category = 'writing';
    else if (/知识库|文档|搜索/.test(content)) category = 'knowledge';

    try {
        await fetch('/api/feedback', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                rating: rating,
                category: category,
                message_preview: content.substring(0, 200)
            })
        });

        // Visual feedback
        const feedbackDiv = btn.closest('.message-feedback');
        feedbackDiv.querySelectorAll('.feedback-btn').forEach(b => {
            b.style.opacity = '0.3';
            b.style.pointerEvents = 'none';
        });
        btn.style.opacity = '1';
        btn.style.borderColor = rating === 'up' ? '#10b981' : '#ef4444';
        btn.style.color = rating === 'up' ? '#10b981' : '#ef4444';

        showToast(rating === 'up' ? '感谢反馈！我会继续改进' : '感谢反馈，我会努力做得更好', 'info');
    } catch (e) {
        console.error('Feedback error:', e);
    }
}

// ==================== 发送消息 ====================

let lastUserMessage = '';

function sendMessageWithText(content) {
    const inputBox = document.getElementById('input-box');
    if (!content) return;
    
    // 检查 WebSocket 连接状态
    if (!ws || ws.readyState !== WebSocket.OPEN) {
        showToast('WebSocket 连接未建立，请检查网络连接或刷新页面', 'error');
        return;
    }
    
    inputBox.value = '';
    updateCharCount();
    hideWelcomePage();
    addMessage(content, 'user');
    document.getElementById('send-btn').disabled = true;
    lastUserMessage = content;

    const webSearchEnabled = document.getElementById('web-search-btn').classList.contains('active');
    ws.send(JSON.stringify({
        content: content,
        options: {
            web_search: webSearchEnabled
        }
    }));
}

function retryLastMessage() {
    if (!lastUserMessage) return;
    // Remove the error message
    const errorMsg = document.querySelector('.message.error');
    if (errorMsg) errorMsg.remove();
    // Also remove the last user message to avoid duplicates
    const userMsgs = document.querySelectorAll('.message.user');
    if (userMsgs.length > 0) {
        userMsgs[userMsgs.length - 1].remove();
    }
    // Resend
    sendMessageWithText(lastUserMessage);
}

function sendMessage() {
    const inputBox = document.getElementById('input-box');
    const content = inputBox.value.trim();

    if (!content && pendingFiles.length === 0) {
        showToast('请输入消息内容', 'warning');
        inputBox.focus();
        return;
    }

    // 如果有待发送文件，先处理文件再合并发送
    if (pendingFiles.length > 0) {
        sendPendingFilesWithText(content);
        return;
    }

    sendMessageWithText(content);
}

async function sendPendingFilesWithText(userText) {
    const textFiles = [];
    const binaryFiles = [];

    for (const file of pendingFiles) {
        if (getFileType(file.name) === 'text') {
            textFiles.push(file);
        } else {
            binaryFiles.push(file);
        }
    }

    let fileParts = [];

    // 读取文本文件内容
    for (const file of textFiles) {
        try {
            const content = await readTextFile(file);
            fileParts.push(`[文件: ${file.name} (${formatFileSize(file.size)})]\n\`\`\`\n${content}\n\`\`\``);
        } catch (err) {
            fileParts.push(`[文件: ${file.name}] 读取失败: ${err.message}`);
        }
    }

    // 二进制文件只显示信息
    for (const file of binaryFiles) {
        fileParts.push(`[文件: ${file.name} (${formatFileSize(file.size)}, 类型: ${file.type || '未知'})]`);
    }

    pendingFiles = [];
    renderFilePreviewList();

    // 合并文件内容和用户文本
    let fullMessage;
    if (userText) {
        fullMessage = fileParts.join('\n\n') + '\n\n' + userText;
    } else {
        fullMessage = fileParts.join('\n\n');
    }

    sendMessageWithText(fullMessage);
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
        inputBox.value += String.fromCharCode(10);
    }
    inputBox.value += command;
    inputBox.focus();
    inputBox.scrollTop = inputBox.scrollHeight;
    updateCharCount();
}

function finishProcessing() {
    document.getElementById('send-btn').disabled = false;
    autoScrollChat();
}

function clearChat() {
    const chatArea = document.getElementById('chat-area');
    chatArea.innerHTML = `
        <div class="welcome-page" id="welcome-page">
            <div class="welcome-center">
                <div class="welcome-logo">DA</div>
                <h2 class="welcome-title">有什么可以帮忙的？</h2>
                <div class="suggestion-grid">
                    <button class="suggestion-card" onclick="insertCommand('帮我分析数据'); sendMessage();">
                        <div style="font-size: 20px; margin-bottom: 6px;">📊</div>
                        <div>帮我分析数据</div>
                    </button>
                    <button class="suggestion-card" onclick="insertCommand('生成一个图表'); sendMessage();">
                        <div style="font-size: 20px; margin-bottom: 6px;">📈</div>
                        <div>生成一个图表</div>
                    </button>
                    <button class="suggestion-card" onclick="insertCommand('写一段 Python 代码'); sendMessage();">
                        <div style="font-size: 20px; margin-bottom: 6px;">💻</div>
                        <div>写一段 Python 代码</div>
                    </button>
                    <button class="suggestion-card" onclick="insertCommand('解析一个文档'); sendMessage();">
                        <div style="font-size: 20px; margin-bottom: 6px;">📄</div>
                        <div>解析一个文档</div>
                    </button>
                </div>
            </div>
        </div>
    `;
    showWelcomePage();
}

// ==================== 字符计数 ====================

function autoResize(textarea) {
    textarea.style.height = 'auto';
    textarea.style.height = Math.min(textarea.scrollHeight, 150) + 'px';
}

function updateCharCount() {
    const inputBox = document.getElementById('input-box');
    const counter = document.getElementById('char-count');
    if (counter) {
        const len = inputBox.value.length;
        counter.textContent = len > 0 ? len + ' 字' : '';
    }
}

// ==================== 侧边栏控制 ====================

function toggleSidebar() {
    const sidebar = document.getElementById('sidebar');
    const overlay = document.getElementById('sidebar-overlay');
    sidebar.classList.toggle('closed');
    overlay.classList.toggle('show');
}

function closeSidebar() {
    const sidebar = document.getElementById('sidebar');
    const overlay = document.getElementById('sidebar-overlay');
    sidebar.classList.add('closed');
    overlay.classList.remove('show');
}

function openSidebar() {
    const sidebar = document.getElementById('sidebar');
    const overlay = document.getElementById('sidebar-overlay');
    sidebar.classList.remove('closed');
    overlay.classList.add('show');
}

// ==================== 模态框控制 ====================

function openModal(id) {
    document.getElementById(id).classList.add('show');
    if (id === 'knowledge-modal') loadKnowledgeBases();
    if (id === 'prompt-modal') loadSkills();
    if (id === 'mcp-modal') loadMcpServers();
    if (id === 'database-modal') loadDatabases();
    if (id === 'nl2sql-modal') loadDatabases();
}

function closeModal(id) {
    document.getElementById(id).classList.remove('show');
}

function showMainChat(el) {
    document.querySelectorAll('.nav-item').forEach(e => e.classList.remove('active'));
    if (el) el.classList.add('active');
}

// ==================== 手风琴组件 ====================

function toggleAccordion(header) {
    const body = header.nextElementSibling;
    const arrow = header.querySelector('.accordion-arrow');
    const isOpen = body.style.display !== 'none';

    body.style.display = isOpen ? 'none' : 'block';
    if (arrow) {
        arrow.textContent = isOpen ? '\u25b6' : '\u25bc';
    }
    header.classList.toggle('active', !isOpen);
}

// ==================== 事件监听 ====================

// 快捷键支持
document.addEventListener('keydown', function(e) {
    // Escape to close modals
    if (e.key === 'Escape') {
        const openModal = document.querySelector('.modal-overlay.show');
        if (openModal) {
            openModal.classList.remove('show');
            e.preventDefault();
        }
        // Also close sidebar
        const sidebar = document.getElementById('sidebar');
        if (sidebar && !sidebar.classList.contains('closed')) {
            closeSidebar();
        }
    }

    // Ctrl+Shift+N for new conversation
    if ((e.metaKey || e.ctrlKey) && e.shiftKey && e.key === 'N') {
        e.preventDefault();
        createNewConversation();
    }

    // Ctrl+/ to toggle sidebar
    if ((e.metaKey || e.ctrlKey) && e.key === '/') {
        e.preventDefault();
        toggleSidebar();
    }

    if ((e.metaKey || e.ctrlKey) && e.key === 'Enter') {
        e.preventDefault();
        sendMessage();
    }
});

// 输入框事件
document.addEventListener('DOMContentLoaded', function() {
    const inputBox = document.getElementById('input-box');
    if (inputBox) {
        inputBox.addEventListener('keydown', function(e) {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendMessage();
            }
        });
        inputBox.addEventListener('input', updateCharCount);
    }
});

// 点击模态框遮罩关闭
document.addEventListener('click', function(e) {
    if (e.target.classList.contains('modal-overlay')) {
        e.target.classList.remove('show');
    }
});

// ==================== 拖拽上传 ====================

// 存储待上传的文件列表
let pendingFiles = [];

// 文本文件扩展名
const TEXT_EXTENSIONS = ['.txt', '.md', '.csv', '.json', '.py', '.js', '.ts', '.html', '.css', '.xml', '.yaml', '.yml', '.toml', '.ini', '.cfg', '.log', '.sh', '.bat', '.sql', '.r', '.java', '.c', '.cpp', '.h', '.go', '.rs', '.rb', '.php', '.swift', '.kt'];

// 二进制文件图标映射
const FILE_ICONS = {
    '.pdf': '📕',
    '.docx': '📘',
    '.doc': '📘',
    '.xlsx': '📗',
    '.xls': '📗',
    '.pptx': '📙',
    '.ppt': '📙',
    '.txt': '📄',
    '.md': '📝',
    '.csv': '📊',
    '.json': '🔧',
    '.py': '🐍',
    '.js': '⚡',
    '.ts': '🔷',
    '.html': '🌐',
    '.css': '🎨',
};

function getFileIcon(filename) {
    const ext = '.' + filename.split('.').pop().toLowerCase();
    return FILE_ICONS[ext] || '📎';
}

function getFileType(filename) {
    const ext = '.' + filename.split('.').pop().toLowerCase();
    return TEXT_EXTENSIONS.includes(ext) ? 'text' : 'binary';
}

function formatFileSize(bytes) {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
}

function renderFilePreviewList() {
    const container = document.getElementById('file-preview-list');
    if (!container) return;

    if (pendingFiles.length === 0) {
        container.innerHTML = '';
        return;
    }

    container.innerHTML = pendingFiles.map((file, index) => `
        <div class="file-preview-card" data-index="${index}">
            <span class="file-icon">${getFileIcon(file.name)}</span>
            <div class="file-info">
                <div class="file-name" title="${escapeHtml(file.name)}">${escapeHtml(file.name)}</div>
                <div class="file-size">${formatFileSize(file.size)} · ${getFileType(file.name) === 'text' ? '文本文件' : '二进制文件'}</div>
            </div>
            <button class="file-remove" onclick="removePendingFile(${index})" title="移除">&times;</button>
        </div>
    `).join('');
}

function removePendingFile(index) {
    pendingFiles.splice(index, 1);
    renderFilePreviewList();
}

function addFilesToPending(files) {
    for (const file of files) {
        pendingFiles.push(file);
    }
    renderFilePreviewList();
}

async function readTextFile(file) {
    return new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = (e) => resolve(e.target.result);
        reader.onerror = (e) => reject(new Error('文件读取失败'));
        // 限制读取大小为 500KB，超过则截断
        if (file.size > 500 * 1024) {
            reader.readAsText(file.slice(0, 500 * 1024));
        } else {
            reader.readAsText(file);
        }
    });
}

async function sendPendingFiles() {
    if (pendingFiles.length === 0) return;

    const textFiles = [];
    const binaryFiles = [];

    for (const file of pendingFiles) {
        if (getFileType(file.name) === 'text') {
            textFiles.push(file);
        } else {
            binaryFiles.push(file);
        }
    }

    let messageParts = [];

    // 读取文本文件内容
    for (const file of textFiles) {
        try {
            const content = await readTextFile(file);
            messageParts.push(`[文件: ${file.name} (${formatFileSize(file.size)})]\n\`\`\`\n${content}\n\`\`\``);
        } catch (err) {
            messageParts.push(`[文件: ${file.name}] 读取失败: ${err.message}`);
        }
    }

    // 二进制文件只显示信息
    for (const file of binaryFiles) {
        messageParts.push(`[文件: ${file.name} (${formatFileSize(file.size)}, 类型: ${file.type || '未知'})]`);
    }

    const fullMessage = messageParts.join('\n\n');
    pendingFiles = [];
    renderFilePreviewList();

    // 发送消息
    sendMessageWithText(fullMessage);
}

function handleFileUpload(event) {
    const files = event.target.files;
    if (files.length > 0) {
        addFilesToPending(files);
    }
    event.target.value = '';
}

(function initDragDrop() {
    const chatArea = document.getElementById('chat-area');
    const inputArea = document.getElementById('input-area');
    if (!chatArea) return;

    let dragCounter = 0;

    // 聊天区域拖拽
    chatArea.addEventListener('dragenter', function(e) {
        e.preventDefault();
        e.stopPropagation();
        dragCounter++;
        chatArea.classList.add('drag-over');
    });

    chatArea.addEventListener('dragleave', function(e) {
        e.preventDefault();
        e.stopPropagation();
        dragCounter--;
        if (dragCounter === 0) {
            chatArea.classList.remove('drag-over');
        }
    });

    chatArea.addEventListener('dragover', function(e) {
        e.preventDefault();
        e.stopPropagation();
    });

    chatArea.addEventListener('drop', function(e) {
        e.preventDefault();
        e.stopPropagation();
        dragCounter = 0;
        chatArea.classList.remove('drag-over');

        const files = e.dataTransfer.files;
        if (files.length > 0) {
            addFilesToPending(files);
        }
    });

    // 输入区域拖拽
    if (inputArea) {
        let inputDragCounter = 0;

        inputArea.addEventListener('dragenter', function(e) {
            e.preventDefault();
            e.stopPropagation();
            inputDragCounter++;
            inputArea.classList.add('drag-over');
        });

        inputArea.addEventListener('dragleave', function(e) {
            e.preventDefault();
            e.stopPropagation();
            inputDragCounter--;
            if (inputDragCounter === 0) {
                inputArea.classList.remove('drag-over');
            }
        });

        inputArea.addEventListener('dragover', function(e) {
            e.preventDefault();
            e.stopPropagation();
        });

        inputArea.addEventListener('drop', function(e) {
            e.preventDefault();
            e.stopPropagation();
            inputDragCounter = 0;
            inputArea.classList.remove('drag-over');

            const files = e.dataTransfer.files;
            if (files.length > 0) {
                addFilesToPending(files);
            }
        });
    }
})();

// ==================== 初始化 ====================

window.onload = function() {
    connectWS();
    loadSettings();
    loadConversations();
};

// ==================== PDF 解析功能 ====================

async function handlePdfUpload(event) {
    const file = event.target.files[0];
    if (!file) return;

    if (!file.name.toLowerCase().endsWith('.pdf')) {
        showToast('请选择PDF文件', 'error');
        return;
    }

    showToast(`正在上传并解析: ${file.name}`, 'info');

    try {
        const formData = new FormData();
        formData.append('file', file);
        formData.append('extract_tables', 'true');

        const response = await fetch('/documents/pdf/parse', {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            throw new Error('PDF解析失败');
        }

        const data = await response.json();

        if (data.error) {
            showToast(data.error, 'error');
            return;
        }

        const preview = data.text ? data.text.substring(0, 500) + '...' : '无文本内容';
        const message = `我已成功解析PDF文件「${file.name}」(${data.page_count || '?'}页)：\n\n${preview}\n\n请告诉我你想对这个文档做什么？`;

        document.getElementById('input-box').value = message;
        showToast('PDF解析完成，已添加到输入框', 'success');
    } catch (error) {
        console.error('PDF解析错误:', error);
        showToast('PDF解析失败: ' + error.message, 'error');
    }

    event.target.value = '';
}

// ==================== 学术与职场功能函数 ====================

// 文献摘要 - 上传PDF自动提取核心观点
async function generateLiteratureSummary(event) {
    const file = event.target.files[0];
    if (!file) return;

    if (!file.name.toLowerCase().endsWith('.pdf')) {
        showToast('请选择PDF文件', 'error');
        return;
    }

    showToast(`正在解析文献: ${file.name}`, 'info');

    try {
        // 第一步：上传PDF获取文本
        const formData = new FormData();
        formData.append('file', file);

        const parseResponse = await fetch('/documents/pdf/parse', {
            method: 'POST',
            body: formData
        });

        if (!parseResponse.ok) {
            throw new Error('PDF解析失败');
        }

        const parseData = await parseResponse.json();
        const text = parseData.text || parseData.content || '';

        if (!text || text.length < 50) {
            showToast('PDF内容过少，无法生成摘要', 'warning');
            return;
        }

        showToast('正在生成文献摘要...', 'info');

        // 第二步：生成结构化摘要
        const summaryResponse = await fetch('/documents/summarize/structured', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                text: text,
                summary_type: 'academic',
                max_length: 500
            })
        });

        if (!summaryResponse.ok) {
            throw new Error('摘要生成失败');
        }

        const data = await summaryResponse.json();

        const resultContent = document.getElementById('literature-result-content');
        const resultDiv = document.getElementById('literature-result');

        // 渲染结构化摘要
        let html = '';
        if (data.title) html += `## ${data.title}\n\n`;
        if (data.summary) html += `${data.summary}\n\n`;
        if (data.key_points && data.key_points.length > 0) {
            html += `### 核心观点\n`;
            data.key_points.forEach(p => { html += `- ${p}\n`; });
            html += '\n';
        }
        if (data.keywords && data.keywords.length > 0) {
            html += `**关键词**: ${data.keywords.join(', ')}`;
        }

        resultContent.innerHTML = renderMarkdownWithCodeFolding(html || data.content || '暂无摘要结果');
        resultDiv.style.display = 'block';

        showToast('文献摘要生成完成', 'success');
    } catch (error) {
        console.error('文献摘要错误:', error);
        showToast('文献摘要生成失败: ' + error.message, 'error');
    }

    event.target.value = '';
}

// 会议纪要 - 从会议记录生成结构化纪要
async function generateMeetingMinutes() {
    const input = document.getElementById('meeting-input').value.trim();

    if (!input) {
        showToast('请输入会议记录内容', 'warning');
        return;
    }

    showToast('正在生成会议纪要...', 'info');

    try {
        const response = await fetch('/documents/meeting-minutes', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ text: input })
        });

        if (!response.ok) {
            throw new Error('会议纪要生成失败');
        }

        const data = await response.json();

        if (data.error) {
            showToast(data.error, 'error');
            return;
        }

        const resultContent = document.getElementById('meeting-result-content');
        const resultDiv = document.getElementById('meeting-result');

        resultContent.innerHTML = renderMarkdownWithCodeFolding(data.result?.content || data.minutes || data.content || '暂无会议纪要结果');
        resultDiv.style.display = 'block';

        showToast('会议纪要生成完成', 'success');
    } catch (error) {
        console.error('会议纪要错误:', error);
        showToast('会议纪要生成失败: ' + error.message, 'error');
    }
}

// PPT生成 - 一键生成演示文稿
async function generatePPT() {
    const topic = document.getElementById('ppt-topic').value.trim();
    const pages = document.getElementById('ppt-pages').value;
    const template = document.getElementById('ppt-template').value;
    const content = document.getElementById('ppt-content').value.trim();

    if (!topic) {
        showToast('请输入PPT主题', 'warning');
        return;
    }

    showToast('正在生成PPT，请稍候...', 'info');

    try {
        // 构建PPT内容结构
        const pptContent = {};
        if (content) {
            // 用户提供了内容，按段落分割
            const sections = content.split('\n').filter(s => s.trim());
            sections.forEach((section, i) => {
                pptContent[`section_${i}`] = [section.trim()];
            });
        } else {
            // 没有提供内容，根据页数生成默认结构
            pptContent['引言'] = [`${topic}概述`, '背景与意义'];
            pptContent['核心内容'] = ['主要观点与分析', '案例研究', '数据支撑'];
            pptContent['深入探讨'] = ['技术路线', '实施方案'];
            pptContent['总结'] = ['关键结论', '未来展望'];
        }

        const response = await fetch('/documents/ppt/generate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                title: topic,
                content: pptContent,
                template: template
            })
        });

        if (!response.ok) {
            const errData = await response.json().catch(() => ({}));
            throw new Error(errData.detail || 'PPT生成失败');
        }

        // 后端返回二进制文件，触发下载
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `${topic}.pptx`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);

        const resultContent = document.getElementById('ppt-result-content');
        const resultDiv = document.getElementById('ppt-result');

        resultContent.innerHTML = renderMarkdownWithCodeFolding(
            `### ✅ PPT生成完成\n\n**文件名**: ${topic}.pptx\n\nPPT已自动下载到您的设备。如未自动下载，请[点击此处](${url})手动下载。`
        );
        resultDiv.style.display = 'block';

        showToast('PPT生成完成，已开始下载', 'success');
    } catch (error) {
        console.error('PPT生成错误:', error);
        showToast('PPT生成失败: ' + error.message, 'error');
    }
}

// 周报生成 - 智能扩写实习周报
async function generateWeeklyReport() {
    const work = document.getElementById('weekly-work').value.trim();
    const problems = document.getElementById('weekly-problems').value.trim();
    const plan = document.getElementById('weekly-plan').value.trim();

    if (!work) {
        showToast('请输入本周工作内容', 'warning');
        return;
    }

    showToast('正在生成周报...', 'info');

    try {
        const response = await fetch('/documents/report', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                type: 'weekly',
                work: work,
                problems: problems,
                plan: plan
            })
        });

        if (!response.ok) {
            throw new Error('周报生成失败');
        }

        const data = await response.json();

        if (data.error) {
            showToast(data.error, 'error');
            return;
        }

        const resultContent = document.getElementById('weekly-result-content');
        const resultDiv = document.getElementById('weekly-result');

        resultContent.innerHTML = renderMarkdownWithCodeFolding(data.report || data.content || '暂无周报结果');
        resultDiv.style.display = 'block';

        showToast('周报生成完成', 'success');
    } catch (error) {
        console.error('周报生成错误:', error);
        showToast('周报生成失败: ' + error.message, 'error');
    }
}

// 快速润色 - 输入框右侧按钮调用
async function quickPolish() {
    const inputBox = document.getElementById('input-box');
    const text = inputBox.value.trim();

    if (!text) {
        showToast('请先输入需要润色的内容', 'warning');
        return;
    }

    showToast('正在润色文本...', 'info');

    try {
        const response = await fetch('/documents/polish', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                text: text,
                style: 'academic',
                language: 'auto'
            })
        });

        if (!response.ok) {
            throw new Error('文本润色失败');
        }

        const data = await response.json();

        if (data.error) {
            showToast(data.error, 'error');
            return;
        }

        // 将润色结果替换到输入框
        inputBox.value = data.polished_text || data.polished || data.content || text;
        autoResize(inputBox);
        updateCharCount();

        showToast('文本润色完成', 'success');
    } catch (error) {
        console.error('文本润色错误:', error);
        showToast('文本润色失败: ' + error.message, 'error');
    }
}

// 语言润色 - 模态框中的润色功能
async function polishText() {
    const input = document.getElementById('polish-input').value.trim();
    const type = document.getElementById('polish-type').value;

    if (!input) {
        showToast('请输入需要润色的文本', 'warning');
        return;
    }

    showToast('正在润色文本...', 'info');

    try {
        const response = await fetch('/documents/polish', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                text: input,
                style: type,
                language: 'auto'
            })
        });

        if (!response.ok) {
            throw new Error('文本润色失败');
        }

        const data = await response.json();

        if (data.error) {
            showToast(data.error, 'error');
            return;
        }

        const resultContent = document.getElementById('polish-result-content');
        const resultDiv = document.getElementById('polish-result');

        resultContent.innerHTML = renderMarkdownWithCodeFolding(data.polished_text || data.polished || data.content || '暂无润色结果');
        resultDiv.style.display = 'block';

        showToast('文本润色完成', 'success');
    } catch (error) {
        console.error('文本润色错误:', error);
        showToast('文本润色失败: ' + error.message, 'error');
    }
}

// 复制润色结果
function copyPolishResult() {
    const resultContent = document.getElementById('polish-result-content');
    const text = resultContent.innerText;

    navigator.clipboard.writeText(text).then(() => {
        showToast('已复制到剪贴板', 'success');
    }).catch(() => {
        showToast('复制失败', 'error');
    });
}

// 待办提取 - 从文档提取行动项
async function extractTodos() {
    const input = document.getElementById('todo-input').value.trim();

    if (!input) {
        showToast('请输入需要提取待办的文本内容', 'warning');
        return;
    }

    showToast('正在提取待办事项...', 'info');

    try {
        const response = await fetch('/documents/todos', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ text: input })
        });

        if (!response.ok) {
            throw new Error('待办提取失败');
        }

        const data = await response.json();

        if (data.error) {
            showToast(data.error, 'error');
            return;
        }

        const resultContent = document.getElementById('todo-result-content');
        const resultDiv = document.getElementById('todo-result');

        // 格式化待办事项列表
        let todoHtml = '';
        if (data.todos && Array.isArray(data.todos) && data.todos.length > 0) {
            todoHtml = `### 待办事项（共${data.total || data.todos.length}项）\n\n`;
            data.todos.forEach((todo, i) => {
                const priority = todo.priority === 'high' ? '🔴' : todo.priority === 'medium' ? '🟡' : '🟢';
                todoHtml += `${i + 1}. ${priority} **${todo.task}**\n`;
                if (todo.deadline) todoHtml += `   - 截止：${todo.deadline}\n`;
                if (todo.assignee) todoHtml += `   - 负责人：${todo.assignee}\n`;
            });
        } else {
            todoHtml = data.content || '暂无待办事项';
        }

        resultContent.innerHTML = renderMarkdownWithCodeFolding(todoHtml);
        resultDiv.style.display = 'block';

        showToast('待办提取完成', 'success');
    } catch (error) {
        console.error('待办提取错误:', error);
        showToast('待办提取失败: ' + error.message, 'error');
    }
}
