# 代码沙箱(Code Sandbox)实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在现有Office Agent聊天界面中嵌入安全的代码沙箱，支持Python/JavaScript代码执行和图表生成，用户在对话中直接运行代码并查看结果。

**Architecture:** 后端使用子进程隔离执行代码（Python通过subprocess、JavaScript通过Node.js），设置超时和资源限制保证安全。前端在聊天消息中嵌入代码编辑器和输出展示区域，图表以base64图片直接嵌入聊天消息。沙箱与现有意图识别系统集成，当识别到代码执行意图时自动触发。

**Tech Stack:** FastAPI(后端API)、subprocess(代码执行)、matplotlib/plotly(图表生成)、CodeMirror或Monaco(前端代码编辑器)、base64(图片传输)

---

## 文件结构

| 操作 | 文件路径 | 职责 |
|------|---------|------|
| 创建 | `api/sandbox.py` | 沙箱核心执行引擎：Python/JS代码执行、安全限制、输出捕获 |
| 创建 | `api/sandbox_routes.py` | 沙箱API路由：/sandbox/execute、/sandbox/languages |
| 修改 | `api/server.py` | 集成沙箱路由、意图识别新增sandbox意图、思维链新增代码执行步骤 |
| 修改 | `frontend/index.html` | 新增代码编辑器组件、代码执行按钮、输出展示区域、图表渲染 |

---

### Task 1: 创建沙箱核心执行引擎

**Files:**
- Create: `api/sandbox.py`

- [ ] **Step 1: 创建sandbox.py，实现Python代码执行器**

```python
import subprocess
import sys
import os
import tempfile
import base64
import json
import time
from pathlib import Path
from typing import Dict, Any, Optional, List

SANBOX_DIR = Path(tempfile.gettempdir()) / "office_agent_sandbox"
SANBOX_DIR.mkdir(exist_ok=True)

SANDBOX_TIMEOUT = 30
SANDBOX_MAX_OUTPUT = 10000

SUPPORTED_LANGUAGES = {
    "python": {
        "name": "Python",
        "extension": ".py",
        "command": [sys.executable, "{file}"],
        "preinstalled": ["pandas", "matplotlib", "numpy", "json", "math", "datetime", "collections", "itertools", "re", "statistics"],
    },
    "javascript": {
        "name": "JavaScript",
        "extension": ".js",
        "command": ["node", "{file}"],
        "preinstalled": ["fs", "path", "http", "url", "util", "os"],
    },
}

def execute_code(code: str, language: str = "python", session_id: str = None) -> Dict[str, Any]:
    start_time = time.time()
    lang_config = SUPPORTED_LANGUAGES.get(language)
    if not lang_config:
        return {
            "success": False,
            "error": f"不支持的语言: {language}。支持的语言: {', '.join(SUPPORTED_LANGUAGES.keys())}",
            "output": "",
            "images": [],
            "duration_ms": 0,
        }

    session_dir = SANBOX_DIR / (session_id or "default")
    session_dir.mkdir(exist_ok=True)

    code_file = session_dir / f"code{lang_config['extension']}"
    code_file.write_text(code, encoding="utf-8")

    if language == "python":
        wrapped_code = _wrap_python_code(code, str(session_dir))
        code_file.write_text(wrapped_code, encoding="utf-8")

    cmd = [arg.replace("{file}", str(code_file)) for arg in lang_config["command"]]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=SANDBOX_TIMEOUT,
            cwd=str(session_dir),
            env={**os.environ, "MPLCONFIGDIR": str(session_dir), "HOME": str(session_dir)},
        )
        duration_ms = int((time.time() - start_time) * 1000)
        stdout = result.stdout[:SANDBOX_MAX_OUTPUT] if result.stdout else ""
        stderr = result.stderr[:SANDBOX_MAX_OUTPUT] if result.stderr else ""

        images = _collect_images(session_dir)

        if result.returncode != 0:
            return {
                "success": False,
                "error": _format_error(language, result.returncode, stderr),
                "output": stdout,
                "images": images,
                "duration_ms": duration_ms,
            }

        return {
            "success": True,
            "output": stdout,
            "images": images,
            "duration_ms": duration_ms,
        }
    except subprocess.TimeoutExpired:
        duration_ms = int((time.time() - start_time) * 1000)
        return {
            "success": False,
            "error": f"❌ 【代码执行超时】\n\n原因：代码执行超过{SANDBOX_TIMEOUT}秒限制\n\n解决方案：\n1. 检查代码中是否有死循环\n2. 优化算法复杂度\n3. 减少数据处理量",
            "output": "",
            "images": [],
            "duration_ms": duration_ms,
        }
    except Exception as e:
        duration_ms = int((time.time() - start_time) * 1000)
        return {
            "success": False,
            "error": f"❌ 【执行引擎错误】\n\n错误类型：{type(e).__name__}\n错误详情：{str(e)}\n\n解决方案：\n1. 检查代码语法是否正确\n2. 确认运行环境是否正常",
            "output": "",
            "images": [],
            "duration_ms": duration_ms,
        }

def _wrap_python_code(code: str, work_dir: str) -> str:
    return f'''import sys
import os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import io
import base64

_original_show = plt.show
_original_savefig = plt.savefig

_saved_figs = []

def _custom_savefig(fname, **kwargs):
    _original_savefig(fname, **kwargs)
    _saved_figs.append(fname)

def _custom_show(*args, **kwargs):
    for fig_num in plt.get_fignums():
        fig = plt.figure(fig_num)
        buf = io.BytesIO()
        fig.savefig(buf, format='png', dpi=150, bbox_inches='tight')
        buf.seek(0)
        img_b64 = base64.b64encode(buf.read()).decode('utf-8')
        _saved_figs.append(f'data:image/png;base64,{{img_b64}}')
        plt.close(fig)

plt.savefig = _custom_savefig
plt.show = _custom_show

try:
{chr(10).join("    " + line for line in code.split(chr(10)))}
except Exception as e:
    print(f"Error: {{type(e).__name__}}: {{e}}", file=sys.stderr)
finally:
    if _saved_figs:
        print("___CHART_OUTPUT___")
        for fig_path in _saved_figs:
            if fig_path.startswith('data:image'):
                print(fig_path)
            else:
                try:
                    with open(fig_path, 'rb') as f:
                        img_b64 = base64.b64encode(f.read()).decode('utf-8')
                        print(f'data:image/png;base64,{{img_b64}}')
                except:
                    pass
'''

def _collect_images(session_dir: Path) -> List[str]:
    images = []
    for f in session_dir.glob("*.png"):
        try:
            with open(f, "rb") as img_file:
                img_b64 = base64.b64encode(img_file.read()).decode("utf-8")
                images.append(f"data:image/png;base64,{img_b64}")
            f.unlink()
        except:
            pass
    return images

def _format_error(language: str, return_code: int, stderr: str) -> str:
    if not stderr:
        return f"❌ 【代码执行失败】\n\n退出码：{return_code}\n\n请检查代码逻辑是否正确。"

    error_lines = stderr.strip().split("\n")
    error_type = ""
    error_msg = ""
    error_line = ""

    for line in reversed(error_lines):
        if "Error" in line or "Exception" in line:
            error_type = line.strip()
            break

    for line in error_lines:
        if 'File "' in line or 'line ' in line.lower():
            error_line = line.strip()
            break

    solution_map = {
        "SyntaxError": "1. 检查括号、引号是否配对\n2. 检查缩进是否正确\n3. 检查是否缺少冒号(:)",
        "NameError": "1. 检查变量名是否拼写正确\n2. 确认变量是否已定义\n3. 检查是否缺少import语句",
        "TypeError": "1. 检查函数参数类型是否正确\n2. 检查是否对不支持的类型进行了操作\n3. 检查是否缺少必要的参数",
        "ImportError": "1. 确认该库是否已安装\n2. 检查库名拼写是否正确\n3. 尝试使用替代库",
        "IndexError": "1. 检查数组/列表索引是否越界\n2. 确认数据长度是否正确\n3. 使用len()检查长度",
        "KeyError": "1. 检查字典键名是否正确\n2. 使用dict.get()避免KeyError\n3. 打印字典keys()确认可用键",
        "ValueError": "1. 检查传入的值是否在有效范围内\n2. 确认数据格式是否正确\n3. 添加数据验证逻辑",
        "ZeroDivisionError": "1. 检查除数是否为零\n2. 添加零值检查\n3. 使用try-except处理异常",
        "RecursionError": "1. 检查递归是否有正确的终止条件\n2. 考虑使用迭代替代递归\n3. 增加递归深度限制sys.setrecursionlimit()",
    }

    error_kind = ""
    for kind in solution_map:
        if kind in error_type:
            error_kind = kind
            break

    solution = solution_map.get(error_kind, "1. 仔细阅读错误信息\n2. 检查代码逻辑\n3. 添加调试打印语句定位问题")

    result = f"❌ 【代码执行失败】\n\n错误类型：{error_type or '未知'}"
    if error_line:
        result += f"\n出错位置：{error_line}"
    result += f"\n\n解决方案：\n{solution}"
    return result

def get_supported_languages() -> List[Dict[str, Any]]:
    return [
        {
            "id": lang_id,
            "name": cfg["name"],
            "extension": cfg["extension"],
            "preinstalled": cfg["preinstalled"],
        }
        for lang_id, cfg in SUPPORTED_LANGUAGES.items()
    ]
```

- [ ] **Step 2: 验证sandbox.py可以被导入**

Run: `cd /workspace/langchain_office_assistant && python -c "from api.sandbox import execute_code, get_supported_languages; print('OK')"`

Expected: `OK`

---

### Task 2: 创建沙箱API路由

**Files:**
- Create: `api/sandbox_routes.py`
- Modify: `api/server.py` (集成路由)

- [ ] **Step 1: 创建sandbox_routes.py**

```python
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from .sandbox import execute_code, get_supported_languages

router = APIRouter(prefix="/sandbox", tags=["sandbox"])

class SandboxRequest(BaseModel):
    code: str
    language: str = "python"
    session_id: Optional[str] = None

class SandboxResponse(BaseModel):
    success: bool
    output: str
    error: Optional[str] = None
    images: List[str] = []
    duration_ms: int
    language: str

@router.post("/execute", response_model=SandboxResponse)
async def sandbox_execute(request: SandboxRequest):
    if not request.code.strip():
        raise HTTPException(status_code=400, detail="代码不能为空")
    if len(request.code) > 50000:
        raise HTTPException(status_code=400, detail="代码长度不能超过50000字符")
    result = execute_code(
        code=request.code,
        language=request.language,
        session_id=request.session_id,
    )
    result["language"] = request.language
    return SandboxResponse(**result)

@router.get("/languages")
async def sandbox_languages():
    return {"languages": get_supported_languages()}
```

- [ ] **Step 2: 在server.py中集成沙箱路由**

在 `api/server.py` 的 `app = FastAPI(...)` 之后添加路由导入和注册：

```python
from api.sandbox_routes import router as sandbox_router
app.include_router(sandbox_router)
```

同时在 TOOLS 列表中添加 sandbox 工具：

```python
{"id": "sandbox", "name": "代码沙箱", "desc": "运行Python/JavaScript代码", "icon": "💻", "color": "cyan"},
```

在 INTENT_KEYWORDS 中添加 sandbox 关键词：

```python
"sandbox": ["运行代码", "执行代码", "写代码", "代码", "编程", "python", "javascript", "code", "跑一下", "运行脚本", "写个程序", "编程实现"],
```

在 SYSTEM_PROMPT 中添加沙箱说明：

```
- 💻 代码沙箱：运行Python/JavaScript代码，生成图表和数据可视化
```

在 `generate_thinking_chain` 函数中添加 sandbox 意图的处理：

```python
elif intent == "sandbox":
    chain.append({
        "title": "思考代码执行",
        "content": "识别到代码执行意图，准备在沙箱环境中运行代码"
    })
```

- [ ] **Step 3: 验证API端点可用**

Run: `cd /workspace/langchain_office_assistant && python -c "from api.sandbox_routes import router; print('Routes:', [r.path for r in router.routes])"`

Expected: `Routes: ['/execute', '/languages']`

---

### Task 3: 前端代码编辑器与执行UI

**Files:**
- Modify: `frontend/index.html` (CSS样式 + JS逻辑 + HTML组件)

- [ ] **Step 1: 添加代码编辑器CSS样式**

在 `frontend/index.html` 的 `<style>` 标签内，在 `.chain-dot` 动画之后添加：

```css
.code-editor-section {
  margin-top: 12px;
  border: 1px solid var(--border);
  border-radius: 10px;
  overflow: hidden;
  background: var(--bg-card);
}

.code-editor-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 14px;
  background: var(--bg-tertiary);
  border-bottom: 1px solid var(--border);
  font-size: 12px;
}

.code-editor-lang {
  display: flex;
  align-items: center;
  gap: 6px;
  font-weight: 600;
  color: var(--text-primary);
}

.code-editor-actions {
  display: flex;
  gap: 6px;
}

.code-run-btn {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 4px 12px;
  background: #22c55e;
  color: white;
  border: none;
  border-radius: 6px;
  font-size: 12px;
  cursor: pointer;
  transition: all 0.15s ease;
}

.code-run-btn:hover {
  background: #16a34a;
}

.code-run-btn:disabled {
  background: var(--text-muted);
  cursor: not-allowed;
}

.code-run-btn.running {
  background: #f59e0b;
}

.code-textarea {
  width: 100%;
  min-height: 120px;
  padding: 14px;
  border: none;
  background: #1e1e2e;
  color: #cdd6f4;
  font-family: 'JetBrains Mono', 'Fira Code', 'Consolas', monospace;
  font-size: 13px;
  line-height: 1.6;
  resize: vertical;
  outline: none;
  tab-size: 4;
}

.code-output-section {
  border-top: 1px solid var(--border);
  background: var(--bg-secondary);
}

.code-output-header {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 14px;
  font-size: 12px;
  font-weight: 600;
  color: var(--text-secondary);
  border-bottom: 1px solid var(--border);
}

.code-output-content {
  padding: 12px 14px;
  font-family: 'JetBrains Mono', monospace;
  font-size: 12px;
  line-height: 1.5;
  white-space: pre-wrap;
  word-break: break-all;
  max-height: 300px;
  overflow-y: auto;
  color: var(--text-primary);
}

.code-output-content.error {
  color: #ef4444;
  background: #fef2f2;
}

.code-chart-output {
  padding: 12px;
  text-align: center;
  border-top: 1px solid var(--border);
}

.code-chart-output img {
  max-width: 100%;
  border-radius: 8px;
  border: 1px solid var(--border);
}

.code-duration {
  font-size: 11px;
  color: var(--text-muted);
  padding: 6px 14px;
  border-top: 1px solid var(--border);
  text-align: right;
}
```

- [ ] **Step 2: 添加代码编辑器JS函数**

在 `frontend/index.html` 的 `<script>` 标签内，在 `toggleChain` 函数之后添加：

```javascript
function addCodeMessage(code, language, result) {
  const container = document.getElementById('chatMessages');
  const div = document.createElement('div');
  div.className = 'chat-message bot';
  const msgId = 'msg-' + Date.now() + '-' + Math.random().toString(36).substr(2, 6);
  div.id = msgId;
  const msgIdx = messageIndexCounter++;
  div.dataset.msgIndex = msgIdx;
  div.dataset.role = 'bot';
  div.dataset.rawContent = code;

  const copySvg = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg>';
  const deleteSvg = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/></svg>';
  const playSvg = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="5 3 19 12 5 21 5 3"/></svg>';

  const langLabel = language === 'python' ? 'Python' : language === 'javascript' ? 'JavaScript' : language;
  const escapedCode = code.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');

  let outputHtml = '';
  if (result) {
    if (result.output) {
      outputHtml += `<div class="code-output-section"><div class="code-output-header">📋 输出</div><div class="code-output-content">${result.output.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;')}</div></div>`;
    }
    if (result.error) {
      outputHtml += `<div class="code-output-section"><div class="code-output-header">❌ 错误</div><div class="code-output-content error">${result.error.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;')}</div></div>`;
    }
    if (result.images && result.images.length > 0) {
      for (const img of result.images) {
        outputHtml += `<div class="code-chart-output"><img src="${img}" alt="chart"></div>`;
      }
    }
    if (result.duration_ms) {
      outputHtml += `<div class="code-duration">⏱ 执行耗时: ${result.duration_ms}ms</div>`;
    }
  }

  div.innerHTML = `
    <div class="chat-avatar">💻</div>
    <div>
      <div class="code-editor-section">
        <div class="code-editor-header">
          <div class="code-editor-lang">💻 ${langLabel}</div>
          <div class="code-editor-actions">
            <button class="code-run-btn" onclick="runCode('${msgId}', '${language}')" id="run-${msgId}">${playSvg}<span>运行</span></button>
          </div>
        </div>
        <textarea class="code-textarea" id="code-${msgId}" spellcheck="false" onkeydown="handleCodeKeydown(event, '${msgId}')">${escapedCode}</textarea>
        ${outputHtml}
      </div>
      <div class="chat-actions">
        <button class="chat-action-btn copy" onclick="copyMessage('${msgId}', this)" title="复制">${copySvg}<span>复制</span></button>
        <button class="chat-action-btn delete" onclick="deleteMessage('${msgId}')" title="删除">${deleteSvg}<span>删除</span></button>
      </div>
    </div>
  `;
  container.appendChild(div);
  container.scrollTop = container.scrollHeight;
}

async function runCode(msgId, language) {
  const textarea = document.getElementById('code-' + msgId);
  const btn = document.getElementById('run-' + msgId);
  const code = textarea.value;
  if (!code.trim()) return;

  btn.classList.add('running');
  btn.disabled = true;
  btn.querySelector('span').textContent = '运行中...';

  try {
    const res = await fetch(`${API_URL}/sandbox/execute`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ code, language, session_id: currentSessionId })
    });

    if (res.ok) {
      const data = await res.json();
      const editorSection = textarea.closest('.code-editor-section');
      const oldOutputs = editorSection.querySelectorAll('.code-output-section, .code-chart-output, .code-duration');
      oldOutputs.forEach(el => el.remove());

      let outputHtml = '';
      if (data.output) {
        outputHtml += `<div class="code-output-section"><div class="code-output-header">📋 输出</div><div class="code-output-content">${data.output.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;')}</div></div>`;
      }
      if (data.error) {
        outputHtml += `<div class="code-output-section"><div class="code-output-header">❌ 错误</div><div class="code-output-content error">${data.error.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;')}</div></div>`;
      }
      if (data.images && data.images.length > 0) {
        for (const img of data.images) {
          outputHtml += `<div class="code-chart-output"><img src="${img}" alt="chart"></div>`;
        }
      }
      outputHtml += `<div class="code-duration">⏱ 执行耗时: ${data.duration_ms}ms</div>`;
      textarea.insertAdjacentHTML('afterend', outputHtml);
    } else {
      const err = await res.json().catch(() => ({ detail: '未知错误' }));
      textarea.insertAdjacentHTML('afterend', `<div class="code-output-section"><div class="code-output-header">❌ 请求失败</div><div class="code-output-content error">${err.detail || '未知错误'}</div></div>`);
    }
  } catch (e) {
    textarea.insertAdjacentHTML('afterend', `<div class="code-output-section"><div class="code-output-header">❌ 网络错误</div><div class="code-output-content error">无法连接到沙箱服务: ${e.message}</div></div>`);
  } finally {
    btn.classList.remove('running');
    btn.disabled = false;
    btn.querySelector('span').textContent = '运行';
  }
}

function handleCodeKeydown(e, msgId) {
  if (e.key === 'Tab') {
    e.preventDefault();
    const ta = e.target;
    const start = ta.selectionStart;
    const end = ta.selectionEnd;
    ta.value = ta.value.substring(0, start) + '    ' + ta.value.substring(end);
    ta.selectionStart = ta.selectionEnd = start + 4;
  }
}
```

- [ ] **Step 3: 修改sendMessage，当AI返回代码时使用代码编辑器展示**

在 `sendMessage` 函数中，在 `addChatMessage('bot', data.response, ...)` 的分支中，添加代码检测逻辑：

```javascript
const codeBlockRegex = /```(\w+)?\n([\s\S]*?)```/g;
let hasCode = false;
let match;
while ((match = codeBlockRegex.exec(data.response)) !== null) {
  hasCode = true;
}
if (hasCode && (data.intent === 'sandbox' || data.intent === 'calculator' || data.intent === 'chart')) {
  renderCodeResponse(data.response, data.thinking);
} else {
  addChatMessage('bot', data.response, {
    intent: data.intent,
    tool: data.tool_used,
    confidence: data.confidence,
    duration: data.duration_ms
  }, data.thinking);
}
```

添加 `renderCodeResponse` 函数：

```javascript
function renderCodeResponse(response, thinking) {
  const codeBlockRegex = /```(\w+)?\n([\s\S]*?)```/g;
  const parts = [];
  let lastIndex = 0;
  let match;

  while ((match = codeBlockRegex.exec(response)) !== null) {
    if (match.index > lastIndex) {
      parts.push({ type: 'text', content: response.slice(lastIndex, match.index) });
    }
    const lang = (match[1] || 'python').toLowerCase();
    const langMap = { py: 'python', js: 'javascript', ts: 'javascript' };
    parts.push({ type: 'code', language: langMap[lang] || lang, content: match[2].trim() });
    lastIndex = match.index + match[0].length;
  }
  if (lastIndex < response.length) {
    parts.push({ type: 'text', content: response.slice(lastIndex) });
  }

  for (const part of parts) {
    if (part.type === 'text' && part.content.trim()) {
      addChatMessage('bot', part.content.trim(), {}, thinking);
      thinking = null;
    } else if (part.type === 'code') {
      addCodeMessage(part.content, part.language, null);
    }
  }
}
```

- [ ] **Step 4: 在快速操作中添加代码沙箱快捷按钮**

找到 `quick-actions` 区域，添加一个快捷按钮：

```html
<button class="quick-action-btn" onclick="sendQuick('帮我写一段Python代码生成柱状图')">💻 代码沙箱</button>
```

---

### Task 4: 集成测试与验证

**Files:**
- Modify: `api/server.py` (最终集成)
- Modify: `frontend/index.html` (最终集成)

- [ ] **Step 1: 重启后端服务，验证沙箱API**

Run: `curl -s http://localhost:8000/sandbox/languages | python3 -m json.tool`

Expected: 返回支持的语言列表

- [ ] **Step 2: 测试Python代码执行**

Run: `curl -s -X POST http://localhost:8000/sandbox/execute -H "Content-Type: application/json" -d '{"code":"print(1+1)", "language":"python"}' | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'Success: {d[\"success\"]}, Output: {d[\"output\"].strip()}')"`

Expected: `Success: True, Output: 2`

- [ ] **Step 3: 测试图表生成**

Run: `curl -s -X POST http://localhost:8000/sandbox/execute -H "Content-Type: application/json" -d '{"code":"import matplotlib.pyplot as plt\nplt.bar([\"A\",\"B\",\"C\"],[1,2,3])\nplt.title(\"Test\")\nplt.savefig(\"test_chart.png\")", "language":"python"}' | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'Success: {d[\"success\"]}, Images: {len(d[\"images\"])}')"`

Expected: `Success: True, Images: 1`

- [ ] **Step 4: 测试错误处理**

Run: `curl -s -X POST http://localhost:8000/sandbox/execute -H "Content-Type: application/json" -d '{"code":"x = 1/0", "language":"python"}' | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'Success: {d[\"success\"]}, Has error: {bool(d[\"error\"])}')"`

Expected: `Success: False, Has error: True`

- [ ] **Step 5: 用Playwright测试前端完整流程**

```python
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={"width": 1280, "height": 800})
    page.goto('http://localhost:8000/')
    page.wait_for_load_state('networkidle')
    page.wait_for_timeout(2000)

    # Test code sandbox via chat
    chat_input = page.locator('#chatInput')
    chat_input.fill('帮我写一段Python代码，生成一个简单的柱状图')
    page.locator('.chat-send-btn').click()
    page.wait_for_timeout(10000)

    # Check for code editor
    code_editors = page.locator('.code-editor-section')
    print(f"Code editors found: {code_editors.count()}")

    # Click run button if code editor exists
    if code_editors.count() > 0:
        run_btn = page.locator('.code-run-btn').first
        run_btn.click()
        page.wait_for_timeout(8000)
        page.screenshot(path='/tmp/test_sandbox.png')

        # Check for output
        outputs = page.locator('.code-output-content')
        charts = page.locator('.code-chart-output img')
        print(f"Output sections: {outputs.count()}")
        print(f"Chart images: {charts.count()}")

    browser.close()
```

Expected: 代码编辑器出现，点击运行后输出结果和图表

---

## 自检清单

**1. 规格覆盖：**
- ✅ Python环境（内置pandas、matplotlib、numpy）→ Task 1, 4
- ✅ JavaScript环境 → Task 1
- ✅ 用户在聊天对话框使用 → Task 3
- ✅ 图表直接嵌入聊天消息 → Task 3 (code-chart-output)
- ✅ 思考过程展示 → Task 2 (思维链集成)
- ✅ 与现有系统对接 → Task 2 (意图识别、TOOLS列表)
- ✅ 界面风格统一 → Task 3 (CSS沿用现有变量)
- ✅ 详细错误处理 → Task 1 (_format_error), Task 3 (error display)

**2. 占位符扫描：** 无TBD/TODO/placeholder

**3. 类型一致性：** SandboxRequest/SandboxResponse在Task 2定义，Task 3前端使用一致的字段名
