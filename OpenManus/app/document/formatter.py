"""
文本格式化模块
提供中文文本的智能排版和格式化功能
"""
import re
from typing import List, Dict, Optional
from dataclasses import dataclass


@dataclass
class FormatResult:
    """格式化结果"""
    original_text: str
    formatted_text: str
    changes_made: List[str]
    format_level: str


class ChineseTextFormatter:
    """中文文本格式化器"""

    def __init__(self):
        self.rules = self._init_default_rules()

    def _init_default_rules(self) -> Dict:
        """初始化默认规则"""
        return {
            "space_rules": {
                "cjk_english": True,
                "cjk_number": True,
                "english_cjk": True,
                "number_english": True,
            },
            "punctuation_rules": {
                "fix_ellipsis": True,
                "fix_quotes": True,
                "fix_dash": True,
                "fix_brackets": True,
                "unify_punctuation": True,
            },
            "fullwidth_rules": {
                "letter": False,
                "number": False,
                "punctuation": False,
            },
            "whitespace_rules": {
                "remove_extra_spaces": True,
                "remove_leading_spaces": True,
                "normalize_line_breaks": True,
            }
        }

    def format(
        self,
        text: str,
        level: str = "standard"
    ) -> FormatResult:
        """
        格式化文本

        Args:
            text: 输入文本
            level: 格式化级别 ("simple", "standard", "strict")

        Returns:
            FormatResult: 格式化结果
        """
        if not text:
            return FormatResult(
                original_text=text,
                formatted_text="",
                changes_made=[],
                format_level=level
            )

        if level == "simple":
            rules = {
                "space_rules": {"cjk_english": True},
                "punctuation_rules": {},
                "whitespace_rules": {"remove_extra_spaces": True}
            }
        elif level == "strict":
            rules = {
                "space_rules": {
                    "cjk_english": True,
                    "cjk_number": True,
                    "english_cjk": True,
                    "number_english": True,
                },
                "punctuation_rules": {
                    "fix_ellipsis": True,
                    "fix_quotes": True,
                    "fix_dash": True,
                    "fix_brackets": True,
                    "unify_punctuation": True,
                },
                "whitespace_rules": {
                    "remove_extra_spaces": True,
                    "remove_leading_spaces": True,
                    "normalize_line_breaks": True,
                }
            }
        else:
            rules = self.rules

        result = text
        changes = []

        if rules.get("whitespace_rules", {}).get("remove_extra_spaces"):
            old_len = len(result)
            result = re.sub(r'[ \t]+', ' ', result)
            if len(result) != old_len:
                changes.append("移除多余空格")

        if rules.get("whitespace_rules", {}).get("remove_leading_spaces"):
            lines = result.split('\n')
            formatted_lines = [line.lstrip() for line in lines]
            result = '\n'.join(formatted_lines)

        if rules.get("space_rules", {}).get("cjk_english"):
            old_result = result
            result = self._add_cjk_english_space(result)
            if result != old_result:
                changes.append("中文与英文之间添加空格")

        if rules.get("space_rules", {}).get("cjk_number"):
            old_result = result
            result = self._add_cjk_number_space(result)
            if result != old_result:
                changes.append("中文与数字之间添加空格")

        if rules.get("space_rules", {}).get("english_cjk"):
            old_result = result
            result = self._add_english_cjk_space(result)
            if result != old_result:
                changes.append("英文与中文之间添加空格")

        if rules.get("punctuation_rules", {}).get("fix_ellipsis"):
            old_result = result
            result = self._fix_ellipsis(result)
            if result != old_result:
                changes.append("修复省略号")

        if rules.get("punctuation_rules", {}).get("fix_quotes"):
            old_result = result
            result = self._fix_quotes(result)
            if result != old_result:
                changes.append("修复引号")

        if rules.get("punctuation_rules", {}).get("fix_dash"):
            old_result = result
            result = self._fix_dashes(result)
            if result != old_result:
                changes.append("修复破折号")

        if rules.get("punctuation_rules", {}).get("unify_punctuation"):
            old_result = result
            result = self._unify_punctuation(result)
            if result != old_result:
                changes.append("统一标点符号")

        return FormatResult(
            original_text=text,
            formatted_text=result,
            changes_made=changes,
            format_level=level
        )

    def _add_cjk_english_space(self, text: str) -> str:
        """在中文和英文之间添加空格"""
        result = re.sub(r'([\u4e00-\u9fff])([a-zA-Z])', r'\1 \2', text)
        return result

    def _add_cjk_number_space(self, text: str) -> str:
        """在中文和数字之间添加空格"""
        result = re.sub(r'([\u4e00-\u9fff])([0-9])', r'\1 \2', text)
        result = re.sub(r'([0-9])([\u4e00-\u9fff])', r'\1 \2', result)
        return result

    def _add_english_cjk_space(self, text: str) -> str:
        """在英文和中文之间添加空格"""
        result = re.sub(r'([a-zA-Z])([\u4e00-\u9fff])', r'\1 \2', text)
        return result

    def _fix_ellipsis(self, text: str) -> str:
        """修复省略号"""
        result = re.sub(r'\.{3,}', '……', text)
        result = re.sub(r'\\.\s\\.\s\\.', '……', result)
        result = re.sub(r'\\.\\.\\.', '……', result)
        return result

    def _fix_quotes(self, text: str) -> str:
        """修复引号"""
        replacements = {
            '"': '"',
            '"': '"',
            "'": "'",
            "'": "'",
            '"': '"',
            '"': '"',
            "'": "'",
            "'": "'",
        }

        for old, new in replacements.items():
            text = text.replace(old, new)

        return text

    def _fix_dashes(self, text: str) -> str:
        """修复破折号"""
        text = re.sub(r'-{3,}', '——', text)
        text = re.sub(r'–{3,}', '——', text)
        text = re.sub(r'—{3,}', '——', text)
        return text

    def _unify_punctuation(self, text: str) -> str:
        """统一标点符号"""
        text = re.sub(r'[,，]+', '，', text)
        text = re.sub(r'[.。]+', '。', text)
        text = re.sub(r'[?？]+', '？', text)
        text = re.sub(r'[!！]+', '！', text)
        text = re.sub(r'[:：]+', '：', text)

        text = re.sub(r'，+', '，', text)
        text = re.sub(r'。+', '。', text)
        text = re.sub(r'？+', '？', text)
        text = re.sub(r'！+', '！', text)

        return text


class DocumentFormatter:
    """文档格式化器"""

    def __init__(self):
        self.text_formatter = ChineseTextFormatter()

    def format_document(
        self,
        text: str,
        format_level: str = "standard"
    ) -> str:
        """格式化文档"""
        result = self.text_formatter.format(text, format_level)
        return result.formatted_text

    def format_headings(
        self,
        text: str,
        heading_style: str = "markdown"
    ) -> str:
        """格式化标题"""
        lines = text.split('\n')
        formatted_lines = []

        for line in lines:
            stripped = line.strip()

            if heading_style == "markdown":
                if stripped.startswith('#'):
                    formatted_lines.append(line)
                elif re.match(r'^\d+\.', stripped):
                    formatted_lines.append(f"## {stripped}")
                elif re.match(r'^[一二三四五六七八九十]+[、.．]', stripped):
                    formatted_lines.append(f"## {stripped}")
                else:
                    formatted_lines.append(line)
            else:
                formatted_lines.append(line)

        return '\n'.join(formatted_lines)

    def format_lists(
        self,
        text: str,
        list_style: str = "bullet"
    ) -> str:
        """格式化列表"""
        lines = text.split('\n')
        formatted_lines = []

        for line in lines:
            stripped = line.strip()

            if stripped.startswith(('•', '- ', '* ')):
                item = stripped.lstrip('•-* ')
                formatted_lines.append(f"- {item}")
            elif re.match(r'^\d+[.)、]', stripped):
                match = re.match(r'^(\d+)[.)、]\s*(.*)', stripped)
                if match:
                    formatted_lines.append(f"{match.group(1)}. {match.group(2)}")
                else:
                    formatted_lines.append(line)
            else:
                formatted_lines.append(line)

        return '\n'.join(formatted_lines)

    def format_paragraphs(
        self,
        text: str,
        line_width: int = 80
    ) -> str:
        """格式化段落"""
        lines = text.split('\n')
        formatted_lines = []
        current_paragraph = []

        for line in lines:
            stripped = line.strip()

            if not stripped:
                if current_paragraph:
                    paragraph_text = ' '.join(current_paragraph)
                    if len(paragraph_text) > line_width:
                        wrapped = self._wrap_text(paragraph_text, line_width)
                        formatted_lines.extend(wrapped)
                    else:
                        formatted_lines.append(paragraph_text)
                    formatted_lines.append('')
                    current_paragraph = []
            else:
                current_paragraph.append(stripped)

        if current_paragraph:
            paragraph_text = ' '.join(current_paragraph)
            formatted_lines.append(paragraph_text)

        return '\n'.join(formatted_lines)

    def _wrap_text(self, text: str, width: int) -> List[str]:
        """文本换行"""
        chars = list(text)
        lines = []
        current_line = []
        current_length = 0

        for char in chars:
            char_width = 2 if ord(char) > 127 else 1

            if current_length + char_width > width:
                if current_line:
                    lines.append(''.join(current_line))
                    current_line = []
                    current_length = 0

            current_line.append(char)
            current_length += char_width

        if current_line:
            lines.append(''.join(current_line))

        return lines if lines else [text]


def format_chinese_text(
    text: str,
    level: str = "standard"
) -> str:
    """
    格式化中文文本的便捷函数

    Args:
        text: 输入文本
        level: 格式化级别 ("simple", "standard", "strict")

    Returns:
        str: 格式化后的文本
    """
    formatter = ChineseTextFormatter()
    result = formatter.format(text, level)
    return result.formatted_text


def format_document(
    text: str,
    format_level: str = "standard"
) -> Dict:
    """
    格式化文档的便捷函数

    Args:
        text: 输入文档
        format_level: 格式化级别

    Returns:
        Dict: 包含格式化结果和详细信息的字典
    """
    formatter = DocumentFormatter()
    formatted = formatter.format_document(text, format_level)

    return {
        "original": text,
        "formatted": formatted,
        "changes": formatter.text_formatter.format(text, format_level).changes_made,
        "level": format_level
    }
