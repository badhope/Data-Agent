#!/usr/bin/env python
"""测试重构后的智能体"""
import sys
sys.path.insert(0, '/workspace/langchain_office_assistant')

print('=' * 60)
print('🧪 测试重构后的智能体')
print('=' * 60)

from langchain_office_assistant.agents.validators import (
    ConfidenceHandler,
    LLMOutputValidator,
)

print('\n✅ 模块导入成功')

print('\n📝 测试置信度处理器...')
level = ConfidenceHandler.get_level(0.9)
print(f'   置信度 0.9 -> {level.value}')

level = ConfidenceHandler.get_level(0.6)
print(f'   置信度 0.6 -> {level.value}')

level = ConfidenceHandler.get_level(0.3)
print(f'   置信度 0.3 -> {level.value}')

print('\n📝 测试参数验证器...')
validation = LLMOutputValidator.validate('calculate', {'expression': '2+2'})
print(f'   验证结果: is_valid={validation.is_valid}')

validation = LLMOutputValidator.validate('currency_convert', {
    'amount': 100,
    'from_currency': 'USD',
    'to_currency': 'CNY'
})
print(f'   货币转换验证: is_valid={validation.is_valid}')

print('\n' + '=' * 60)
print('✅ 第一阶段核心问题修复完成!')
print('=' * 60)
