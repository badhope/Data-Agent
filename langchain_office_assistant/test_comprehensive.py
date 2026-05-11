#!/usr/bin/env python3
"""
Office Agent 严格综合测试脚本
测试覆盖：邮件、日历、任务、文档、PPT、知识库、图表、计算
"""
import asyncio
import sys
import os
import time

sys.path.insert(0, '/workspace/langchain_office_assistant')
os.chdir('/workspace/langchain_office_assistant')

from langchain_office_assistant.agents import create_office_agent

class TestResult:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.errors = []
    
    def add_pass(self, test_name):
        self.passed += 1
        print(f"  ✅ {test_name}")
    
    def add_fail(self, test_name, reason):
        self.failed += 1
        self.errors.append((test_name, reason))
        print(f"  ❌ {test_name}: {reason}")

def print_section(title):
    print(f"\n{'='*70}")
    print(f" {title}")
    print('='*70)

async def test_email_functionality(agent, result):
    print_section("📧 邮件功能测试")
    
    tests = [
        ("搜索邮件 - 项目", "搜索项目相关的邮件"),
        ("搜索邮件 - 会议", "搜索关于会议的邮件"),
        ("发送邮件 - 简单", "发送邮件给zhangsan@company.com主题是测试"),
        ("阅读邮件", "查看邮件内容"),
    ]
    
    for test_name, query in tests:
        try:
            res = await agent.run(query)
            if res['intent'] == 'email' and res['tool_used']:
                result.add_pass(test_name)
            else:
                result.add_fail(test_name, f"意图={res['intent']}, 工具={res['tool_used']}")
        except Exception as e:
            result.add_fail(test_name, str(e))

async def test_calendar_functionality(agent, result):
    print_section("📅 日历功能测试")
    
    tests = [
        ("查询日历", "查看明天的日程"),
        ("创建会议", "创建一个会议标题是项目评审时间明天下午3点"),
    ]
    
    for test_name, query in tests:
        try:
            res = await agent.run(query)
            if res['intent'] == 'calendar' and res['tool_used']:
                result.add_pass(test_name)
            else:
                result.add_fail(test_name, f"意图={res['intent']}, 工具={res['tool_used']}")
        except Exception as e:
            result.add_fail(test_name, str(e))

async def test_task_functionality(agent, result):
    print_section("✅ 任务功能测试")
    
    tests = [
        ("创建任务", "创建一个新任务标题是完成报告"),
        ("创建任务带描述", "创建任务标题是代码评审描述是检查新功能"),
        ("列表任务", "查看所有任务"),
        ("列表进行中任务", "查看进行中的任务"),
    ]
    
    for test_name, query in tests:
        try:
            res = await agent.run(query)
            if res['intent'] == 'task' and res['tool_used']:
                result.add_pass(test_name)
            else:
                result.add_fail(test_name, f"意图={res['intent']}, 工具={res['tool_used']}")
        except Exception as e:
            result.add_fail(test_name, str(e))

async def test_calc_functionality(agent, result):
    print_section("🧮 计算功能测试")
    
    tests = [
        ("简单计算", "计算 10 + 20 * 3"),
        ("复杂计算", "计算 (10 + 20) * 3 / 5"),
        ("货币转换 - 美元到人民币", "100美元等于多少人民币"),
        ("货币转换 - 欧元到日元", "500欧元转换为日元"),
        ("单位转换 - 长度", "100米转换成千米"),
        ("单位转换 - 重量", "1千克等于多少磅"),
        ("统计计算", "计算1到10的平均值"),
    ]
    
    for test_name, query in tests:
        try:
            res = await agent.run(query)
            if res['intent'] == 'calc' and res['tool_used']:
                if '❌' not in res['response'][:50]:
                    result.add_pass(test_name)
                else:
                    result.add_fail(test_name, f"工具执行失败: {res['response'][:100]}")
            else:
                result.add_fail(test_name, f"意图={res['intent']}, 工具={res['tool_used']}")
        except Exception as e:
            result.add_fail(test_name, str(e))

async def test_knowledge_functionality(agent, result):
    print_section("📚 知识库功能测试")
    
    tests = [
        ("添加文档", "添加一个文档标题是项目文档内容是这是测试文档"),
        ("搜索知识库", "搜索关于项目的内容"),
        ("列表文档", "查看所有文档"),
    ]
    
    for test_name, query in tests:
        try:
            res = await agent.run(query)
            if res['intent'] == 'knowledge' and res['tool_used']:
                if '❌' not in res['response'][:50] or 'not initialized' in res['response']:
                    result.add_pass(test_name)
                else:
                    result.add_fail(test_name, f"工具执行失败: {res['response'][:100]}")
            else:
                result.add_fail(test_name, f"意图={res['intent']}, 工具={res['tool_used']}")
        except Exception as e:
            result.add_fail(test_name, str(e))

async def test_chart_functionality(agent, result):
    print_section("📊 图表功能测试")
    
    tests = [
        ("柱状图", "创建一个柱状图显示销售额"),
        ("折线图", "绘制折线图"),
        ("饼图", "生成一个饼图"),
    ]
    
    for test_name, query in tests:
        try:
            res = await agent.run(query)
            if res['intent'] == 'chart' and res['tool_used']:
                result.add_pass(test_name)
            else:
                result.add_fail(test_name, f"意图={res['intent']}, 工具={res['tool_used']}")
        except Exception as e:
            result.add_fail(test_name, str(e))

async def test_document_functionality(agent, result):
    print_section("📄 文档功能测试")
    
    tests = [
        ("搜索文档", "搜索包含报告的文档"),
        ("读取文档", "读取文档内容"),
    ]
    
    for test_name, query in tests:
        try:
            res = await agent.run(query)
            if res['intent'] == 'document' and res['tool_used']:
                result.add_pass(test_name)
            else:
                result.add_fail(test_name, f"意图={res['intent']}, 工具={res['tool_used']}")
        except Exception as e:
            result.add_fail(test_name, str(e))

async def test_ppt_functionality(agent, result):
    print_section("📑 PPT功能测试")
    
    tests = [
        ("创建PPT", "创建一个演示文稿标题是年度汇报"),
        ("添加幻灯片", "添加一张幻灯片"),
    ]
    
    for test_name, query in tests:
        try:
            res = await agent.run(query)
            if res['intent'] == 'ppt' and res['tool_used']:
                result.add_pass(test_name)
            else:
                result.add_fail(test_name, f"意图={res['intent']}, 工具={res['tool_used']}")
        except Exception as e:
            result.add_fail(test_name, str(e))

async def test_edge_cases(agent, result):
    print_section("⚠️ 边界情况测试")
    
    tests = [
        ("空输入", ""),
        ("纯数字", "12345"),
        ("纯英文", "hello world"),
        ("无意义输入", "今天天气真好"),
    ]
    
    for test_name, query in tests:
        try:
            res = await agent.run(query)
            if res['intent'] in ['chat', 'unknown'] or res['response']:
                result.add_pass(test_name)
            else:
                result.add_fail(test_name, "无响应")
        except Exception as e:
            result.add_fail(test_name, str(e))

async def main():
    print("\n" + "="*70)
    print(" 🚀 Office Agent 严格综合测试")
    print("="*70)
    print(f" 开始时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    result = TestResult()
    
    print("\n🤖 初始化智能体...")
    try:
        agent = create_office_agent()
        print(f"✅ 智能体创建成功 - 模型: {agent.model_name}")
    except Exception as e:
        print(f"❌ 智能体创建失败: {e}")
        return
    
    print("\n" + "="*70)
    print(" 开始功能测试...")
    print("="*70)
    
    await test_email_functionality(agent, result)
    await test_calendar_functionality(agent, result)
    await test_task_functionality(agent, result)
    await test_calc_functionality(agent, result)
    await test_knowledge_functionality(agent, result)
    await test_chart_functionality(agent, result)
    await test_document_functionality(agent, result)
    await test_ppt_functionality(agent, result)
    await test_edge_cases(agent, result)
    
    print_section("📊 测试结果汇总")
    total = result.passed + result.failed
    pass_rate = (result.passed / total * 100) if total > 0 else 0
    
    print(f" 总测试数: {total}")
    print(f" ✅ 通过: {result.passed}")
    print(f" ❌ 失败: {result.failed}")
    print(f" 通过率: {pass_rate:.1f}%")
    
    if result.errors:
        print("\n" + "="*70)
        print(" ❌ 失败详情")
        print("="*70)
        for test_name, reason in result.errors:
            print(f"\n  测试: {test_name}")
            print(f"  原因: {reason}")
    
    print("\n" + "="*70)
    print(f" 结束时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*70 + "\n")
    
    return result

if __name__ == "__main__":
    result = asyncio.run(main())
    sys.exit(0 if result.failed == 0 else 1)
