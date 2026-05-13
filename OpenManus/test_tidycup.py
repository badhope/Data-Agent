"""
泰迪杯B题功能测试脚本
测试所有功能模块
"""
import asyncio
from pathlib import Path
import sys

# 添加项目路径
BASE_DIR = Path(__file__).parent
sys.path.insert(0, str(BASE_DIR))

from web.tidycup import (
    FullTidyCupPipeline,
    RAGEngine,
    MultiIntentPlanner,
    AttributionAnalyzer,
    FullNL2SQLPipeline
)


async def test_rag_engine():
    """测试RAG引擎"""
    print("\n=== 测试RAG引擎...")
    try:
        rag = RAGEngine()
        results = await rag.retrieve("贵州茅台 2023")
        print(f"  ✓ RAG检索成功，找到 {len(results)} 个相关文档")
        for i, chunk in enumerate(results, 1):
            print(f"  文档{i}: {chunk.content[:50]}...")
        print("  ✓ RAG引擎测试通过")
        return True
    except Exception as e:
        print(f"  ✗ RAG引擎测试失败: {e}")
        return False


async def test_intent_planner():
    """测试意图规划器"""
    print("\n=== 测试意图规划器...")
    try:
        planner = MultiIntentPlanner()
        
        test_queries = [
            "贵州茅台2023年营收",
            "对比贵州茅台和平安银行的业绩",
            "贵州茅台的收入增长趋势"
        ]
        
        for query in test_queries:
            plan = planner.plan(query)
            print(f"  ✓ 查询: {query}")
            print(f"  ✓ 任务数量: {len(plan.sub_tasks)}")
        
        print("  ✓ 意图规划器测试通过")
        return True
    except Exception as e:
        print(f"  ✗ 意图规划器测试失败: {e}")
        return False


async def test_nl2sql():
    """测试NL2SQL引擎"""
    print("\n=== 测试NL2SQL引擎...")
    try:
        db_path = BASE_DIR / "data" / "test_tidycup.db"
        db_path.parent.mkdir(parents=True, exist_ok=True)
        
        pipeline = FullNL2SQLPipeline(db_path)
        pipeline.initialize()
        
        # 测试意图分析
        result = await pipeline.process_query("贵州茅台2023年")
        print(f"  ✓ NL2SQL处理完成: {result.get('type', 'unknown')}")
        print("  ✓ NL2SQL引擎测试通过")
        return True
    except Exception as e:
        print(f"  ✗ NL2SQL引擎测试失败: {e}")
        import traceback
        print(traceback.format_exc())
        return False


async def test_full_pipeline():
    """测试完整流水线"""
    print("\n=== 测试完整流水线...")
    try:
        db_path = BASE_DIR / "data" / "test_tidycup.db"
        db_path.parent.mkdir(parents=True, exist_ok=True)
        
        pipeline = FullTidyCupPipeline(db_path)
        pipeline.initialize()
        
        # 测试查询
        result = await pipeline.process_complex_query("贵州茅台2023年财务数据")
        
        print(f"  ✓ 完整查询处理成功")
        print(f"  ✓ 任务计划包含 {len(result['task_plan']['sub_tasks'])} 个子任务")
        print(f"  ✓ RAG检索到 {len(result['rag_results'])} 个文档")
        print("  ✓ 完整流水线测试通过")
        return True
    except Exception as e:
        print(f"  ✗ 完整流水线测试失败: {e}")
        import traceback
        print(traceback.format_exc())
        return False


async def main():
    """主测试函数"""
    print("="*50)
    print("泰迪杯B题功能测试")
    print("="*50)
    
    results = []
    
    results.append(("RAG引擎", await test_rag_engine()))
    results.append(("意图规划器", await test_intent_planner()))
    results.append(("NL2SQL引擎", await test_nl2sql()))
    results.append(("完整流水线", await test_full_pipeline()))
    
    print("\n" + "="*50)
    print("测试结果汇总")
    print("="*50)
    for name, passed in results:
        status = "✓ 通过" if passed else "✗ 失败"
        print(f"{name}: {status}")
    
    passed_count = sum(1 for _, p in results if p)
    print(f"\n总测试数: {len(results)}")
    print(f"通过数: {passed_count}")
    print(f"失败数: {len(results) - passed_count}")


if __name__ == "__main__":
    asyncio.run(main())
