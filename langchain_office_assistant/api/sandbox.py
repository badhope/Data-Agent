import subprocess
import sys
import os
import tempfile
import base64
import re
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
        clean_stdout, chart_images = _extract_chart_output(stdout)
        images.extend(chart_images)

        if result.returncode != 0:
            return {
                "success": False,
                "error": _format_error(language, result.returncode, stderr),
                "output": clean_stdout,
                "images": images,
                "duration_ms": duration_ms,
            }

        return {
            "success": True,
            "output": clean_stdout,
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

_chart_counter = 0

def _custom_savefig(fname, **kwargs):
    _original_savefig(fname, **kwargs)

def _custom_show(*args, **kwargs):
    global _chart_counter
    for fig_num in plt.get_fignums():
        fig = plt.figure(fig_num)
        _chart_counter += 1
        fname = os.path.join(r'{work_dir}', f'_chart_{{_chart_counter}}.png')
        fig.savefig(fname, format='png', dpi=150, bbox_inches='tight')
        plt.close(fig)

plt.savefig = _custom_savefig
plt.show = _custom_show

try:
{chr(10).join("    " + line for line in code.split(chr(10)))}
except Exception as e:
    print(f"__SANDBOX_ERROR__:{{type(e).__name__}}:{{e}}", file=sys.stderr)
    sys.exit(1)
'''


def _extract_chart_output(stdout: str) -> tuple:
    images = []
    clean_lines = []
    in_chart_section = False

    for line in stdout.split('\n'):
        if line.strip() == '___CHART_OUTPUT___':
            in_chart_section = True
            continue
        if in_chart_section:
            if line.startswith('data:image/png;base64,'):
                images.append(line.strip())
            else:
                in_chart_section = False
                clean_lines.append(line)
        else:
            clean_lines.append(line)

    return '\n'.join(clean_lines), images


def _collect_images(session_dir: Path) -> List[str]:
    images = []
    for f in sorted(session_dir.glob("_chart_*.png")):
        try:
            with open(f, "rb") as img_file:
                img_b64 = base64.b64encode(img_file.read()).decode("utf-8")
                images.append(f"data:image/png;base64,{img_b64}")
            f.unlink()
        except:
            pass
    for f in session_dir.glob("*.png"):
        if f.name.startswith("_chart_"):
            continue
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
    error_line = ""

    for line in reversed(error_lines):
        stripped = line.strip()
        if stripped.startswith("__SANDBOX_ERROR__:"):
            error_type = stripped.replace("__SANDBOX_ERROR__:", "", 1)
            break
        if "Error" in stripped or "Exception" in stripped:
            error_type = stripped
            if error_type.startswith("Error: "):
                error_type = error_type[len("Error: "):]
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
