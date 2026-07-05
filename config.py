# ==============================================================================
# config.py — 项目路径配置
# 所有文件的硬编码路径统一引用此文件
# Phase A Task A-2: 硬编码路径全部改为相对路径
# ==============================================================================

import os

# 项目根目录（config.py 所在目录）
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# 数据目录（统一存放缓存文件）
DATA_DIR = os.path.join(BASE_DIR, "data")
CACHE_DIR = os.path.join(DATA_DIR, "kline")   # K线CSV缓存
DB_DIR = os.path.join(DATA_DIR, "db")          # SQLite数据库

# K线全量数据集（根目录下的CSV文件，用于无缓存时的技术指标计算）
KLINE_CSV_PATH = os.path.join(DATA_DIR, "全A股K线数据_汇总.csv")

# 保证目录存在
os.makedirs(CACHE_DIR, exist_ok=True)
os.makedirs(DB_DIR, exist_ok=True)

# ==============================================================================
# API 密钥配置（从 .env 文件读取）
# ==============================================================================

import os

# 手动解析 .env 文件（不依赖 python-dotenv）
_env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
if os.path.exists(_env_path):
    with open(_env_path, 'r', encoding='utf-8') as _f:
        for _line in _f:
            _line = _line.strip()
            if _line and not _line.startswith('#'):
                if '=' in _line:
                    _key, _val = _line.split('=', 1)
                    _key = _key.strip()
                    _val = _val.strip().strip('"').strip("'")
                    if _key and not os.environ.get(_key):
                        os.environ[_key] = _val

DEEPSEEK_API_KEY = os.environ.get('DEEPSEEK_API_KEY', '')
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY', '')

# LLM 供应商切换
def get_llm_provider() -> str:
    return os.environ.get('LLM_PROVIDER', 'deepseek')
