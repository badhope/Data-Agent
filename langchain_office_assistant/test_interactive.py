#!/usr/bin/env python3
"""
Office Agent 交互式对话测试
"""
import asyncio
import sys
import os

sys.path.insert(0, '/workspace/langchain_office_assistant')
os.chdir('/workspace/langchain_office_assistant')

from langchain_office_assistant.agents import create_office_agent

def print_banner():
    print("\n" + "="*70)
    print(" 🤖 Office Agent 交互式对话测试")
    print("="*70)
    print("\n📝 输入命令：")
    print("   - 输入问题直接对话")
    print("   - 'help' 查看帮助")
    print("   - 'clear' 清屏")
    print("   - 'exit' 退出")
    print("="*70 + "\n")

async def interactive_chat():
    print_banner()

    print("🔄 初始化智能体...")
    try:
        agent = create_office_agent()
        print(f"✅ 智能体就绪 - 模型: {agent.model_name}\n")
    except Exception as e:
        print(f"❌ 智能体初始化失败: {e}")
        return

    session_id = None

    while True:
        try:
            user_input = input("\n👤 你: ").strip()

            if not user_input:
                continue

            if user_input.lower() in ['exit', 'quit', '退出']:
                print("\n👋 再见！")
                break

            if user_input.lower() == 'help':
                print("\n📖 帮助信息:")
                print("   - 输入任何问题与我对话")
                print("   - 我可以帮你：")
                print("     • 发送和搜索邮件")
                print("     • 管理日历和会议")
                print("     • 创建和跟踪任务")
                print("     • 创建图表（柱状图、折线图等）")
                print("     • 进行各种计算")
                print("     • 搜索知识库")
                print("     • 读取和写入文档")
                print("     • 创建PPT演示文稿")
                print("\n   示例命令:")
                print("     '计算 100 + 200'")
                print("     '100美元等于多少人民币'")
                print("     '搜索项目相关的邮件'")
                print("     '创建一个任务标题是完成报告'")
                print("     '创建一个柱状图显示销售数据'")
                continue

            if user_input.lower() == 'clear':
                print("\n" * 50)
                print_banner()
                continue

            print("\n🔄 处理中...", end="", flush=True)

            result = await agent.run(user_input, session_id)

            if not session_id:
                session_id = result["session_id"]

            print(f"\r⏱️  耗时: {result['duration_ms']}ms | 意图: {result['intent']}\n")

            print("🤖 助手:")
            print("-" * 70)
            print(result["response"])
            print("-" * 70)

            print(f"\n📋 详情: Trace ID: {result['trace_id']}")

        except KeyboardInterrupt:
            print("\n\n👋 再见！")
            break
        except Exception as e:
            print(f"\n❌ 处理出错: {e}")

if __name__ == "__main__":
    asyncio.run(interactive_chat())
