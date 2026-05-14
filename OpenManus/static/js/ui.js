/**
 * 通用 UI 组件函数
 * 提取自 app.js，消除各模块重复代码
 */

/**
 * 通用 Tab 切换函数（替代 showSettingsTab/showKbTab/showSkillTab/showMcpTab/showDbTab）
 * @param {string} modalId - 模态框 ID
 * @param {string} prefix - section ID 前缀（如 'settings', 'kb', 'skill'）
 * @param {string} tab - 要激活的 tab 名称
 * @param {HTMLElement} el - 被点击的 tab 元素（可选）
 */
function showTab(modalId, prefix, tab, el) {
    const modal = document.getElementById(modalId);
    if (!modal) return;
    modal.querySelectorAll('.settings-tab').forEach(t => t.classList.remove('active'));
    modal.querySelectorAll('.settings-section').forEach(s => s.classList.remove('active'));
    if (el) {
        el.classList.add('active');
    } else {
        modal.querySelectorAll('.settings-tab').forEach(t => {
            if (t.getAttribute('onclick') && t.getAttribute('onclick').includes("'" + tab + "'")) {
                t.classList.add('active');
            }
        });
    }
    const section = document.getElementById(prefix + '-' + tab);
    if (section) section.classList.add('active');
}

/**
 * 通用确认对话框（替代原生 confirm）
 */
function showConfirm(message, onConfirm) {
    // 移除已有确认框
    const existing = document.getElementById('confirm-dialog');
    if (existing) existing.remove();

    const dialog = document.createElement('div');
    dialog.id = 'confirm-dialog';
    dialog.style.cssText = 'position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,0.5);display:flex;align-items:center;justify-content:center;z-index:10000;';
    dialog.innerHTML = `
        <div style="background:#1e293b;border-radius:12px;padding:24px;max-width:400px;width:90%;box-shadow:0 20px 60px rgba(0,0,0,0.3);">
            <p style="color:#e2e8f0;margin:0 0 20px;font-size:15px;line-height:1.5;">${message}</p>
            <div style="display:flex;gap:10px;justify-content:flex-end;">
                <button id="confirm-cancel" class="btn btn-secondary" style="padding:8px 20px;">取消</button>
                <button id="confirm-ok" class="btn btn-primary" style="padding:8px 20px;background:#ef444444;color:#f87171;border:1px solid rgba(239,68,68,0.3);">确定</button>
            </div>
        </div>
    `;
    document.body.appendChild(dialog);
    document.getElementById('confirm-cancel').onclick = () => dialog.remove();
    document.getElementById('confirm-ok').onclick = () => { dialog.remove(); onConfirm(); };
    dialog.addEventListener('click', (e) => { if (e.target === dialog) dialog.remove(); });
}

/**
 * 通用表格结果渲染（替代 databases.js 和 nl2sql.js 中的重复代码）
 */
function renderQueryResults(data, containerId) {
    const container = document.getElementById(containerId);
    if (!container) return;

    if (data.error) {
        container.innerHTML = `<div class="error-message">${escapeHtml(data.error)}</div>`;
        return;
    }
    if (!data.columns || data.columns.length === 0) {
        container.innerHTML = '<div style="color:#94a3b8;text-align:center;padding:20px;">查询结果为空</div>';
        return;
    }

    let html = '<div style="overflow-x:auto;"><table class="query-result-table"><thead><tr>';
    data.columns.forEach(col => { html += `<th>${escapeHtml(col)}</th>`; });
    html += '</tr></thead><tbody>';
    (data.rows || []).forEach(row => {
        html += '<tr>';
        row.forEach(cell => { html += `<td>${escapeHtml(String(cell))}</td>`; });
        html += '</tr>';
    });
    html += '</tbody></table></div>';
    html += `<div style="color:#64748b;font-size:12px;margin-top:8px;">共 ${data.rows ? data.rows.length : 0} 行</div>`;
    container.innerHTML = html;
}

/**
 * 代码块添加复制按钮
 */
function addCodeCopyButtons() {
    document.querySelectorAll('.message-text pre code').forEach(block => {
        if (block.parentElement.querySelector('.code-copy-btn')) return;
        const btn = document.createElement('button');
        btn.className = 'code-copy-btn';
        btn.textContent = '复制';
        btn.onclick = () => {
            navigator.clipboard.writeText(block.textContent).then(() => {
                btn.textContent = '已复制';
                setTimeout(() => { btn.textContent = '复制'; }, 2000);
            });
        };
        block.parentElement.style.position = 'relative';
        block.parentElement.appendChild(btn);
    });
}
