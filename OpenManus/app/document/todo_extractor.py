"""
待办事项提取模块
从文本中自动识别和提取待办事项
"""
from typing import List, Dict, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import re


@dataclass
class TodoItem:
    """待办事项"""
    task: str
    assignee: str = ""
    deadline: str = ""
    priority: str = "medium"
    category: str = "general"
    context: str = ""
    status: str = "pending"
    confidence: float = 1.0

    def to_dict(self) -> Dict:
        return {
            'task': self.task,
            'assignee': self.assignee,
            'deadline': self.deadline,
            'priority': self.priority,
            'category': self.category,
            'context': self.context,
            'status': self.status,
            'confidence': self.confidence
        }


class TodoExtractor:
    """待办事项提取器"""

    def __init__(self):
        self.todo_keywords = [
            '待办', 'TODO', '任务', '需要做', '必须做', '应该做',
            '待完成', '待处理', '待审核', '待确认', '待回复',
            'action', 'task', 'todo', 'to-do', 'pending'
        ]

        self.priority_keywords = {
            'high': ['紧急', '紧急', '重要', '优先', '马上', '立即', '尽快', 'critical', 'urgent', 'important'],
            'medium': ['正常', '一般', '普通'],
            'low': ['不急', '可以', '有空', '缓一缓', '低优先级']
        }

        self.person_keywords = ['负责人', '负责', '由', '执行', '操作', 'owner', 'responsible']

        self.time_keywords = {
            'today': ['今天', '今日', 'today'],
            'tomorrow': ['明天', '明日', 'tomorrow'],
            'this_week': ['本周', '这周', '本周内'],
            'next_week': ['下周', '下周', 'next week'],
            'this_month': ['本月', '这个月', 'this month'],
            'deadline': ['截止', '截止到', '截止日期', 'deadline']
        }

        self.category_keywords = {
            'meeting': ['会议', '开会', '讨论', 'meeting', 'conference'],
            'development': ['开发', '编程', '代码', '实现', 'develop', 'code', 'implement'],
            'review': ['审核', '审查', 'review', 'check'],
            'document': ['文档', '报告', '总结', 'document', 'report'],
            'communication': ['沟通', '联系', '回复', '回复邮件', 'communication', 'email'],
            'research': ['研究', '调研', '分析', 'research', 'analysis'],
        }

    def extract_from_text(
        self,
        text: str,
        min_confidence: float = 0.5
    ) -> List[TodoItem]:
        """从文本中提取待办事项"""
        todos = []

        lines = text.split('\n')

        for i, line in enumerate(lines):
            line = line.strip()
            if not line or len(line) < 5:
                continue

            context = self._get_context(lines, i)

            todo = self._extract_todo_from_line(line, context)
            if todo and todo.confidence >= min_confidence:
                todos.append(todo)

        for paragraph in text.split('\n\n'):
            paragraph = paragraph.strip()
            if len(paragraph) > 50:
                todos_from_para = self._extract_todos_from_paragraph(paragraph)
                todos.extend(todos_from_para)

        todos = self._deduplicate_todos(todos)

        return todos

    def _extract_todo_from_line(self, line: str, context: str = "") -> Optional[TodoItem]:
        """从单行中提取待办"""
        line_lower = line.lower()

        has_todo_keyword = any(kw in line_lower for kw in self.todo_keywords)

        has_action_verb = any(verb in line for verb in ['完成', '处理', '准备', '提交', '发送', '联系', '更新', '修复', '改进'])

        if not (has_todo_keyword or has_action_verb):
            return None

        todo = TodoItem(task=self._clean_task(line), context=context)

        todo.priority = self._extract_priority(line)
        todo.assignee = self._extract_assignee(line)
        todo.deadline = self._extract_deadline(line)
        todo.category = self._extract_category(line)
        todo.confidence = self._calculate_confidence(line)

        return todo

    def _extract_todos_from_paragraph(self, paragraph: str) -> List[TodoItem]:
        """从段落中提取待办"""
        todos = []

        bullet_patterns = [
            r'[-•·]\s*(.+?)(?:\n|$)',
            r'\d+[.)、]\s*(.+?)(?:\n|$)',
            r'\[ \]\s*(.+?)(?:\n|$)',
            r'\[[xX]\]\s*(.+?)(?:\n|$)',
        ]

        for pattern in bullet_patterns:
            matches = re.findall(pattern, paragraph)
            for match in matches:
                task_text = match.strip()
                if len(task_text) > 10:
                    todo = self._extract_todo_from_line(task_text, paragraph)
                    if todo:
                        todos.append(todo)

        if not todos:
            sentences = paragraph.split('。')
            for sentence in sentences:
                sentence = sentence.strip()
                if len(sentence) > 15 and any(kw in sentence for kw in self.todo_keywords):
                    todo = self._extract_todo_from_line(sentence, paragraph)
                    if todo:
                        todos.append(todo)

        return todos

    def _clean_task(self, line: str) -> str:
        """清理任务文本"""
        task = re.sub(r'^[#\d\s\-•·\[\]TODO待办]+', '', line)
        task = re.sub(r'^\d+[.、)]\s*', '', task)
        task = task.strip(':-： ')

        task = re.sub(r'\s+', ' ', task)

        if len(task) > 200:
            task = task[:200]

        return task

    def _extract_priority(self, line: str) -> str:
        """提取优先级"""
        line_lower = line.lower()

        for priority, keywords in self.priority_keywords.items():
            if any(kw.lower() in line_lower for kw in keywords):
                return priority

        return "medium"

    def _extract_assignee(self, line: str) -> str:
        """提取负责人"""
        patterns = [
            r'负责人[：:]\s*([\u4e00-\u9fff]{2,4})',
            r'负责[：:]\s*([\u4e00-\u9fff]{2,4})',
            r'由\s*([\u4e00-\u9fff]{2,4})\s*负责',
            r'([\u4e00-\u9fff]{2,4})\s*[负负]责',
            r'[@]\s*([\w]+)',
        ]

        for pattern in patterns:
            match = re.search(pattern, line)
            if match:
                return match.group(1).strip()

        return ""

    def _extract_deadline(self, line: str) -> str:
        """提取截止时间"""
        patterns = [
            r'(\d{4}[-/年]\d{1,2}[-/月]\d{1,2}[日]?)',
            r'(\d{1,2}[-/月]\d{1,2}[日]?)',
            r'周([一二三四五六日])',
            r'本[周月]([上下])?',
            r'今[天日]',
            r'明[天日]',
        ]

        for pattern in patterns:
            match = re.search(pattern, line)
            if match:
                deadline_text = match.group(0)

                deadline_text = self._normalize_deadline(deadline_text)
                return deadline_text

        return ""

    def _normalize_deadline(self, deadline: str) -> str:
        """标准化截止时间"""
        today = datetime.now()

        if '今天' in deadline or '今日' in deadline:
            return today.strftime("%Y-%m-%d")
        elif '明天' in deadline or '明日' in deadline:
            return (today + timedelta(days=1)).strftime("%Y-%m-%d")
        elif '一周' in deadline or '本周' in deadline:
            return (today + timedelta(days=7)).strftime("%Y-%m-%d")

        try:
            if '-' in deadline:
                parsed = datetime.strptime(deadline.replace('/', '-'), "%Y-%m-%d")
                return parsed.strftime("%Y-%m-%d")
        except:
            pass

        return deadline

    def _extract_category(self, line: str) -> str:
        """提取分类"""
        line_lower = line.lower()

        for category, keywords in self.category_keywords.items():
            if any(kw.lower() in line_lower for kw in keywords):
                return category

        return "general"

    def _calculate_confidence(self, line: str) -> float:
        """计算置信度"""
        confidence = 0.5

        line_lower = line.lower()

        if any(kw in line_lower for kw in self.todo_keywords):
            confidence += 0.3

        if any(verb in line for verb in ['完成', '处理', '准备', '提交', '修复']):
            confidence += 0.2

        if self._extract_assignee(line):
            confidence += 0.1

        if self._extract_deadline(line):
            confidence += 0.1

        if re.search(r'\[ \]|\[[xX]\]', line):
            confidence += 0.2

        return min(confidence, 1.0)

    def _get_context(self, lines: List[str], index: int, window: int = 2) -> str:
        """获取上下文"""
        start = max(0, index - window)
        end = min(len(lines), index + window + 1)

        context_lines = lines[start:end]
        return ' '.join([line.strip() for line in context_lines if line.strip()])

    def _deduplicate_todos(self, todos: List[TodoItem]) -> List[TodoItem]:
        """去重"""
        seen_tasks = set()
        unique_todos = []

        for todo in todos:
            task_key = todo.task.lower().strip()

            if task_key not in seen_tasks:
                seen_tasks.add(task_key)
                unique_todos.append(todo)

        return unique_todos

    def to_markdown(self, todos: List[TodoItem]) -> str:
        """转换为Markdown列表"""
        if not todos:
            return "- 无待办事项"

        lines = ["## 待办事项", ""]

        by_priority = {'high': [], 'medium': [], 'low': []}
        for todo in todos:
            priority = todo.priority if todo.priority in by_priority else 'medium'
            by_priority[priority].append(todo)

        priority_names = {'high': '🔴 高优先级', 'medium': '🟡 中优先级', 'low': '🟢 低优先级'}

        for priority in ['high', 'medium', 'low']:
            if by_priority[priority]:
                lines.append(f"### {priority_names[priority]}")
                lines.append("")
                for i, todo in enumerate(by_priority[priority], 1):
                    lines.append(f"{i}. **{todo.task}**")

                    details = []
                    if todo.assignee:
                        details.append(f"👤 {todo.assignee}")
                    if todo.deadline:
                        details.append(f"📅 {todo.deadline}")
                    if todo.category != 'general':
                        details.append(f"🏷️ {todo.category}")

                    if details:
                        lines.append(f"   {' | '.join(details)}")

                    lines.append("")

        return '\n'.join(lines)

    def to_todo_list(self, todos: List[TodoItem]) -> str:
        """转换为Todo列表"""
        if not todos:
            return ""

        lines = []
        for todo in todos:
            checkbox = "[ ]"
            assignee = f"@{todo.assignee} " if todo.assignee else ""
            deadline = f" 📅{todo.deadline}" if todo.deadline else ""

            lines.append(f"- {checkbox} {assignee}{todo.task}{deadline}")

        return '\n'.join(lines)

    def to_dict(self, todos: List[TodoItem]) -> Dict:
        """转换为字典"""
        return {
            'total': len(todos),
            'by_priority': {
                'high': len([t for t in todos if t.priority == 'high']),
                'medium': len([t for t in todos if t.priority == 'medium']),
                'low': len([t for t in todos if t.priority == 'low'])
            },
            'by_status': {
                'pending': len([t for t in todos if t.status == 'pending']),
                'completed': len([t for t in todos if t.status == 'completed'])
            },
            'todos': [todo.to_dict() for todo in todos]
        }


def extract_todos(text: str) -> List[Dict]:
    """
    快速提取待办事项的便捷函数

    Args:
        text: 输入文本

    Returns:
        List[Dict]: 待办事项列表
    """
    extractor = TodoExtractor()
    todos = extractor.extract_from_text(text)
    return [todo.to_dict() for todo in todos]


def extract_todos_markdown(text: str) -> str:
    """
    提取待办并转换为Markdown

    Args:
        text: 输入文本

    Returns:
        str: Markdown格式的待办列表
    """
    extractor = TodoExtractor()
    todos = extractor.extract_from_text(text)
    return extractor.to_markdown(todos)
