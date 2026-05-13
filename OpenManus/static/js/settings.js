// 设置功能

async function loadSettings() {
    try {
        const res = await fetch('/api/settings');
        appSettings = await res.json();
        populateSettings(appSettings);
    } catch (e) { console.log(e); }
}

function populateSettings(settings) {
    document.getElementById('setting-provider').value = settings.llm.provider;
    document.getElementById('setting-model').value = settings.llm.model;
    document.getElementById('setting-base-url').value = settings.llm.base_url;
    document.getElementById('setting-api-key').value = settings.llm.api_key;
    document.getElementById('setting-max-tokens').value = settings.llm.max_tokens;
    document.getElementById('setting-temperature').value = settings.llm.temperature;
    document.getElementById('setting-sandbox-timeout').value = settings.sandbox.timeout;

    if (settings.langsmith) {
        if (settings.langsmith.enabled) {
            document.getElementById('setting-langsmith-enabled').classList.add('on');
        }
        document.getElementById('setting-langsmith-api-key').value = settings.langsmith.api_key || '';
        document.getElementById('setting-langsmith-project').value = settings.langsmith.project || 'dataagent';
        document.getElementById('setting-langsmith-endpoint').value = settings.langsmith.endpoint || 'https://api.smith.langchain.com';
    }
}

async function saveSettings() {
    const settings = {
        llm: {
            provider: document.getElementById('setting-provider').value,
            model: document.getElementById('setting-model').value,
            base_url: document.getElementById('setting-base-url').value,
            api_key: document.getElementById('setting-api-key').value,
            max_tokens: parseInt(document.getElementById('setting-max-tokens').value),
            temperature: parseFloat(document.getElementById('setting-temperature').value),
            top_p: 0.9,
            stream: false
        },
        sandbox: {
            enabled: document.getElementById('setting-sandbox-enabled').classList.contains('on'),
            timeout: parseInt(document.getElementById('setting-sandbox-timeout').value),
            allow_network: false
        },
        knowledge_base: {
            enabled: document.getElementById('setting-kb-enabled').classList.contains('on'),
            vector_db: 'sqlite',
            chunk_size: 1000,
            chunk_overlap: 200,
            embedding_model: 'text-embedding-v3'
        },
        conversation: { history_enabled: true, max_history: 50, auto_title: true },
        display: { theme: 'dark', thinking_chain: true, code_highlight: true, markdown_render: true },
        agent: { max_steps: 5, auto_mode: true, reasoning_mode: 'auto' },
        langsmith: {
            enabled: document.getElementById('setting-langsmith-enabled').classList.contains('on'),
            api_key: document.getElementById('setting-langsmith-api-key').value,
            project: document.getElementById('setting-langsmith-project').value,
            endpoint: document.getElementById('setting-langsmith-endpoint').value
        }
    };

    // 验证必填字段
    if (!settings.llm.api_key) {
        showError('请输入API Key');
        return;
    }
    if (!settings.llm.base_url) {
        showError('请输入Base URL');
        return;
    }
    if (!settings.llm.max_tokens || settings.llm.max_tokens < 1) {
        showError('最大Token必须大于0');
        return;
    }
    if (settings.llm.temperature < 0 || settings.llm.temperature > 2) {
        showError('温度系数必须在0-2之间');
        return;
    }

    try {
        const res = await fetch('/api/settings', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(settings)
        });

        if (!res.ok) {
            const errorData = await res.json().catch(() => ({ detail: '保存失败' }));
            throw new Error(errorData.detail || `请求失败 (${res.status})`);
        }

        appSettings = settings;
        closeModal('settings-modal');
        showSuccess('设置已保存成功！');

    } catch (e) {
        showError(`保存失败: ${e.message}`);
        console.error('Save settings error:', e);
    }
}

function resetSettings() {
    document.getElementById('setting-provider').value = 'aliyun';
    document.getElementById('setting-model').value = 'qwen-plus-latest';
    document.getElementById('setting-base-url').value = 'https://dashscope.aliyuncs.com/compatible-mode/v1';
    document.getElementById('setting-api-key').value = '';
}

function showSettingsTab(tab) {
    document.querySelectorAll('.settings-tab').forEach(t => t.classList.remove('active'));
    document.querySelectorAll('.settings-section').forEach(s => s.classList.remove('active'));
    event.target.classList.add('active');
    document.getElementById(`settings-${tab}`).classList.add('active');
}

function toggleSwitch(el) {
    el.classList.toggle('on');
}
