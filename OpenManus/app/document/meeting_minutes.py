"""
会议纪要生成模块
自动从文本生成结构化的会议纪要
支持AI增强分析和多语言处理
"""
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, field, asdict
from datetime import datetime
import re
from enum import Enum


class LanguageCode(str, Enum):
    """支持的语言代码"""
    ZH = "zh"
    EN = "en"
    JA = "ja"
    KO = "ko"


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
    language: str = LanguageCode.ZH

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
    sentiment: str = "neutral"
    importance: int = 3

    def to_dict(self) -> Dict:
        return {
            'topic': self.topic,
            'speaker': self.speaker,
            'content': self.content,
            'key_points': self.key_points,
            'timestamp': self.timestamp,
            'sentiment': self.sentiment,
            'importance': self.importance
        }


@dataclass
class ActionItem:
    """待办事项"""
    task: str = ""
    assignee: str = ""
    deadline: str = ""
    priority: str = "medium"
    status: str = "pending"
    category: str = "general"

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
    summary: str = ""
    key_insights: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict:
        return {
            'meeting_info': self.meeting_info.to_dict(),
            'agenda': self.agenda,
            'discussion_points': [dp.to_dict() for dp in self.discussion_points],
            'decisions': self.decisions,
            'action_items': [ai.to_dict() for ai in self.action_items],
            'next_meeting': self.next_meeting,
            'generated_at': self.generated_at,
            'summary': self.summary,
            'key_insights': self.key_insights
        }


class MeetingMinutesGenerator:
    """会议纪要生成器"""

    def __init__(self):
        self.action_keywords = {
            'zh': ['待办', 'TODO', '任务', '负责', '完成', '截止', 'action', '行动项'],
            'en': ['todo', 'task', 'action', 'responsible', 'complete', 'deadline', 'due'],
            'ja': ['タスク', 'やること', '期限', '担当'],
            'ko': ['할 일', '과제', '마감', '담당']
        }
        self.decision_keywords = {
            'zh': ['决定', '通过', '批准', '同意', '确认', '决策', '共识', '决议'],
            'en': ['decide', 'approve', 'agree', 'confirm', 'resolve', 'decision'],
            'ja': ['決定', '承認', '同意', '確認'],
            'ko': ['결정', '승인', '동의', '확인']
        }
        self.person_keywords = {
            'zh': ['说', '表示', '指出', '认为', '提出', '强调'],
            'en': ['said', 'stated', 'pointed', 'argued', 'suggested'],
            'ja': ['言った', '述べた', '指摘した', '提案した'],
            'ko': ['말했다', '지적했다', '제안했다']
        }
        self.agenda_keywords = {
            'zh': ['议程', 'Agenda', '会议议题', '日程', '议题'],
            'en': ['agenda', 'topic', 'schedule', 'item'],
            'ja': ['議題', 'アジェンダ', '日程'],
            'ko': ['의제', '일정']
        }
        self.discussion_keywords = {
            'zh': ['讨论', '认为', '表示', '提出', '谈及', '指出', '讨论要点'],
            'en': ['discuss', 'discussion', 'talked', 'debated'],
            'ja': ['討論', '話し合い', '議論'],
            'ko': ['토론', '논의']
        }

    def _detect_language(self, text: str) -> str:
        """检测文本语言"""
        zh_chars = re.findall(r'[\u4e00-\u9fff]', text)
        ja_chars = re.findall(r'[\u3040-\u30ff]', text)
        ko_chars = re.findall(r'[\uac00-\ud7af]', text)
        
        if len(zh_chars) > len(ja_chars) and len(zh_chars) > len(ko_chars):
            return LanguageCode.ZH
        elif len(ja_chars) > len(zh_chars) and len(ja_chars) > len(ko_chars):
            return LanguageCode.JA
        elif len(ko_chars) > len(zh_chars) and len(ko_chars) > len(ja_chars):
            return LanguageCode.KO
        else:
            if re.search(r'[a-zA-Z]', text):
                return LanguageCode.EN
            return LanguageCode.ZH

    def generate_from_text(
        self,
        text: str,
        meeting_date: Optional[str] = None,
        language: Optional[str] = None
    ) -> MeetingMinutes:
        """从文本生成会议纪要"""
        detected_lang = language or self._detect_language(text)
        
        meeting_info = self._extract_meeting_info(text, meeting_date, detected_lang)
        meeting_info.language = detected_lang
        
        agenda = self._extract_agenda(text, detected_lang)
        discussion_points = self._extract_discussions(text, detected_lang)
        decisions = self._extract_decisions(text, detected_lang)
        action_items = self._extract_action_items(text, detected_lang)
        
        summary = self._generate_summary(meeting_info, agenda, discussion_points, decisions, action_items, detected_lang)
        key_insights = self._extract_key_insights(discussion_points, decisions, action_items, detected_lang)

        return MeetingMinutes(
            meeting_info=meeting_info,
            agenda=agenda,
            discussion_points=discussion_points,
            decisions=decisions,
            action_items=action_items,
            next_meeting=self._extract_next_meeting(text, detected_lang),
            generated_at=datetime.now().isoformat(),
            summary=summary,
            key_insights=key_insights
        )

    def _extract_meeting_info(
        self,
        text: str,
        meeting_date: Optional[str],
        lang: str
    ) -> MeetingInfo:
        """提取会议基本信息"""
        info = MeetingInfo()
        info.date = meeting_date or datetime.now().strftime("%Y-%m-%d")

        lines = text.split('\n')
        text_sample = '\n'.join(lines[:30])

        title_patterns = [
            r'会议[主题标题][：:]\s*(.+?)(?:\n|$)',
            r'#\s*(.+?)(?:\n|$)',
            r'^(.{5,50})(?:\n|$)',
            r'Meeting[\s_]*(?:Title|Topic)[：:]\s*(.+?)(?:\n|$)',
            r'議事[\s_]*(?:録|題目)[：:]\s*(.+?)(?:\n|$)',
            r'회의[\s_]*(?:제목|주제)[：:]\s*(.+?)(?:\n|$)'
        ]

        for pattern in title_patterns:
            match = re.search(pattern, text_sample, re.MULTILINE)
            if match:
                title = match.group(1).strip()
                if len(title) > 5 and len(title) < 150:
                    info.title = title
                    break

        date_patterns = [
            r'(\d{4}[-/年]\d{1,2}[-/月]\d{1,2}日?)',
            r'(\d{1,2}[-/月]\d{1,2}日?)',
            r'(\d{4}-\d{2}-\d{2})',
            r'(\d{4}/\d{2}/\d{2})'
        ]

        for pattern in date_patterns:
            match = re.search(pattern, text_sample)
            if match:
                info.date = match.group(1)
                break

        time_pattern = r'(\d{1,2}:\d{2}(?::\d{2})?)\s*[-~至]\s*(\d{1,2}:\d{2}(?::\d{2})?)'
        match = re.search(time_pattern, text_sample)
        if match:
            info.time = f"{match.group(1)} - {match.group(2)}"
            info.duration = self._calculate_duration(match.group(1), match.group(2))
        else:
            time_pattern_single = r'(\d{1,2}:\d{2}(?::\d{2})?)'
            match = re.search(time_pattern_single, text_sample)
            if match:
                info.time = match.group(1)

        host_patterns = [
            r'主持人[：:]\s*(.+?)(?:\n|$)',
            r'主持[：:]\s*(.+?)(?:\n|$)',
            r'Host[：:]\s*(.+?)(?:\n|$)',
            r'Chair[：:]\s*(.+?)(?:\n|$)',
            r'司会者[：:]\s*(.+?)(?:\n|$)',
            r'사회자[：:]\s*(.+?)(?:\n|$)'
        ]

        for pattern in host_patterns:
            match = re.search(pattern, text_sample)
            if match:
                info.host = match.group(1).strip()
                break

        participant_patterns = [
            r'参会[人员者][：:]\s*(.+?)(?:\n|$)',
            r'参与[人员][：:]\s*(.+?)(?:\n|$)',
            r'Participants[：:]\s*(.+?)(?:\n|$)',
            r'Attendees[：:]\s*(.+?)(?:\n|$)',
            r'出席者[：:]\s*(.+?)(?:\n|$)',
            r'참석자[：:]\s*(.+?)(?:\n|$)'
        ]

        for pattern in participant_patterns:
            match = re.search(pattern, text_sample)
            if match:
                participants_text = match.group(1)
                separators = r'[,，、;；\n]'
                info.participants = [p.strip() for p in re.split(separators, participants_text) if p.strip()]
                break

        location_patterns = [
            r'地点[：:]\s*(.+?)(?:\n|$)',
            r'Location[：:]\s*(.+?)(?:\n|$)',
            r'場所[：:]\s*(.+?)(?:\n|$)',
            r'장소[：:]\s*(.+?)(?:\n|$)'
        ]

        for pattern in location_patterns:
            match = re.search(pattern, text_sample)
            if match:
                info.location = match.group(1).strip()
                break

        return info

    def _calculate_duration(self, start_time: str, end_time: str) -> str:
        """计算会议时长"""
        try:
            start = datetime.strptime(start_time, '%H:%M')
            end = datetime.strptime(end_time, '%H:%M')
            delta = end - start
            hours = delta.seconds // 3600
            minutes = (delta.seconds % 3600) // 60
            if hours > 0:
                return f"{hours}小时{minutes}分钟"
            return f"{minutes}分钟"
        except:
            return ""

    def _extract_agenda(self, text: str, lang: str) -> List[str]:
        """提取议程"""
        agenda = []
        lines = text.split('\n')
        keywords = self.agenda_keywords.get(lang, self.agenda_keywords['zh'])

        in_agenda_section = False

        for line in lines:
            line = line.strip()

            if any(kw.lower() in line.lower() for kw in keywords):
                in_agenda_section = True
                continue

            if in_agenda_section:
                if not line:
                    if len(agenda) >= 3:
                        break
                    continue

                if line.startswith(('#', '##', '###')) or any(kw in line for kw in keywords):
                    continue

                bullet_patterns = r'^[\d\.\s•\-·▸●*]+'
                if re.match(bullet_patterns, line):
                    item = re.sub(bullet_patterns, '', line).strip()
                    if item and len(item) > 2:
                        agenda.append(item)
                elif len(line) > 5 and len(line) < 200:
                    if not any(kw in line for kw in ['讨论', '决定', '待办', 'discussion', 'decision', 'todo']):
                        agenda.append(line)

                if len(agenda) >= 10:
                    break

        return agenda[:10]

    def _extract_discussions(self, text: str, lang: str) -> List[DiscussionPoint]:
        """提取讨论要点"""
        discussions = []
        paragraphs = re.split(r'\n\n+', text)
        keywords = self.discussion_keywords.get(lang, self.discussion_keywords['zh'])

        for para in paragraphs:
            para = para.strip()
            if len(para) < 30:
                continue

            para_lines = para.split('\n')
            first_line = para_lines[0].strip()

            if any(kw in para for kw in keywords):
                topic = first_line[:100] if len(first_line) > 100 else first_line
                speaker = self._extract_speaker(para, lang)
                key_points = self._extract_key_points_from_text(para)
                sentiment = self._analyze_sentiment(para)
                importance = self._calculate_importance(para)

                discussions.append(DiscussionPoint(
                    topic=topic,
                    speaker=speaker,
                    content=para[:800],
                    key_points=key_points,
                    sentiment=sentiment,
                    importance=importance
                ))

            if len(discussions) >= 15:
                break

        return discussions

    def _extract_speaker(self, text: str, lang: str) -> Optional[str]:
        """提取发言人"""
        patterns = [
            r'([\u4e00-\u9fff]{2,4})[说表示指出认为提出]',
            r'([\u4e00-\u9fff]{2,4})[:：]',
            r'发言人[：:]\s*([\u4e00-\u9fff]+)',
            r'([A-Z][a-zA-Z]+)\s*[：:]',
            r'([A-Z][a-zA-Z]+)\s+said',
            r'([\u3040-\u30ff]{2,})[：:]',
            r'([\uac00-\ud7af]{2,})[：:]'
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
            r'[-•·*]\s*(.+?)(?:\n|$)',
            r'(\d+)[.、)](.+?)(?:\n|$)',
        ]

        for pattern in bullet_patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                point = match if isinstance(match, str) else match[-1]
                point = point.strip()
                if len(point) > 5 and len(point) < 200 and point not in points:
                    points.append(point)

                if len(points) >= 8:
                    break

        return points[:8]

    def _analyze_sentiment(self, text: str) -> str:
        """分析情感倾向"""
        positive_words = ['好', '优秀', '成功', '达成', '满意', '支持', '赞同', 'good', 'great', 'excellent', 'success']
        negative_words = ['问题', '困难', '失败', '担忧', '反对', '风险', 'bad', 'problem', 'difficult', 'fail']
        
        positive_count = sum(1 for word in positive_words if word in text.lower())
        negative_count = sum(1 for word in negative_words if word in text.lower())
        
        if positive_count > negative_count:
            return "positive"
        elif negative_count > positive_count:
            return "negative"
        return "neutral"

    def _calculate_importance(self, text: str) -> int:
        """计算重要性评分(1-5)"""
        score = 3
        important_words = ['重要', '关键', '核心', '必须', '紧急', '重点', 'critical', 'important', 'key', 'must']
        
        for word in important_words:
            if word in text:
                score += 1
        
        if len(text) > 500:
            score += 1
            
        return min(score, 5)

    def _extract_decisions(self, text: str, lang: str) -> List[str]:
        """提取决策"""
        decisions = []
        lines = text.split('\n')
        keywords = self.decision_keywords.get(lang, self.decision_keywords['zh'])

        for line in lines:
            line = line.strip()
            if not line or len(line) < 8:
                continue

            if any(kw in line for kw in keywords):
                decision = re.sub(r'^[#\d\.\s]+', '', line).strip()
                if decision:
                    decisions.append(decision)

            if len(decisions) >= 12:
                break

        return decisions

    def _extract_action_items(self, text: str, lang: str) -> List[ActionItem]:
        """提取待办事项"""
        action_items = []
        lines = text.split('\n')
        keywords = self.action_keywords.get(lang, self.action_keywords['zh'])

        for line in lines:
            line = line.strip()
            if not line or len(line) < 8:
                continue

            if any(kw.lower() in line.lower() for kw in keywords):
                task = self._clean_action_task(line)
                if task:
                    assignee = self._extract_assignee(task, lang)
                    deadline = self._extract_deadline(task)
                    priority = self._extract_priority(task)
                    category = self._classify_task(task)

                    action_items.append(ActionItem(
                        task=task,
                        assignee=assignee,
                        deadline=deadline,
                        priority=priority,
                        category=category
                    ))

            if len(action_items) >= 15:
                break

        return action_items

    def _clean_action_task(self, line: str) -> str:
        """清理任务文本"""
        task = re.sub(r'^[#待办TODO任务action\s]+', '', line, flags=re.IGNORECASE)
        task = re.sub(r'^\d+[.、]\s*', '', task)
        task = task.strip(':-： ')
        return task

    def _extract_assignee(self, text: str, lang: str) -> str:
        """提取负责人"""
        patterns = [
            r'负责人[：:]\s*([\u4e00-\u9fff]{2,4})',
            r'负责[：:]\s*([\u4e00-\u9fff]{2,4})',
            r'由\s*([\u4e00-\u9fff]{2,4})\s*负责',
            r'([\u4e00-\u9fff]{2,4})\s*负责',
            r'负责\s*([A-Za-z]+)',
            r'([A-Za-z]+)\s*负责',
            r'Assignee[：:]\s*([A-Za-z]+)',
            r'担当[：:]\s*([\u3040-\u30ff]{2,})',
            r'담당[：:]\s*([\uac00-\ud7af]{2,})'
        ]

        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(1)

        return ""

    def _extract_deadline(self, text: str) -> str:
        """提取截止时间"""
        patterns = [
            r'截止[到时间][：:]\s*(\d{1,2}[月/\-]\d{1,2}[日号]?)',
            r'截止[到]?\s*(\d{1,2}[月/\-]\d{1,2}[日号]?)',
            r'(\d{1,2}[月/\-]\d{1,2}[日号]?)前',
            r'周([一二三四五六日])',
            r'Deadline[：:]\s*(\d{4}-\d{2}-\d{2})',
            r'Due[：:]\s*(\d{4}-\d{2}-\d{2})',
            r'期限[：:]\s*(\d{1,2}月\d{1,2}日)',
            r'마감[：:]\s*(\d{1,2}월\d{1,2}일)'
        ]

        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(1)

        return ""

    def _extract_priority(self, text: str) -> str:
        """提取优先级"""
        high_patterns = ['紧急', '高优先', '立刻', '马上', 'urgent', 'high', 'priority']
        low_patterns = ['低优先', '稍后', '不急', 'low', 'later']
        
        if any(p in text.lower() for p in high_patterns):
            return "high"
        elif any(p in text.lower() for p in low_patterns):
            return "low"
        return "medium"

    def _classify_task(self, text: str) -> str:
        """分类任务类型"""
        categories = {
            '文档': ['文档', '报告', '文档编写', 'report', 'document'],
            '开发': ['开发', '代码', '实现', 'develop', 'code', 'implement'],
            '测试': ['测试', '验证', 'test', 'verify'],
            '会议': ['会议', '讨论', 'meeting', 'discuss'],
            '调研': ['调研', '研究', 'research', 'investigate'],
            '设计': ['设计', 'design']
        }
        
        for category, keywords in categories.items():
            if any(kw in text.lower() for kw in keywords):
                return category
        return "general"

    def _extract_next_meeting(self, text: str, lang: str) -> Optional[Dict]:
        """提取下次会议信息"""
        patterns = [
            r'下次会议[：:]\s*(.+?)(?:\n|$)',
            r'下次[：:]\s*(.+?)(?:\n|$)',
            r'Next meeting[：:]\s*(.+?)(?:\n|$)',
            r'次回[：:]\s*(.+?)(?:\n|$)',
            r'다음 회의[：:]\s*(.+?)(?:\n|$)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                content = match.group(1)
                date_match = re.search(r'(\d{4}[-/年]\d{1,2}[-/月]\d{1,2}日?)', content)
                topic_match = re.search(r'[议题主题Topic][：:]\s*(.+?)(?:\s|$)', content)
                return {
                    'date': date_match.group(1) if date_match else '',
                    'topic': topic_match.group(1) if topic_match else ''
                }
        
        return None

    def _generate_summary(
        self,
        meeting_info: MeetingInfo,
        agenda: List[str],
        discussions: List[DiscussionPoint],
        decisions: List[str],
        action_items: List[ActionItem],
        lang: str
    ) -> str:
        """生成会议总结"""
        parts = []
        
        if lang == LanguageCode.ZH:
            if meeting_info.title:
                parts.append(f"本次{meeting_info.title}于{meeting_info.date}召开")
            else:
                parts.append(f"本次会议于{meeting_info.date}召开")
            
            if agenda:
                parts.append(f"共讨论了{len(agenda)}个议题")
            
            if discussions:
                important_discussions = [d for d in discussions if d.importance >= 4]
                if important_discussions:
                    parts.append(f"重点讨论了{len(important_discussions)}个关键问题")
            
            if decisions:
                parts.append(f"达成了{len(decisions)}项决议")
            
            if action_items:
                high_priority = [a for a in action_items if a.priority == "high"]
                parts.append(f"确定了{len(action_items)}项待办事项，其中{len(high_priority)}项为高优先级")
        else:
            if meeting_info.title:
                parts.append(f"The {meeting_info.title} meeting was held on {meeting_info.date}")
            else:
                parts.append(f"The meeting was held on {meeting_info.date}")
            
            if agenda:
                parts.append(f"{len(agenda)} topics were discussed")
            
            if discussions:
                important_discussions = [d for d in discussions if d.importance >= 4]
                if important_discussions:
                    parts.append(f"{len(important_discussions)} key issues were highlighted")
            
            if decisions:
                parts.append(f"{len(decisions)} decisions were made")
            
            if action_items:
                high_priority = [a for a in action_items if a.priority == "high"]
                parts.append(f"{len(action_items)} action items were identified, {len(high_priority)} of which are high priority")
        
        return "。".join(parts) + "。"

    def _extract_key_insights(
        self,
        discussions: List[DiscussionPoint],
        decisions: List[str],
        action_items: List[ActionItem],
        lang: str
    ) -> List[str]:
        """提取关键洞察"""
        insights = []
        
        if lang == LanguageCode.ZH:
            positive_discussions = [d for d in discussions if d.sentiment == "positive"]
            if positive_discussions:
                insights.append(f"{len(positive_discussions)}个讨论点呈现积极态势")
            
            high_priority_items = [a for a in action_items if a.priority == "high"]
            if high_priority_items:
                insights.append(f"有{len(high_priority_items)}项高优先级任务需要处理")
            
            if decisions:
                insights.append("会议达成了明确的决策共识")
        else:
            positive_discussions = [d for d in discussions if d.sentiment == "positive"]
            if positive_discussions:
                insights.append(f"{len(positive_discussions)} discussion points showed positive sentiment")
            
            high_priority_items = [a for a in action_items if a.priority == "high"]
            if high_priority_items:
                insights.append(f"{len(high_priority_items)} high-priority action items need attention")
            
            if decisions:
                insights.append("Clear decisions were reached in the meeting")
        
        return insights

    def to_markdown(self, minutes: MeetingMinutes) -> str:
        """转换为Markdown格式"""
        lang = minutes.meeting_info.language
        
        if lang == LanguageCode.ZH:
            title_prefix = "会议纪要"
            info_title = "📋 会议信息"
            agenda_title = "📌 议程"
            discussion_title = "💬 讨论要点"
            decisions_title = "✅ 决策"
            action_title = "📎 待办事项"
            next_title = "📅 下次会议"
            summary_title = "📊 会议总结"
            insights_title = "💡 关键洞察"
        elif lang == LanguageCode.EN:
            title_prefix = "Meeting Minutes"
            info_title = "📋 Meeting Information"
            agenda_title = "📌 Agenda"
            discussion_title = "💬 Discussion Points"
            decisions_title = "✅ Decisions"
            action_title = "📎 Action Items"
            next_title = "📅 Next Meeting"
            summary_title = "📊 Meeting Summary"
            insights_title = "💡 Key Insights"
        elif lang == LanguageCode.JA:
            title_prefix = "議事録"
            info_title = "📋 会議情報"
            agenda_title = "📌 議題"
            discussion_title = "💬 議論要点"
            decisions_title = "✅ 決定事項"
            action_title = "📎 アクションアイテム"
            next_title = "📅 次回の会議"
            summary_title = "📊 会議まとめ"
            insights_title = "💡 重要な洞察"
        else:
            title_prefix = "회의록"
            info_title = "📋 회의 정보"
            agenda_title = "📌 의제"
            discussion_title = "💬 토론 내용"
            decisions_title = "✅ 결정 사항"
            action_title = "📎 행동 항목"
            next_title = "📅 다음 회의"
            summary_title = "📊 회의 요약"
            insights_title = "💡 핵심 인사이트"

        md_lines = [
            f"# {minutes.meeting_info.title or title_prefix}",
            "",
            info_title,
            f"- **{('日期' if lang == LanguageCode.ZH else 'Date' if lang == LanguageCode.EN else '日付' if lang == LanguageCode.JA else '날짜')}**: {minutes.meeting_info.date}",
            f"- **{('时间' if lang == LanguageCode.ZH else 'Time' if lang == LanguageCode.EN else '時間' if lang == LanguageCode.JA else '시간')}**: {minutes.meeting_info.time or ('未指定' if lang == LanguageCode.ZH else 'Not specified' if lang == LanguageCode.EN else '未指定' if lang == LanguageCode.JA else '지정되지 않음')}",
            f"- **{('主持人' if lang == LanguageCode.ZH else 'Host' if lang == LanguageCode.EN else '司会者' if lang == LanguageCode.JA else '사회자')}**: {minutes.meeting_info.host or ('未指定' if lang == LanguageCode.ZH else 'Not specified' if lang == LanguageCode.EN else '未指定' if lang == LanguageCode.JA else '지정되지 않음')}",
            f"- **{('地点' if lang == LanguageCode.ZH else 'Location' if lang == LanguageCode.EN else '場所' if lang == LanguageCode.JA else '장소')}**: {minutes.meeting_info.location or ('未指定' if lang == LanguageCode.ZH else 'Not specified' if lang == LanguageCode.EN else '未指定' if lang == LanguageCode.JA else '지정되지 않음')}",
        ]

        if minutes.meeting_info.participants:
            participant_label = ('参会人' if lang == LanguageCode.ZH else 'Participants' if lang == LanguageCode.EN else '出席者' if lang == LanguageCode.JA else '참석자')
            md_lines.append(f"- **{participant_label}**: {', '.join(minutes.meeting_info.participants)}")

        if minutes.meeting_info.duration:
            duration_label = ('时长' if lang == LanguageCode.ZH else 'Duration' if lang == LanguageCode.EN else '所要時間' if lang == LanguageCode.JA else '기간')
            md_lines.append(f"- **{duration_label}**: {minutes.meeting_info.duration}")

        if minutes.agenda:
            md_lines.extend(["", agenda_title, ""])
            for i, item in enumerate(minutes.agenda, 1):
                md_lines.append(f"{i}. {item}")

        if minutes.discussion_points:
            md_lines.extend(["", discussion_title, ""])
            for point in minutes.discussion_points:
                md_lines.append(f"### {point.topic}")
                if point.speaker:
                    speaker_label = ('发言人' if lang == LanguageCode.ZH else 'Speaker' if lang == LanguageCode.EN else '発言者' if lang == LanguageCode.JA else '발언자')
                    importance_stars = '⭐' * point.importance
                    md_lines.append(f"*{speaker_label}: {point.speaker} | {importance_stars}*")
                md_lines.append(point.content)
                if point.key_points:
                    md_lines.append("**关键点:**")
                    for p in point.key_points:
                        md_lines.append(f"- {p}")
                md_lines.append("")

        if minutes.decisions:
            md_lines.extend(["", decisions_title, ""])
            for decision in minutes.decisions:
                md_lines.append(f"- {decision}")

        if minutes.action_items:
            md_lines.extend(["", action_title, ""])
            headers = [
                ('任务' if lang == LanguageCode.ZH else 'Task' if lang == LanguageCode.EN else 'タスク' if lang == LanguageCode.JA else '과제'),
                ('负责人' if lang == LanguageCode.ZH else 'Assignee' if lang == LanguageCode.EN else '担当者' if lang == LanguageCode.JA else '담당자'),
                ('截止时间' if lang == LanguageCode.ZH else 'Deadline' if lang == LanguageCode.EN else '期限' if lang == LanguageCode.JA else '마감일'),
                ('优先级' if lang == LanguageCode.ZH else 'Priority' if lang == LanguageCode.EN else '優先度' if lang == LanguageCode.JA else '우선순위'),
                ('分类' if lang == LanguageCode.ZH else 'Category' if lang == LanguageCode.EN else 'カテゴリ' if lang == LanguageCode.JA else '카테고리')
            ]
            md_lines.append(f"| {' | '.join(headers)} |")
            md_lines.append("| " + " | ".join(['------'] * len(headers)) + " |")
            for item in minutes.action_items:
                md_lines.append(f"| {item.task} | {item.assignee or '-'} | {item.deadline or '-'} | {item.priority} | {item.category} |")

        if minutes.next_meeting:
            md_lines.extend(["", next_title, ""])
            date_label = ('时间' if lang == LanguageCode.ZH else 'Date' if lang == LanguageCode.EN else '日付' if lang == LanguageCode.JA else '날짜')
            topic_label = ('议题' if lang == LanguageCode.ZH else 'Topic' if lang == LanguageCode.EN else '議題' if lang == LanguageCode.JA else '주제')
            md_lines.append(f"- **{date_label}**: {minutes.next_meeting.get('date', '')}")
            md_lines.append(f"- **{topic_label}**: {minutes.next_meeting.get('topic', '')}")

        if minutes.summary:
            md_lines.extend(["", summary_title, ""])
            md_lines.append(minutes.summary)

        if minutes.key_insights:
            md_lines.extend(["", insights_title, ""])
            for insight in minutes.key_insights:
                md_lines.append(f"- {insight}")

        md_lines.extend(["", "---", f"*{'生成时间' if lang == LanguageCode.ZH else 'Generated at' if lang == LanguageCode.EN else '生成時間' if lang == LanguageCode.JA else '생성 시간'}: {minutes.generated_at}*"])

        return '\n'.join(md_lines)

    def to_dict(self, minutes: MeetingMinutes) -> Dict:
        """转换为字典"""
        return minutes.to_dict()

    def to_text(self, minutes: MeetingMinutes) -> str:
        """转换为纯文本"""
        lang = minutes.meeting_info.language
        
        if lang == LanguageCode.ZH:
            lines = [
                f"{minutes.meeting_info.title or '会议纪要'}",
                f"日期: {minutes.meeting_info.date}",
                f"主持人: {minutes.meeting_info.host or '未指定'}",
                "",
                "【议程】"
            ]
        elif lang == LanguageCode.EN:
            lines = [
                f"{minutes.meeting_info.title or 'Meeting Minutes'}",
                f"Date: {minutes.meeting_info.date}",
                f"Host: {minutes.meeting_info.host or 'Not specified'}",
                "",
                "[Agenda]"
            ]
        elif lang == LanguageCode.JA:
            lines = [
                f"{minutes.meeting_info.title or '議事録'}",
                f"日付: {minutes.meeting_info.date}",
                f"司会者: {minutes.meeting_info.host or '未指定'}",
                "",
                "【議題】"
            ]
        else:
            lines = [
                f"{minutes.meeting_info.title or '회의록'}",
                f"날짜: {minutes.meeting_info.date}",
                f"사회자: {minutes.meeting_info.host or '지정되지 않음'}",
                "",
                "【의제】"
            ]

        for i, item in enumerate(minutes.agenda, 1):
            lines.append(f"{i}. {item}")

        if minutes.discussion_points:
            section_label = ('【讨论要点】' if lang == LanguageCode.ZH else '[Discussion Points]' if lang == LanguageCode.EN else '【議論要点】' if lang == LanguageCode.JA else '【토론 내용】')
            lines.append("", section_label)
            for point in minutes.discussion_points:
                lines.append(f"• {point.topic}")
                lines.append(f"  {point.content[:200]}")

        if minutes.decisions:
            section_label = ('【决策】' if lang == LanguageCode.ZH else '[Decisions]' if lang == LanguageCode.EN else '【決定事項】' if lang == LanguageCode.JA else '【결정 사항】')
            lines.append("", section_label)
            for decision in minutes.decisions:
                lines.append(f"• {decision}")

        if minutes.action_items:
            section_label = ('【待办】' if lang == LanguageCode.ZH else '[Action Items]' if lang == LanguageCode.EN else '【アクションアイテム】' if lang == LanguageCode.JA else '【행동 항목】')
            lines.append("", section_label)
            for item in minutes.action_items:
                assignee = f" - {item.assignee}" if item.assignee else ""
                deadline = f" ({('截止' if lang == LanguageCode.ZH else 'Due' if lang == LanguageCode.EN else '期限' if lang == LanguageCode.JA else '마감')}: {item.deadline})" if item.deadline else ""
                lines.append(f"• {item.task}{assignee}{deadline}")

        return '\n'.join(lines)


def generate_meeting_minutes(
    text: str,
    meeting_date: Optional[str] = None,
    language: Optional[str] = None,
    output_format: str = "dict"
) -> any:
    """快速生成会议纪要的便捷函数"""
    generator = MeetingMinutesGenerator()
    minutes = generator.generate_from_text(text, meeting_date, language)

    if output_format == "markdown":
        return generator.to_markdown(minutes)
    elif output_format == "text":
        return generator.to_text(minutes)
    else:
        return generator.to_dict(minutes)