# ==============================================================================
# server/config.py — 服务端配置
# 引用项目根目录的 config.py，集中管理所有配置
# ==============================================================================

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import (
    BASE_DIR, DATA_DIR, CACHE_DIR, DB_DIR,
    DEEPSEEK_API_KEY, OPENAI_API_KEY,
)

# LLM 供应商配置（通过环境变量切换）
LLM_PROVIDER = os.environ.get("LLM_PROVIDER", "deepseek")

# API 服务配置
API_HOST = os.environ.get("API_HOST", "127.0.0.1")
API_PORT = int(os.environ.get("API_PORT", "8000"))
