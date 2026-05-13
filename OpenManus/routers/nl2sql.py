"""
DataAgent - NL2SQL 路由
包含意图分析、SQL 生成、SQL 执行等端点
"""

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse
from database import current_settings, databases
from config import OPENAI_AVAILABLE
import json, re, sqlite3

router = APIRouter()


# ==================== 意图分析 ====================

@router.post("/api/nl2sql/analyze-intent")
async def analyze_intent(request: Request):
    data = await request.json()
    query = data.get("query", "")
    db_id = data.get("database_id")

    if not query:
        raise HTTPException(status_code=400, detail="请提供查询语句")

    intent_types = {
        "query_data": ["查询", "显示", "列出", "找出", "搜索", "获取", "统计", "计算"],
        "aggregate": ["总计", "合计", "平均", "最大", "最小", "求和", "计数", "多少"],
        "compare": ["对比", "比较", "差异", "增长", "下降", "变化", "同比", "环比"],
        "trend": ["趋势", "走势", "变化", "随时间", "历史"],
        "ranking": ["排名", "前几", "最大值", "最小值", "排序", "top"],
        "filter": ["筛选", "过滤", "条件", "满足", "大于", "小于", "等于"]
    }

    detected_intents = []
    query_lower = query.lower()
    for intent_type, keywords in intent_types.items():
        for kw in keywords:
            if kw in query_lower:
                detected_intents.append(intent_type)
                break

    if not detected_intents:
        detected_intents.append("query_data")

    tables = []
    if db_id and db_id in databases:
        db = databases[db_id]
        conn = sqlite3.connect(db.path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        conn.close()

    return JSONResponse({
        "query": query,
        "intents": list(set(detected_intents)),
        "tables": tables,
        "need_clarification": len(detected_intents) > 2 or len(tables) > 1
    })


# ==================== SQL 生成 ====================

@router.post("/api/nl2sql/generate")
async def generate_sql(request: Request):
    data = await request.json()
    query = data.get("query", "")
    db_id = data.get("database_id")
    intent = data.get("intent", "query_data")

    if not query:
        raise HTTPException(status_code=400, detail="请提供查询语句")

    if not current_settings.llm.api_key:
        raise HTTPException(status_code=400, detail="请先配置API Key")

    schema_info = ""
    if db_id and db_id in databases:
        db = databases[db_id]
        conn = sqlite3.connect(db.path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]

        for table in tables:
            cursor.execute(f"PRAGMA table_info({table})")
            columns = [row[1] for row in cursor.fetchall()]
            schema_info += f"表 {table}({', '.join(columns)})\n"
        conn.close()

    prompt = f"""你是一个SQL专家。根据用户的自然语言查询，生成对应的SQLite SQL语句。

数据库结构：
{schema_info}

用户查询：{query}
意图类型：{intent}

要求：
1. 只返回SQL语句，不要其他内容
2. 使用标准SQLite语法
3. 如果涉及聚合，使用GROUP BY
4. 如果涉及排序，使用ORDER BY
5. 如果涉及限制数量，使用LIMIT

SQL:"""

    try:
        from openai import AsyncOpenAI
        client = AsyncOpenAI(
            api_key=current_settings.llm.api_key,
            base_url=current_settings.llm.base_url or "https://api.openai.com/v1"
        )
        response = await client.chat.completions.create(
            model=current_settings.llm.model or "gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=500,
            temperature=0.1
        )

        sql = response.choices[0].message.content.strip()
        sql = re.sub(r'^```sql\s*', '', sql)
        sql = re.sub(r'\s*```$', '', sql)

        return JSONResponse({"sql": sql, "query": query, "intent": intent})
    except Exception as e:
        return JSONResponse({"success": False, "error": str(e)})


# ==================== SQL 执行 ====================

@router.post("/api/nl2sql/execute")
async def nl2sql_execute(request: Request):
    data = await request.json()
    sql = data.get("sql", "")
    db_id = data.get("database_id")

    if not sql or not db_id:
        raise HTTPException(status_code=400, detail="缺少SQL或数据库ID")

    if db_id not in databases:
        raise HTTPException(status_code=404, detail="数据库不存在")

    db = databases[db_id]
    try:
        import pandas as pd
        conn = sqlite3.connect(db.path)
        df = pd.read_sql_query(sql, conn)
        conn.close()

        return JSONResponse({
            "success": True,
            "sql": sql,
            "columns": list(df.columns),
            "data": df.values.tolist(),
            "row_count": len(df)
        })
    except Exception as e:
        return JSONResponse({"success": False, "error": str(e), "sql": sql})
