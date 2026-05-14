#!/usr/bin/env python3
"""
实际生成一个完整的PPT文件用于验证
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.document.ppt_generator import PPTGenerator, PPTTemplate


def generate_complete_ppt():
    """生成一个完整的演示文稿"""
    print("=" * 70)
    print("🎯 生成完整PPT文件")
    print("=" * 70)
    
    # 创建PPT生成器
    generator = PPTGenerator()
    
    # 创建演示文稿
    generator.create_presentation("DataAgent 智能助手", "DataAgent")
    
    print(f"\n📄 演示文稿标题: DataAgent 智能助手")
    
    # 标题页
    generator.add_title_slide(
        title="DataAgent - 万能智能助手",
        subtitle="让AI成为你的得力助手"
    )
    print(f"✅ 添加标题页")
    
    # 目录页
    generator.add_content_slide(
        title="目录",
        content=[
            "1. 产品介绍",
            "2. 核心功能",
            "3. 应用场景",
            "4. 技术架构"
        ]
    )
    print(f"✅ 添加目录页")
    
    # 产品介绍页
    generator.add_content_slide(
        title="产品介绍",
        content=[
            "DataAgent 是一个完整的智能助手系统",
            "支持自然语言对话、代码执行、图表生成",
            "集成知识库管理、技能系统、MCP工具",
            "提供完整的文档处理能力"
        ]
    )
    print(f"✅ 添加产品介绍页")
    
    # 核心功能页
    generator.add_content_slide(
        title="核心功能",
        content=[
            "💬 智能对话 - 自然语言理解、上下文记忆、多轮对话",
            "📄 文档处理 - PPT生成、会议纪要、文档摘要",
            "📊 数据分析 - 数据处理、图表生成、统计分析",
            "🎯 项目管理 - 待办跟踪、报告生成、进度监控"
        ]
    )
    print(f"✅ 添加核心功能页")
    
    # 应用场景页
    generator.add_content_slide(
        title="应用场景",
        content=[
            "办公场景：",
            "• 会议纪要生成",
            "• 周报自动编写",
            "• 项目管理协助",
            "",
            "技术场景：",
            "• 代码审查",
            "• 数据分析",
            "• 技术方案设计"
        ]
    )
    print(f"✅ 添加应用场景页")
    
    # 技术架构页
    generator.add_content_slide(
        title="技术架构",
        content=[
            "后端: FastAPI + Python",
            "前端: HTML + JavaScript + CSS",
            "AI: 支持多种大语言模型",
            "数据库: SQLite + 向量存储"
        ]
    )
    print(f"✅ 添加技术架构页")
    
    # 结束页
    generator.add_title_slide(
        title="谢谢观看",
        subtitle="Q&A 时间"
    )
    print(f"✅ 添加结束页")
    
    # 保存到文件
    output_path = os.path.join(os.path.dirname(__file__), "dataagent_demo.pptx")
    generator.save(output_path)
    
    print(f"\n" + "=" * 70)
    print(f"✅ PPT生成成功！")
    print(f"📁 保存位置: {output_path}")
    print(f"📊 文件大小: {os.path.getsize(output_path)} bytes")
    print(f"📄 幻灯片数量: {generator.get_slide_count()}")
    print(f"=" * 70)
    
    return output_path


if __name__ == "__main__":
    try:
        output_path = generate_complete_ppt()
        print(f"\n✅ PPT文件已生成: {output_path}")
    except Exception as e:
        print(f"❌ 生成失败: {e}")
        import traceback
        traceback.print_exc()
