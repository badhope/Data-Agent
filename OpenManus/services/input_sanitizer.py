"""
DataAgent - 输入净化服务
防止 Prompt 注入和恶意输入
"""

import re
from typing import Optional


# Prompt 注入检测模式
INJECTION_PATTERNS = [
    r'ignore\s+(all\s+)?previous\s+instructions',
    r'you\s+are\s+now\s+(a|an)\s+',
    r'forget\s+(everything|all|your)',
    r'disregard\s+(your|the|all)',
    r'system\s*:\s*',
    r'new\s+instructions?\s*:',
    r'override\s+(your|the|all)',
    r'pretend\s+(you\s+are|to\s+be)',
    r'act\s+as\s+(if|a|an)',
    r'roleplay\s+as',
    r'jailbreak',
    r'dan\s*\d+\.\d+',
]

# 危险内容检测
DANGEROUS_PATTERNS = [
    r'rm\s+-rf',
    r'del\s+/[sf]',
    r'drop\s+table',
    r'__import__\s*\(.*os',
    r'eval\s*\(',
    r'exec\s*\(',
    r'subprocess',
    r'os\.system',
]


def sanitize_input(text: str) -> str:
    """净化用户输入，移除潜在危险内容"""
    if not text:
        return text

    # 移除控制字符（保留换行和制表符）
    sanitized = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', text)

    # 限制输入长度
    if len(sanitized) > 50000:
        sanitized = sanitized[:50000] + "\n\n[输入过长，已截断]"

    return sanitized


def detect_prompt_injection(text: str) -> Optional[str]:
    """检测 Prompt 注入尝试，返回匹配的模式或 None"""
    text_lower = text.lower()

    for pattern in INJECTION_PATTERNS:
        if re.search(pattern, text_lower, re.IGNORECASE):
            return pattern

    return None


def detect_dangerous_content(text: str) -> list:
    """检测潜在危险内容"""
    dangers = []

    for pattern in DANGEROUS_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            dangers.append(pattern)

    return dangers


def validate_message(message: str) -> dict:
    """验证用户消息，返回验证结果"""
    if not message or not message.strip():
        return {"valid": False, "error": "消息不能为空"}

    sanitized = sanitize_input(message)

    injection = detect_prompt_injection(sanitized)
    if injection:
        return {
            "valid": True,
            "sanitized": sanitized,
            "warning": f"检测到可能的 Prompt 注入模式: {injection[:50]}",
            "severity": "medium"
        }

    dangers = detect_dangerous_content(sanitized)
    if dangers:
        return {
            "valid": True,
            "sanitized": sanitized,
            "warning": f"检测到潜在危险操作: {', '.join(dangers[:3])}",
            "severity": "high"
        }

    return {"valid": True, "sanitized": sanitized}
