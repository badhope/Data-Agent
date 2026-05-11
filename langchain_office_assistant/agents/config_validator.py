"""
配置验证器
在启动时验证配置，发现配置错误
"""
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum
import re
from ..utils.logger import get_logger

logger = get_logger(__name__)


class ConfigLevel(Enum):
    """配置验证级别"""
    STRICT = "strict"    # 严格模式，必须提供所有必需配置
    WARNING = "warning"  # 警告模式，缺失配置给出警告
    LENIENT = "lenient"  # 宽松模式，使用默认值


@dataclass
class ConfigValidationResult:
    """配置验证结果"""
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    missing_required: List[str]
    invalid_format: List[str]


class ConfigValidator:
    """配置验证器"""

    REQUIRED_CONFIGS = {
        "api_key": {
            "required": True,
            "pattern": r"^sk-",
            "error_msg": "API密钥格式不正确"
        },
        "agent_model": {
            "required": False,
            "default": "qwen-plus",
            "allowed_values": [
                "qwen-max", "qwen-plus", "qwen-turbo", "qwen-flash",
                "gpt-4", "gpt-3.5-turbo", "claude-3"
            ]
        }
    }

    def __init__(self, validation_level: ConfigLevel = ConfigLevel.WARNING):
        self.validation_level = validation_level

    def validate(self, config: Dict[str, Any]) -> ConfigValidationResult:
        """验证配置"""
        errors = []
        warnings = []
        missing_required = []
        invalid_format = []

        for key, rules in self.REQUIRED_CONFIGS.items():
            value = config.get(key)

            if value is None:
                if rules.get("required", False):
                    if "default" in rules:
                        warnings.append(f"配置项 '{key}' 未提供，使用默认值: {rules['default']}")
                    else:
                        missing_required.append(key)
                        errors.append(f"缺少必需配置项: {key}")
                else:
                    if "default" in rules:
                        warnings.append(f"配置项 '{key}' 未提供，使用默认值: {rules['default']}")
            else:
                if "pattern" in rules:
                    if not re.match(rules["pattern"], str(value)):
                        invalid_format.append(key)
                        errors.append(f"{rules['error_msg']}: {key}={value}")

                if "allowed_values" in rules:
                    if value not in rules["allowed_values"]:
                        warnings.append(
                            f"配置项 '{key}' 的值 '{value}' 不在推荐列表中，"
                            f"推荐值: {', '.join(rules['allowed_values'][:5])}"
                        )

        is_valid = len(errors) == 0

        if self.validation_level == ConfigLevel.WARNING and missing_required:
            logger.warning(f"Missing required configs: {missing_required}")
        elif self.validation_level == ConfigLevel.STRICT and not is_valid:
            logger.error(f"Configuration validation failed: {errors}")

        return ConfigValidationResult(
            is_valid=is_valid,
            errors=errors,
            warnings=warnings,
            missing_required=missing_required,
            invalid_format=invalid_format
        )

    def validate_api_keys(self, config: Dict[str, Any]) -> Dict[str, bool]:
        """验证API密钥"""
        results = {}

        if config.get("openai_api_key"):
            results["openai"] = self._validate_openai_key(config["openai_api_key"])

        if config.get("anthropic_api_key"):
            results["anthropic"] = self._validate_anthropic_key(config["anthropic_api_key"])

        if config.get("gemini_api_key"):
            results["gemini"] = self._validate_gemini_key(config["gemini_api_key"])

        return results

    def _validate_openai_key(self, key: str) -> bool:
        """验证OpenAI API密钥格式"""
        return bool(re.match(r"^sk-", key))

    def _validate_anthropic_key(self, key: str) -> bool:
        """验证Anthropic API密钥格式"""
        return bool(re.match(r"^sk-ant-", key))

    def _validate_gemini_key(self, key: str) -> bool:
        """验证Gemini API密钥格式"""
        return len(key) >= 20

    def get_recommended_config(self) -> Dict[str, Any]:
        """获取推荐配置"""
        return {
            "agent_model": "qwen-plus",
            "redis_url": "redis://localhost:6379",
            "log_level": "INFO",
            "debug_mode": False,
            "vector_db_type": "faiss"
        }
