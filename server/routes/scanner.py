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
    stocks = await _scan_market_top50()
    if not stocks:
        stocks = _mock_stocks(50)
    # Filter out 创业板/科创板/北交所 (user can't trade these)
    stocks = [s for s in stocks if not str(s.get('code','')).startswith(('300','301','688','689','8'))]
    if not stocks:
        stocks = _mock_stocks(50)
    return {"timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "total": len(stocks), "stocks": stocks}

@router.get("/api/scanner")
async def get_scanner():
    return await _scanner_data()
