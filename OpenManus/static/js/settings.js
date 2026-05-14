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

    if (settings.conversation) {
        document.getElementById('setting-context-rounds').value = settings.conversation.context_rounds || 10;
        document.getElementById('setting-system-prompt').value = settings.conversation.system_prompt || '';
    }
    if (settings.display) {
        document.getElementById('setting-font-size').value = settings.display.font_size || 'medium';
        const showThinking = document.getElementById('setting-show-thinking');
        if (settings.display.thinking_chain === false) showThinking.classList.remove('on');
        else showThinking.classList.add('on');
        const codeHighlight = document.getElementById('setting-code-highlight');
        if (settings.display.code_highlight === false) codeHighlight.classList.remove('on');
        else codeHighlight.classList.add('on');
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
            stream: document.getElementById('setting-stream-enabled').classList.contains('on')
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
        conversation: {
            history_enabled: true,
            max_history: 50,
            auto_title: true,
            context_rounds: parseInt(document.getElementById('setting-context-rounds').value) || 10,
            system_prompt: document.getElementById('setting-system-prompt').value || ''
        },
        display: {
            theme: 'dark',
            thinking_chain: document.getElementById('setting-show-thinking').classList.contains('on'),
            code_highlight: document.getElementById('setting-code-highlight').classList.contains('on'),
            markdown_render: true,
            font_size: document.getElementById('setting-font-size').value || 'medium'
        },
        agent: { max_steps: parseInt(document.getElementById('setting-max-steps').value) || 10, auto_mode: true, reasoning_mode: 'auto' },
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
    document.getElementById('setting-max-tokens').value = '4096';
    document.getElementById('setting-temperature').value = '0.7';
    document.getElementById('setting-context-rounds').value = '10';
    document.getElementById('setting-system-prompt').value = '';
    document.getElementById('setting-font-size').value = 'medium';

    // Reset switches
    document.getElementById('setting-stream-enabled').classList.add('on');
    document.getElementById('setting-show-thinking').classList.add('on');
    document.getElementById('setting-code-highlight').classList.add('on');
    document.getElementById('setting-sandbox-enabled').classList.add('on');
    document.getElementById('setting-sandbox-timeout').value = '60';
    document.getElementById('setting-kb-enabled').classList.add('on');
    document.getElementById('setting-max-steps').value = '5';

    // Reset langsmith
    document.getElementById('setting-langsmith-enabled').classList.remove('on');
    document.getElementById('setting-langsmith-api-key').value = '';
    document.getElementById('setting-langsmith-project').value = 'dataagent';
    document.getElementById('setting-langsmith-endpoint').value = 'https://api.smith.langchain.com';

    showToast('已重置为默认设置', 'info');
}

function showSettingsTab(tab, el) {
    document.querySelectorAll('#settings-modal .settings-tab').forEach(t => t.classList.remove('active'));
    document.querySelectorAll('#settings-modal .settings-section').forEach(s => s.classList.remove('active'));
    if (el) {
        el.classList.add('active');
    } else {
        document.querySelectorAll('#settings-modal .settings-tab').forEach(t => {
            if (t.getAttribute('onclick') && t.getAttribute('onclick').includes(`'${tab}'`)) {
                t.classList.add('active');
            }
        });
    }
    document.getElementById(`settings-${tab}`).classList.add('active');
}

function toggleSwitch(el) {
    el.classList.toggle('on');
}
