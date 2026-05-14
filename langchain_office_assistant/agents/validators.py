"""
置信度处理器和LLM输出验证器
解决AI输出的不确定性和幻觉问题
"""
from typing import Dict, Any, Optional, Tuple, List
from dataclasses import dataclass
from enum import Enum
import logging
import json
import re

logger = logging.getLogger(__name__)


class ConfidenceLevel(Enum):
    """置信度等级"""
    HIGH = "high"      # > 0.8
    MEDIUM = "medium"  # 0.5 - 0.8
    LOW = "low"        # < 0.5


@dataclass
class ValidationResult:
    """验证结果"""
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    corrected_params: Dict[str, Any]
    confidence_level: ConfidenceLevel


class ConfidenceHandler:
    """置信度处理器"""

    HIGH_THRESHOLD = 0.8
    LOW_THRESHOLD = 0.5

    @classmethod
    def get_level(cls, confidence: float) -> ConfidenceLevel:
        """获取置信度等级"""
        if confidence >= cls.HIGH_THRESHOLD:
            return ConfidenceLevel.HIGH
        elif confidence >= cls.LOW_THRESHOLD:
            return ConfidenceLevel.MEDIUM
        else:
            return ConfidenceLevel.LOW

    @classmethod
    def should_confirm(cls, confidence: float) -> bool:
        """是否需要用户确认"""
        return confidence < cls.LOW_THRESHOLD

    @classmethod
    def should_retry(cls, confidence: float) -> bool:
        """是否需要重试"""
        return confidence < cls.LOW_THRESHOLD

    @classmethod
    def format_confidence_message(cls, confidence: float, tool_name: str) -> str:
        """生成置信度提示消息"""
        level = cls.get_level(confidence)

        if level == ConfidenceLevel.HIGH:
            return ""
        elif level == ConfidenceLevel.MEDIUM:
            return f"⚠️ 检测到中等置信度({confidence:.0%})，已尽力理解您的意图。"
        else:
            return f"⚠️ 检测到低置信度({confidence:.0%})，可能未能正确理解您的需求。请确认或重新描述。"


class LLMOutputValidator:
    """LLM输出验证器"""

    VALIDATION_RULES = {
        "send_email": {
            "to": {
                "type": "list",
                "item_pattern": r'^[\w\.-]+@[\w\.-]+\.\w+$',
                "error_msg": "邮箱格式无效"
            },
            "subject": {
                "type": "str",
                "min_length": 1,
                "max_length": 200,
                "error_msg": "主题长度应在1-200字符之间"
            },
            "body": {
                "type": "str",
                "min_length": 1,
                "error_msg": "邮件内容不能为空"
            }
        },
        "schedule_meeting": {
            "date": {
                "type": "str",
                "pattern": r'^\d{4}[-/]\d{1,2}[-/]\d{1,2}$',
                "error_msg": "日期格式应为YYYY-MM-DD",
                "default": "today"
            },
            "time": {
                "type": "str",
                "pattern": r'^\d{1,2}:\d{2}$',
                "error_msg": "时间格式应为HH:MM",
                "default": "14:00"
            }
        },
        "create_line_chart": {
            "x_data": {
                "type": "list",
                "min_items": 2,
                "error_msg": "至少需要2个数据点"
            },
            "y_data": {
                "type": "list",
                "min_items": 2,
                "item_type": "number",
                "error_msg": "至少需要2个数值"
            }
        },
        "create_bar_chart": {
            "labels": {
                "type": "list",
                "min_items": 2,
                "error_msg": "至少需要2个标签"
            },
            "values": {
                "type": "list",
                "min_items": 2,
                "item_type": "number",
                "error_msg": "至少需要2个数值"
            }
        },
        "calculate": {
            "expression": {
                "type": "str",
                "pattern": r'^[\d\s\+\-\*\/\(\)\.\w]+$',
                "error_msg": "表达式包含非法字符"
            }
        },
        "statistics": {
            "numbers": {
                "type": "list",
                "min_items": 1,
                "item_type": "number",
                "error_msg": "至少需要1个数值"
            }
        },
        "currency_convert": {
            "amount": {
                "type": "number",
                "min_value": 0,
                "error_msg": "金额必须大于等于0"
            },
            "from_currency": {
                "type": "str",
                "allowed_values": ["USD", "CNY", "EUR", "GBP", "JPY", "KRW", "AUD", "CAD"],
                "error_msg": "不支持的货币类型"
            },
            "to_currency": {
                "type": "str",
                "allowed_values": ["USD", "CNY", "EUR", "GBP", "JPY", "KRW", "AUD", "CAD"],
                "error_msg": "不支持的货币类型"
            }
        }
    }

    @classmethod
    def validate(cls, tool_name: str, params: Dict[str, Any], confidence: float = 1.0) -> ValidationResult:
        """验证参数"""
        errors = []
        warnings = []
        corrected_params = params.copy()

        rules = cls.VALIDATION_RULES.get(tool_name, {})

        for param_name, rule in rules.items():
            value = params.get(param_name)

            if value is None:
                if rule.get("required", False):
                    if "default" in rule:
                        corrected_params[param_name] = rule["default"]
                        warnings.append(f"参数 {param_name} 未提供，使用默认值: {rule['default']}")
                    else:
                        errors.append(f"缺少必需参数: {param_name}")
                continue

            param_errors = cls._validate_param(param_name, value, rule)
            errors.extend(param_errors)

        confidence_level = ConfidenceHandler.get_level(confidence)

        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            corrected_params=corrected_params,
            confidence_level=confidence_level
        )

    @classmethod
    def _validate_param(cls, name: str, value: Any, rule: Dict) -> List[str]:
        """验证单个参数"""
        errors = []
        expected_type = rule.get("type")

        if expected_type == "str":
            if not isinstance(value, str):
                errors.append(f"{name}: 期望字符串类型")
            else:
                if "pattern" in rule and not re.match(rule["pattern"], value):
                    if "default" in rule:
                        pass
                    else:
                        errors.append(f"{name}: {rule.get('error_msg', '格式无效')}")
                if "min_length" in rule and len(value) < rule["min_length"]:
                    errors.append(f"{name}: 长度不足{rule['min_length']}")
                if "max_length" in rule and len(value) > rule["max_length"]:
                    errors.append(f"{name}: 长度超过{rule['max_length']}")
                if "allowed_values" in rule and value not in rule["allowed_values"]:
                    errors.append(f"{name}: {rule.get('error_msg', '值不在允许范围内')}")

        elif expected_type == "number":
            if not isinstance(value, (int, float)):
                errors.append(f"{name}: 期望数值类型")
            else:
                if "min_value" in rule and value < rule["min_value"]:
                    errors.append(f"{name}: 值小于最小值{rule['min_value']}")
                if "max_value" in rule and value > rule["max_value"]:
                    errors.append(f"{name}: 值大于最大值{rule['max_value']}")

        elif expected_type == "list":
            if not isinstance(value, list):
                errors.append(f"{name}: 期望列表类型")
            else:
                if "min_items" in rule and len(value) < rule["min_items"]:
                    errors.append(f"{name}: {rule.get('error_msg', '列表项数不足')}")
                if "item_type" in rule:
                    item_type = rule["item_type"]
                    for i, item in enumerate(value):
                        if item_type == "number" and not isinstance(item, (int, float)):
                            errors.append(f"{name}[{i}]: 期望数值类型")
                if "item_pattern" in rule:
                    pattern = rule["item_pattern"]
                    for i, item in enumerate(value):
                        if not re.match(pattern, str(item)):
                            errors.append(f"{name}[{i}]: {rule.get('error_msg', '格式无效')}")

        return errors


class ErrorRecovery:
    """错误恢复机制"""

    MAX_RETRIES = 3
    RETRY_DELAY = 0.5

    @classmethod
    async def execute_with_recovery(cls, func, *args, **kwargs) -> Tuple[bool, Any]:
        """带恢复机制的执行"""
        import asyncio

        last_error = None

        for attempt in range(cls.MAX_RETRIES):
            try:
                result = await func(*args, **kwargs)
                return True, result
            except Exception as e:
                last_error = e
                logger.warning(f"执行失败(尝试 {attempt + 1}/{cls.MAX_RETRIES}): {e}")

                if attempt < cls.MAX_RETRIES - 1:
                    await asyncio.sleep(cls.RETRY_DELAY * (attempt + 1))

        return False, str(last_error)

    @classmethod
    def generate_recovery_suggestion(cls, error: str, tool_name: str) -> str:
        """生成恢复建议"""
        error_lower = error.lower()

        if "timeout" in error_lower:
            return "⏱️ 操作超时，请稍后重试或简化您的请求。"
        elif "rate limit" in error_lower:
            return "🚦 请求过于频繁，请等待几秒后重试。"
        elif "invalid" in error_lower or "format" in error_lower:
            return f"📝 参数格式有误，请检查您的输入格式是否正确。"
        elif "not found" in error_lower:
            return "🔍 未找到相关内容，请尝试不同的关键词。"
        elif "permission" in error_lower or "auth" in error_lower:
            return "🔐 权限不足，请检查API密钥配置。"
        else:
            return f"❌ 操作失败: {error}\n请尝试重新描述您的需求。"
