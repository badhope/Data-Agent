#!/usr/bin/env python3
"""
简单启动脚本 - 直接运行FastAPI应用
"""
import sys
from pathlib import Path

# 确保我们在正确的目录
BASE_DIR = Path(__file__).parent
sys.path.insert(0, str(BASE_DIR))

# 检查必要的包
print("📦 检查依赖...")

try:
    import fastapi
    print("✅ FastAPI 可用")
except ImportError:
    print("⚠️ FastAPI未安装，尝试安装...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "fastapi", "python-multipart"])

try:
    from fastapi.staticfiles import StaticFiles
    from fastapi.templating import Jinja2Templates
except:
    pass

# 直接导入我们的应用
print("🚀 导入应用...")
from web_app_refactored import app

if __name__ == "__main__":
    # 尝试用uvicorn启动，如果没有就用内置服务器
    try:
        import uvicorn
        print("✅ 使用 Uvicorn 启动")
        uvicorn.run(app, host="0.0.0.0", port=8000)
    except ImportError:
        print("⚠️ Uvicorn 未安装，使用简单服务器...")
        # 使用简单启动方式
        import http.server
        import socketserver
        import threading
        import webbrowser
        from pathlib import Path
        
        # 实际上我们应该更好地处理，但为了快速启动：
        print("\n" + "="*60)
        print("请手动运行以下命令：")
        print("="*60)
        print("cd /workspace/OpenManus")
        print("pip install uvicorn")
        print("python -m uvicorn web_app_refactored:app --host 0.0.0.0 --port 8000")
        print("="*60)
        
        # 或者我们尝试用另一种方式
        print("\n\n尝试备用启动方式...")
        from pathlib import Path
        import sys
        
        sys.path.insert(0, str(Path(__file__).parent))
        from web_app_refactored import app
        
        print("\n✅ 应用已加载！")
        print("请使用以下方式之一：")
        print("1. 安装 uvicorn 后正常启动")
        print("2. 或者我尝试用 Python 内置的简单方式...")
        
        # 最小方案：显示提示
        print("\n📋 快速提示：")
        print("前端文件在：web/templates/ 和 web/static/")
        print("后端API在：web_app_refactored.py")
        print("泰迪杯功能在：web/tidycup/")
