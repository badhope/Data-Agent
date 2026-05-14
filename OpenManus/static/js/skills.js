// 技能功能

function showSkillTab(tab, el) {
    document.querySelectorAll('#prompt-modal .settings-tab').forEach(t => t.classList.remove('active'));
    document.querySelectorAll('#prompt-modal .settings-section').forEach(s => s.classList.remove('active'));
    if (el) {
        el.classList.add('active');
    } else {
        document.querySelectorAll('#prompt-modal .settings-tab').forEach(t => {
            if (t.getAttribute('onclick') && t.getAttribute('onclick').includes(`'${tab}'`)) {
                t.classList.add('active');
            }
        });
    }
    document.getElementById(`skill-${tab}`).classList.add('active');
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
                        <div class="skill-icon">${skill.icon}</div>
                        <div class="skill-details">
                            <h4>${skill.name}</h4>
                            <p>${skill.description}</p>
                        </div>
                    </div>
                    <div style="display: flex; align-items: center; gap: 8px;">
                        <span class="skill-badge">${skill.type}</span>
                        <button class="delete-btn" onclick="deleteSkill('${skill.id}')" title="删除技能" style="background: none; border: 1px solid rgba(239,68,68,0.3); color: #f87171; width: 28px; height: 28px; border-radius: 6px; cursor: pointer; font-size: 14px; display: flex; align-items: center; justify-content: center;">\u00d7</button>
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

    try {
        const res = await fetch('/api/skills', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name, icon, description: desc, parameters: [], prompts: {} })
        });

        if (!res.ok) {
            const errorData = await res.json().catch(() => ({ detail: '创建失败' }));
            throw new Error(errorData.detail || `请求失败 (${res.status})`);
        }

        await res.json();
        document.getElementById('skill-name').value = '';
        document.getElementById('skill-desc').value = '';
        loadSkills();
        showSkillTab('list');
        showSuccess(`技能 "${name}" 创建成功！`);

    } catch (e) {
        showError(`创建技能失败: ${e.message}`, 'skill-create');
        console.error('Create skill error:', e);
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
    if (!confirm('确定要删除这个技能吗？')) return;
    try {
        await fetch(`/api/skills/${skillId}`, { method: 'DELETE' });
        loadSkills();
        showSuccess('技能已删除');
    } catch (e) {
        showError('删除技能失败: ' + e.message);
    }
}
