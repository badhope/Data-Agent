"""
Office Agent - Main Entry Point
主程序入口
"""

import os
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

from src.core.agent import OfficeAgent
from src.core.config import OfficeAgentConfig
from src.tools import ALL_TOOLS


def create_agent(config: OfficeAgentConfig = None) -> OfficeAgent:
    """
    创建 Office Agent 实例
    
    Args:
        config: Agent 配置，默认使用环境变量配置
    
    Returns:
        OfficeAgent 实例
    """
    # 检查 API Key
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("⚠️ 警告: 未设置 OPENAI_API_KEY 环境变量")
        print("请设置您的 OpenAI API Key:")
        print("  export OPENAI_API_KEY=sk-your-key-here")
    
    # 创建 Agent
    agent = OfficeAgent(
        config=config,
        tools=ALL_TOOLS
    )
    
    return agent


def run_interactive(agent: OfficeAgent):
    """
    运行交互式对话模式
    
    Args:
        agent: OfficeAgent 实例
    """
    print("=" * 60)
    print("🤖 Office Agent - 智能办公助手")
    print("=" * 60)
    print()
    print("我可以帮您：")
    print("  📧 邮件管理 - 发送、回复、搜索邮件")
    print("  📅 日程安排 - 创建会议、查看日程")
    print("  📄 文档处理 - 读取、总结、创建文档")
    print("  ✅ 任务管理 - 创建、追踪、完成待办")
    print()
    print("输入 'exit' 或 'quit' 退出程序")
    print("输入 'clear' 清除对话历史")
    print("=" * 60)
    print()
    
    while True:
        try:
            user_input = input("👤 您: ").strip()
            
            if not user_input:
                continue
            
            if user_input.lower() in ['exit', 'quit', '退出']:
                print("\n👋 再见！祝您工作愉快！")
                break
            
            if user_input.lower() == 'clear':
                agent.clear_memory()
                print("✅ 对话历史已清除\n")
                continue
            
            print("\n🤖 正在处理...")
            response = agent.process(user_input)
            print(f"\n🤖 助手: {response}\n")
            
        except KeyboardInterrupt:
            print("\n\n👋 已退出")
            break
        except Exception as e:
            print(f"\n❌ 发生错误: {str(e)}\n")


def run_demo(agent: OfficeAgent):
    """
    运行演示模式
    
    Args:
        agent: OfficeAgent 实例
    """
    print("=" * 60)
    print("🎬 Office Agent - 演示模式")
    print("=" * 60)
    print()
    
    demo_queries = [
        "查看一下我今天有什么日程安排？",
        "帮我搜索一下关于项目进度的邮件",
        "列出我当前有哪些待完成的任务",
        "帮我查看 documents/project_report.md 这份文档的内容",
        "创建一个任务：准备下周的团队会议材料，截止日期是下周五"
    ]
    
    for i, query in enumerate(demo_queries, 1):
        print(f"\n{'=' * 40}")
        print(f"演示 {i}/{len(demo_queries)}")
        print(f"{'=' * 40}")
        print(f"👤 您: {query}")
        print()
        print("🤖 正在处理...")
        
        try:
            response = agent.process(query)
            print(f"\n🤖 助手:\n{response}")
        except Exception as e:
            print(f"❌ 错误: {str(e)}")
        
        if i < len(demo_queries):
            input("\n按 Enter 继续下一项演示...")


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Office Agent - 智能办公助手")
    parser.add_argument(
        "--mode",
        "-m",
        choices=["interactive", "demo"],
        default="interactive",
        help="运行模式: interactive(交互模式) 或 demo(演示模式)"
    )
    parser.add_argument(
        "--model",
        choices=["gpt-4", "gpt-3.5-turbo", "gpt-4-turbo"],
        default=None,
        help="使用的模型"
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="显示详细日志"
    )
    
    args = parser.parse_args()
    
    # 创建配置
    config = OfficeAgentConfig.from_env()
    if args.model:
        config.llm.model = args.model
    if args.verbose:
        config.agent.verbose = True
    
    # 创建 Agent
    print("🚀 初始化 Office Agent...")
    agent = create_agent(config)
    print("✅ Agent 初始化完成！\n")
    
    # 运行
    if args.mode == "demo":
        run_demo(agent)
    else:
        run_interactive(agent)


if __name__ == "__main__":
    main()
