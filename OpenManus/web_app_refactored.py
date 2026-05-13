from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path

from web.routes import router
from web.storage import initialize_storage

app = FastAPI(
    title="DATA-AI - 万能智能助手",
    description="完整的系统化智能助手：知识库、技能系统、MCP工具、数据清洗",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = Path(__file__).parent

# 挂载静态文件
static_dir = BASE_DIR / "web" / "static"
static_dir.mkdir(exist_ok=True)
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# 包含路由
app.include_router(router)

# 初始化存储
initialize_storage()


@app.get("/", response_class=HTMLResponse)
async def get_index():
    template_dir = BASE_DIR / "web" / "templates"
    index_file = template_dir / "index.html"
    with open(index_file, 'r', encoding='utf-8') as f:
        return f.read()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("web_app_refactored:app", host="0.0.0.0", port=8000, reload=True)
