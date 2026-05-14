// 通用工具函数

function escapeHtml(text) {
    if (text === null || text === undefined) return '';
    const div = document.createElement('div');
    div.textContent = String(text);
    return div.innerHTML;
}

// 全局变量
let ws = null;
let appSettings = {};
let currentConversationId = null;
let currentKnowledgeBaseId = null;

// Toast通知系统
function showToast(message, type = 'info') {
    // Remove existing toasts
    document.querySelectorAll('.toast').forEach(t => t.remove());

    const toast = document.createElement('div');
    toast.className = 'toast';

    const icons = { success: '✅', error: '❌', warning: '⚠️', info: 'ℹ️' };
    const colors = { success: '#10b981', error: '#ef4444', warning: '#f59e0b', info: '#3b82f6' };

    toast.innerHTML = `
        <span style="margin-right: 8px;">${icons[type] || icons.info}</span>
        <span>${escapeHtml(message)}</span>
    `;
    toast.style.borderLeft = `3px solid ${colors[type] || colors.info}`;

    document.body.appendChild(toast);

    // Trigger show animation
    requestAnimationFrame(() => {
        toast.classList.add('show');
    });

    // Auto remove after 3 seconds
    setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

// 涟漪效果
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

// 显示错误
function showError(message, targetId = null) {
    if (targetId) {
        const target = document.getElementById(targetId);
        if (target) {
            const errorDiv = document.createElement('div');
            errorDiv.className = 'error-message';
            errorDiv.style.cssText = 'margin-top: 8px; padding: 10px; background: rgba(239, 68, 68, 0.15); border: 1px solid rgba(239, 68, 68, 0.3); border-radius: 8px; color: #f87171; font-size: 13px;';
            errorDiv.textContent = '\u274c ' + message;
            target.appendChild(errorDiv);
            setTimeout(() => errorDiv.remove(), 5000);
        }
    } else {
        addMessage('\u274c ' + message, 'system');
    }
}

// 显示成功
function showSuccess(message) {
    showToast(message, 'success');
}

// 格式化文件大小
function formatFileSize(bytes) {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
}

// 按钮加载状态
function setButtonLoading(btn, loading) {
    if (loading) {
        btn._originalText = btn.textContent;
        btn.disabled = true;
        btn.style.opacity = '0.7';
        btn.textContent = '⏳ 处理中...';
    } else {
        btn.disabled = false;
        btn.style.opacity = '';
        btn.textContent = btn._originalText || btn.textContent;
    }
}
