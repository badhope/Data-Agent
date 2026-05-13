"""
向量嵌入服务
提供文本向量化和相似度计算功能
"""

from typing import List
from openai import AsyncOpenAI


async def generate_embeddings(text: str, api_key: str, base_url: str = "https://api.openai.com/v1", model: str = "text-embedding-3-small") -> List[float]:
    try:
        client = AsyncOpenAI(api_key=api_key, base_url=base_url)
        response = await client.embeddings.create(input=text[:8000], model=model)
        return response.data[0].embedding
    except Exception as e:
        print(f"Embedding error: {e}")
        return []


def cosine_similarity(a: List[float], b: List[float]) -> float:
    if not a or not b or len(a) != len(b):
        return 0.0
    dot_product = sum(x * y for x, y in zip(a, b))
    norm_a = sum(x * x for x in a) ** 0.5
    norm_b = sum(x * x for x in b) ** 0.5
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot_product / (norm_a * norm_b)
