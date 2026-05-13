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

function connectWS() {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    ws = new WebSocket(protocol + '//' + window.location.host + '/ws');

    ws.onopen = () => {
        console.log('WebSocket connected');
        updateWSStatus('connected', '已连接');
    };

    ws.onmessage = (event) => handleWSMessage(JSON.parse(event.data));

    ws.onclose = () => {
        updateWSStatus('error', '已断开');
        setTimeout(connectWS, 3000);
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
                <div class="thinking-title">${data.title}</div>
                <div class="thinking-toggle">\u25bc</div>
            </div>
            <div class="thinking-content">${data.content}</div>
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

            textEl.innerHTML += data.content.replace(/\\n/g, '<br>');
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
        hideWelcomePage();
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
                    <span style="font-size: 18px;">\u274c</span>
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
    toggle.textContent = content.classList.contains('collapsed') ? '\u25b6' : '\u25bc';
}

function addMessage(content, type) {
    const chatArea = document.getElementById('chat-area');
    const messageEl = document.createElement('div');
    messageEl.className = `message ${type}`;
    let formatted = content.replace(/\\n/g, '<br>');

    const time = new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' });

    messageEl.innerHTML = `
        <div class="message-content">
            <div class="message-text">${formatted}</div>
            <div class="message-actions">
                <button class="message-action-btn" onclick="copyMessage(this)" title="复制">\ud83d\udccb</button>
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

// ==================== 发送消息 ====================

function sendMessage() {
    const inputBox = document.getElementById('input-box');
    const content = inputBox.value.trim();
    if (!content || !ws || ws.readyState !== WebSocket.OPEN) return;
    inputBox.value = '';
    updateCharCount();
    hideWelcomePage();
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
    chatArea.innerHTML = '';
    showWelcomePage();
}

// ==================== 字符计数 ====================

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
}

function closeModal(id) {
    document.getElementById(id).classList.remove('show');
}

function showMainChat() {
    document.querySelectorAll('.nav-item').forEach(el => el.classList.remove('active'));
    event.currentTarget.classList.add('active');
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

// ==================== NL2SQL 功能 ====================

async function analyzeNL2SQL() {
    const input = document.getElementById('nl2sql-input');
    const query = input.value.trim();
    if (!query) {
        showToast('请输入自然语言查询', 'warning');
        return;
    }

    const resultArea = document.getElementById('nl2sql-result');
    resultArea.style.display = 'block';
    resultArea.innerHTML = '<p style="color: #60a5fa;">\u23f3 正在分析意图...</p>';

    try {
        const resp = await fetch('/api/nl2sql/analyze-intent', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ query: query })
        });
        const data = await resp.json();

        let tagsHtml = '';
        if (data.intent) tagsHtml += `<span class="intent-tag">\ud83c\udfaf 意图: ${data.intent}</span>`;
        if (data.tables) tagsHtml += `<span class="intent-tag">\ud83d\udcdd 表: ${data.tables.join(', ')}</span>`;
        if (data.columns) tagsHtml += `<span class="intent-tag">\ud83d\udcc8 列: ${data.columns.join(', ')}</span>`;
        if (data.agg) tagsHtml += `<span class="intent-tag">\ud83d\udcca 聚合: ${data.agg}</span>`;

        resultArea.innerHTML = `
            <h4>\ud83c\udfaf 意图分析</h4>
            <div class="intent-tags">${tagsHtml}</div>
        `;

        // 自动生成SQL
        const sqlResp = await fetch('/api/nl2sql/generate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ query: query, intent: data })
        });
        const sqlData = await sqlResp.json();

        if (sqlData.sql) {
            resultArea.innerHTML += `
                <h4>\ud83d\udcbb 生成的SQL</h4>
                <div class="sql-display">${sqlData.sql}</div>
                <button class="btn btn-primary" onclick="executeNL2SQL('${sqlData.sql.replace(/'/g, "\\'")}')">\u25b6 执行查询</button>
            `;
        }
    } catch (err) {
        resultArea.innerHTML = `<p style="color: #ef4444;">\u274c 分析失败: ${err.message}</p>`;
    }
}

async function executeNL2SQL(sql) {
    const resultArea = document.getElementById('nl2sql-result');
    resultArea.innerHTML += '<p style="color: #60a5fa; margin-top: 12px;">\u23f3 正在执行查询...</p>';

    try {
        const resp = await fetch('/api/databases/query', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ sql: sql })
        });
        const data = await resp.json();

        if (data.results) {
            let tableHtml = '<table class="db-result-table"><thead><tr>';
            if (data.columns && data.columns.length > 0) {
                data.columns.forEach(col => { tableHtml += `<th>${col}</th>`; });
            }
            tableHtml += '</tr></thead><tbody>';
            data.results.forEach(row => {
                tableHtml += '<tr>';
                Object.values(row).forEach(val => { tableHtml += `<td>${val}</td>`; });
                tableHtml += '</tr>';
            });
            tableHtml += '</tbody></table>';

            resultArea.innerHTML += `
                <h4>\ud83d\udcca 查询结果 (${data.results.length} 行)</h4>
                <div style="overflow-x: auto;">${tableHtml}</div>
            `;
        } else if (data.error) {
            resultArea.innerHTML += `<p style="color: #ef4444;">\u274c ${data.error}</p>`;
        }
    } catch (err) {
        resultArea.innerHTML += `<p style="color: #ef4444;">\u274c 执行失败: ${err.message}</p>`;
    }
}

// ==================== 事件监听 ====================

// 快捷键支持
document.addEventListener('keydown', function(e) {
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

// ==================== 初始化 ====================

window.onload = function() {
    connectWS();
    loadSettings();
    loadConversations();
};
