#!/usr/bin/env python3
"""
Data-Agent 一键环境检测与自动修复工具
======================================
用法: python auto_setup.py [--fix] [--skip-browser]

功能:
  1. 检测 Python 版本 (>=3.10)
  2. 检测所有依赖包是否安装
  3. 检测配置文件是否存在
  4. 检测 API Key 是否配置
  5. 检测目录结构是否完整
  6. 检测关键模块能否正常导入
  7. 自动修复所有可修复的问题

参数:
  --fix          自动修复所有问题（默认仅检测）
  --skip-browser 跳过浏览器依赖安装
"""

import sys
import os
import importlib
import subprocess
import shutil
from pathlib import Path

# ============================================================
# 配色输出
# ============================================================

class Color:
    OK = "\033[92m"       # 绿色
    FAIL = "\033[91m"     # 红色
    WARN = "\033[93m"     # 黄色
    INFO = "\033[96m"     # 青色
    BOLD = "\033[1m"      # 粗体
    END = "\033[0m"       # 重置

def ok(msg):   print(f"  {Color.OK}✅ {msg}{Color.END}")
def fail(msg): print(f"  {Color.FAIL}❌ {msg}{Color.END}")
def warn(msg): print(f"  {Color.WARN}⚠️  {msg}{Color.END}")
def info(msg): print(f"  {Color.INFO}ℹ️  {msg}{Color.END}")
def fix(msg):  print(f"  {Color.INFO}🔧 {msg}{Color.END}")

def separator():
    print()

# ============================================================
# 检测项定义
# ============================================================

# 所有需要检测的 Python 包
# 格式: (import_name, pip_name, description)
REQUIRED_PACKAGES = [
    ("fastapi",              "fastapi",              "Web 框架"),
    ("uvicorn",              "uvicorn[standard]",    "ASGI 服务器"),
    ("pydantic",             "pydantic",             "数据验证"),
    ("pydantic_settings",    "pydantic-settings",    "Pydantic 配置"),
    ("openai",               "openai",               "OpenAI SDK"),
    ("anthropic",            "anthropic",            "Anthropic SDK"),
    ("tomli",                "tomli",                "TOML 解析 (3.10兼容)"),
    ("websockets",           "websockets",           "WebSocket"),
    ("httpx",                "httpx",                "HTTP 客户端"),
    ("aiohttp",              "aiohttp",              "异步 HTTP"),
    ("requests",             "requests",             "HTTP 请求"),
    ("pandas",               "pandas",               "数据处理"),
    ("numpy",                "numpy",                "数值计算"),
    ("PIL",                  "Pillow",               "图像处理"),
    ("pdfplumber",           "pdfplumber",           "PDF 解析"),
    ("pptx",                 "python-pptx",          "PPT 生成"),
    ("markdown",             "markdown",             "Markdown 渲染"),
    ("pygments",             "pygments",             "代码高亮"),
    ("loguru",               "loguru",               "日志"),
    ("rich",                 "rich",                 "终端美化"),
    ("aiosqlite",            "aiosqlite",            "异步 SQLite"),
    ("mcp",                  "mcp",                  "MCP 协议"),
    ("tenacity",             "tenacity",             "重试机制"),
    ("jinja2",               "jinja2",               "模板引擎"),
    ("dotenv",               "python-dotenv",        "环境变量"),
    ("multipart",            "python-multipart",     "表单解析"),
    ("aiofiles",             "aiofiles",             "异步文件"),
    ("bs4",                  "beautifulsoup4",       "HTML 解析"),
]

# 可选包
OPTIONAL_PACKAGES = [
    ("browser_use",          "browser-use",          "浏览器自动化"),
    ("boto3",                "boto3",                "AWS Bedrock"),
    ("tiktoken",             "tiktoken",             "Token 计算"),
    ("duckduckgo_search",    "duckduckgo-search",    "DuckDuckGo 搜索"),
    ("googlesearch",         "googlesearch-python",  "Google 搜索"),
]

# 必须存在的目录
REQUIRED_DIRS = [
    "app", "app/agent", "app/tool", "app/prompt", "app/flow",
    "config", "routers", "services", "static", "templates",
    "static/css", "static/js", "web", "web/templates",
]

# 必须存在的文件
REQUIRED_FILES = [
    "web_app.py", "main.py", "config.py", "models.py", "database.py",
    "requirements.txt",
]

# ============================================================
# 检测函数
# ============================================================

results = []  # (name, status: "ok"|"fail"|"warn"|"skip")

def check_python_version():
    """检测 Python 版本"""
    print(f"\n{Color.BOLD}📋 [1/6] Python 版本检测{Color.END}")
    version = sys.version_info
    ver_str = f"{version.major}.{version.minor}.{version.micro}"

    if version.major == 3 and version.minor >= 10:
        ok(f"Python {ver_str} (符合要求 >=3.10)")
        results.append(("Python 版本", "ok"))
        return True
    else:
        fail(f"Python {ver_str} (需要 >=3.10)")
        results.append(("Python 版本", "fail"))
        return False


def check_dependencies(auto_fix=False):
    """检测所有依赖包"""
    print(f"\n{Color.BOLD}📦 [2/6] 依赖包检测{Color.END}")

    missing_required = []
    missing_optional = []

    # 检测必需包
    for import_name, pip_name, desc in REQUIRED_PACKAGES:
        try:
            importlib.import_module(import_name)
            ok(f"{desc} ({pip_name})")
        except ImportError:
            fail(f"{desc} ({pip_name}) - 未安装")
            missing_required.append(pip_name)

    # 检测可选包
    for import_name, pip_name, desc in OPTIONAL_PACKAGES:
        try:
            importlib.import_module(import_name)
            ok(f"{desc} ({pip_name}) [可选]")
        except ImportError:
            warn(f"{desc} ({pip_name}) - 未安装 [可选]")
            missing_optional.append(pip_name)

    if not auto_fix:
        if not missing_required:
            results.append(("核心依赖", "ok"))
        else:
            results.append(("核心依赖", "fail"))

    # 自动安装缺失的包
    if auto_fix and missing_required:
        fix(f"正在安装 {len(missing_required)} 个缺失必需包...")
        try:
            subprocess.run(
                [sys.executable, "-m", "pip", "install", *missing_required,
                 "--break-system-packages", "-q"],
                check=True, capture_output=True, timeout=300
            )
            ok(f"成功安装 {len(missing_required)} 个必需包")
            # 安装成功后重新验证
            still_missing = []
            for import_name, pip_name, desc in REQUIRED_PACKAGES:
                if pip_name in missing_required:
                    try:
                        importlib.import_module(import_name)
                    except ImportError:
                        still_missing.append(pip_name)
            if still_missing:
                fail(f"以下包安装后仍不可用: {still_missing}")
                results.append(("自动安装", "fail"))
            else:
                results.append(("核心依赖", "ok"))
                results.append(("自动安装", "ok"))
        except subprocess.CalledProcessError as e:
            fail(f"必需包安装失败: {e}")
            results.append(("自动安装", "fail"))
    elif not missing_required:
        results.append(("核心依赖", "ok"))

    if auto_fix and missing_optional:
        fix(f"正在安装 {len(missing_optional)} 个可选包...")
        try:
            subprocess.run(
                [sys.executable, "-m", "pip", "install", *missing_optional,
                 "--break-system-packages", "-q"],
                check=True, capture_output=True, timeout=300
            )
            ok(f"成功安装 {len(missing_optional)} 个可选包")
        except subprocess.CalledProcessError:
            warn(f"部分可选包安装失败（不影响核心功能）")

    return len(missing_required) == 0


def check_config(auto_fix=False):
    """检测配置文件"""
    print(f"\n{Color.BOLD}⚙️  [3/6] 配置文件检测{Color.END}")

    config_dir = Path("config")
    config_file = config_dir / "config.toml"
    example_file = config_dir / "config.example.toml"

    # 检测配置文件
    if config_file.exists():
        ok("config/config.toml 存在")
    elif example_file.exists():
        warn("config/config.toml 不存在（将从示例创建）")
        if auto_fix:
            shutil.copy(example_file, config_file)
            ok("已从 config.example.toml 创建 config.toml")
        results.append(("配置文件", "ok" if config_file.exists() else "fail"))
    else:
        fail("配置文件和示例都不存在")
        results.append(("配置文件", "fail"))
        return False

    # 检测 API Key
    if config_file.exists():
        try:
            import re
            content = config_file.read_text(encoding="utf-8")
            match = re.search(r'^api_key\s*=\s*"([^"]*)"', content, re.MULTILINE)
            if match and match.group(1) not in ("", "YOUR_API_KEY"):
                ok("API Key 已配置")
                results.append(("API Key", "ok"))
            else:
                warn("API Key 未配置 (需手动编辑 config/config.toml)")
                results.append(("API Key", "warn"))
        except Exception as e:
            fail(f"读取配置失败: {e}")
            results.append(("API Key", "fail"))

    return True


def check_directories():
    """检测目录结构"""
    print(f"\n{Color.BOLD}📁 [4/6] 目录结构检测{Color.END}")

    all_ok = True
    for dir_name in REQUIRED_DIRS:
        if Path(dir_name).is_dir():
            ok(f"{dir_name}/")
        else:
            fail(f"{dir_name}/ (缺失)")
            all_ok = False

    for file_name in REQUIRED_FILES:
        if Path(file_name).is_file():
            ok(f"{file_name}")
        else:
            fail(f"{file_name} (缺失)")
            all_ok = False

    results.append(("目录结构", "ok" if all_ok else "fail"))
    return all_ok


def check_module_imports():
    """检测关键模块能否正常导入"""
    print(f"\n{Color.BOLD}🔧 [5/6] 模块导入检测{Color.END}")

    modules = [
        ("config",     "项目配置"),
        ("models",     "数据模型"),
        ("database",   "数据库层"),
        ("web_app",    "Web 应用"),
    ]

    all_ok = True
    for module, desc in modules:
        try:
            importlib.import_module(module)
            ok(f"{desc} ({module})")
        except Exception as e:
            fail(f"{desc} ({module}) - {type(e).__name__}: {e}")
            all_ok = False

    results.append(("模块导入", "ok" if all_ok else "fail"))
    return all_ok


def check_tomllib_compat():
    """检测 tomllib 兼容性"""
    print(f"\n{Color.BOLD}🔍 [6/6] Python 3.10 兼容性检测{Color.END}")

    issues = []

    # 检测 tomllib 导入
    try:
        import tomllib
        ok("tomllib 可用 (Python 3.11+)")
    except ImportError:
        try:
            import tomli as tomllib
            ok("tomli 可用 (Python 3.10 兼容)")
        except ImportError:
            fail("tomllib/tomli 均不可用")
            issues.append("tomli")

    # 检测 app/config.py 是否有兼容处理
    config_py = Path("app/config.py")
    if config_py.exists():
        content = config_py.read_text()
        if "import tomllib" in content and "tomli" not in content:
            warn("app/config.py 未做 Python 3.10 兼容处理")
            issues.append("config.py兼容")
        elif "tomli as tomllib" in content or "except" in content:
            ok("app/config.py 已做 Python 3.10 兼容处理")

    if not issues:
        results.append(("3.10 兼容性", "ok"))
    else:
        results.append(("3.10 兼容性", "fail"))

    return len(issues) == 0


# ============================================================
# 主函数
# ============================================================

def main():
    auto_fix = "--fix" in sys.argv
    skip_browser = "--skip-browser" in sys.argv

    os.chdir(Path(__file__).parent)

    print(f"\n{Color.BOLD}{'='*60}")
    print(f"  Data-Agent 环境检测与自动修复工具")
    print(f"{'='*60}{Color.END}")
    print(f"  模式: {'🔧 自动修复' if auto_fix else '🔍 仅检测'}")
    print(f"  Python: {sys.version.split()[0]}")
    print(f"  路径: {os.getcwd()}")

    # 执行所有检测
    check_python_version()
    check_dependencies(auto_fix=auto_fix)
    check_config(auto_fix=auto_fix)
    check_directories()
    check_module_imports()
    check_tomllib_compat()

    # 汇总结果
    print(f"\n{Color.BOLD}{'='*60}")
    print(f"  📊 检测结果汇总")
    print(f"{'='*60}{Color.END}")

    passed = sum(1 for _, s in results if s == "ok")
    failed = sum(1 for _, s in results if s == "fail")
    warned = sum(1 for _, s in results if s == "warn")
    total = len(results)

    for name, status in results:
        if status == "ok":
            ok(name)
        elif status == "fail":
            fail(name)
        elif status == "warn":
            warn(name)

    print(f"\n  {Color.BOLD}总计: {Color.OK}{passed} 通过{Color.END} / "
          f"{Color.FAIL}{failed} 失败{Color.END} / "
          f"{Color.WARN}{warned} 警告{Color.END} / 共 {total} 项")

    if failed == 0 and warned == 0:
        print(f"\n  {Color.OK}{Color.BOLD}🎉 所有检测通过！可以启动应用：{Color.END}")
        print(f"  {Color.INFO}   python web_app.py{Color.END}")
        return 0
    elif failed == 0:
        print(f"\n  {Color.WARN}{Color.BOLD}⚠️  基本可用，但有警告项需要关注{Color.END}")
        if not auto_fix:
            print(f"  {Color.INFO}   提示: 运行 python auto_setup.py --fix 自动修复{Color.END}")
        return 0
    else:
        print(f"\n  {Color.FAIL}{Color.BOLD}❌ 存在 {failed} 个问题需要修复{Color.END}")
        if not auto_fix:
            print(f"  {Color.INFO}   运行 python auto_setup.py --fix 自动修复{Color.END}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
