// NL2SQL 功能

let nl2sqlGeneratedSQL = '';

async function generateSQL() {
    const input = document.getElementById('nl2sql-input').value.trim();
    const dbId = document.getElementById('nl2sql-db-target').value;
    if (!input) { showToast('请输入自然语言查询', 'warning'); return; }

    // Show intent section
    document.getElementById('nl2sql-intent').style.display = 'block';
    document.getElementById('nl2sql-intent-content').innerHTML = '<p style="color: #60a5fa;">⏳ 正在分析意图...</p>';
    document.getElementById('nl2sql-generated').style.display = 'none';
    document.getElementById('nl2sql-results').style.display = 'none';

    try {
        // Step 1: Analyze intent
        const intentResp = await fetch('/api/nl2sql/analyze-intent', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ query: input, database_id: dbId || undefined })
        });
        const intentData = await intentResp.json();

        document.getElementById('intent-type').textContent = intentData.intents ? intentData.intents.join(', ') : '--';
        document.getElementById('intent-tables').textContent = intentData.tables ? intentData.tables.join(', ') : '--';
        document.getElementById('intent-fields').textContent = intentData.need_clarification ? '需要更多信息' : '已识别';

        // Step 2: Generate SQL
        const sqlResp = await fetch('/api/nl2sql/generate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ query: input, database_id: dbId || undefined, intent: intentData.intents ? intentData.intents[0] : 'query_data' })
        });
        const sqlData = await sqlResp.json();

        if (sqlData.sql) {
            nl2sqlGeneratedSQL = sqlData.sql;
            document.getElementById('nl2sql-sql-output').textContent = sqlData.sql;
            document.getElementById('nl2sql-generated').style.display = 'block';
        } else {
            showToast('SQL生成失败: ' + (sqlData.error || '未知错误'), 'error');
        }
    } catch (e) {
        showToast('生成失败: ' + e.message, 'error');
    }
}

function copyNL2SQL() {
    if (!nl2sqlGeneratedSQL) { showToast('没有可复制的SQL', 'warning'); return; }
    navigator.clipboard.writeText(nl2sqlGeneratedSQL).then(() => {
        showToast('SQL已复制到剪贴板', 'success');
    }).catch(() => {
        showToast('复制失败', 'error');
    });
}

async function executeNL2SQL() {
    if (!nl2sqlGeneratedSQL) { showToast('没有可执行的SQL', 'warning'); return; }
    const dbId = document.getElementById('nl2sql-db-target').value;
    if (!dbId) { showToast('请选择目标数据库', 'warning'); return; }

    document.getElementById('nl2sql-results').style.display = 'block';
    const resultsDiv = document.getElementById('nl2sql-results-content');
    resultsDiv.innerHTML = '<p style="color: #60a5fa;">⏳ 正在执行查询...</p>';

    try {
        const res = await fetch('/api/nl2sql/execute', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ sql: nl2sqlGeneratedSQL, database_id: dbId })
        });
        const data = await res.json();

        if (data.success && data.columns) {
            let html = '<div style="overflow-x: auto;"><table style="width:100%;border-collapse:collapse;font-size:13px;"><thead><tr>';
            data.columns.forEach(col => {
                html += `<th style="padding:8px 12px;text-align:left;background:rgba(59,130,246,0.15);color:#60a5fa;border-bottom:1px solid rgba(255,255,255,0.1);">${col}</th>`;
            });
            html += '</tr></thead><tbody>';
            data.data.forEach((row, idx) => {
                const bg = idx % 2 === 0 ? 'transparent' : 'rgba(71,85,105,0.1)';
                html += `<tr style="background:${bg}">`;
                row.forEach(val => {
                    html += `<td style="padding:8px 12px;border-bottom:1px solid rgba(255,255,255,0.05);color:#cbd5e1;">${val !== null ? val : '<span style="color:#475569">NULL</span>'}</td>`;
                });
                html += '</tr>';
            });
            html += '</tbody></table></div>';
            html += `<p style="color:#64748b;font-size:12px;margin-top:8px;">共 ${data.row_count} 行</p>`;
            resultsDiv.innerHTML = html;
        } else if (data.error) {
            resultsDiv.innerHTML = `<p style="color:#ef4444;">❌ ${data.error}</p>`;
        }
    } catch (e) {
        resultsDiv.innerHTML = `<p style="color:#ef4444;">❌ 执行失败: ${e.message}</p>`;
    }
}
