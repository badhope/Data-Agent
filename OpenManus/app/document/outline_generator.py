"""
提纲生成模块
智能生成文章结构和内容大纲
"""
from typing import List, Dict, Optional
from dataclasses import dataclass, field, asdict
import re


@dataclass
class OutlineNode:
    """提纲节点"""
    title: str
    level: int = 1
    children: List['OutlineNode'] = field(default_factory=list)
    content_hint: str = ""
    word_count: int = 0

    def to_dict(self) -> Dict:
        return {
            'title': self.title,
            'level': self.level,
            'content_hint': self.content_hint,
            'word_count': self.word_count,
            'children': [child.to_dict() for child in self.children]
        }

    def flatten(self) -> List['OutlineNode']:
        """展开为扁平列表"""
        result = [self]
        for child in self.children:
            result.extend(child.flatten())
        return result


@dataclass
class OutlineResult:
    """提纲生成结果"""
    title: str
    nodes: List[OutlineNode]
    word_count_estimate: int
    sections: int
    depth: int

    def to_dict(self) -> Dict:
        return {
            'title': self.title,
            'nodes': [node.to_dict() for node in self.nodes],
            'word_count_estimate': self.word_count_estimate,
            'sections': self.sections,
            'depth': self.depth
        }


class OutlineGenerator:
    """提纲生成器"""

    def __init__(self):
        self.templates = {
            'general': {
                'name': '通用文章',
                'structure': ['引言', '主体', '结论']
            },
            'academic': {
                'name': '学术论文',
                'structure': ['引言', '相关工作', '方法', '实验结果', '讨论', '结论']
            },
            'report': {
                'name': '工作报告',
                'structure': ['概述', '完成情况', '问题分析', '下一步计划']
            },
            'story': {
                'name': '故事创作',
                'structure': ['开端', '发展', '高潮', '结局']
            },
            'business': {
                'name': '商业提案',
                'structure': ['项目概述', '市场分析', '解决方案', '实施计划', '预算', '风险评估']
            },
            'essay': {
                'name': '议论文',
                'structure': ['引言', '论点一', '论点二', '论点三', '结论']
            }
        }

    def generate(
        self,
        topic: str,
        document_type: str = 'general',
        depth: int = 3,
        sections_per_level: int = 3
    ) -> OutlineResult:
        """
        生成提纲

        Args:
            topic: 主题
            document_type: 文档类型
            depth: 提纲深度
            sections_per_level: 每级节数

        Returns:
            OutlineResult: 提纲结果
        """
        template = self.templates.get(document_type, self.templates['general'])
        nodes = []

        for i, section in enumerate(template['structure'], 1):
            node = self._create_node(section, 1, topic)
            if depth > 1:
                node.children = self._generate_subsections(
                    section, topic, 2, depth, sections_per_level
                )
            nodes.append(node)

        return OutlineResult(
            title=topic,
            nodes=nodes,
            word_count_estimate=self._estimate_word_count(nodes),
            sections=self._count_sections(nodes),
            depth=depth
        )

    def _create_node(self, title: str, level: int, topic: str) -> OutlineNode:
        """创建节点"""
        content_hint = self._generate_content_hint(title, topic)
        word_count = self._estimate_section_words(level)
        return OutlineNode(
            title=title,
            level=level,
            content_hint=content_hint,
            word_count=word_count
        )

    def _generate_subsections(
        self,
        parent_title: str,
        topic: str,
        level: int,
        max_depth: int,
        sections_per_level: int
    ) -> List[OutlineNode]:
        """生成子节"""
        if level >= max_depth:
            return []

        subsections = self._get_subsections(parent_title, topic, sections_per_level)
        nodes = []

        for i, subsection in enumerate(subsections, 1):
            node = self._create_node(subsection, level, topic)
            if level + 1 < max_depth:
                node.children = self._generate_subsections(
                    subsection, topic, level + 1, max_depth, sections_per_level
                )
            nodes.append(node)

        return nodes

    def _get_subsections(self, parent_title: str, topic: str, count: int) -> List[str]:
        """获取子节标题"""
        subsection_templates = {
            '引言': [
                f'{topic}的背景与意义',
                '研究现状与问题',
                '研究目标与方法'
            ],
            '主体': [
                f'{topic}的核心概念',
                f'{topic}的关键技术',
                f'{topic}的应用案例'
            ],
            '结论': [
                '主要研究成果',
                '研究局限性',
                '未来研究方向'
            ],
            '概述': [
                '项目背景',
                '目标与范围',
                '预期成果'
            ],
            '完成情况': [
                '已完成工作',
                '进度分析',
                '成果展示'
            ],
            '问题分析': [
                '存在问题',
                '原因分析',
                '解决方案'
            ],
            '下一步计划': [
                '工作计划',
                '时间安排',
                '资源需求'
            ],
            '相关工作': [
                '国内外研究现状',
                '现有方法分析',
                '研究空白'
            ],
            '方法': [
                '研究方法概述',
                '实验设计',
                '数据分析方法'
            ],
            '实验结果': [
                '实验设置',
                '结果分析',
                '对比实验'
            ],
            '讨论': [
                '结果解读',
                '与相关工作对比',
                '研究意义'
            ],
            '开端': [
                '背景介绍',
                '人物登场',
                '矛盾初现'
            ],
            '发展': [
                '情节推进',
                '冲突升级',
                '转折出现'
            ],
            '高潮': [
                '危机时刻',
                '关键抉择',
                '高潮爆发'
            ],
            '结局': [
                '结局揭晓',
                '余韵悠长',
                '主题升华'
            ],
            '项目概述': [
                '项目背景',
                '目标定位',
                '核心价值'
            ],
            '市场分析': [
                '市场现状',
                '竞争分析',
                '目标用户'
            ],
            '解决方案': [
                '产品方案',
                '技术架构',
                '核心功能'
            ],
            '实施计划': [
                '项目阶段',
                '时间规划',
                '里程碑'
            ],
            '预算': [
                '成本估算',
                '投资回报',
                '资金来源'
            ],
            '风险评估': [
                '风险识别',
                '风险评估',
                '应对策略'
            ],
            '论点一': [
                f'{topic}的重要性',
                '相关证据',
                '反驳与回应'
            ],
            '论点二': [
                f'{topic}的影响',
                '案例分析',
                '数据支持'
            ],
            '论点三': [
                f'{topic}的解决方案',
                '实施路径',
                '预期效果'
            ]
        }

        base_subsections = subsection_templates.get(parent_title, [
            f'{parent_title}概述',
            f'{parent_title}详细分析',
            f'{parent_title}案例研究'
        ])

        return base_subsections[:count]

    def _generate_content_hint(self, title: str, topic: str) -> str:
        """生成内容提示"""
        hints = {
            '引言': f'介绍{topic}的背景、现状和研究意义',
            '主体': f'详细阐述{topic}的核心内容',
            '结论': f'总结{topic}的主要观点和研究成果',
            '概述': f'{topic}的整体情况介绍',
            '完成情况': '已完成工作的详细汇报',
            '问题分析': '分析存在的问题及原因',
            '下一步计划': '未来的工作计划和安排',
            '相关工作': '国内外相关研究的综述',
            '方法': '研究方法和实验设计',
            '实验结果': '实验数据和结果分析',
            '讨论': '对实验结果的深入讨论',
            '项目概述': '项目的整体介绍',
            '市场分析': '市场调研和竞争分析',
            '解决方案': '具体的解决方案',
            '实施计划': '项目实施的时间计划',
            '预算': '项目预算和投资分析',
            '风险评估': '项目风险识别和应对'
        }
        return hints.get(title, f'详细阐述{title}相关内容')

    def _estimate_section_words(self, level: int) -> int:
        """估算节字数"""
        if level == 1:
            return 500
        elif level == 2:
            return 300
        else:
            return 150

    def _estimate_word_count(self, nodes: List[OutlineNode]) -> int:
        """估算总字数"""
        total = 0
        for node in nodes:
            total += node.word_count
            total += self._estimate_word_count(node.children)
        return total

    def _count_sections(self, nodes: List[OutlineNode]) -> int:
        """统计节数"""
        count = len(nodes)
        for node in nodes:
            count += self._count_sections(node.children)
        return count

    def to_markdown(self, result: OutlineResult) -> str:
        """转换为Markdown格式"""
        lines = [f"# {result.title}", ""]

        def add_node(node: OutlineNode):
            prefix = '#' * node.level
            lines.append(f"{prefix} {node.title}")
            if node.content_hint:
                lines.append(f"**内容提示**: {node.content_hint}")
                lines.append(f"**预计字数**: {node.word_count}字")
            lines.append("")
            for child in node.children:
                add_node(child)

        for node in result.nodes:
            add_node(node)

        lines.append(f"---")
        lines.append(f"**预计总字数**: {result.word_count_estimate}字")
        lines.append(f"**总节数**: {result.sections}节")

        return '\n'.join(lines)

    def to_text(self, result: OutlineResult) -> str:
        """转换为纯文本格式"""
        lines = [f"{result.title}", "=" * len(result.title), ""]

        def add_node(node: OutlineNode, prefix: str = ""):
            lines.append(f"{prefix}{node.title}")
            for i, child in enumerate(node.children, 1):
                new_prefix = prefix + f"{i}."
                add_node(child, new_prefix)

        for i, node in enumerate(result.nodes, 1):
            add_node(node, f"{i}.")

        return '\n'.join(lines)

    def from_text(self, text: str) -> OutlineResult:
        """从文本解析提纲"""
        lines = text.split('\n')
        nodes = []
        stack = []

        for line in lines:
            line = line.strip()
            if not line:
                continue

            level = self._detect_level(line)
            title = self._clean_title(line)

            if not title:
                continue

            node = OutlineNode(title=title, level=level, content_hint="")

            while stack and stack[-1].level >= level:
                stack.pop()

            if stack:
                stack[-1].children.append(node)
            else:
                nodes.append(node)

            stack.append(node)

        return OutlineResult(
            title=nodes[0].title if nodes else "提纲",
            nodes=nodes[1:] if nodes else [],
            word_count_estimate=self._estimate_word_count(nodes),
            sections=self._count_sections(nodes),
            depth=max(n.level for n in nodes) if nodes else 1
        )

    def _detect_level(self, line: str) -> int:
        """检测标题级别"""
        if line.startswith('###'):
            return 3
        elif line.startswith('##'):
            return 2
        elif line.startswith('#'):
            return 1
        elif line.startswith('3.'):
            return 3
        elif line.startswith('2.'):
            return 2
        elif line.startswith('1.'):
            return 1
        elif line.startswith('  '):
            return 3
        elif line.startswith(' '):
            return 2
        return 1

    def _clean_title(self, line: str) -> str:
        """清理标题"""
        line = re.sub(r'^#+\s*', '', line)
        line = re.sub(r'^\d+[.\uff0e]\s*', '', line)
        line = line.strip()
        return line

    def get_templates(self) -> List[Dict]:
        """获取模板列表"""
        return [
            {'id': key, 'name': value['name'], 'structure': value['structure']}
            for key, value in self.templates.items()
        ]


def generate_outline(
    topic: str,
    document_type: str = 'general',
    depth: int = 3
) -> Dict:
    """
    快速生成提纲的便捷函数

    Args:
        topic: 主题
        document_type: 文档类型
        depth: 提纲深度

    Returns:
        Dict: 提纲结果
    """
    generator = OutlineGenerator()
    result = generator.generate(topic, document_type, depth)
    return result.to_dict()


def generate_outline_markdown(
    topic: str,
    document_type: str = 'general',
    depth: int = 3
) -> str:
    """
    生成提纲并返回Markdown格式

    Args:
        topic: 主题
        document_type: 文档类型
        depth: 提纲深度

    Returns:
        str: Markdown格式的提纲
    """
    generator = OutlineGenerator()
    result = generator.generate(topic, document_type, depth)
    return generator.to_markdown(result)


def parse_outline(text: str) -> Dict:
    """
    从文本解析提纲

    Args:
        text: 文本内容

    Returns:
        Dict: 提纲结果
    """
    generator = OutlineGenerator()
    result = generator.from_text(text)
    return result.to_dict()
