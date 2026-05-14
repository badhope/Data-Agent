#!/usr/bin/env python
"""
全面测试脚本 - 模拟人类各种操作和边界情况
测试覆盖：意图识别、工具调用、参数提取、错误恢复、性能监控
"""
import sys
import asyncio
import random
import time
from typing import Dict, Any, List
from datetime import datetime

# 当前目录就是 langchain_office_assistant 包
sys.path.insert(0, '/workspace')

from langchain_office_assistant.agents import (
    OfficeAgent,
    run_office_assistant,
    IntentRecognizer,
    IntentType,
    SmartParamExtractor,
    ConfidenceHandler,
    LLMOutputValidator,
    get_cache_manager,
    get_performance_monitor,
    get_concurrency_limiter,
)

from langchain_office_assistant.utils.config import config

print("=" * 70)
print("🚀 全面API测试套件")
print("=" * 70)

# 测试用例集合
TEST_CASES = [
    # 正常测试用例
    {"name": "简单计算", "input": "计算 123 + 456", "expected_intent": "calc"},
    {"name": "货币转换", "input": "把100美元换成人民币", "expected_intent": "calc"},
    {"name": "统计分析", "input": "分析数据 [1, 2, 3, 4, 5] 的平均值", "expected_intent": "calc"},
    {"name": "创建任务", "input": "创建一个任务：完成项目报告，优先级高", "expected_intent": "task"},
    {"name": "搜索知识库", "input": "在知识库中搜索机器学习相关内容", "expected_intent": "knowledge"},
    {"name": "创建图表", "input": "生成一个柱状图，数据是[10, 20, 30, 40]", "expected_intent": "chart"},
    {"name": "发送邮件", "input": "发送邮件给张三，主题是会议通知，内容是明天下午开会", "expected_intent": "email"},
    {"name": "查询日程", "input": "查看明天的日程安排", "expected_intent": "calendar"},
    
    # 边界测试用例
    {"name": "空输入", "input": "", "expected_intent": "chat"},
    {"name": "超长输入", "input": "你" * 500, "expected_intent": "chat"},
    {"name": "特殊字符", "input": "!@#$%^&*()_+-=[]{}|;':\",./<>?", "expected_intent": "chat"},
    {"name": "纯数字", "input": "1234567890", "expected_intent": "calc"},
    {"name": "纯英文", "input": "Hello world, how are you?", "expected_intent": "chat"},
    {"name": "中英文混合", "input": "Please calculate 10 + 20 in Chinese", "expected_intent": "calc"},
    
    # 错误恢复测试
    {"name": "格式错误的邮件", "input": "发送邮件给 invalid-email", "expected_intent": "email"},
    {"name": "不存在的工具", "input": "打开浏览器搜索", "expected_intent": "chat"},
    {"name": "矛盾的指令", "input": "计算 abc + def", "expected_intent": "calc"},
    {"name": "模糊的请求", "input": "做点什么", "expected_intent": "chat"},
    
    # 多轮对话测试
    {"name": "多轮上下文1", "input": "计算 2 + 2", "expected_intent": "calc"},
    {"name": "多轮上下文2", "input": "再加上3", "expected_intent": "calc"},
    {"name": "多轮上下文3", "input": "结果乘以4", "expected_intent": "calc"},
]

async def run_test_cases():
    """运行所有测试用例"""
    results = []
    session_id = f"test-session-{int(time.time())}"
    
    for i, test_case in enumerate(TEST_CASES, 1):
        print(f"\n--- 测试用例 {i}/{len(TEST_CASES)}: {test_case['name']} ---")
        print(f"输入: {test_case['input'][:50]}..." if len(test_case['input']) > 50 else f"输入: {test_case['input']}")
        
        try:
            start_time = time.time()
            result = await run_office_assistant(
                user_input=test_case['input'],
                session_id=session_id,
                config={
                    "agent_model": config.agent_model,
                    "openai_api_key": config.openai_api_key,
                    "openai_api_base": config.openai_api_base
                }
            )
            duration = (time.time() - start_time) * 1000
            
            print(f"意图: {result['intent']} (预期: {test_case['expected_intent']})")
            print(f"置信度: {result['confidence']:.2%}")
            print(f"工具: {result['tool_used']}")
            print(f"耗时: {duration:.2f}ms")
            print(f"响应: {result['response'][:100]}...")
            
            # 验证意图识别
            intent_match = result['intent'] == test_case['expected_intent']
            confidence_ok = result['confidence'] >= 0.5
            
            results.append({
                "name": test_case['name'],
                "input": test_case['input'],
                "intent": result['intent'],
                "expected_intent": test_case['expected_intent'],
                "confidence": result['confidence'],
                "duration_ms": duration,
                "success": intent_match and confidence_ok,
                "trace_id": result['trace_id']
            })
            
        except Exception as e:
            print(f"❌ 测试失败: {e}")
            results.append({
                "name": test_case['name'],
                "input": test_case['input'],
                "success": False,
                "error": str(e)
            })
    
    return results

async def test_param_extractor():
    """测试智能参数提取器"""
    print("\n" + "=" * 70)
    print("🧪 测试智能参数提取器")
    print("=" * 70)
    
    extractor = SmartParamExtractor(
        model_name=config.agent_model,
        api_key=config.openai_api_key,
        api_base=config.openai_api_base
    )
    
    test_inputs = [
        "发送邮件给 zhangsan@company.com，主题是会议通知",
        "创建一个柱状图，数据是销售数据：一月100，二月200，三月300",
        "计算 100 USD 转换为 CNY",
        "安排明天下午2点的会议，时长1小时",
        "搜索机器学习入门教程"
    ]
    
    results = []
    for input_text in test_inputs:
        print(f"\n输入: {input_text}")
        result = extractor.extract(input_text, "unknown")
        print(f"工具: {result.tool_name}")
        print(f"参数: {result.params}")
        print(f"置信度: {result.confidence:.2%}")
        print(f"推理: {result.reasoning[:50]}...")
        
        results.append({
            "input": input_text,
            "tool_name": result.tool_name,
            "confidence": result.confidence,
            "has_params": len(result.params) > 0
        })
    
    return results

async def test_confidence_handling():
    """测试置信度处理"""
    print("\n" + "=" * 70)
    print("🧪 测试置信度处理")
    print("=" * 70)
    
    test_cases = [0.95, 0.75, 0.55, 0.35, 0.15]
    
    for confidence in test_cases:
        level = ConfidenceHandler.get_level(confidence)
        should_confirm = ConfidenceHandler.should_confirm(confidence)
        should_retry = ConfidenceHandler.should_retry(confidence)
        message = ConfidenceHandler.format_confidence_message(confidence, "test_tool")
        
        print(f"\n置信度: {confidence:.2%}")
        print(f"级别: {level.value}")
        print(f"需要确认: {should_confirm}")
        print(f"需要重试: {should_retry}")
        print(f"提示消息: {'(无)' if not message else message}")

async def test_validation():
    """测试参数验证"""
    print("\n" + "=" * 70)
    print("🧪 测试参数验证")
    print("=" * 70)
    
    test_params = [
        ("calculate", {"expression": "2+2"}, True),
        ("calculate", {"expression": ""}, False),
        ("currency_convert", {"amount": 100, "from_currency": "USD", "to_currency": "CNY"}, True),
        ("currency_convert", {"amount": -100, "from_currency": "USD", "to_currency": "CNY"}, False),
        ("currency_convert", {"amount": 100, "from_currency": "INVALID", "to_currency": "CNY"}, False),
        ("create_bar_chart", {"labels": ["A", "B"], "values": [10, 20]}, True),
        ("create_bar_chart", {"labels": ["A"], "values": [10]}, False),
    ]
    
    for tool_name, params, should_be_valid in test_params:
        result = LLMOutputValidator.validate(tool_name, params)
        status = "✅" if result.is_valid == should_be_valid else "❌"
        print(f"\n{status} {tool_name}")
        print(f"参数: {params}")
        print(f"验证结果: {result.is_valid} (预期: {should_be_valid})")
        if result.errors:
            print(f"错误: {result.errors}")
        if result.warnings:
            print(f"警告: {result.warnings}")

async def test_performance():
    """测试性能监控"""
    print("\n" + "=" * 70)
    print("🧪 测试性能监控")
    print("=" * 70)
    
    monitor = get_performance_monitor()
    
    # 模拟一些请求
    for i in range(5):
        duration = random.uniform(50, 200)
        success = random.choice([True, True, True, False])
        monitor.record_request("test_component", success, duration)
        time.sleep(0.1)
    
    metrics = monitor.get_metrics("test_component")
    health = monitor.get_health_status()
    
    print(f"健康状态: {health}")
    print(f"总请求数: {metrics['total_requests']}")
    print(f"成功率: {metrics['success_rate']}")
    print(f"平均耗时: {metrics['avg_duration_ms']}ms")
    print(f"最大耗时: {metrics['max_duration_ms']}ms")
    print(f"最小耗时: {metrics['min_duration_ms']}ms")

async def test_cache():
    """测试缓存机制"""
    print("\n" + "=" * 70)
    print("🧪 测试缓存机制")
    print("=" * 70)
    
    cache_manager = get_cache_manager()
    cache = cache_manager.get_cache("test")
    
    # 测试缓存基本操作
    cache.set("key1", "value1", ttl=60)
    cache.set("key2", "value2", ttl=1)
    
    value1 = cache.get("key1")
    value2 = cache.get("key2")
    
    print(f"缓存key1: {'命中' if value1 == 'value1' else '未命中'}")
    print(f"缓存key2: {'命中' if value2 == 'value2' else '未命中'}")
    
    # 测试过期
    time.sleep(2)
    value2_expired = cache.get("key2")
    print(f"缓存key2过期后: {'命中' if value2_expired else '已过期'}")
    
    stats = cache.get_stats()
    print(f"缓存统计: {stats}")

async def main():
    """主测试函数"""
    print("\n📋 测试开始时间:", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    print("=" * 70)
    
    # 运行所有测试
    await test_param_extractor()
    await test_confidence_handling()
    await test_validation()
    await test_cache()
    await test_performance()
    
    # 运行API调用测试
    results = await run_test_cases()
    
    # 生成测试报告
    print("\n" + "=" * 70)
    print("📊 测试报告")
    print("=" * 70)
    
    passed = sum(1 for r in results if r.get("success"))
    total = len(results)
    pass_rate = (passed / total) * 100
    
    print(f"通过: {passed}/{total}")
    print(f"通过率: {pass_rate:.1f}%")
    
    if pass_rate >= 90:
        print("🎉 测试通过!")
    else:
        print("⚠️ 需要修复部分测试用例")
        
        print("\n失败的测试用例:")
        for r in results:
            if not r.get("success"):
                print(f"  ❌ {r['name']}: {r.get('error', '意图识别失败')}")
    
    print("\n📋 测试结束时间:", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

if __name__ == "__main__":
    asyncio.run(main())
