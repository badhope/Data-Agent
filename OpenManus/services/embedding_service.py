"""
DataAgent - 向量嵌入服务
提供文本向量化和相似度计算功能
使用懒加载方式导入 openai，避免模块级依赖
"""

from typing import List


async def generate_embeddings(
    text: str,
    api_key: str,
    base_url: str = "https://api.openai.com/v1",
    model: str = "text-embedding-3-small"
) -> List[float]:
    """生成单条文本的向量嵌入"""
    try:
        from openai import AsyncOpenAI
        client = AsyncOpenAI(api_key=api_key, base_url=base_url)
        response = await client.embeddings.create(input=text[:8000], model=model)
        return response.data[0].embedding
    except Exception as e:
        print(f"Embedding error: {e}")
        return []


async def batch_generate_embeddings(
    texts: List[str],
    api_key: str,
    base_url: str = "https://api.openai.com/v1",
    model: str = "text-embedding-3-small"
) -> List[List[float]]:
    """批量生成多条文本的向量嵌入"""
    try:
        from openai import AsyncOpenAI
        client = AsyncOpenAI(api_key=api_key, base_url=base_url)
        # openai 批量接口一次最多支持 2048 条
        batch_inputs = [t[:8000] for t in texts]
        response = await client.embeddings.create(input=batch_inputs, model=model)
        # 按 index 排序确保顺序一致
        sorted_data = sorted(response.data, key=lambda x: x.index)
        return [item.embedding for item in sorted_data]
    except Exception as e:
        print(f"Batch embedding error: {e}")
        return [[] for _ in texts]


def cosine_similarity(a: List[float], b: List[float]) -> float:
    """计算两个向量的余弦相似度"""
    if not a or not b or len(a) != len(b):
        return 0.0
    dot_product = sum(x * y for x, y in zip(a, b))
    norm_a = sum(x * x for x in a) ** 0.5
    norm_b = sum(x * x for x in b) ** 0.5
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot_product / (norm_a * norm_b)
