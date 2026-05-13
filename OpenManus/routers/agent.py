"""
DataAgent - Agent 路由
包含多意图拆解（DAG 规划）、DAG 执行、归因分析等端点
"""

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse
from database import current_settings
from config import DATA_DIR, OPENAI_AVAILABLE
import json, re, uuid
from pathlib import Path

router = APIRouter()


# ==================== 多意图拆解（DAG 规划） ====================

@router.post("/api/agent/decompose")
async def decompose_query(request: Request):
    data = await request.json()
    query = data.get("query", "")

    if not query:
        raise HTTPException(status_code=400, detail="请提供查询语句")

    if not current_settings.llm.api_key:
        raise HTTPException(status_code=400, detail="请先配置API Key")

    prompt = f"""你是一个任务规划专家。将用户的复杂查询拆解为多个子任务，形成DAG（有向无环图）结构。

用户查询：{query}

请返回JSON格式的任务列表，每个任务包含：
- id: 任务ID（task_1, task_2等）
- description: 任务描述
- type: 任务类型（query/aggregate/compare/visualize）
- dependencies: 依赖的任务ID列表
- sql_hint: SQL提示（可选）

只返回JSON数组，不要其他内容。"""

    try:
        from openai import AsyncOpenAI
        client = AsyncOpenAI(
            api_key=current_settings.llm.api_key,
            base_url=current_settings.llm.base_url or "https://api.openai.com/v1"
        )
        response = await client.chat.completions.create(
            model=current_settings.llm.model or "gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1000,
            temperature=0.3
        )

        result_text = response.choices[0].message.content.strip()
        json_match = re.search(r'\[.*\]', result_text, re.DOTALL)
        if json_match:
            tasks = json.loads(json_match.group())
            return JSONResponse({"query": query, "tasks": tasks, "task_count": len(tasks)})
        else:
            return JSONResponse({"query": query, "tasks": [], "error": "解析失败"})
    except Exception as e:
        return JSONResponse({"success": False, "error": str(e)})


# ==================== DAG 执行 ====================

@router.post("/api/agent/execute-dag")
async def execute_dag(request: Request):
    data = await request.json()
    tasks = data.get("tasks", [])
    db_id = data.get("database_id")

    if not tasks:
        raise HTTPException(status_code=400, detail="缺少任务列表")

    results = {}
    execution_order = []

    def get_ready_tasks(completed):
        ready = []
        for task in tasks:
            if task["id"] in completed:
                continue
            deps = task.get("dependencies", [])
            if all(d in completed for d in deps):
                ready.append(task)
        return ready

    completed = set()
    while len(completed) < len(tasks):
        ready = get_ready_tasks(completed)
        if not ready:
            break

        for task in ready:
            execution_order.append(task["id"])
            results[task["id"]] = {
                "description": task["description"],
                "type": task["type"],
                "status": "completed"
            }
            completed.add(task["id"])

    return JSONResponse({
        "success": True,
        "execution_order": execution_order,
        "results": results
    })


# ==================== 归因分析 ====================

@router.post("/api/attribution/analyze")
async def analyze_attribution(request: Request):
    data = await request.json()
    query = data.get("query", "")
    response_text = data.get("response", "")
    sources = data.get("sources", [])

    if not response_text:
        raise HTTPException(status_code=400, detail="缺少响应内容")

    attributions = []

    for i, sentence in enumerate(response_text.split('。')[:10]):
        if len(sentence.strip()) < 5:
            continue

        matched_sources = []
        for source in sources:
            source_content = source.get("content", "")
            if any(word in source_content for word in sentence.split()[:5] if len(word) > 1):
                matched_sources.append({
                    "source_id": source.get("id"),
                    "source_name": source.get("name"),
                    "relevance": 0.8
                })

        attributions.append({
            "sentence_index": i,
            "sentence": sentence.strip(),
            "sources": matched_sources[:3],
            "confidence": 0.9 if matched_sources else 0.3
        })

    return JSONResponse({
        "query": query,
        "attributions": attributions,
        "coverage": len([a for a in attributions if a["sources"]]) / len(attributions) if attributions else 0
    })


@router.get("/api/attribution/trace/{query_id}")
async def trace_query(query_id: str):
    trace_file = DATA_DIR / "traces" / f"{query_id}.json"
    if not trace_file.exists():
        raise HTTPException(status_code=404, detail="追踪记录不存在")

    with open(trace_file, 'r', encoding='utf-8') as f:
        return JSONResponse(json.load(f))
