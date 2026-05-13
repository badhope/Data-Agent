"""
DataAgent - 财报路由
包含 PDF 财报解析、表格提取等端点
"""

from fastapi import APIRouter, HTTPException, Request, UploadFile, File
from fastapi.responses import JSONResponse
from database import databases, save_databases
import json, uuid, datetime, tempfile, shutil, sqlite3
from pathlib import Path

router = APIRouter()


# ==================== PDF 财报解析 ====================

@router.post("/api/financial/parse-pdf")
async def parse_financial_pdf(file: UploadFile = File(...)):
    try:
        import pdfplumber

        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            shutil.copyfileobj(file.file, tmp)
            tmp_path = tmp.name

        tables_data = []
        text_content = []

        with pdfplumber.open(tmp_path) as pdf:
            for page_num, page in enumerate(pdf.pages):
                text = page.extract_text()
                if text:
                    text_content.append({"page": page_num + 1, "text": text})

                tables = page.extract_tables()
                for table_idx, table in enumerate(tables):
                    if table and len(table) > 1:
                        headers = table[0] if table[0] else [f"col_{i}" for i in range(len(table[1]))]
                        rows = table[1:]
                        import pandas as pd
                        df = pd.DataFrame(rows, columns=headers)
                        tables_data.append({
                            "page": page_num + 1,
                            "table_index": table_idx,
                            "headers": headers,
                            "data": rows,
                            "shape": df.shape
                        })

        Path(tmp_path).unlink()
        return JSONResponse({
            "success": True,
            "filename": file.filename,
            "tables": tables_data,
            "text_content": text_content,
            "table_count": len(tables_data)
        })
    except ImportError:
        return JSONResponse({"success": False, "error": "请安装 pdfplumber: pip install pdfplumber"})
    except Exception as e:
        return JSONResponse({"success": False, "error": str(e)})


# ==================== 表格提取入库 ====================

@router.post("/api/financial/extract-tables")
async def extract_financial_tables(request: Request):
    data = await request.json()
    tables = data.get("tables", [])
    db_id = data.get("database_id")

    if db_id and db_id in databases:
        db = databases[db_id]
        conn = sqlite3.connect(db.path)
        cursor = conn.cursor()

        for table_data in tables:
            table_name = table_data.get("name", f"table_{uuid.uuid4().hex[:8]}")
            headers = table_data.get("headers", [])
            rows = table_data.get("data", [])

            if headers and rows:
                columns_def = ", ".join([f'"{h}" TEXT' for h in headers])
                cursor.execute(f'CREATE TABLE IF NOT EXISTS "{table_name}" ({columns_def})')

                placeholders = ", ".join(["?" for _ in headers])
                for row in rows:
                    if len(row) == len(headers):
                        cursor.execute(f'INSERT INTO "{table_name}" VALUES ({placeholders})', row)

        conn.commit()
        conn.close()
        databases[db_id].updated_at = datetime.datetime.now().isoformat()
        save_databases()

    return JSONResponse({"success": True, "imported_tables": len(tables)})
