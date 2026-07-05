# ==============================================================================
# server/routes/scanner.py — REST 端点：全市场扫描
# Phase B-8: 一次性返回候选股列表（前端初始加载用）
# ==============================================================================

import asyncio, json, random
from datetime import datetime
from fastapi import APIRouter

router = APIRouter()

_MOCK_CODES = ['600519','000858','300750','002594','601899','600276','000333','300274','600036','601318',
    '600900','002415','300124','600809','000651','601012','600031','002230','300059','600585']
_MOCK_NAMES = ['贵州茅台','五粮液','宁德时代','比亚迪','紫金矿业','恒瑞医药','美的集团','阳光电源','招商银行','中国平安',
    '长江电力','海康威视','汇川技术','山西汾酒','格力电器','隆基绿能','三一重工','科大讯飞','东方财富','海螺水泥']

def _mock_stocks(n=50):
    stocks = []
    for i in range(n):
        ci = i % len(_MOCK_CODES)
        code = _MOCK_CODES[ci] if i < len(_MOCK_CODES) else f"60{random.randint(1000,9999)}"
        name = _MOCK_NAMES[ci] if i < len(_MOCK_NAMES) else f"Mock{i:02d}"
        score = random.randint(55, 95)
        stocks.append({
            "code": code, "name": name,
            "price": round(random.uniform(5, 300), 2),
            "pct_chg": round(random.uniform(-5, 8), 2),
            "score": score,
            "signal": "BUY" if score >= 85 else "WATCH" if score >= 70 else "SELL",
        })
    return stocks

async def _scanner_data():
    from server.routes.ws import _scan_market_top50
    print("[Scanner] 调用 DataSourceManager.get_all_market_stocks()...")
    try:
        stocks = await _scan_market_top50()
        print(f"[Scanner] DataSourceManager 返回 {len(stocks)} 只股票")
    except Exception as e:
        print(f"[Scanner] ❌ DataSourceManager 异常: {e}")
        stocks = []
    if not stocks:
        print("[Scanner] ⚠️ 无数据，降级到 mock")
        stocks = _mock_stocks(50)
    print(f"[Scanner] 最终返回 {len(stocks)} 只")
    return {"timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), , "data_source": "live" if len(stocks) > 0 and stocks[0].get("price", 0) > 0 else "mock"}

@router.get("/api/scanner")
async def get_scanner():
    return await _scanner_data()
