// 知识库功能

function showKbTab(tab, el) {
    document.querySelectorAll('#knowledge-modal .settings-tab').forEach(t => t.classList.remove('active'));
    document.querySelectorAll('#knowledge-modal .settings-section').forEach(s => s.classList.remove('active'));
    if (el) {
        el.classList.add('active');
    } else {
        // Programmatically find and activate the correct tab
        document.querySelectorAll('#knowledge-modal .settings-tab').forEach(t => {
            if (t.getAttribute('onclick') && t.getAttribute('onclick').includes(`'${tab}'`)) {
                t.classList.add('active');
            }
        });
    }
    document.getElementById(`kb-${tab}`).classList.add('active');
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
                    <div class="kb-card-icon">\ud83d\udcda</div>
                    <h4>${escapeHtml(kb.name)}</h4>
                    <p>${escapeHtml(kb.description || '暂无描述')}</p>
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

    // 前端验证
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
        currentKnowledgeBaseId = result.id;
        loadKnowledgeBases();
        showKbTab('list');
        showSuccess(`知识库 "${name}" 创建成功！`);

    } catch (e) {
        showError(`创建知识库失败: ${e.message}`, 'kb-create');
        console.error('Create knowledge base error:', e);
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
        // 验证所有文件
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

        // 获取当前知识库（如果没有，先创建一个默认的）
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
                currentKnowledgeBaseId = kb.id;
            } catch (e) {
                throw new Error('无法创建知识库，请刷新页面重试');
            }
        }

        // 逐个上传文件
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
        uploadStatus.textContent = `\u2705 成功上传 ${successCount} 个文件`;

        setTimeout(() => {
            progressDiv.style.display = 'none';
            showSuccess(`已上传 ${successCount} 个文档到知识库`);
            loadKnowledgeBases(); // 刷新知识库列表
        }, 1500);

    } catch (e) {
        progressDiv.style.display = 'none';
        errorDiv.style.display = 'block';
        errorMsg.textContent = e.message;
        console.error('Upload error:', e);
    }
}

function handleFileUpload(event) {
    const files = event.target.files;
    if (files.length > 0) {
        uploadFiles(files);
    }
}

function handleKbFileUpload(event) {
    const files = event.target.files;
    if (files.length > 0) {
        uploadFiles(files);
    }
}

async function searchKnowledgeBase() {
    const query = document.getElementById('kb-search-input').value.trim();
    if (!query) {
        showToast('请输入搜索关键词', 'warning');
        return;
    }
    const resultsDiv = document.getElementById('kb-search-results');
    resultsDiv.innerHTML = '<p style="color: #60a5fa;">⏳ 正在搜索...</p>';

    try {
        // Get first knowledge base for now
        const kbRes = await fetch('/api/knowledge-bases');
        const kbs = await kbRes.json();
        if (kbs.length === 0) {
            resultsDiv.innerHTML = '<p style="color: #94a3b8;">暂无知识库，请先创建知识库</p>';
            return;
        }

        const kbId = kbs[0].id;
        const res = await fetch(`/api/knowledge-bases/${kbId}/search`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ query, top_k: 5 })
        });
        const data = await res.json();

        if (data.results && data.results.length > 0) {
            resultsDiv.innerHTML = data.results.map(r => `
                <div style="padding: 12px; background: rgba(71,85,105,0.2); border-radius: 8px; margin-bottom: 8px;">
                    <div style="font-size: 12px; color: #64748b; margin-bottom: 4px;">📄 ${r.doc_name} (相关度: ${(r.score * 100).toFixed(1)}%)</div>
                    <div style="color: #cbd5e1; font-size: 13px; line-height: 1.6;">${r.content.substring(0, 200)}...</div>
                </div>
            `).join('');
        } else {
            resultsDiv.innerHTML = '<p style="color: #94a3b8;">未找到相关内容</p>';
        }
    } catch (e) {
        resultsDiv.innerHTML = `<p style="color: #ef4444;">搜索失败: ${e.message}</p>`;
    }
}

async function deleteKnowledgeBase(kbId) {
    if (!confirm('确定要删除这个知识库吗？所有文档也将被删除。')) return;
    try {
        await fetch(`/api/knowledge-bases/${kbId}`, { method: 'DELETE' });
        loadKnowledgeBases();
        showSuccess('知识库已删除');
    } catch (e) {
        showError('删除知识库失败: ' + e.message);
    }
}
