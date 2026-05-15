"""测试PPT生成功能"""
import sys
import os
sys.path.insert(0, '.')

def test_pptx_import():
    """测试python-pptx导入"""
    print('测试 python-pptx 导入...')
    try:
        from pptx import Presentation
        from pptx.util import Inches, Pt
        from pptx.enum.text import PP_ALIGN
        print('✓ python-pptx 导入成功')
        return True
    except ImportError as e:
        print(f'✗ python-pptx 导入失败: {e}')
        print('  请运行: pip install python-pptx')
        return False

def test_ppt_generator():
    """测试PPT生成器"""
    print('\n测试 PPTGenerator 类...')
    
    from app.document.ppt_generator import PPTGenerator, PPTTemplate
    
    # 创建生成器
    generator = PPTGenerator()
    print('✓ PPTGenerator 初始化成功')
    
    # 创建演示文稿
    generator.create_presentation(title="测试演示文稿", author="测试用户")
    print('✓ 创建演示文稿成功')
    
    # 添加标题页
    generator.add_title_slide("测试标题", "副标题内容")
    print('✓ 添加标题页成功')
    
    # 添加内容页
    generator.add_content_slide("目录", ["第一部分", "第二部分", "第三部分"])
    print('✓ 添加内容页成功')
    
    # 添加双栏页
    generator.add_two_column_slide("对比分析", ["左侧内容A", "左侧内容B"], ["右侧内容A", "右侧内容B"])
    print('✓ 添加双栏页成功')
    
    # 添加图表页
    data = [["产品", "销量"], ["A产品", 100], ["B产品", 150], ["C产品", 80]]
    generator.add_chart_slide("销售数据", data, chart_type="bar")
    print('✓ 添加图表页成功')
    
    # 保存到内存
    output = generator.save_to_buffer()
    print(f'✓ 保存到缓冲区成功，大小: {len(output)} bytes')
    
    # 保存到文件
    output_path = 'test_output.pptx'
    generator.save_to_file(output_path)
    print(f'✓ 保存到文件成功: {output_path}')
    
    # 验证文件存在
    if os.path.exists(output_path):
        file_size = os.path.getsize(output_path)
        print(f'✓ 文件已创建，大小: {file_size} bytes')
    else:
        print('✗ 文件创建失败')
        return False
    
    return True

def test_templates():
    """测试PPT模板"""
    print('\n测试 PPTTemplate 类...')
    
    from app.document.ppt_generator import PPTTemplate
    
    templates = PPTTemplate.list_templates()
    print(f'✓ 加载了 {len(templates)} 个模板')
    
    for template in templates:
        print(f'  - {template["id"]}: {template["name"]}')
    
    # 测试生成商业报告
    result = PPTTemplate.generate("business", {
        "title": "2026年度商业报告",
        "subtitle": "数据分析与业务展望",
        "overview": ["业务增长", "市场分析", "未来规划"],
        "data": [["Q1", 100], ["Q2", 150], ["Q3", 180], ["Q4", 220]],
        "conclusion": ["业绩增长显著", "市场份额提升", "持续创新发展"]
    })
    
    if result.get('success'):
        print('✓ 商业报告模板生成成功')
        print(f'  输出文件: {result.get("output_path")}')
    else:
        print(f'✗ 商业报告模板生成失败: {result.get("error")}')
        return False
    
    return True

def main():
    print('='*60)
    print('PPT生成功能测试')
    print('='*60)
    
    tests = [
        test_pptx_import,
        test_ppt_generator,
        test_templates
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f'\n✗ {test.__name__} 执行失败: {e}')
            import traceback
            traceback.print_exc()
            failed += 1
    
    print('\n' + '='*60)
    print(f'测试完成！')
    print(f'通过: {passed}/{len(tests)}')
    print(f'失败: {failed}/{len(tests)}')
    print('='*60)
    
    if failed == 0:
        print('🎉 PPT生成功能测试通过！')
        print('\n生成的测试文件:')
        print('  - test_output.pptx')
        print('  - output/business_report_2026.pptx')
        return 0
    else:
        return 1

if __name__ == '__main__':
    sys.exit(main())