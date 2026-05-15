// 技能功能

// 当前正在编辑的技能ID（null 表示创建模式）
let editingSkillId = null;

function showSkillTab(tab, el) {
    showTab('prompt-modal', 'skill', tab, el);
}

async function loadSkills() {
    try {
        const res = await fetch('/api/skills');
        const skills = await res.json();
        const list = document.getElementById('skill-list-content');
        if (skills.length === 0) {
            list.innerHTML = '<div style="color: #94a3b8; text-align: center; padding: 40px;">暂无技能，点击上方标签创建</div>';
        } else {
            list.innerHTML = skills.map(skill => `
                <div class="skill-item">
                    <div class="skill-info">
                        <div class="skill-icon">${escapeHtml(skill.icon)}</div>
                        <div class="skill-details">
                            <h4>${escapeHtml(skill.name)}</h4>
                            <p>${escapeHtml(skill.description)}</p>
                        </div>
                    </div>
                    <div style="display: flex; align-items: center; gap: 6px;">
                        <span class="skill-badge">${escapeHtml(skill.type)}</span>
                        <button class="skill-action-btn" onclick="useSkill('${escapeHtml(skill.id)}')" title="在对话中使用" style="background: rgba(59,130,246,0.15); border: 1px solid rgba(59,130,246,0.3); color: #60a5fa; width: 28px; height: 28px; border-radius: 6px; cursor: pointer; font-size: 13px; display: flex; align-items: center; justify-content: center; white-space: nowrap; padding: 0 4px;">&#9654;</button>
                        <button class="skill-action-btn" onclick="testSkill('${escapeHtml(skill.id)}')" title="测试技能" style="background: rgba(16,185,129,0.15); border: 1px solid rgba(16,185,129,0.3); color: #34d399; width: 28px; height: 28px; border-radius: 6px; cursor: pointer; font-size: 13px; display: flex; align-items: center; justify-content: center;">&#9889;</button>
                        <button class="skill-action-btn" onclick="editSkill('${escapeHtml(skill.id)}')" title="编辑技能" style="background: rgba(251,191,36,0.15); border: 1px solid rgba(251,191,36,0.3); color: #fbbf24; width: 28px; height: 28px; border-radius: 6px; cursor: pointer; font-size: 13px; display: flex; align-items: center; justify-content: center;">&#9998;</button>
                        <button class="delete-btn" onclick="deleteSkill('${escapeHtml(skill.id)}')" title="删除技能" style="background: none; border: 1px solid rgba(239,68,68,0.3); color: #f87171; width: 28px; height: 28px; border-radius: 6px; cursor: pointer; font-size: 14px; display: flex; align-items: center; justify-content: center;">\u00d7</button>
                    </div>
                </div>
            `).join('');
        }
    } catch (e) {
        console.log(e);
    }
}

function applySkillTemplate(templateId) {
    const templates = {
        'code-review': {
            name: '代码审查专家',
            icon: '🔍',
            desc: '智能代码审查，发现潜在问题并提供优化建议',
            purpose: '审查代码质量、安全性和最佳实践'
        },
        'data-analyst': {
            name: '数据分析师',
            icon: '📊',
            desc: '数据清洗、统计分析和可视化报告',
            purpose: '执行数据分析和可视化'
        },
        'translator': {
            name: '翻译助手',
            icon: '🌐',
            desc: '多语言翻译与本地化支持',
            purpose: '多语言翻译与本地化'
        },
        'writer': {
            name: '文案撰写',
            icon: '✍️',
            desc: '营销文案、技术文档和创意写作',
            purpose: '撰写营销文案和技术文档'
        }
    };
    const t = templates[templateId];
    if (!t) return;
    document.getElementById('skill-name').value = t.name;
    document.getElementById('skill-icon').value = t.icon;
    document.getElementById('skill-desc').value = t.desc;
    document.getElementById('skill-purpose').value = t.purpose;
    showSkillTab('create');
    showToast(`已加载"${t.name}"模板`, 'success');
}

async function createSkill() {
    const name = document.getElementById('skill-name').value.trim();
    const icon = document.getElementById('skill-icon').value.trim() || '\u26a1';
    const desc = document.getElementById('skill-desc').value.trim();

    if (!name) {
        showError('请输入技能名称', 'skill-create');
        return;
    }
    if (name.length > 50) {
        showError('技能名称不能超过50个字符', 'skill-create');
        return;
    }
    if (desc && desc.length > 500) {
        showError('描述不能超过500个字符', 'skill-create');
        return;
    }

    // 判断是创建还是更新
    const isEditing = editingSkillId !== null;
    const url = isEditing ? `/api/skills/${editingSkillId}` : '/api/skills';
    const method = isEditing ? 'PUT' : 'POST';

    try {
        const res = await fetch(url, {
            method: method,
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name, icon, description: desc, parameters: [], prompts: {} })
        });

        if (!res.ok) {
            const errorData = await res.json().catch(() => ({ detail: isEditing ? '更新失败' : '创建失败' }));
            throw new Error(errorData.detail || `请求失败 (${res.status})`);
        }

        await res.json();
        document.getElementById('skill-name').value = '';
        document.getElementById('skill-icon').value = '\u26a1';
        document.getElementById('skill-desc').value = '';
        document.getElementById('skill-purpose').value = '';

        // 重置编辑状态
        editingSkillId = null;
        resetSkillFormButton();

        loadSkills();
        showSkillTab('list');
        showSuccess(isEditing ? `技能 "${name}" 更新成功！` : `技能 "${name}" 创建成功！`);

    } catch (e) {
        showError(`${isEditing ? '更新' : '创建'}技能失败: ${e.message}`, 'skill-create');
        console.error(`${isEditing ? 'Update' : 'Create'} skill error:`, e);
    }
}

// 重置技能表单按钮为"创建技能"模式
function resetSkillFormButton() {
    const btn = document.querySelector('#skill-create .btn-primary');
    if (btn) {
        btn.textContent = '创建技能';
        btn.onclick = createSkill;
    }
}

// 切换技能表单为"更新技能"模式
function setSkillFormToEditMode() {
    const btn = document.querySelector('#skill-create .btn-primary');
    if (btn) {
        btn.textContent = '更新技能';
        btn.onclick = createSkill; // createSkill 内部会根据 editingSkillId 判断
    }
}

// 编辑技能 - 获取详情并填充到创建表单
async function editSkill(id) {
    try {
        const res = await fetch(`/api/skills/${id}`);
        if (!res.ok) {
            throw new Error(`获取技能详情失败 (${res.status})`);
        }
        const skill = await res.json();

        // 填充表单
        document.getElementById('skill-name').value = skill.name || '';
        document.getElementById('skill-icon').value = skill.icon || '\u26a1';
        document.getElementById('skill-desc').value = skill.description || '';
        document.getElementById('skill-purpose').value = skill.description || '';

        // 设置编辑模式
        editingSkillId = id;
        setSkillFormToEditMode();

        // 切换到创建/编辑标签页
        showSkillTab('create');
        showToast(`正在编辑技能「${skill.name}」`, 'info');

    } catch (e) {
        showError('获取技能详情失败: ' + e.message);
        console.error('Edit skill error:', e);
    }
}

// 测试技能
async function testSkill(id) {
    showToast('正在测试技能...', 'info');

    try {
        const res = await fetch(`/api/skills/${id}/test`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });

        if (!res.ok) {
            const errorData = await res.json().catch(() => ({ detail: '测试失败' }));
            throw new Error(errorData.detail || `请求失败 (${res.status})`);
        }

        const result = await res.json();

        // 在对话框中显示测试结果
        const chatArea = document.getElementById('chat-area');
        hideWelcomePage();

        const messageEl = document.createElement('div');
        messageEl.className = 'message system';
        messageEl.style.cssText = 'background: rgba(16,185,129,0.08); border: 1px solid rgba(16,185,129,0.2); border-radius: 12px; padding: 12px 16px; margin: 8px 0;';

        let resultHtml = '<div style="display: flex; align-items: center; gap: 8px; margin-bottom: 8px;">';
        resultHtml += '<span style="font-size: 16px;">&#9889;</span>';
        resultHtml += '<span style="color: #34d399; font-weight: 600;">技能测试结果</span>';
        resultHtml += '</div>';

        if (result.success !== undefined) {
            const statusIcon = result.success ? '&#9989;' : '&#10060;';
            const statusColor = result.success ? '#34d399' : '#f87171';
            resultHtml += `<div style="color: ${statusColor}; margin-bottom: 8px;">${statusIcon} ${result.success ? '测试通过' : '测试失败'}</div>`;
        }

        if (result.output || result.result || result.message) {
            const outputText = result.output || result.result || result.message;
            resultHtml += `<div style="color: #cbd5e1; font-size: 13px; white-space: pre-wrap; max-height: 200px; overflow-y: auto;">${escapeHtml(typeof outputText === 'string' ? outputText : JSON.stringify(outputText, null, 2))}</div>`;
        }

        messageEl.innerHTML = resultHtml;
        chatArea.appendChild(messageEl);
        chatArea.scrollTop = chatArea.scrollHeight;

        showToast('技能测试完成', 'success');

    } catch (e) {
        showError('技能测试失败: ' + e.message);
        console.error('Test skill error:', e);
    }
}

// 在对话中使用技能
async function useSkill(id) {
    try {
        const res = await fetch(`/api/skills/${id}/use`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });

        if (!res.ok) {
            const errorData = await res.json().catch(() => ({ detail: '调用技能失败' }));
            throw new Error(errorData.detail || `请求失败 (${res.status})`);
        }

        const result = await res.json();

        // 关闭技能弹窗
        closeModal('prompt-modal');

        // 将技能的 system_prompt 注入对话上下文
        if (result.system_prompt) {
            const inputBox = document.getElementById('input-box');
            const prefix = `[技能模式: ${result.name || id}]\n`;
            inputBox.value = prefix + inputBox.value;
            inputBox.focus();
            autoResize(inputBox);
            updateCharCount();
            showToast(`已启用技能「${result.name || id}」，请输入你的问题`, 'success');
        } else if (result.message) {
            // 如果后端返回了直接的消息，发送到对话
            sendMessageWithText(result.message);
            showToast(`技能「${result.name || id}」已执行`, 'success');
        } else {
            showToast(`技能「${result.name || id}」已激活`, 'success');
        }

    } catch (e) {
        showError('调用技能失败: ' + e.message);
        console.error('Use skill error:', e);
    }
}

async function aiGenerateSkill() {
    const purpose = document.getElementById('skill-purpose').value.trim();
    const generatingDiv = document.getElementById('ai-generating');

    if (!purpose) {
        showError('请先描述技能用途', 'skill-create');
        return;
    }

    generatingDiv.style.display = 'block';

    try {
        // 调用后端AI生成API
        const res = await fetch('/api/skills/generate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ purpose })
        });

        if (!res.ok) {
            const errorData = await res.json().catch(() => ({ detail: '生成失败' }));
            throw new Error(errorData.detail || `请求失败 (${res.status})`);
        }

        const result = await res.json();

        document.getElementById('skill-name').value = result.name || '';
        document.getElementById('skill-icon').value = result.icon || '\u26a1';
        document.getElementById('skill-desc').value = result.description || '';

        generatingDiv.style.display = 'none';
        showSuccess('AI已为您生成技能建议！');

    } catch (e) {
        generatingDiv.style.display = 'none';
        showError('AI生成失败: ' + e.message, 'skill-create');
        console.error('AI generate error:', e);
    }
}

async function deleteSkill(skillId) {
    showConfirm('确定要删除这个技能吗？', async () => {
        try {
            await fetch(`/api/skills/${skillId}`, { method: 'DELETE' });
            loadSkills();
            showSuccess('技能已删除');
        } catch (e) {
            showError('删除技能失败: ' + e.message);
        }
    });
}
