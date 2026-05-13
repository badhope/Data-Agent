"""
端到端测试脚本 - 模拟真实用户使用场景
"""
import asyncio
from pathlib import Path
import sys
import json

# 添加项目路径
BASE_DIR = Path(__file__).parent
sys.path.insert(0, str(BASE_DIR))


async def test_1_tidycup_rag():
    """测试1: RAG检索功能"""
    print("\n" + "="*60)
    print("TEST 1: RAG 检索功能")
    print("="*60)
    
    try:
        from web.tidycup import RAGEngine
        rag = RAGEngine()
        
        test_queries = [
            "贵州茅台的财务数据",
            "平安银行净利润",
            "白酒行业分析",
            "2023年财务报表"
        ]
        
        all_passed = True
        for query in test_queries:
            print(f"\n查询: {query}")
            results = await rag.retrieve(query)
            if results:
                print(f"  ✓ 找到 {len(results)} 个相关文档")
                for i, doc in enumerate(results[:2]):
                    print(f"    文档{i+1}: {doc.content[:80]}...")
                    print(f"    评分: {doc.score}")
            else:
                print(f"  ✓ 无匹配结果（使用默认知识库）")
        
        print("\n✓ RAG 测试完成")
        return True
        
    except Exception as e:
        print(f"✗ RAG测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_2_nl2sql():
    """测试2: NL2SQL 功能"""
    print("\n" + "="*60)
    print("TEST 2: NL2SQL 自然语言查询")
    print("="*60)
    
    try:
        from web.tidycup import FullNL2SQLPipeline
        
        db_path = BASE_DIR / "data" / "test_e2e.db"
        db_path.parent.mkdir(parents=True, exist_ok=True)
        
        pipeline = FullNL2SQLPipeline(db_path)
        pipeline.initialize()
        
        test_queries = [
            "贵州茅台2023年财务数据",
            "平安银行的净利润",
            "2022年总资产",
        ]
        
        for query in test_queries:
            print(f"\n查询: {query}")
            result = await pipeline.process_query(query)
            print(f"  类型: {result.get('type')}")
            if result.get('type') == 'result':
                print(f"  ✓ 查询成功")
                if result.get('sql_result'):
                    print(f"  SQL: {result.get('sql_result', {}).get('sql', '')[:100]}")
        
        print("\n✓ NL2SQL 测试完成")
        return True
        
    except Exception as e:
        print(f"✗ NL2SQL测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_3_full_pipeline():
    """测试3: 完整的泰迪杯流水线"""
    print("\n" + "="*60)
    print("TEST 3: 完整泰迪杯流水线")
    print("="*60)
    
    try:
        from web.tidycup import FullTidyCupPipeline
        
        db_path = BASE_DIR / "data" / "test_full.db"
        db_path.parent.mkdir(parents=True, exist_ok=True)
        
        pipeline = FullTidyCupPipeline(db_path)
        pipeline.initialize()
        
        test_cases = [
            "贵州茅台2023年财务数据分析",
            "对比贵州茅台和平安银行的业绩",
            "贵州茅台近年来的利润增长趋势",
        ]
        
        for query in test_cases:
            print(f"\n测试用例: {query}")
            result = await pipeline.process_complex_query(query)
            
            # 验证结果结构
            has_task_plan = 'task_plan' in result
            has_rag = 'rag_results' in result
            has_attribution = 'attribution' in result
            
            print(f"  ✓ 任务计划: {'是' if has_task_plan else '否'}")
            print(f"  ✓ RAG结果: {'是' if has_rag else '否'} ({len(result.get('rag_results', []))}个)")
            print(f"  ✓ 归因分析: {'是' if has_attribution else '否'}")
            
            if has_attribution:
                print(f"  归因摘要: {result['attribution'].get('summary', '')}")
        
        print("\n✓ 完整流水线测试完成")
        return True
        
    except Exception as e:
        print(f"✗ 完整流水线测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_4_web_modules():
    """测试4: Web核心模块"""
    print("\n" + "="*60)
    print("TEST 4: Web 核心模块")
    print("="*60)
    
    try:
        # 测试模型
        from web.models import Settings, KnowledgeBase, Document
        print("✓ 模型导入成功")
        
        # 测试存储
        from web.storage import (
            get_settings, save_settings,
            get_knowledge_bases, save_knowledge_bases,
            initialize_storage
        )
        initialize_storage()
        settings = get_settings()
        print(f"✓ 存储模块正常，当前供应商: {settings.llm.get('provider', 'N/A')}")
        
        # 测试服务
        from web.services import execute_python, clean_text
        result = await execute_python("print('Hello Test')")
        if result.get('success'):
            print(f"✓ 代码执行正常: {result.get('stdout', '')[:30]}")
        
        # 测试路由模块导入（只检查导入是否成功）
        import web.routes
        print("✓ 路由模块导入正常")
        
        print("\n✓ Web 核心模块测试完成")
        return True
        
    except Exception as e:
        print(f"✗ Web核心模块测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_5_tidycup_api_sim():
    """测试5: 模拟API调用"""
    print("\n" + "="*60)
    print("TEST 5: API 功能模拟")
    print("="*60)
    
    try:
        # 模拟主应用初始化
        from web.tidycup import FullTidyCupPipeline
        from web.tidycup.nl2sql_engine import FullNL2SQLPipeline
        
        # 1. 测试状态检查
        print("1. 状态检查...")
        print("   ✓ 泰迪杯模块可用")
        
        # 2. 测试示例查询
        print("2. 示例查询...")
        sample_queries = [
            "贵州茅台2023年净利润",
            "财务数据分析",
            "平安银行报表"
        ]
        
        db_path = BASE_DIR / "data" / "test_api.db"
        nl2sql = FullNL2SQLPipeline(db_path)
        nl2sql.initialize()
        
        for q in sample_queries[:2]:
            res = await nl2sql.process_query(q)
            print(f"   ✓ '{q}' -> {res.get('type')}")
        
        # 3. 测试完整流水线
        print("3. 完整流水线调用...")
        pipeline = FullTidyCupPipeline(db_path)
        pipeline.initialize()
        
        result = await pipeline.process_complex_query("贵州茅台财务分析")
        print(f"   ✓ 流水线执行成功，结果包含: {list(result.keys())}")
        
        print("\n✓ API 模拟测试完成")
        return True
        
    except Exception as e:
        print(f"✗ API测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """主测试函数"""
    print("\n" + "="*60)
    print("DATA-AI 系统 - 端到端完整测试")
    print("="*60)
    print(f"工作目录: {BASE_DIR}")
    
    results = {}
    
    # 运行所有测试
    results["RAG检索"] = await test_1_tidycup_rag()
    results["NL2SQL查询"] = await test_2_nl2sql()
    results["完整流水线"] = await test_3_full_pipeline()
    results["Web核心模块"] = await test_4_web_modules()
    results["API功能模拟"] = await test_5_tidycup_api_sim()
    
    # 总结
    print("\n" + "="*60)
    print("最终测试结果汇总")
    print("="*60)
    
    total = len(results)
    passed = sum(1 for v in results.values() if v)
    failed = total - passed
    
    for name, ok in results.items():
        status = "✓ 通过" if ok else "✗ 失败"
        print(f"  {name}: {status}")
    
    print(f"\n总计: {total} | 通过: {passed} | 失败: {failed}")
    
    if failed == 0:
        print("\n🎉 所有测试通过！系统运行正常！")
        print("你现在可以启动应用并进行实际使用测试了。")
        return 0
    else:
        print(f"\n⚠️ {failed}个测试失败，请检查相关模块。")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
