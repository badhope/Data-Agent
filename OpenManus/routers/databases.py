"""
DataAgent - 数据库路由
包含数据库 CRUD、表管理、SQL 查询等端点
"""

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse
from database import databases, save_databases, Database
from config import DATABASES_DIR
from utils.validation import validate_table_name as _validate_table_name
from utils.db_helper import get_db_connection
import json, uuid, datetime, sqlite3
from pathlib import Path

router = APIRouter()


# ==================== 数据库 CRUD ====================

@router.get("/api/databases")
async def list_databases():
    return JSONResponse([db.model_dump() if hasattr(db, 'model_dump') else db for db in databases.values()])


@router.post("/api/databases")
async def create_database(request: Request):
    data = await request.json()
    db_id = str(uuid.uuid4())
    db_name = data.get("name", "新数据库")
    db_path = DATABASES_DIR / f"{db_id}.db"
    now = datetime.datetime.now().isoformat()

    conn = sqlite3.connect(str(db_path))
    conn.close()

    db = Database(id=db_id, name=db_name, path=str(db_path), created_at=now, updated_at=now)
    databases[db_id] = db
    save_databases()
    return JSONResponse(db.model_dump())


@router.delete("/api/databases/{db_id}")
async def delete_database(db_id: str):
    if db_id not in databases:
        raise HTTPException(status_code=404, detail="数据库不存在")
    db = databases[db_id]
    if Path(db.path).exists():
        Path(db.path).unlink()
    del databases[db_id]
    save_databases()
    return JSONResponse({"success": True})


# ==================== 表管理 ====================

@router.get("/api/databases/{db_id}/tables")
async def list_tables(db_id: str):
    with get_db_connection(db_id) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
    return JSONResponse({"tables": tables})


@router.get("/api/databases/{db_id}/tables/{table_name}")
async def get_table_schema(db_id: str, table_name: str):
    table_name = _validate_table_name(table_name)
    with get_db_connection(db_id) as conn:
        cursor = conn.cursor()
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = [{"name": row[1], "type": row[2]} for row in cursor.fetchall()]
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        count = cursor.fetchone()[0]
    return JSONResponse({"table": table_name, "columns": columns, "row_count": count})


# ==================== SQL 查询 ====================

@router.post("/api/databases/{db_id}/query")
async def execute_query(db_id: str, request: Request):
    if db_id not in databases:
        raise HTTPException(status_code=404, detail="数据库不存在")
    data = await request.json()
    sql = data.get("sql", "")
    if not sql:
        raise HTTPException(status_code=400, detail="SQL语句不能为空")

    forbidden = ["DROP", "DELETE", "UPDATE", "INSERT", "ALTER", "CREATE", "TRUNCATE"]
    sql_upper = sql.strip().upper()
    if not sql_upper.startswith('SELECT') and not sql_upper.startswith('PRAGMA'):
        raise HTTPException(status_code=403, detail="只允许执行SELECT或PRAGMA查询")
    for kw in forbidden:
        if kw in sql_upper:
            raise HTTPException(status_code=403, detail=f"禁止执行 {kw} 操作")

    db = databases[db_id]
    try:
        import pandas as pd
        with get_db_connection(db_id) as conn:
            df = pd.read_sql_query(sql, conn)
        return JSONResponse({
            "success": True,
            "columns": list(df.columns),
            "data": df.values.tolist(),
            "row_count": len(df)
        })
    except Exception as e:
        return JSONResponse({"success": False, "error": str(e)})
