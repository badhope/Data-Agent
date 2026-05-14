// 主应用逻辑

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
    ws = new WebSocket(protocol + '//' + window.location.host + '/ws');

    ws.onopen = () => {
        console.log('WebSocket connected');
        wsReconnectAttempts = 0;
        updateWSStatus('connected', '已连接');
    };

    ws.onmessage = (event) => handleWSMessage(JSON.parse(event.data));

    ws.onclose = () => {
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

    ws.onerror = () => {
        updateWSStatus('error', '连接失败');
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
            // Only update DOM every frame using requestAnimationFrame
            if (!textEl._rafPending) {
                textEl._rafPending = true;
                requestAnimationFrame(() => {
                    textEl.innerHTML = textEl.getAttribute('data-raw').replace(/\n/g, '<br>');
                    // Highlight code blocks
                    textEl.querySelectorAll('pre code').forEach(block => {
                        if (window.hljs) hljs.highlightElement(block);
                    });
                    textEl._rafPending = false;
                });
            }
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
    // Escape HTML for user messages to prevent XSS; assistant messages may contain formatting
    let formatted;
    if (type === 'user') {
        formatted = escapeHtml(content).replace(/\n/g, '<br>');
    } else {
        // Use marked.js for markdown rendering
        if (window.marked) {
            formatted = marked.parse(content);
        } else {
            formatted = content.replace(/\n/g, '<br>');
        }
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
    if (!content || !ws || ws.readyState !== WebSocket.OPEN) return;
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
    if (!content) return;
    sendMessageWithText(content);
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
    document.getElementById('chat-area').scrollTop = document.getElementById('chat-area').scrollHeight;
}

function clearChat() {
    const chatArea = document.getElementById('chat-area');
    // Remove all children except welcome-page
    const welcomePage = document.getElementById('welcome-page');
    chatArea.innerHTML = '';
    if (welcomePage) {
        chatArea.appendChild(welcomePage);
    } else {
        // Recreate welcome page if it was destroyed
        chatArea.innerHTML = `
            <div class="welcome-page" id="welcome-page">
                <div class="welcome-message">
                    <div class="welcome-avatar">\ud83e\udd16</div>
                    <div class="welcome-bubble">
                        <p>你好！我是 DataAgent 智能助手。</p>
                        <p>我可以帮你进行<strong>代码编写</strong>、<strong>数据分析</strong>、<strong>图表生成</strong>、<strong>文档处理</strong>等工作。</p>
                        <p>试试在下方输入你的需求，或点击快捷指令快速开始 👇</p>
                    </div>
                </div>
            </div>
        `;
    }
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

(function initDragDrop() {
    const chatArea = document.getElementById('chat-area');
    if (!chatArea) return;

    let dragCounter = 0;

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
            // Open knowledge modal and trigger upload
            openModal('knowledge-modal');
            setTimeout(() => {
                if (typeof uploadFiles === 'function') {
                    uploadFiles(files);
                }
            }, 300);
        }
    });
})();

// ==================== 初始化 ====================

window.onload = function() {
    connectWS();
    loadSettings();
    loadConversations();
};
