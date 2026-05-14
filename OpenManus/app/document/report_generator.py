"""
周报和工作汇报生成模块
自动生成日报、周报、月报
"""
from typing import List, Dict, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import re


@dataclass
class WorkItem:
    """工作项"""
    title: str
    description: str
    status: str = "completed"
    category: str = "general"
    hours_spent: Optional[float] = None
    tags: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict:
        return {
            'title': self.title,
            'description': self.description,
            'status': self.status,
            'category': self.category,
            'hours_spent': self.hours_spent,
            'tags': self.tags
        }


@dataclass
class Report:
    """工作报告"""
    title: str
    period: str
    report_type: str
    summary: str
    completed_items: List[WorkItem] = field(default_factory=list)
    in_progress_items: List[WorkItem] = field(default_factory=list)
    planned_items: List[WorkItem] = field(default_factory=list)
    metrics: Dict = field(default_factory=dict)
    challenges: List[str] = field(default_factory=list)
    next_plan: List[str] = field(default_factory=list)
    author: str = "DataAgent"

    def to_dict(self) -> Dict:
        return {
            'title': self.title,
            'period': self.period,
            'report_type': self.report_type,
            'summary': self.summary,
            'completed_items': [item.to_dict() for item in self.completed_items],
            'in_progress_items': [item.to_dict() for item in self.in_progress_items],
            'planned_items': [item.to_dict() for item in self.planned_items],
            'metrics': self.metrics,
            'challenges': self.challenges,
            'next_plan': self.next_plan,
            'author': self.author
        }


class ReportGenerator:
    """报告生成器"""

    TEMPLATES = {
        "daily": {
            "name": "日报",
            "sections": ["今日完成", "问题与建议", "明日计划"],
            "period_format": "%Y-%m-%d"
        },
        "weekly": {
            "name": "周报",
            "sections": ["本周完成", "本周进展", "下周计划", "工作指标", "问题与建议"],
            "period_format": "%Y-W%W"
        },
        "monthly": {
            "name": "月报",
            "sections": ["本月完成", "本月进展", "下月计划", "KPI完成情况", "问题与建议"],
            "period_format": "%Y-%m"
        }
    }

    def generate(
        self,
        work_items: List[WorkItem],
        report_type: str = "weekly",
        period_start: Optional[str] = None,
        period_end: Optional[str] = None,
        author: str = "DataAgent"
    ) -> Report:
        """生成工作报告"""
        template = self.TEMPLATES.get(report_type, self.TEMPLATES["weekly"])

        completed = [w for w in work_items if w.status == "completed"]
        in_progress = [w for w in work_items if w.status == "in_progress"]
        planned = [w for w in work_items if w.status == "planned"]

        summary = self._generate_summary(work_items, report_type)

        metrics = self._extract_metrics(work_items)

        challenges = self._identify_challenges(work_items)

        next_plan = self._generate_next_plan(work_items, report_type)

        period = self._format_period(period_start, period_end, report_type)

        report_title = f"{template['name']} - {period}"

        return Report(
            title=report_title,
            period=period,
            report_type=report_type,
            summary=summary,
            completed_items=completed,
            in_progress_items=in_progress,
            planned_items=planned,
            metrics=metrics,
            challenges=challenges,
            next_plan=next_plan,
            author=author
        )

    def _generate_summary(
        self,
        work_items: List[WorkItem],
        report_type: str
    ) -> str:
        """生成报告摘要"""
        total = len(work_items)
        completed = len([w for w in work_items if w.status == "completed"])

        total_hours = sum(w.hours_spent or 0 for w in work_items if w.hours_spent)

        if report_type == "daily":
            summary = f"今日完成了{completed}项工作任务"
        elif report_type == "weekly":
            summary = f"本周共完成{completed}/{total}项工作任务"
        else:
            summary = f"本月共完成{completed}/{total}项工作任务"

        if total_hours > 0:
            summary += f"，总工时{total_hours:.1f}小时"

        summary += "，整体进度符合预期。"

        return summary

    def _extract_metrics(self, work_items: List[WorkItem]) -> Dict:
        """提取工作指标"""
        total = len(work_items)
        completed = len([w for w in work_items if w.status == "completed"])

        total_hours = sum(w.hours_spent or 0 for w in work_items if w.hours_spent)

        by_category = {}
        for item in work_items:
            cat = item.category or "other"
            if cat not in by_category:
                by_category[cat] = {'total': 0, 'completed': 0}
            by_category[cat]['total'] += 1
            if item.status == "completed":
                by_category[cat]['completed'] += 1

        completion_rate = (completed / total * 100) if total > 0 else 0

        return {
            'total_items': total,
            'completed_count': completed,
            'in_progress_count': len([w for w in work_items if w.status == "in_progress"]),
            'total_hours': total_hours,
            'by_category': by_category,
            'completion_rate': f"{completion_rate:.1f}%"
        }

    def _identify_challenges(self, work_items: List[WorkItem]) -> List[str]:
        """识别挑战和问题"""
        challenges = []
        challenge_keywords = ['困难', '问题', '阻碍', '挑战', '风险', '阻塞']

        for item in work_items:
            text = f"{item.title} {item.description}"
            if any(kw in text for kw in challenge_keywords):
                challenges.append(item.description)

        return challenges[:5]

    def _generate_next_plan(
        self,
        work_items: List[WorkItem],
        report_type: str
    ) -> List[str]:
        """生成下一步计划"""
        planned = [w for w in work_items if w.status == "planned"]

        if planned:
            return [f"{i+1}. {item.title}" for i, item in enumerate(planned[:5])]

        return [f"{i+1}. 继续推进 {item.title}" for i, item in enumerate(work_items[:3])]

    def _format_period(
        self,
        start: Optional[str],
        end: Optional[str],
        report_type: str
    ) -> str:
        """格式化时间段"""
        if start and end:
            return f"{start} 至 {end}"

        today = datetime.now()

        if report_type == "daily":
            return today.strftime("%Y-%m-%d")
        elif report_type == "weekly":
            week_start = today - timedelta(days=today.weekday())
            week_end = week_start + timedelta(days=6)
            return f"{week_start.strftime('%m/%d')} - {week_end.strftime('%m/%d')}"
        else:
            return today.strftime("%Y年%m月")

    def to_markdown(self, report: Report) -> str:
        """转换为Markdown"""
        md_lines = [
            f"# {report.title}",
            "",
            f"**报告人**: {report.author}",
            f"**类型**: {report.report_type}",
            "",
            "---",
            "",
            "## 📊 工作概况",
            report.summary,
            ""
        ]

        if report.completed_items:
            md_lines.extend(["", "## ✅ 本期完成", ""])
            for item in report.completed_items:
                md_lines.append(f"### {item.title}")
                md_lines.append(item.description)
                if item.hours_spent:
                    md_lines.append(f"*工时: {item.hours_spent}h*")
                if item.category:
                    md_lines.append(f"*分类: {item.category}*")
                md_lines.append("")

        if report.in_progress_items:
            md_lines.extend(["", "## 🔄 进行中", ""])
            for item in report.in_progress_items:
                md_lines.append(f"- **{item.title}**")
                md_lines.append(f"  - {item.description}")

        if report.planned_items:
            md_lines.extend(["", "## 📋 下期计划", ""])
            for i, item in enumerate(report.planned_items, 1):
                md_lines.append(f"{i}. {item.title}")
                if item.description:
                    md_lines.append(f"   - {item.description}")

        if report.metrics:
            md_lines.extend(["", "## 📈 工作指标", ""])
            md_lines.append(f"- 总任务数: {report.metrics.get('total_items', 0)}")
            md_lines.append(f"- 已完成: {report.metrics.get('completed_count', 0)}")
            md_lines.append(f"- 进行中: {report.metrics.get('in_progress_count', 0)}")
            md_lines.append(f"- 总工时: {report.metrics.get('total_hours', 0)}h")
            md_lines.append(f"- 完成率: {report.metrics.get('completion_rate', '0%')}")

        if report.challenges:
            md_lines.extend(["", "## ⚠️ 问题与挑战", ""])
            for challenge in report.challenges:
                md_lines.append(f"- {challenge}")

        md_lines.extend(["", "---", f"*报告生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}*"])

        return '\n'.join(md_lines)

    def to_ppt(self, report: Report) -> bytes:
        """转换为PPT"""
        from app.document.ppt_generator import PPTGenerator

        generator = PPTGenerator()
        generator.create_presentation(report.title, report.author)

        generator.add_title_slide(
            report.title,
            f"{report.author} | {report.period}"
        )

        generator.add_content_slide("工作概况", [report.summary])

        if report.completed_items:
            completed_text = [f"{item.title}: {item.description[:50]}"
                            for item in report.completed_items[:5]]
            generator.add_content_slide("本期完成", completed_text)

        if report.in_progress_items:
            progress_text = [item.title for item in report.in_progress_items]
            generator.add_content_slide("进行中", progress_text)

        if report.planned_items:
            planned_text = [item.title for item in report.planned_items]
            generator.add_content_slide("下期计划", planned_text)

        if report.metrics:
            metrics_text = [
                f"总任务: {report.metrics.get('total_items', 0)}",
                f"已完成: {report.metrics.get('completed_count', 0)}",
                f"完成率: {report.metrics.get('completion_rate', '0%')}"
            ]
            generator.add_content_slide("工作指标", metrics_text)

        return generator.get_bytes()

    def to_dict(self, report: Report) -> Dict:
        """转换为字典"""
        return report.to_dict()


class TemplateReportGenerator:
    """基于模板的报告生成器"""

    TEMPLATES = {
        "standard": """# {title}

## 工作概况
{summary}

## 本期完成
{completed}

## 下期计划
{planned}

## 问题与建议
{challenges}
""",
        "detailed": """# {title}

**报告人**: {author}
**报告周期**: {period}
**报告类型**: {report_type}

---

## 📊 工作概况

{summary}

---

## ✅ 本期完成

{completed}

### 详细说明

{completed_details}

---

## 🔄 进行中

{in_progress}

---

## 📋 下期计划

{planned}

---

## 📈 工作指标

{metrics}

---

## ⚠️ 问题与挑战

{challenges}

---

*报告生成时间: {generated_time}*
"""
    }

    def generate_from_template(
        self,
        report: Report,
        template_name: str = "standard"
    ) -> str:
        """使用模板生成报告"""
        template = self.TEMPLATES.get(template_name, self.TEMPLATES["standard"])

        completed = '\n'.join([f"- {item.title}" for item in report.completed_items])
        completed_details = '\n'.join([f"**{item.title}**: {item.description}"
                                     for item in report.completed_items])
        in_progress = '\n'.join([f"- {item.title}" for item in report.in_progress_items])
        planned = '\n'.join([f"- {item.title}" for item in report.planned_items])
        challenges = '\n'.join([f"- {c}" for c in report.challenges]) if report.challenges else "- 无"

        metrics_parts = [
            f"- 总任务: {report.metrics.get('total_items', 0)}",
            f"- 已完成: {report.metrics.get('completed_count', 0)}",
            f"- 进行中: {report.metrics.get('in_progress_count', 0)}",
            f"- 完成率: {report.metrics.get('completion_rate', '0%')}"
        ]
        metrics = '\n'.join(metrics_parts)

        content = {
            'title': report.title,
            'author': report.author,
            'period': report.period,
            'report_type': report.report_type,
            'summary': report.summary,
            'completed': completed,
            'completed_details': completed_details or "- 无",
            'in_progress': in_progress or "- 无",
            'planned': planned or "- 暂无明确计划",
            'challenges': challenges,
            'metrics': metrics,
            'generated_time': datetime.now().strftime('%Y-%m-%d %H:%M')
        }

        try:
            return template.format(**content)
        except KeyError:
            return self.TEMPLATES["standard"].format(**{
                'title': report.title,
                'summary': report.summary,
                'completed': completed,
                'planned': planned,
                'challenges': challenges
            })


def generate_weekly_report(
    work_items: List[Dict],
    author: str = "DataAgent"
) -> str:
    """快速生成周报的便捷函数"""
    items = [WorkItem(**item) if isinstance(item, dict) else item
             for item in work_items]

    generator = ReportGenerator()
    report = generator.generate(items, report_type="weekly", author=author)

    template_gen = TemplateReportGenerator()
    return template_gen.generate_from_template(report, template_name="detailed")


def generate_daily_report(
    work_items: List[Dict],
    author: str = "DataAgent"
) -> str:
    """快速生成日报的便捷函数"""
    items = [WorkItem(**item) if isinstance(item, dict) else item
             for item in work_items]

    generator = ReportGenerator()
    report = generator.generate(items, report_type="daily", author=author)

    return generator.to_markdown(report)


def generate_monthly_report(
    work_items: List[Dict],
    author: str = "DataAgent"
) -> str:
    """快速生成月报的便捷函数"""
    items = [WorkItem(**item) if isinstance(item, dict) else item
             for item in work_items]

    generator = ReportGenerator()
    report = generator.generate(items, report_type="monthly", author=author)

    template_gen = TemplateReportGenerator()
    return template_gen.generate_from_template(report, template_name="detailed")
