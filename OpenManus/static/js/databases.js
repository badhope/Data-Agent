// 数据库管理功能

let currentDatabaseId = null;

function showDbTab(tab, el) {
    showTab('database-modal', 'db', tab, el);
    if (tab === 'list') loadDatabases();
}

async function loadDatabases() {
    try {
        const res = await fetch('/api/databases');
        const dbs = await res.json();
        const list = document.getElementById('db-list-content');

        // Update database selectors
        const selectors = [document.getElementById('db-query-target'), document.getElementById('nl2sql-db-target')];
        selectors.forEach(sel => {
            if (!sel) return;
            const currentVal = sel.value;
            sel.innerHTML = '<option value="">-- 请选择数据库 --</option>';
            dbs.forEach(db => {
                sel.innerHTML += `<option value="${db.id}">${db.name}</option>`;
            });
            sel.value = currentVal;
        });

        if (dbs.length === 0) {
            list.innerHTML = '<div style="color: #94a3b8; text-align: center; padding: 40px 20px;"><div style="font-size: 48px; margin-bottom: 12px;">🗄️</div><p>暂无数据库</p><p style="font-size: 13px; margin-top: 8px;">点击"创建数据库"标签页添加新数据库</p></div>';
        } else {
            list.innerHTML = dbs.map(db => `
                <div class="db-item" style="display: flex; align-items: center; justify-content: space-between; padding: 14px; background: rgba(71,85,105,0.2); border-radius: 10px; margin-bottom: 8px; cursor: pointer;" onclick="selectDatabase('${db.id}')">
                    <div style="display: flex; align-items: center; gap: 12px;">
                        <span style="font-size: 24px;">🗄️</span>
                        <div>
                            <h4 style="color: white; margin: 0; font-size: 14px;">${db.name}</h4>
                            <p style="color: #64748b; margin: 2px 0 0; font-size: 12px;">创建于 ${new Date(db.created_at).toLocaleDateString()}</p>
                        </div>
                    </div>
                    <button class="delete-btn" onclick="event.stopPropagation(); deleteDatabase('${db.id}')" style="background: rgba(239,68,68,0.15); border: 1px solid rgba(239,68,68,0.3); color: #f87171; padding: 4px 10px; border-radius: 6px; cursor: pointer; font-size: 12px;">删除</button>
                </div>
            `).join('');
        }
    } catch (e) {
        console.error('Load databases error:', e);
    }
}

function selectDatabase(dbId) {
    currentDatabaseId = dbId;
    showDbTab('query');
    document.getElementById('db-query-target').value = dbId;
}

async function createDatabase() {
    const name = document.getElementById('db-create-name').value.trim();
    const type = document.getElementById('db-create-type').value;
    const desc = document.getElementById('db-create-desc').value.trim();
    if (!name) {
        showToast('请输入数据库名称', 'warning');
        return;
    }
    try {
        const body = { name };
        if (type) body.type = type;
        if (desc) body.description = desc;
        const res = await fetch('/api/databases', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(body)
        });
        if (!res.ok) throw new Error('创建失败');
        document.getElementById('db-create-name').value = '';
        document.getElementById('db-create-desc').value = '';
        loadDatabases();
        showDbTab('list');
        showToast(`数据库 "${name}" 创建成功！`, 'success');
    } catch (e) {
        showToast(`创建数据库失败: ${e.message}`, 'error');
    }
}

async function deleteDatabase(dbId) {
    showConfirm('确定要删除这个数据库吗？', async () => {
        try {
            await fetch(`/api/databases/${dbId}`, { method: 'DELETE' });
            loadDatabases();
            showToast('数据库已删除', 'success');
        } catch (e) {
            showToast('删除数据库失败: ' + e.message, 'error');
        }
    });
}

async function executeDbQuery() {
    const dbId = document.getElementById('db-query-target').value;
    const sql = document.getElementById('db-sql-input').value.trim();
    if (!dbId) { showToast('请选择数据库', 'warning'); return; }
    if (!sql) { showToast('请输入SQL语句', 'warning'); return; }

    const resultsDiv = document.getElementById('db-query-results');
    resultsDiv.innerHTML = '<p style="color: #60a5fa;">⏳ 正在执行查询...</p>';

    try {
        const res = await fetch(`/api/databases/${dbId}/query`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ sql })
        });
        const data = await res.json();

        if (data.success && data.columns) {
            renderQueryResults({ columns: data.columns, rows: data.data }, 'db-query-results');
            document.getElementById('db-query-results').innerHTML += `<p style="color: #64748b; font-size: 12px; margin-top: 8px;">共 ${data.row_count} 行</p>`;
        } else if (data.error) {
            resultsDiv.innerHTML = `<p style="color: #ef4444;">❌ ${escapeHtml(data.error)}</p>`;
        } else {
            resultsDiv.innerHTML = '<p style="color: #94a3b8;">查询完成，无返回数据</p>';
        }
    } catch (e) {
        resultsDiv.innerHTML = `<p style="color: #ef4444;">❌ 执行失败: ${e.message}</p>`;
    }
}
