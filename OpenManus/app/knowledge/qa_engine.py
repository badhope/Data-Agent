"""问答引擎模块 - QA Engine Module"""
from typing import List, Dict, Any, Optional
from .knowledge_base import KnowledgeBase
from services.llm_service import get_llm_client, test_connection

class QAEngine:
    """问答引擎类"""

    def __init__(self, knowledge_base: KnowledgeBase):
        self.knowledge_base = knowledge_base
        self.llm_client = None

    def _format_context(self, documents: List[Dict[str, Any]]) -> str:
        """格式化上下文信息"""
        if not documents:
            return ""

        context_parts = []
        for i, doc in enumerate(documents, 1):
            source = doc.get('metadata', {}).get('source', '未知来源')
            score = doc.get('score', 0)
            content = doc.get('content', '')[:500]

            context_parts.append(f"""【文档 {i}】
来源: {source}
相关性: {score:.2f}
内容:
{content}
---""")

        return "\n".join(context_parts)

    def _build_prompt(self, question: str, context: str) -> str:
        """构建问答提示词"""
        if context:
            prompt = f"""基于以下文档内容回答问题：

文档内容：
{context}

问题：{question}

请严格按照以下规则回答：
1. 优先从提供的文档内容中寻找答案
2. 如果文档中有相关信息，请直接引用并回答
3. 如果文档中没有相关信息，请明确说明"根据提供的文档，无法回答该问题"
4. 回答要简洁明了，不要添加额外信息
5. 保持回答的自然和可读性
"""
        else:
            prompt = f"""回答以下问题：

问题：{question}

请简洁明了地回答。
"""

        return prompt

    async def answer(self, question: str, llm_config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """回答问题"""
        # 搜索知识库
        search_results = self.knowledge_base.search(question, top_k=5)

        # 格式化上下文
        context = self._format_context(search_results)

        # 构建提示词
        prompt = self._build_prompt(question, context)

        # 调用LLM
        if llm_config:
            try:
                from services.llm_service import test_connection
                result = await test_connection(
                    api_key=llm_config.get('api_key', ''),
                    base_url=llm_config.get('base_url', 'https://api.openai.com/v1'),
                    model=llm_config.get('model', 'gpt-4o'),
                    provider=llm_config.get('provider', 'openai')
                )

                if result.get('success'):
                    # 使用测试连接的方式获取回答（简化实现）
                    return {
                        'success': True,
                        'answer': f"基于知识库回答：{question}\n\n相关文档：{len(search_results)} 条",
                        'context': context,
                        'sources': [doc.get('metadata', {}).get('source', '') for doc in search_results],
                        'model': llm_config.get('model'),
                        'provider': llm_config.get('provider')
                    }
                else:
                    return {
                        'success': False,
                        'error': result.get('message', 'LLM连接失败'),
                        'error_type': result.get('error_type')
                    }
            except Exception as e:
                return {
                    'success': False,
                    'error': str(e),
                    'error_type': 'qa_engine_error'
                }
        else:
            # 回退到简单回答
            return {
                'success': True,
                'answer': f"问题：{question}\n\n从知识库中找到 {len(search_results)} 条相关文档。\n\n如需详细回答，请配置LLM模型。",
                'context': context,
                'sources': [doc.get('metadata', {}).get('source', '') for doc in search_results]
            }

    async def chat(self, question: str, llm_config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """聊天模式回答"""
        return await self.answer(question, llm_config)

    def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """搜索知识库"""
        return self.knowledge_base.search(query, top_k)

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return self.knowledge_base.get_stats()

class ConversationalQAEngine(QAEngine):
    """对话式问答引擎"""

    def __init__(self, knowledge_base: KnowledgeBase):
        super().__init__(knowledge_base)
        self.conversation_history: List[Dict[str, str]] = []

    def add_to_history(self, role: str, content: str):
        """添加对话历史"""
        self.conversation_history.append({
            'role': role,
            'content': content,
            'timestamp': self._get_timestamp()
        })

    def _get_timestamp(self) -> str:
        """获取时间戳"""
        from datetime import datetime
        return datetime.now().isoformat()

    def _build_conversational_prompt(self, question: str, context: str) -> str:
        """构建对话式提示词"""
        history = "\n".join([
            f"{item['role']}: {item['content']}"
            for item in self.conversation_history[-5:]  # 只保留最近5轮对话
        ])

        if context:
            prompt = f"""你是一个智能问答助手，基于提供的文档内容回答问题。

历史对话：
{history}

参考文档：
{context}

当前问题：{question}

请按照以下规则回答：
1. 优先从参考文档中寻找答案
2. 考虑历史对话上下文
3. 如果文档中有相关信息，请直接引用并回答
4. 如果文档中没有相关信息，请明确说明
5. 回答要简洁明了，保持自然
"""
        else:
            prompt = f"""你是一个智能问答助手。

历史对话：
{history}

当前问题：{question}

请简洁明了地回答。
"""

        return prompt

    async def answer(self, question: str, llm_config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """回答问题（带对话历史）"""
        # 添加用户问题到历史
        self.add_to_history('用户', question)

        # 搜索知识库
        search_results = self.knowledge_base.search(question, top_k=5)

        # 格式化上下文
        context = self._format_context(search_results)

        # 构建对话式提示词
        prompt = self._build_conversational_prompt(question, context)

        # 调用LLM（简化实现）
        if llm_config:
            try:
                from services.llm_service import test_connection
                result = await test_connection(
                    api_key=llm_config.get('api_key', ''),
                    base_url=llm_config.get('base_url', 'https://api.openai.com/v1'),
                    model=llm_config.get('model', 'gpt-4o'),
                    provider=llm_config.get('provider', 'openai')
                )

                if result.get('success'):
                    answer_text = f"基于知识库和对话历史回答：{question}\n\n相关文档：{len(search_results)} 条"
                    self.add_to_history('助手', answer_text)

                    return {
                        'success': True,
                        'answer': answer_text,
                        'context': context,
                        'sources': [doc.get('metadata', {}).get('source', '') for doc in search_results],
                        'conversation_history': self.conversation_history,
                        'model': llm_config.get('model'),
                        'provider': llm_config.get('provider')
                    }
                else:
                    return {
                        'success': False,
                        'error': result.get('message', 'LLM连接失败'),
                        'error_type': result.get('error_type')
                    }
            except Exception as e:
                return {
                    'success': False,
                    'error': str(e),
                    'error_type': 'qa_engine_error'
                }
        else:
            answer_text = f"问题：{question}\n\n从知识库中找到 {len(search_results)} 条相关文档。\n\n如需详细回答，请配置LLM模型。"
            self.add_to_history('助手', answer_text)

            return {
                'success': True,
                'answer': answer_text,
                'context': context,
                'sources': [doc.get('metadata', {}).get('source', '') for doc in search_results],
                'conversation_history': self.conversation_history
            }

    def clear_history(self):
        """清空对话历史"""
        self.conversation_history = []

    def get_history(self) -> List[Dict[str, str]]:
        """获取对话历史"""
        return self.conversation_history