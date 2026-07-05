# ==============================================================================
# server/app.py — FastAPI 应用入口
# Phase B-1: API 网关骨架
# 启动: uvircorn server.app:app --host 127.0.0.1 --port 8000
# ==============================================================================

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from server.config import DEEPSEEK_API_KEY
from server.routes.ws import router as ws_router
from server.routes.scanner import router as scanner_router
from server.routes.overview import router as overview_router
from server.routes.research import router as research_router

from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="AI Quant Decision Platform",
    version="0.1.0",
    description="AI 量化决策平台后端 API",
)

# CORS：允许 Vue3 开发服务器访问
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(ws_router)
app.include_router(scanner_router)
app.include_router(research_router)
app.include_router(overview_router)


@app.get("/health")
async def health():
    """健康检查端点"""
    return {
        "status": "ok",
        "version": "0.1.0",
        "llm_configured": bool(DEEPSEEK_API_KEY),
        "llm_provider": __import__("server.config", fromlist=["LLM_PROVIDER"]).LLM_PROVIDER,
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server.app:app", host="0.0.0.0", port=8000, reload=True)
