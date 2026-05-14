"""
会议纪要生成模块
自动从文本生成结构化的会议纪要
"""
from typing import List, Dict, Optional
from dataclasses import dataclass, field, asdict
from datetime import datetime
import re


@dataclass
class MeetingInfo:
    """会议信息"""
    title: str = ""
    date: str = ""
    time: str = ""
    duration: str = ""
    host: str = ""
    participants: List[str] = field(default_factory=list)
    location: str = ""

    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class DiscussionPoint:
    """讨论要点"""
    topic: str = ""
    speaker: Optional[str] = None
    content: str = ""
    key_points: List[str] = field(default_factory=list)
    timestamp: Optional[str] = None

    def to_dict(self) -> Dict:
        return {
            'topic': self.topic,
            'speaker': self.speaker,
            'content': self.content,
            'key_points': self.key_points,
            'timestamp': self.timestamp
        }


@dataclass
class ActionItem:
    """待办事项"""
    task: str = ""
    assignee: str = ""
    deadline: str = ""
    priority: str = "medium"
    status: str = "pending"

    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class MeetingMinutes:
    """会议纪要"""
    meeting_info: MeetingInfo = field(default_factory=MeetingInfo)
    agenda: List[str] = field(default_factory=list)
    discussion_points: List[DiscussionPoint] = field(default_factory=list)
    decisions: List[str] = field(default_factory=list)
    action_items: List[ActionItem] = field(default_factory=list)
    next_meeting: Optional[Dict] = None
    generated_at: str = ""

    def to_dict(self) -> Dict:
        return {
            'meeting_info': self.meeting_info.to_dict(),
            'agenda': self.agenda,
            'discussion_points': [dp.to_dict() for dp in self.discussion_points],
            'decisions': self.decisions,
            'action_items': [ai.to_dict() for ai in self.action_items],
            'next_meeting': self.next_meeting,
            'generated_at': self.generated_at
        }


class MeetingMinutesGenerator:
    """会议纪要生成器"""

    def __init__(self):
        self.action_keywords = ['待办', 'TODO', '任务', '负责', '完成', '截止', 'action']
        self.decision_keywords = ['决定', '通过', '批准', '同意', '确认', '决策', '共识']
        self.person_keywords = ['说', '表示', '指出', '认为', '提出']

    def generate_from_text(
        self,
        text: str,
        meeting_date: Optional[str] = None
    ) -> MeetingMinutes:
        """从文本生成会议纪要"""
        meeting_info = self._extract_meeting_info(text, meeting_date)
        agenda = self._extract_agenda(text)
        discussion_points = self._extract_discussions(text)
        decisions = self._extract_decisions(text)
        action_items = self._extract_action_items(text)

        return MeetingMinutes(
            meeting_info=meeting_info,
            agenda=agenda,
            discussion_points=discussion_points,
            decisions=decisions,
            action_items=action_items,
            next_meeting=None,
            generated_at=datetime.now().isoformat()
        )

    def _extract_meeting_info(
        self,
        text: str,
        meeting_date: Optional[str]
    ) -> MeetingInfo:
        """提取会议基本信息"""
        info = MeetingInfo()
        info.date = meeting_date or datetime.now().strftime("%Y-%m-%d")

        lines = text.split('\n')
        text_sample = '\n'.join(lines[:20])

        title_patterns = [
            r'会议[主题标题][：:]\s*(.+?)(?:\n|$)',
            r'#\s*(.+?)(?:\n|$)',
            r'^(.{5,50})(?:\n|$)'
        ]

        for pattern in title_patterns:
            match = re.search(pattern, text_sample, re.MULTILINE)
            if match:
                title = match.group(1).strip()
                if len(title) > 5 and len(title) < 100:
                    info.title = title
                    break

        date_patterns = [
            r'(\d{4}[-/年]\d{1,2}[-/月]\d{1,2}日?)',
            r'(\d{1,2}[-/月]\d{1,2}日?)',
        ]

        for pattern in date_patterns:
            match = re.search(pattern, text_sample)
            if match:
                info.date = match.group(1)
                break

        time_pattern = r'(\d{1,2}:\d{2})'
        match = re.search(time_pattern, text_sample)
        if match:
            info.time = match.group(1)

        host_patterns = [
            r'主持人[：:]\s*(.+?)(?:\n|$)',
            r'主持[：:]\s*(.+?)(?:\n|$)',
        ]

        for pattern in host_patterns:
            match = re.search(pattern, text_sample)
            if match:
                info.host = match.group(1).strip()
                break

        participant_patterns = [
            r'参会[人员者][：:]\s*(.+?)(?:\n|$)',
            r'参与[人员][：:]\s*(.+?)(?:\n|$)',
        ]

        for pattern in participant_patterns:
            match = re.search(pattern, text_sample)
            if match:
                participants_text = match.group(1)
                info.participants = [p.strip() for p in re.split(r'[,，、]', participants_text)]
                break

        return info

    def _extract_agenda(self, text: str) -> List[str]:
        """提取议程"""
        agenda = []
        lines = text.split('\n')

        in_agenda_section = False
        agenda_section_keywords = ['议程', 'Agenda', '会议议题', '日程']

        for line in lines:
            line = line.strip()

            if any(kw in line for kw in agenda_section_keywords):
                in_agenda_section = True
                continue

            if in_agenda_section:
                if not line:
                    if len(agenda) >= 3:
                        break
                    continue

                if line.startswith(('#', '##', '###', '议程', 'Agenda')):
                    continue

                if line.startswith(('1.', '2.', '3.', '4.', '5.', '•', '-', '·', '▸', '●')):
                    item = re.sub(r'^[\d\.\s•\-\·▸●]+', '', line).strip()
                    if item and len(item) > 2:
                        agenda.append(item)
                elif len(line) > 5 and len(line) < 200:
                    if not any(kw in line for kw in ['讨论', '决定', '待办']):
                        agenda.append(line)

                if len(agenda) >= 7:
                    break

        return agenda[:7]

    def _extract_discussions(self, text: str) -> List[DiscussionPoint]:
        """提取讨论要点"""
        discussions = []
        paragraphs = text.split('\n\n')

        discussion_keywords = ['讨论', '认为', '表示', '提出', '谈及', '指出']

        for para in paragraphs:
            para = para.strip()
            if len(para) < 30:
                continue

            para_lines = para.split('\n')
            first_line = para_lines[0].strip()

            if any(kw in para for kw in discussion_keywords):
                topic = first_line[:80] if len(first_line) > 80 else first_line

                speaker = self._extract_speaker(para)

                key_points = self._extract_key_points_from_text(para)

                discussions.append(DiscussionPoint(
                    topic=topic,
                    speaker=speaker,
                    content=para[:500],
                    key_points=key_points
                ))

            if len(discussions) >= 10:
                break

        return discussions

    def _extract_speaker(self, text: str) -> Optional[str]:
        """提取发言人"""
        patterns = [
            r'([\u4e00-\u9fff]{2,4})[说表示指出认为提出]',
            r'([\u4e00-\u9fff]{2,4})[:：]',
            r'发言人[：:]\s*([\u4e00-\u9fff]+)',
        ]

        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(1)

        return None

    def _extract_key_points_from_text(self, text: str) -> List[str]:
        """从文本中提取关键点"""
        points = []

        bullet_patterns = [
            r'[-•·]\s*(.+?)(?:\n|$)',
            r'(\d+)[.、](.+?)(?:\n|$)',
        ]

        for pattern in bullet_patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                point = match if isinstance(match, str) else match[-1]
                point = point.strip()
                if len(point) > 5 and len(point) < 200:
                    points.append(point)

                if len(points) >= 5:
                    break

        return points[:5]

    def _extract_decisions(self, text: str) -> List[str]:
        """提取决策"""
        decisions = []
        lines = text.split('\n')

        for line in lines:
            line = line.strip()
            if not line or len(line) < 10:
                continue

            if any(kw in line for kw in self.decision_keywords):
                decision = re.sub(r'^[#\d\.\s]+', '', line).strip()
                if decision:
                    decisions.append(decision)

            if len(decisions) >= 8:
                break

        return decisions

    def _extract_action_items(self, text: str) -> List[ActionItem]:
        """提取待办事项"""
        action_items = []
        lines = text.split('\n')

        for line in lines:
            line = line.strip()
            if not line or len(line) < 10:
                continue

            if any(kw in line for kw in self.action_keywords):
                task = self._clean_action_task(line)
                if task:
                    assignee = self._extract_assignee(task)
                    deadline = self._extract_deadline(task)

                    action_items.append(ActionItem(
                        task=task,
                        assignee=assignee,
                        deadline=deadline
                    ))

            if len(action_items) >= 10:
                break

        return action_items

    def _clean_action_task(self, line: str) -> str:
        """清理任务文本"""
        task = re.sub(r'^[#待办TODO任务\s]+', '', line)
        task = re.sub(r'^\d+[.、]\s*', '', task)
        task = task.strip(':-： ')
        return task

    def _extract_assignee(self, text: str) -> str:
        """提取负责人"""
        patterns = [
            r'负责人[：:]\s*([\u4e00-\u9fff]{2,4})',
            r'负责[：:]\s*([\u4e00-\u9fff]{2,4})',
            r'由\s*([\u4e00-\u9fff]{2,4})\s*负责',
            r'([\u4e00-\u9fff]{2,4})\s*负责',
        ]

        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(1)

        return ""

    def _extract_deadline(self, text: str) -> str:
        """提取截止时间"""
        patterns = [
            r'截止[到时间][：:]\s*(\d{1,2}[月/\-]\d{1,2}[日]?)',
            r'截止[到]?\s*(\d{1,2}[月/\-]\d{1,2}[日]?)',
            r'(\d{1,2}[月/\-]\d{1,2}[日]?)前',
            r'周([一二三四五六日])',
        ]

        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(1)

        return ""

    def to_markdown(self, minutes: MeetingMinutes) -> str:
        """转换为Markdown格式"""
        md_lines = [
            f"# {minutes.meeting_info.title or '会议纪要'}",
            "",
            "## 📋 会议信息",
            f"- **日期**: {minutes.meeting_info.date}",
            f"- **时间**: {minutes.meeting_info.time or '未指定'}",
            f"- **主持人**: {minutes.meeting_info.host or '未指定'}",
            f"- **地点**: {minutes.meeting_info.location or '未指定'}",
        ]

        if minutes.meeting_info.participants:
            md_lines.append(f"- **参会人**: {', '.join(minutes.meeting_info.participants)}")

        if minutes.agenda:
            md_lines.extend(["", "## 📌 议程", ""])
            for i, item in enumerate(minutes.agenda, 1):
                md_lines.append(f"{i}. {item}")

        if minutes.discussion_points:
            md_lines.extend(["", "## 💬 讨论要点", ""])
            for point in minutes.discussion_points:
                md_lines.append(f"### {point.topic}")
                if point.speaker:
                    md_lines.append(f"*发言人: {point.speaker}*")
                md_lines.append(point.content)
                if point.key_points:
                    md_lines.append("**关键点:**")
                    for p in point.key_points:
                        md_lines.append(f"- {p}")
                md_lines.append("")

        if minutes.decisions:
            md_lines.extend(["", "## ✅ 决策", ""])
            for decision in minutes.decisions:
                md_lines.append(f"- {decision}")

        if minutes.action_items:
            md_lines.extend(["", "## 📎 待办事项", ""])
            md_lines.append("| 任务 | 负责人 | 截止时间 | 优先级 |")
            md_lines.append("|------|--------|----------|--------|")
            for item in minutes.action_items:
                md_lines.append(f"| {item.task} | {item.assignee or '-'} | {item.deadline or '-'} | {item.priority} |")

        if minutes.next_meeting:
            md_lines.extend(["", "## 📅 下次会议", ""])
            md_lines.append(f"- **时间**: {minutes.next_meeting.get('date', '')}")
            md_lines.append(f"- **议题**: {minutes.next_meeting.get('topic', '')}")

        md_lines.extend(["", "---", f"*生成时间: {minutes.generated_at}*"])

        return '\n'.join(md_lines)

    def to_dict(self, minutes: MeetingMinutes) -> Dict:
        """转换为字典"""
        return minutes.to_dict()

    def to_text(self, minutes: MeetingMinutes) -> str:
        """转换为纯文本"""
        lines = [
            f"{minutes.meeting_info.title or '会议纪要'}",
            f"日期: {minutes.meeting_info.date}",
            f"主持人: {minutes.meeting_info.host or '未指定'}",
            "",
            "【议程】"
        ]

        for i, item in enumerate(minutes.agenda, 1):
            lines.append(f"{i}. {item}")

        if minutes.discussion_points:
            lines.append("", "【讨论要点】")
            for point in minutes.discussion_points:
                lines.append(f"• {point.topic}")
                lines.append(f"  {point.content[:200]}")

        if minutes.decisions:
            lines.append("", "【决策】")
            for decision in minutes.decisions:
                lines.append(f"• {decision}")

        if minutes.action_items:
            lines.append("", "【待办】")
            for item in minutes.action_items:
                assignee = f" - {item.assignee}" if item.assignee else ""
                deadline = f" (截止: {item.deadline})" if item.deadline else ""
                lines.append(f"• {item.task}{assignee}{deadline}")

        return '\n'.join(lines)


def generate_meeting_minutes(
    text: str,
    meeting_date: Optional[str] = None,
    output_format: str = "dict"
) -> any:
    """快速生成会议纪要的便捷函数"""
    generator = MeetingMinutesGenerator()
    minutes = generator.generate_from_text(text, meeting_date)

    if output_format == "markdown":
        return generator.to_markdown(minutes)
    elif output_format == "text":
        return generator.to_text(minutes)
    else:
        return generator.to_dict(minutes)
