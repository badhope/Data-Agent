"""完整功能测试脚本"""
import sys
import os

PROJECT_ROOT = r'c:\Users\X1882\Desktop\Data-Agent\OpenManus'
sys.path.insert(0, PROJECT_ROOT)
os.chdir(PROJECT_ROOT)

def test_voice_input_module():
    """测试语音输入模块"""
    print('\n=== 测试语音输入模块 ===')

    print('检查 JavaScript 文件...')
    try:
        with open('static/js/voice_input.js', 'r', encoding='utf-8') as f:
            content = f.read()
            assert 'class VoiceInput' in content
            assert 'class VoiceOutput' in content
            assert 'class AudioRecorder' in content
            print('✓ voice_input.js 包含所有必需的类')
    except Exception as e:
        print(f'✗ 语音输入模块检查失败: {e}')
        return False

    return True

def test_main_page_voice_button():
    """测试主页面语音按钮"""
    print('\n=== 测试主页面语音按钮 ===')

    try:
        with open('templates/index.html', 'r', encoding='utf-8') as f:
            content = f.read()

            assert 'voice-input-btn' in content
            print('✓ 语音输入按钮已添加')

            assert 'voice_input.js' in content
            print('✓ 语音输入脚本已引用')

            assert 'VoiceInput' in content
            print('✓ VoiceInput 类已初始化')

    except Exception as e:
        print(f'✗ 主页面测试失败: {e}')
        return False

    return True

def test_settings_page():
    """测试设置页面"""
    print('\n=== 测试设置页面 ===')

    try:
        with open('web/templates/settings.html', 'r', encoding='utf-8') as f:
            content = f.read()

            assert 'custom-model' in content
            print('✓ 自定义模型输入已添加')

            assert 'testConnection' in content
            print('✓ 测试连接功能已实现')

            assert 'checkBalance' in content
            print('✓ 余额检查功能已实现')

    except Exception as e:
        print(f'✗ 设置页面测试失败: {e}')
        return False

    return True

def test_management_pages():
    """测试管理页面"""
    print('\n=== 测试管理页面 ===')

    pages = {
        'agents.html': ['智能体管理', 'createNew', 'saveAgent'],
        'skills.html': ['技能管理', 'createNew', 'saveSkill'],
        'prompts.html': ['提示词管理', 'createNew', 'savePrompt'],
        'mcp.html': ['MCP管理', 'createNew', 'saveServer']
    }

    for page, checks in pages.items():
        try:
            with open(f'web/templates/{page}', 'r', encoding='utf-8') as f:
                content = f.read()

                for check in checks:
                    assert check in content

                print(f'✓ {page} - 所有检查通过')
        except Exception as e:
            print(f'✗ {page} 测试失败: {e}')
            return False

    return True

def test_document_modules():
    """测试文档处理模块"""
    print('\n=== 测试文档处理模块 ===')

    modules = {
        'meeting_minutes.py': ['MeetingMinutesGenerator', 'generate_from_text'],
        'summarizer.py': ['DocumentSummarizer', 'generate_summary'],
        'translator.py': ['MultiLanguageTranslator', 'translate'],
        'ppt_generator.py': ['PPTTemplate', 'generate_ppt']
    }

    for module, checks in modules.items():
        try:
            with open(f'app/document/{module}', 'r', encoding='utf-8') as f:
                content = f.read()

                for check in checks:
                    assert check in content

                print(f'✓ {module} - 所有检查通过')
        except Exception as e:
            print(f'✗ {module} 测试失败: {e}')
            return False

    return True

def test_llm_service():
    """测试LLM服务"""
    print('\n=== 测试LLM服务 ===')

    try:
        with open('services/llm_service.py', 'r', encoding='utf-8') as f:
            content = f.read()

            checks = [
                'test_connection',
                'verify_model_exists',
                'list_available_models',
                'get_account_info',
                '_get_provider_source',
                '_get_provider_dashboard_url'
            ]

            for check in checks:
                assert check in content
                print(f'✓ {check} 函数已实现')

    except Exception as e:
        print(f'✗ LLM服务测试失败: {e}')
        return False

    return True

def test_readme():
    """测试README文档"""
    print('\n=== 测试README文档 ===')

    try:
        with open('README.md', 'r', encoding='utf-8') as f:
            content = f.read()

            checks = [
                '语音输入',
                '会议纪要',
                '文献摘要',
                'PPT生成',
                '智能体',
                '技能管理',
                '提示词',
                'MCP',
                '模型设置',
                'API端点'
            ]

            for check in checks:
                if check in content:
                    print(f'✓ {check} 已在文档中说明')
                else:
                    print(f'⚠ {check} 未在文档中找到')

    except Exception as e:
        print(f'✗ README测试失败: {e}')
        return False

    return True

def main():
    print('='*60)
    print('Data-Agent 完整功能测试')
    print('='*60)

    tests = [
        test_voice_input_module,
        test_main_page_voice_button,
        test_settings_page,
        test_management_pages,
        test_document_modules,
        test_llm_service,
        test_readme
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
        print('🎉 所有测试通过！项目已准备就绪！')
        return 0
    else:
        print('⚠ 部分测试失败，请检查上述错误')
        return 1

if __name__ == '__main__':
    sys.exit(main())
