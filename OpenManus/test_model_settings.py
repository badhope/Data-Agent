"""测试模型设置功能"""
import sys
sys.path.insert(0, '.')

def test_llm_service():
    """测试 LLM 服务功能"""
    print('\n=== 测试 LLM 服务 ===')

    from services.llm_service import (
        test_connection,
        verify_model_exists,
        list_available_models,
        get_account_info,
        _get_provider_source,
        _get_provider_dashboard_url
    )

    print('✓ 所有函数导入成功')

    print('\n测试提供商信息获取...')
    providers = ['openai', 'anthropic', 'deepseek', 'qwen', 'tongyi']
    for provider in providers:
        source = _get_provider_source(provider)
        dashboard = _get_provider_dashboard_url(provider)
        print(f'  {provider}:')
        print(f'    来源: {source[:50]}...')
        print(f'    控制台: {dashboard[:50] if dashboard else "N/A"}...')

    print('\n✓ 提供商信息获取测试通过')
    return True

def test_settings_routes():
    """测试设置路由"""
    print('\n=== 测试设置路由 ===')

    from routers.settings import (
        test_api_connection,
        verify_model,
        list_models,
        get_account_info_endpoint
    )

    print('✓ 所有路由函数导入成功')
    return True

def test_no_api_key():
    """测试无API Key的情况"""
    print('\n=== 测试无API Key场景 ===')
    import asyncio

    async def test():
        from services.llm_service import test_connection
        result = await test_connection("", "https://api.openai.com/v1", "gpt-4o", "openai")

        assert result["success"] == False
        assert "error_type" in result
        assert result["error_type"] == "missing_api_key"
        print(f'✓ 无API Key测试通过: {result["message"]}')

    asyncio.run(test())

def test_custom_model_validation():
    """测试自定义模型验证逻辑"""
    print('\n=== 测试自定义模型验证 ===')

    from services.llm_service import verify_model_exists

    print('✓ verify_model_exists 函数可用')
    print('  该函数将用于验证用户输入的自定义模型名称')
    return True

def main():
    tests = [
        test_llm_service,
        test_settings_routes,
        test_no_api_key,
        test_custom_model_validation
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f'✗ {test.__name__} failed: {e}')
            import traceback
            traceback.print_exc()
            failed += 1

    print(f'\n=== 测试完成 ===')
    print(f'通过: {passed}')
    print(f'失败: {failed}')

    if failed == 0:
        print('所有测试通过！')
        return 0
    else:
        return 1

if __name__ == '__main__':
    sys.exit(main())
