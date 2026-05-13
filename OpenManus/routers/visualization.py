"""
DataAgent - 可视化路由
包含图表生成等端点
"""

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse
from config import DATA_DIR
import json, uuid
from pathlib import Path

router = APIRouter()


# ==================== 图表生成 ====================

@router.post("/api/visualization/generate")
async def generate_chart(request: Request):
    data = await request.json()
    chart_type = data.get("type", "bar")
    columns = data.get("columns", [])
    rows = data.get("data", [])
    title = data.get("title", "数据图表")

    if not columns or not rows:
        raise HTTPException(status_code=400, detail="缺少数据")

    import pandas as pd
    df = pd.DataFrame(rows, columns=columns)

    try:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt

        fig, ax = plt.subplots(figsize=(10, 6))

        if chart_type == "bar":
            if len(columns) >= 2:
                df.plot(kind='bar', x=columns[0], y=columns[1], ax=ax)
            else:
                df.plot(kind='bar', ax=ax)
        elif chart_type == "line":
            if len(columns) >= 2:
                df.plot(kind='line', x=columns[0], y=columns[1], ax=ax)
            else:
                df.plot(kind='line', ax=ax)
        elif chart_type == "pie":
            if len(columns) >= 2:
                df.plot(kind='pie', y=columns[1], labels=df[columns[0]], ax=ax)
        elif chart_type == "scatter":
            if len(columns) >= 2:
                ax.scatter(df[columns[0]], df[columns[1]])
                ax.set_xlabel(columns[0])
                ax.set_ylabel(columns[1])
        elif chart_type == "heatmap":
            import seaborn as sns
            numeric_df = df.select_dtypes(include=['number'])
            if not numeric_df.empty:
                sns.heatmap(numeric_df.corr(), annot=True, ax=ax)

        ax.set_title(title)
        plt.tight_layout()

        chart_path = DATA_DIR / "charts" / f"{uuid.uuid4().hex}.png"
        chart_path.parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(chart_path, dpi=100, bbox_inches='tight')
        plt.close()

        return JSONResponse({
            "success": True,
            "chart_path": str(chart_path),
            "chart_type": chart_type,
            "title": title
        })
    except ImportError as e:
        return JSONResponse({"success": False, "error": f"请安装可视化库: {str(e)}"})
    except Exception as e:
        return JSONResponse({"success": False, "error": str(e)})
