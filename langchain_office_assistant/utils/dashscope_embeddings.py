"""
阿里百炼嵌入模型封装
使用DashScope SDK实现LangChain兼容的嵌入模型
"""
from typing import List
from langchain_core.embeddings import Embeddings
import dashscope
from dashscope import TextEmbedding
import logging
import os

logger = logging.getLogger(__name__)


class DashScopeEmbeddings(Embeddings):
    """阿里百炼嵌入模型"""

    def __init__(self, api_key: str, model: str = "text-embedding-v3"):
        self.api_key = api_key
        self.model = model
        os.environ["DASHSCOPE_API_KEY"] = api_key
        dashscope.api_key = api_key

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """嵌入多个文档"""
        try:
            result = TextEmbedding.call(
                model=self.model,
                input=texts
            )
            if result.status_code == 200:
                return [item["embedding"] for item in result.output["embeddings"]]
            else:
                logger.error(f"Embedding failed: {result.message}")
                raise Exception(f"Embedding failed: {result.message}")
        except Exception as e:
            logger.error(f"Error in embed_documents: {e}")
            raise

    def embed_query(self, text: str) -> List[float]:
        """嵌入单个查询"""
        try:
            result = TextEmbedding.call(
                model=self.model,
                input=[text]
            )
            if result.status_code == 200:
                return result.output["embeddings"][0]["embedding"]
            else:
                logger.error(f"Embedding failed: {result.message}")
                raise Exception(f"Embedding failed: {result.message}")
        except Exception as e:
            logger.error(f"Error in embed_query: {e}")
            raise
