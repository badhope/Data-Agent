// 对话功能

async function loadConversations() {
    try {
        const res = await fetch('/api/conversations');
        const convs = await res.json();
        const list = document.getElementById('conversation-list');
        if (convs.length === 0) {
            list.innerHTML = '<div style="color: #94a3b8; text-align: center; padding: 20px;">还没有对话记录</div>';
        } else {
            list.innerHTML = convs.map(conv => `
                <div class="conversation-item ${conv.id === currentConversationId ? 'active' : ''}" onclick="loadConversation('${escapeHtml(conv.id)}')">
                    <div class="conversation-title">${escapeHtml(conv.title)}</div>
                    <div class="conversation-time">${new Date(conv.updated_at).toLocaleDateString()}</div>
                    <button class="delete-btn" onclick="event.stopPropagation(); deleteConversation('${escapeHtml(conv.id)}')">\u00d7</button>
                </div>
            `).join('');
        }
    } catch (e) { console.log(e); }
}

async function createNewConversation() {
    try {
        const res = await fetch('/api/conversations', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ title: '新对话' })
        });
        const conv = await res.json();
        currentConversationId = conv.id;
        clearChat();
        loadConversations();
        showSuccess('新对话已创建');
    } catch (e) {
        showError('创建对话失败: ' + e.message);
    }
}

async function loadConversation(convId) {
    try {
        const res = await fetch(`/api/conversations/${convId}`);
        const conv = await res.json();
        currentConversationId = conv.id;
        const chatArea = document.getElementById('chat-area');
        chatArea.innerHTML = conv.messages.map(msg => {
            let content;
            if (msg.type === 'assistant' && window.marked) {
                content = marked.parse(msg.content || '');
            } else {
                content = escapeHtml(msg.content || '').replace(/\n/g, '<br>');
            }
            return `
            <div class="message ${escapeHtml(msg.type)}">
                <div class="message-content">
                    <div class="message-text">${content}</div>
                </div>
            </div>`;
        }).join('');
        // 高亮代码块
        chatArea.querySelectorAll('pre code').forEach(block => {
            if (window.hljs) hljs.highlightElement(block);
        });
        loadConversations();
    } catch (e) {
        showError('加载对话失败: ' + e.message);
    }
}

async function deleteConversation(convId) {
    showConfirm('确定要删除这个对话吗？', async () => {
        try {
            await fetch(`/api/conversations/${convId}`, { method: 'DELETE' });
            if (currentConversationId === convId) {
                currentConversationId = null;
                clearChat();
            }
            loadConversations();
            showSuccess('对话已删除');
        } catch (e) {
            showError('删除对话失败: ' + e.message);
        }
    });
}

async function saveCurrentConversation() {
    if (!currentConversationId) {
        await createNewConversation();
    }
    const messages = [];
    document.querySelectorAll('.message').forEach(msg => {
        const type = msg.classList.contains('user') ? 'user' : msg.classList.contains('assistant') ? 'assistant' : 'system';
        const content = msg.querySelector('.message-content')?.textContent || '';
        if (type !== 'system') {
            messages.push({ type, content });
        }
    });
    try {
        await fetch(`/api/conversations/${currentConversationId}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ messages })
        });
    } catch (e) { console.log(e); }
}
