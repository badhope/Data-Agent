// MCP功能

async function loadMcpServers() {
    try {
        const res = await fetch('/api/mcp/servers');
        const servers = await res.json();
        const list = document.getElementById('mcp-list-content');
        if (servers.length === 0) {
            list.innerHTML = '<div style="color: #94a3b8; text-align: center; padding: 40px;">还没有配置MCP服务器</div>';
        } else {
            list.innerHTML = servers.map(s => `
                <div class="mcp-item">
                    <div class="skill-info">
                        <div class="skill-icon">${s.icon}</div>
                        <div class="skill-details">
                            <h4>${s.name}</h4>
                            <p>类型: ${s.type}</p>
                        </div>
                    </div>
                    <div class="setting-switch ${s.enabled ? 'on' : ''}" onclick="toggleSwitch(this)"></div>
                </div>
            `).join('');
        }
    } catch (e) {
        console.log(e);
    }
}

async function createMcpServer() {
    const name = document.getElementById('mcp-name').value.trim();
    const type = document.getElementById('mcp-type').value;
    const command = document.getElementById('mcp-command').value.trim();

    if (!name) {
        showError('请输入MCP服务器名称', 'mcp-create');
        return;
    }
    if (name.length > 50) {
        showError('名称不能超过50个字符', 'mcp-create');
        return;
    }
    if (!command && type === 'process') {
        showError('请输入启动命令', 'mcp-create');
        return;
    }

    try {
        const res = await fetch('/api/mcp/servers', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name, type, command, args: [], enabled: true })
        });

        if (!res.ok) {
            const errorData = await res.json().catch(() => ({ detail: '创建失败' }));
            throw new Error(errorData.detail || `请求失败 (${res.status})`);
        }

        await res.json();
        document.getElementById('mcp-name').value = '';
        document.getElementById('mcp-command').value = '';
        loadMcpServers();
        showSuccess(`MCP服务器 "${name}" 配置成功！`);

    } catch (e) {
        showError(`配置MCP服务器失败: ${e.message}`, 'mcp-create');
        console.error('Create MCP server error:', e);
    }
}

function quickAddMcp(type) {
    const mcpPresets = {
        'filesystem': {
            name: '\ud83d\udcc1 文件系统',
            command: 'npx',
            args: ['-y', '@modelcontextprotocol/server-filesystem', '/']
        },
        'github': {
            name: '\ud83d\udc19 GitHub',
            command: 'npx',
            args: ['-y', '@modelcontextprotocol/server-github']
        },
        'notion': {
            name: '\ud83d\udcd3 Notion',
            command: 'npx',
            args: ['-y', '@modelcontextprotocol/server-notion']
        },
        'brave': {
            name: '\ud83d\udd0d Brave搜索',
            command: 'npx',
            args: ['-y', '@modelcontextprotocol/server-brave-search']
        },
        'sqlite': {
            name: '\ud83d\uddc2 SQLite',
            command: 'npx',
            args: ['-y', '@modelcontextprotocol/server-sqlite']
        },
        'postgres': {
            name: '\ud83d\udc18 PostgreSQL',
            command: 'npx',
            args: ['-y', '@modelcontextprotocol/server-postgres']
        },
        'slack': {
            name: '\ud83d\udcac Slack',
            command: 'npx',
            args: ['-y', '@modelcontextprotocol/server-slack']
        },
        'gmail': {
            name: '\ud83d\udce7 Gmail',
            command: 'npx',
            args: ['-y', '@modelcontextprotocol/server-gmail']
        }
    };

    const preset = mcpPresets[type];
    if (preset) {
        document.getElementById('mcp-name').value = preset.name;
        document.getElementById('mcp-type').value = 'stdio';
        document.getElementById('mcp-command').value = preset.command + ' ' + preset.args.join(' ');
        showSuccess(`已填充 ${preset.name} 配置！请添加后配置相关环境变量`);
    }
}

async function deleteMcpServer(serverId) {
    if (!confirm('确定要删除这个MCP服务器吗？')) return;
    try {
        await fetch(`/api/mcp/servers/${serverId}`, { method: 'DELETE' });
        loadMcpServers();
        showSuccess('MCP服务器已删除');
    } catch (e) {
        showError('删除MCP服务器失败: ' + e.message);
    }
}

async function executeMcpTool(serverId, toolName, params) {
    try {
        const res = await fetch(`/api/mcp/servers/${serverId}/execute`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ tool: toolName, parameters: params })
        });
        const result = await res.json();
        return result.result;
    } catch (e) {
        showError('MCP执行失败: ' + e.message);
        return null;
    }
}
