#!/usr/bin/env python3
"""
Data-Agent 配置验证工具
检查环境、依赖和配置是否正确
"""
import os
import sys
import subprocess
from pathlib import Path

def check_python_version():
    """检查 Python 版本"""
    print("📋 检查 Python 版本...")
    version = sys.version_info
    if version.major == 3 and version.minor >= 10:
        print(f"   ✅ Python {version.major}.{version.minor}.{version.micro}")
        return True
    else:
        print(f"   ❌ Python {version.major}.{version.minor}.{version.micro} (需要 3.10+)")
        return False

def check_dependencies():
    """检查关键依赖"""
    print("\n📦 检查依赖...")
    required = [
        ("fastapi", "FastAPI"),
        ("uvicorn", "Uvicorn"),
        ("pydantic", "Pydantic"),
        ("openai", "OpenAI"),
    ]
    
    all_ok = True
    for module, name in required:
        try:
            __import__(module)
            print(f"   ✅ {name}")
        except ImportError:
            print(f"   ❌ {name} (未安装)")
            all_ok = False
    
    return all_ok

def check_config_file():
    """检查配置文件"""
    print("\n⚙️  检查配置文件...")
    config_path = Path("config/config.toml")
    example_path = Path("config/config.example.toml")
    
    if not config_path.exists():
        if example_path.exists():
            print("   ⚠️  配置文件不存在，已从示例创建")
            import shutil
            shutil.copy(example_path, config_path)
            return False
        else:
            print("   ❌ 配置文件和示例都不存在")
            return False
    
    print("   ✅ 配置文件存在")
    
    # 检查 API Key - 使用正则表达式读取，避免依赖 toml 库
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        # 简单解析 api_key
        import re
        match = re.search(r'^api_key\s*=\s*"([^"]*)"', content, re.MULTILINE)
        if match:
            api_key = match.group(1)
            if api_key in ["", "YOUR_API_KEY"]:
                print("   ⚠️  请设置 API Key (config/config.toml)")
                return False
            else:
                print("   ✅ API Key 已设置")
                return True
        else:
            print("   ⚠️  未找到 API Key 配置")
            return False
    except Exception as e:
        print(f"   ❌ 读取配置失败: {e}")
        return False

def check_directories():
    """检查必要目录"""
    print("\n📁 检查目录结构...")
    required_dirs = ["app", "config", "routers", "services", "static", "templates"]
    all_ok = True
    
    for dir_name in required_dirs:
        if Path(dir_name).exists():
            print(f"   ✅ {dir_name}/")
        else:
            print(f"   ❌ {dir_name}/ (缺失)")
            all_ok = False
    
    return all_ok

def check_entry_points():
    """检查入口文件"""
    print("\n🚀 检查入口文件...")
    entry_points = [
        ("web_app.py", "Web 模式"),
        ("main.py", "CLI 模式"),
        ("run_flow.py", "Flow 模式"),
    ]
    
    all_ok = True
    for file, desc in entry_points:
        if Path(file).exists():
            print(f"   ✅ {file} ({desc})")
        else:
            print(f"   ❌ {file} ({desc}) 缺失")
            all_ok = False
    
    return all_ok

def test_import():
    """测试关键导入"""
    print("\n🔧 测试模块导入...")
    try:
        sys.path.insert(0, str(Path(__file__).parent))
        from web_app import app
        print("   ✅ web_app 可导入")
        return True
    except Exception as e:
        print(f"   ❌ web_app 导入失败: {e}")
        return False

def main():
    """主函数"""
    print("=" * 50)
    print("🔍 Data-Agent 配置检查工具")
    print("=" * 50)
    
    checks = [
        ("Python 版本", check_python_version),
        ("依赖包", check_dependencies),
        ("目录结构", check_directories),
        ("入口文件", check_entry_points),
        ("配置文件", check_config_file),
        ("模块导入", test_import),
    ]
    
    results = []
    for name, check_func in checks:
        try:
            result = check_func()
            results.append((name, result))
        except Exception as e:
            print(f"   ❌ 检查失败: {e}")
            results.append((name, False))
    
    # 总结
    print("\n" + "=" * 50)
    print("📊 检查结果")
    print("=" * 50)
    
    passed = sum(1 for _, r in results if r)
    total = len(results)
    
    for name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"   {status} - {name}")
    
    print(f"\n总计: {passed}/{total} 项通过")
    
    if passed == total:
        print("\n🎉 所有检查通过！可以启动应用：")
        print("   python web_app.py")
        return 0
    else:
        print("\n⚠️  部分检查未通过，请修复后重试")
        print("   运行 ./setup.sh 进行自动修复")
        return 1

if __name__ == "__main__":
    sys.exit(main())
