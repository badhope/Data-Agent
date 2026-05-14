"""
全面诊断和端到端测试脚本
模拟真实用户使用场景，发现并修复问题
"""
import asyncio
from pathlib import Path
import sys
import traceback
import json
from typing import Dict, Any

# 添加项目路径
BASE_DIR = Path(__file__).parent
sys.path.insert(0, str(BASE_DIR))

print("="*70)
print("DATA-AI 系统全面诊断和测试")
print("="*70)


def print_section(title):
    """打印章节标题"""
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}")


def print_pass(message):
    print(f"  ✓ {message}")


def print_fail(message):
    print(f"  ✗ {message}")


def print_info(message):
    print(f"  ℹ {message}")


def check_file_structure():
    """检查文件结构"""
    print_section("1. 文件结构检查")
    
    checks = [
        ("web_app.py", "主应用文件"),
        ("web/__init__.py", "Web模块初始化"),
        ("web/models.py", "数据模型"),
        ("web/storage.py", "存储模块"),
        ("web/services.py", "服务模块"),
        ("web/routes.py", "路由模块"),
        ("web/tidycup/__init__.py", "泰迪杯模块初始化"),
        ("web/tidycup/pdf_parser.py", "PDF解析器"),
        ("web/tidycup/nl2sql_engine.py", "NL2SQL引擎"),
        ("web/tidycup/rag_and_planning.py", "RAG与规划"),
        ("web/templates/index.html", "前端模板"),
        ("web/static/css/style.css", "CSS样式"),
        ("web/static/js/app.js", "前端JS"),
    ]
    
    all_exist = True
    for file, desc in checks:
        path = BASE_DIR / file
        if path.exists():
            size_mb = path.stat().st_size / 1024 / 1024
            print_pass(f"{desc} - {file} ({size_mb:.2f} MB)")
        else:
            print_fail(f"{desc} - {file} [缺失]")
            all_exist = False
    
    return all_exist


def check_imports():
    """检查模块导入"""
    print_section("2. 模块导入检查")
    
    checks = []
    try:
        import fastapi
        print_pass("FastAPI - 正常")
    except Exception as e:
        print_fail(f"FastAPI - 导入失败: {e}")
        checks.append(False)
    else:
        checks.append(True)
    
    try:
        from web import models, storage, services, routes
        print_pass("Web核心模块 - 正常")
    except Exception as e:
        print_fail(f"Web核心模块 - 导入失败: {e}")
        traceback.print_exc()
        checks.append(False)
    else:
        checks.append(True)
    
    try:
        from web.tidycup import FullTidyCupPipeline
        print_pass("泰迪杯模块 - 正常")
    except Exception as e:
        print_fail(f"泰迪杯模块 - 导入失败: {e}")
        traceback.print_exc()
        checks.append(False)
    else:
        checks.append(True)
    
    return all(checks)


def test_data_models():
    """测试数据模型"""
    print_section("3. 数据模型测试")
    
    try:
        from web import models
        
        test_settings = models.Settings(
            llm={"provider": "test", "api_key": "test"},
            knowledge_base={"enabled": True}
        )
        print_pass("Settings模型 - 正常")
        
        test_kb = models.KnowledgeBase(
            id="test",
            name="测试知识库",
            created_at="2024-01-01",
            updated_at="2024-01-01"
        )
        print_pass("KnowledgeBase模型 - 正常")
        
        return True
    except Exception as e:
        print_fail(f"数据模型测试失败: {e}")
        traceback.print_exc()
        return False


def test_storage_system():
    """测试存储系统"""
    print_section("4. 存储系统测试")
    
    try:
        from web import storage
        
        storage.initialize_storage()
        print_pass("存储初始化 - 正常")
        
        settings = storage.get_settings()
        print_pass("读取配置 - 正常")
        
        kbs = storage.get_knowledge_bases()
        print_pass("读取知识库 - 正常")
        
        return True
    except Exception as e:
        print_fail(f"存储系统测试失败: {e}")
        traceback.print_exc()
        return False


async def test_tidycup_rag():
    """测试泰迪杯RAG"""
    print_section("5. 泰迪杯RAG引擎测试")
    
    try:
        from web.tidycup import RAGEngine
        
        rag = RAGEngine()
        
        # 测试多个查询
        test_queries = [
            "贵州茅台",
            "平安银行",
            "白酒行业",
            "净利润",
            "2023年"
        ]
        
        all_good = True
        for query in test_queries:
            try:
                results = await rag.retrieve(query)
                if results:
                    print_pass(f"查询 '{query}' - 返回 {len(results)} 个结果")
                else:
                    print_info(f"查询 '{query}' - 无结果 (预期)")
            except Exception as e:
                print_fail(f"查询 '{query}' - 失败: {e}")
                all_good = False
        
        return all_good
    except Exception as e:
        print_fail(f"RAG测试失败: {e}")
        traceback.print_exc()
        return False


async def test_tidycup_planner():
    """测试意图规划器"""
    print_section("6. 意图规划器测试")
    
    try:
        from web.tidycup import MultiIntentPlanner
        
        planner = MultiIntentPlanner()
        
        test_cases = [
            ("简单查询", "贵州茅台2023年数据"),
            ("对比查询", "对比贵州茅台和平安银行"),
            ("趋势查询", "贵州茅台的增长趋势"),
        ]
        
        all_good = True
        for case_name, query in test_cases:
            try:
                plan = planner.plan(query)
                print_pass(f"{case_name}: '{query}' - 分解为 {len(plan.sub_tasks)} 个子任务")
            except Exception as e:
                print_fail(f"{case_name}: '{query}' - 失败: {e}")
                all_good = False
        
        return all_good
    except Exception as e:
        print_fail(f"规划器测试失败: {e}")
        traceback.print_exc()
        return False


async def test_tidycup_nl2sql():
    """测试NL2SQL引擎"""
    print_section("7. NL2SQL引擎测试")
    
    try:
        from web.tidycup import FullNL2SQLPipeline
        
        db_path = BASE_DIR / "data" / "test_diagnose.db"
        db_path.parent.mkdir(parents=True, exist_ok=True)
        
        pipeline = FullNL2SQLPipeline(db_path)
        pipeline.initialize()
        print_pass("NL2SQL初始化 - 正常")
        
        # 测试澄清场景
        result = await pipeline.process_query("财务数据")
        print_pass(f"模糊查询 - 类型: {result.get('type')}")
        
        # 测试具体查询
        result = await pipeline.process_query("贵州茅台2023年")
        print_pass(f"具体查询 - 类型: {result.get('type')}")
        
        return True
    except Exception as e:
        print_fail(f"NL2SQL测试失败: {e}")
        traceback.print_exc()
        return False


async def test_full_tidycup_pipeline():
    """测试完整泰迪杯流水线"""
    print_section("8. 完整泰迪杯流水线测试")
    
    try:
        from web.tidycup import FullTidyCupPipeline
        
        db_path = BASE_DIR / "data" / "test_full_diagnose.db"
        db_path.parent.mkdir(parents=True, exist_ok=True)
        
        pipeline = FullTidyCupPipeline(db_path)
        pipeline.initialize()
        print_pass("流水线初始化 - 正常")
        
        # 端到端测试
        queries = [
            "贵州茅台2023年财务数据",
            "平安银行净利润",
        ]
        
        all_good = True
        for query in queries:
            try:
                result = await pipeline.process_complex_query(query)
                print_pass(f"查询 '{query}' - 成功")
                print_info(f"  - 任务数: {len(result['task_plan']['sub_tasks'])}")
                print_info(f"  - RAG结果: {len(result['rag_results'])}")
            except Exception as e:
                print_fail(f"查询 '{query}' - 失败: {e}")
                all_good = False
        
        return all_good
    except Exception as e:
        print_fail(f"完整流水线测试失败: {e}")
        traceback.print_exc()
        return False


def test_fastapi_app():
    """测试FastAPI应用"""
    print_section("9. FastAPI应用测试")
    
    try:
        from web_app import app
        print_pass("FastAPI应用 - 导入正常")
        
        routes = [route.path for route in app.routes]
        print_info(f"路由数量: {len(routes)}")
        
        required_routes = ["/", "/api/settings", "/ws", "/api/tidycup/status"]
        for route in required_routes:
            if route in routes:
                print_pass(f"路由 '{route}' - 存在")
            else:
                print_fail(f"路由 '{route}' - 缺失")
        
        return True
    except Exception as e:
        print_fail(f"FastAPI应用测试失败: {e}")
        traceback.print_exc()
        return False


def test_frontend_files():
    """测试前端文件"""
    print_section("10. 前端文件检查")
    
    try:
        html_path = BASE_DIR / "web" / "templates" / "index.html"
        if html_path.exists():
            content = html_path.read_text(encoding='utf-8')
            print_pass(f"HTML文件 - 存在 ({len(content)} 字符)")
        else:
            print_fail("HTML文件 - 缺失")
            return False
        
        css_path = BASE_DIR / "web" / "static" / "css" / "style.css"
        if css_path.exists():
            content = css_path.read_text(encoding='utf-8')
            print_pass(f"CSS文件 - 存在 ({len(content)} 字符)")
        else:
            print_fail("CSS文件 - 缺失")
            return False
        
        js_path = BASE_DIR / "web" / "static" / "js" / "app.js"
        if js_path.exists():
            content = js_path.read_text(encoding='utf-8')
            print_pass(f"JS文件 - 存在 ({len(content)} 字符)")
        else:
            print_fail("JS文件 - 缺失")
            return False
        
        return True
    except Exception as e:
        print_fail(f"前端文件检查失败: {e}")
        traceback.print_exc()
        return False


async def main():
    """主诊断函数"""
    
    results = []
    
    # 运行所有检查
    results.append(("文件结构", check_file_structure()))
    results.append(("模块导入", check_imports()))
    results.append(("数据模型", test_data_models()))
    results.append(("存储系统", test_storage_system()))
    results.append(("RAG引擎", await test_tidycup_rag()))
    results.append(("意图规划器", await test_tidycup_planner()))
    results.append(("NL2SQL引擎", await test_tidycup_nl2sql()))
    results.append(("完整流水线", await test_full_tidycup_pipeline()))
    results.append(("FastAPI应用", test_fastapi_app()))
    results.append(("前端文件", test_frontend_files()))
    
    # 总结
    print_section("诊断结果汇总")
    
    total = len(results)
    passed = sum(1 for _, passed in results if passed)
    failed = total - passed
    
    for name, passed in results:
        status = "✓ 通过" if passed else "✗ 失败"
        print(f"  {name}: {status}")
    
    print(f"\n  总计: {total}")
    print(f"  通过: {passed}")
    print(f"  失败: {failed}")
    
    if failed == 0:
        print("\n  🎉 所有检查通过！系统运行正常！")
        return 0
    else:
        print(f"\n  ⚠️ {failed} 个检查失败，需要修复")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
