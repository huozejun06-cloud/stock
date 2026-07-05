# ==============================================================================
# server/routes/ws.py — WebSocket 实时行情
# Phase B-7: 每 5 秒推送 TOP 50 候选股
# ==============================================================================

import asyncio
import json
from datetime import datetime
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

router = APIRouter()


async def _scan_market_top50():
    """异步包装：全市场扫描取 TOP 50（实时腾讯数据）"""
    import sys, os
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

    loop = asyncio.get_event_loop()

    def _fetch():
        from 工具库.数据源管理器 import get_manager
        mgr = get_manager()
        stocks = mgr.get_all_market_stocks()
        # Filter BEFORE sorting — 排除 创业板/科创板/北交所
        stocks = [s for s in stocks if isinstance(s, dict) and not str(s.get('code','')).startswith(('300','301','688','689','8'))]
        return stocks

    try:
        stocks = await loop.run_in_executor(None, _fetch)
    except Exception as e:
        print(f'  ⚠️ 全市场扫描失败: {e}')
        return []

    if not stocks or len(stocks) == 0:
        return []

    # _fetch() returns list[dict] with fields: code, price, change_pct, volume, name
    valid = []
    for s in stocks:
        code = str(s.get('code', '')).zfill(6)
        if not code or len(code) != 6:
            continue
        valid.append({
            'code': code,
            'price': round(float(s.get('price', 0)), 2),
            'change_pct': round(float(s.get('change_pct', 0)), 2),
            'volume': int(float(s.get('volume', 0))),
            'name': str(s.get('name', code)),
        })

    valid.sort(key=lambda x: abs(x['change_pct']), reverse=True)
    return valid[:50]

@router.websocket("/ws/scanner")
async def scanner_websocket(websocket: WebSocket):
    """WebSocket 端点：每 5 秒推送 TOP 50 候选股"""
    await websocket.accept()
    try:
        while True:
            stocks = await _scan_market_top50()
            payload = {
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "total": len(stocks),
                "stocks": stocks,
            }
            await websocket.send_json(payload)
            await asyncio.sleep(5)
    except WebSocketDisconnect:
        pass  # 客户端断开 → 自动停止
