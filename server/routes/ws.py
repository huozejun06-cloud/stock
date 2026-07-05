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
        return mgr.get_all_market_stocks()

    try:
        df = await loop.run_in_executor(None, _fetch)
    except Exception as e:
        print(f'  ⚠️ 全市场扫描失败: {e}')
        return []

    if df is None or df.empty:
        return []

    rows = df.to_dict('records')
    stocks = []
    for row in rows:
        code = str(row.get('代码', '')).zfill(6)
        if not code or len(code) != 6:
            continue
        stocks.append({
            'code': code,
            'price': round(float(row.get('最新价', 0)), 2),
            'change_pct': round(float(row.get('涨跌幅', 0)), 2),
            'volume': int(float(row.get('成交量', 0))),
            'name': str(row.get('名称', code)),
        })

    stocks.sort(key=lambda x: abs(x['change_pct']), reverse=True)
    return stocks[:50]

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
