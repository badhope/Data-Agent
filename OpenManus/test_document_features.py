#!/usr/bin/env python3
"""
文档处理功能测试脚本
测试所有文档处理模块
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


async def test_document_features():
    print("=" * 70)
    print("📄 文档处理功能测试")
    print("=" * 70)

    results = {}

    # ========== 1. 测试文档摘要模块 ==========
    print("\n📋 1. 文档摘要测试")
    print("-" * 50)
    try:
        from app.document.summarizer import DocumentSummarizer, StructuredSummaryGenerator
        
        summarizer = DocumentSummarizer()
        test_text = """人工智能是研究、开发用于模拟、延伸和扩展人的智能的理论、方法、技术及应用系统的一门新的技术科学。人工智能领域的研究包括机器人、语言识别、图像识别、自然语言处理和专家系统等。人工智能从诞生以来，理论和技术日益成熟，应用领域也不断扩大，可以设想，未来人工智能带来的科技产品，将会是人类智慧的"容器"。"""
        
        result = await summarizer.summarize(test_text, method="extractive", num_sentences=3)
        print(f"  ✅ 抽取式摘要成功")
        print(f"     原始长度: {result.original_length}")
        print(f"     摘要长度: {result.summary_length}")
        print(f"     关键词: {', '.join(result.keywords[:5])}")
        
        struct_generator = StructuredSummaryGenerator()
        struct_result = struct_generator.generate(test_text, "general")
        print(f"  ✅ 结构化摘要成功")
        results["文档摘要"] = True
    except Exception as e:
        print(f"  ❌ 文档摘要失败: {e}")
        results["文档摘要"] = False

    # ========== 2. 测试会议纪要模块 ==========
    print("\n📋 2. 会议纪要测试")
    print("-" * 50)
    try:
        from app.document.meeting_minutes import MeetingMinutesGenerator, generate_meeting_minutes
        
        meeting_text = """会议主题：项目进度评审
日期：2024年1月15日
主持人：张三
参会人员：李四、王五、赵六

议程：
1. 项目进度汇报
2. 问题讨论
3. 下周工作计划

讨论要点：
张三说：目前项目整体进度正常，完成了80%。
李四提出：数据库性能需要优化。
王五表示：前端界面需要调整。

决策：
1. 同意增加数据库索引优化方案
2. 批准前端界面调整计划

待办事项：
- 李四负责数据库优化，截止日期1月20日
- 王五负责界面调整，截止日期1月22日"""
        
        minutes = generate_meeting_minutes(meeting_text, output_format="markdown")
        print(f"  ✅ 会议纪要生成成功")
        lines = minutes.split('\n')[:10]
        print(f"     生成内容（前10行）:")
        for line in lines:
            print(f"     {line}")
        results["会议纪要"] = True
    except Exception as e:
        print(f"  ❌ 会议纪要失败: {e}")
        results["会议纪要"] = False

    # ========== 3. 测试待办提取模块 ==========
    print("\n📋 3. 待办提取测试")
    print("-" * 50)
    try:
        from app.document.todo_extractor import TodoExtractor, extract_todos
        
        test_text = """今日待办：
1. 完成文档编写（紧急）
2. 发送邮件给客户
3. 张三负责项目报告，截止日期下周五
4. 准备会议材料"""
        
        todos = extract_todos(test_text)
        print(f"  ✅ 待办提取成功")
        print(f"     提取到 {len(todos)} 个待办事项")
        for todo in todos[:3]:
            print(f"     - {todo['task']}")
        results["待办提取"] = True
    except Exception as e:
        print(f"  ❌ 待办提取失败: {e}")
        results["待办提取"] = False

    # ========== 4. 测试文本格式化模块 ==========
    print("\n📋 4. 文本格式化测试")
    print("-" * 50)
    try:
        from app.document.formatter import format_chinese_text, format_document
        
        test_text = "这是一段测试文本包含中文和English混合内容数字123需要格式化。"
        result = format_document(test_text, "strict")
        print(f"  ✅ 文本格式化成功")
        print(f"     原文本: {test_text}")
        print(f"     格式化后: {result['formatted']}")
        print(f"     修改内容: {result['changes']}")
        results["文本格式化"] = True
    except Exception as e:
        print(f"  ❌ 文本格式化失败: {e}")
        results["文本格式化"] = False

    # ========== 5. 测试PPT生成模块 ==========
    print("\n📋 5. PPT生成测试")
    print("-" * 50)
    try:
        from app.document.ppt_generator import PPTGenerator, PPTTemplate
        
        generator = PPTGenerator()
        generator.create_presentation("测试演示", "DataAgent")
        generator.add_title_slide("测试演示文稿", "副标题")
        generator.add_content_slide("目录", ["第一部分", "第二部分", "第三部分"])
        ppt_bytes = generator.get_bytes()
        print(f"  ✅ PPT生成成功")
        print(f"     文件大小: {len(ppt_bytes)} bytes")
        
        templates = PPTTemplate.list_templates()
        print(f"  ✅ PPT模板列表获取成功")
        print(f"     可用模板: {', '.join(t['id'] for t in templates)}")
        results["PPT生成"] = True
    except Exception as e:
        print(f"  ❌ PPT生成失败: {e}")
        results["PPT生成"] = False

    # ========== 6. 测试报告生成模块 ==========
    print("\n📋 6. 报告生成测试")
    print("-" * 50)
    try:
        from app.document.report_generator import ReportGenerator, generate_weekly_report
        
        work_items = [
            {"title": "完成项目需求文档", "description": "编写详细的需求规格说明", "status": "completed", "hours_spent": 8},
            {"title": "代码审查", "description": "审查团队提交的代码", "status": "completed", "hours_spent": 4},
            {"title": "技术方案设计", "description": "设计系统架构方案", "status": "in_progress", "hours_spent": 6},
        ]
        
        report = generate_weekly_report(work_items, "测试用户")
        print(f"  ✅ 周报生成成功")
        lines = report.split('\n')[:8]
        print(f"     报告内容（前8行）:")
        for line in lines:
            print(f"     {line}")
        results["报告生成"] = True
    except Exception as e:
        print(f"  ❌ 报告生成失败: {e}")
        results["报告生成"] = False

    # ========== 7. 测试引用管理模块 ==========
    print("\n📋 7. 引用管理测试")
    print("-" * 50)
    try:
        from app.document.citation_manager import CitationManager, format_citation
        
        test_citation = "Smith, J. (2020). Artificial Intelligence. Journal of AI, 15(2), 45-67."
        formatted = format_citation(test_citation, "gbt")
        print(f"  ✅ 引用格式化成功 (GB/T 7714格式)")
        print(f"     格式化结果: {formatted[:100]}...")
        
        manager = CitationManager()
        manager.add_from_text(test_citation)
        apa_format = manager.format_bibliography("apa")
        print(f"  ✅ APA格式引用成功")
        results["引用管理"] = True
    except Exception as e:
        print(f"  ❌ 引用管理失败: {e}")
        results["引用管理"] = False

    # ========== 8. 测试PDF解析模块 ==========
    print("\n📋 8. PDF解析测试")
    print("-" * 50)
    try:
        from app.document.pdf_parser import PDFParser, parse_pdf_bytes
        
        sample_pdf = b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n2 0 obj\n<<\n/Type /Pages\n/Kids [3 0 R]\n/Count 1\n>>\nendobj\n3 0 obj\n<<\n/Type /Page\n/Parent 2 0 R\n/MediaBox [0 0 612 792]\n>>\nendobj\nxref\n0 4\n0000000000 65535 f \n0000000009 00000 n \n0000000058 00000 n \n0000000115 00000 n \ntrailer\n<<\n/Size 4\n/Root 1 0 R\n>>\nstartxref\n199\n%%EOF"
        
        content = parse_pdf_bytes(sample_pdf)
        print(f"  ✅ PDF解析成功")
        print(f"     页数: {content.get('page_count', 0)}")
        print(f"     元数据: {content.get('metadata', {})}")
        results["PDF解析"] = True
    except Exception as e:
        print(f"  ❌ PDF解析失败: {e}")
        results["PDF解析"] = False

    # ========== 9. 测试提纲生成模块 ==========
    print("\n📋 9. 提纲生成测试")
    print("-" * 50)
    try:
        from app.document.outline_generator import OutlineGenerator, generate_outline, generate_outline_markdown
        
        outline = generate_outline("人工智能发展趋势", "general", 3)
        print(f"  ✅ 提纲生成成功")
        print(f"     标题: {outline['title']}")
        print(f"     节数: {outline['sections']}")
        print(f"     预计字数: {outline['word_count_estimate']}字")
        
        md_outline = generate_outline_markdown("机器学习入门", "academic", 2)
        lines = md_outline.split('\n')[:6]
        print(f"  ✅ Markdown提纲生成成功")
        for line in lines:
            print(f"     {line}")
        results["提纲生成"] = True
    except Exception as e:
        print(f"  ❌ 提纲生成失败: {e}")
        results["提纲生成"] = False

    # ========== 10. 测试文档服务整合 ==========
    print("\n📋 10. 文档服务整合测试")
    print("-" * 50)
    try:
        from app.services.document_service import DocumentService
        
        doc_service = DocumentService()
        
        summary = await doc_service.summarize_document("这是一段测试文本用于测试文档服务。")
        print(f"  ✅ 文档服务摘要功能正常")
        
        outline = await doc_service.generate_outline("测试主题")
        print(f"  ✅ 文档服务提纲功能正常")
        
        todos = await doc_service.extract_todos("待办：完成测试")
        print(f"  ✅ 文档服务待办提取功能正常")
        
        results["文档服务"] = True
    except Exception as e:
        print(f"  ❌ 文档服务失败: {e}")
        results["文档服务"] = False

    # ========== 总结 ==========
    print("\n" + "=" * 70)
    print("📊 测试总结")
    print("=" * 70)

    total = len(results)
    passed = sum(1 for v in results.values() if v)
    failed = total - passed

    for name, result in results.items():
        status = "✅ 通过" if result else "❌ 失败"
        print(f"  {name:15s}: {status}")

    print(f"\n  总计: {passed}/{total} 通过, {failed} 失败")
    print("=" * 70)

    return failed == 0


if __name__ == "__main__":
    success = asyncio.run(test_document_features())
    sys.exit(0 if success else 1)