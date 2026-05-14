#!/usr/bin/env python3
"""
测试重构后的 web 模块
"""
import sys
import os
import asyncio
import importlib

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def test_import(module_path, description):
    try:
        module = importlib.import_module(module_path)
        print(f"✅ {description}")
        return True
    except Exception as e:
        print(f"❌ {description} - {e}")
        return False


async def main():
    print("=" * 70)
    print("🚀 DATA-AI Web 模块测试")
    print("=" * 70)

    results = {}

    print("\n📋 1. 核心模块导入测试")
    print("-" * 50)

    results["web.__init__"] = test_import("web", "Web 包初始化")
    results["web.models"] = test_import("web.models", "数据模型模块")
    results["web.storage"] = test_import("web.storage", "存储模块")
    results["web.services"] = test_import("web.services", "业务逻辑模块")
    results["web.routes"] = test_import("web.routes", "路由模块")

    print("\n📋 2. 模型类可用性测试")
    print("-" * 50)
    try:
        from web.models import Settings, KnowledgeBase, Document, ProcessingRule, Skill, MCPServer
        print("✅ 所有模型类导入成功")
        results["模型类"] = True
        
        # 测试实例化
        settings = Settings()
        print("  ✓ Settings 实例化成功")
        
        knowledge_base = KnowledgeBase(id="test", name="测试知识库", description="测试", created_at="2024-01-01", updated_at="2024-01-01")
        print("  ✓ KnowledgeBase 实例化成功")
        
        results["模型实例化"] = True
    except Exception as e:
        print(f"❌ 模型测试失败: {e}")
        results["模型类"] = False
        results["模型实例化"] = False

    print("\n📋 3. 存储模块功能测试")
    print("-" * 50)
    try:
        from web.storage import (
            get_settings, save_settings,
            get_knowledge_bases, save_knowledge_bases,
            get_skills, save_skills,
            get_mcp_servers, save_mcp_servers,
            initialize_storage
        )
        print("✅ 存储函数导入成功")
        
        initialize_storage()
        print("  ✓ 初始化存储成功")
        
        current_settings = get_settings()
        print(f"  ✓ 获取设置成功 (提供商: {current_settings.llm.get('provider')})")
        
        results["存储模块"] = True
    except Exception as e:
        print(f"❌ 存储测试失败: {e}")
        results["存储模块"] = False

    print("\n📋 4. 服务模块功能测试")
    print("-" * 50)
    try:
        from web.services import execute_python, call_llm, clean_text, run_universal_agent
        print("✅ 服务函数导入成功")
        
        # 测试 clean_text
        cleaned = await clean_text("  hello world  ", {})
        print(f"  ✓ clean_text 测试成功: '{cleaned}'")
        
        results["服务模块"] = True
    except Exception as e:
        print(f"❌ 服务模块测试失败: {e}")
        results["服务模块"] = False

    print("\n📋 5. 主应用文件测试")
    print("-" * 50)
    try:
        # 尝试导入主应用
        import web_app
        print("✅ web_app.py 导入成功")
        
        # 检查 app 对象存在
        if hasattr(web_app, 'app'):
            print("  ✓ FastAPI app 实例存在")
        
        results["主应用"] = True
    except Exception as e:
        print(f"❌ 主应用测试失败: {e}")
        results["主应用"] = False

    print("\n" + "=" * 70)
    print("📊 测试总结")
    print("=" * 70)
    
    total = len(results)
    passed = sum(1 for v in results.values() if v)
    failed = total - passed
    
    for name, result in results.items():
        status = "✅ 通过" if result else "❌ 失败"
        print(f"  {name:20s}: {status}")
    
    print(f"\n  总计: {passed}/{total} 通过, {failed} 失败")
    print("=" * 70)
    
    return failed == 0


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
