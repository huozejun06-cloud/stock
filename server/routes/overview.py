# ==============================================================================
# server/routes/overview.py — REST 端点：市场全景聚合
# Phase E-2: 一次返回 6 组数据 (A股/全球/情绪/板块/快讯/AI日志)
# ==============================================================================

import asyncio, random
from datetime import datetime
from fastapi import APIRouter

router = APIRouter()

# ── Mock fallbacks (per sub-module) ──

def _mock_indices():
    return [
        {"code": "000001", "name": "上证指数", "price": 3342.17, "change_pct": 0.72},
        {"code": "399001", "name": "深证成指", "price": 10891.55, "change_pct": 0.89},
        {"code": "399006", "name": "创业板指", "price": 2194.33, "change_pct": -0.14},
        {"code": "000688", "name": "科创50", "price": 1025.60, "change_pct": 1.23},
    ]

def _mock_global():
    return [
        {"name": "道琼斯", "price": 42130.55, "change_pct": 0.35},
        {"name": "纳斯达克", "price": 19854.21, "change_pct": 0.52},
        {"name": "恒生指数", "price": 22340.18, "change_pct": -0.28},
        {"name": "日经225", "price": 38762.44, "change_pct": 0.18},
    ]

def _mock_sentiment():
    return {
        "up_down_ratio": "2,847 : 2,156",
        "limit_up": 62, "limit_down": 8,
        "max_board_height": 7,
        "volume": "11,428亿",
        "market_temp": 65,
        "temp_label": "偏暖",
    }

def _mock_sectors():
    return [
        {"name": "半导体", "count": 48, "change_pct": 3.52},
        {"name": "人工智能", "count": 62, "change_pct": 2.87},
        {"name": "新能源车", "count": 35, "change_pct": 2.14},
        {"name": "生物医药", "count": 56, "change_pct": 1.68},
        {"name": "军工航天", "count": 28, "change_pct": -0.43},
    ]

def _mock_news():
    return [
        "北向资金今日净流入 58.3 亿，外资连续第 5 日加仓 A 股",
        "央行开展 2000 亿 MLF 操作，利率维持不变",
        "半导体板块集体走强，板块内 12 只个股涨停",
    ]

def _mock_ai_logs():
    return [
        {"agent": "Trend", "msg": "市场整体处于多头排列，MA20 向上发散，中期趋势看多。", "time": "14:32:05"},
        {"agent": "Macro", "msg": "北向资金今日净流入 58.3 亿，外资连续第 5 日加仓 A 股。", "time": "14:31:42"},
        {"agent": "Sector", "msg": "半导体板块 RS 强度突破 85，板块内涨停 12 家，强势特征明显。", "time": "14:30:18"},
    ]

# ── Safe callers (try real data, fall back to mock) ──

def _safe_get(fn, fallback_fn):
    try:
        result = fn()
        if result is not None and (not isinstance(result, (list, dict)) or len(result) > 0):
            return result
    except Exception:
        pass
    return fallback_fn()

def _try_real_indices():
    try:
        import sys, os
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
        from 工具库.数据源管理器 import get_manager
        mgr = get_manager()
        stocks = mgr.get_all_market_stocks()
        if stocks and len(stocks) >= 4:
            result = []
            for s in stocks[:4]:
                result.append({
                    "code": s.get("code", ""),
                    "name": s.get("name", ""),
                    "price": s.get("price", 0),
                    "change_pct": s.get("pct_chg", s.get("change_pct", 0)),
                })
            return result
    except Exception:
        pass
    return None

def _try_real_global():
    try:
        import sys, os
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
        from 工具库.全球市场 import 获取全球指数快照
        data = 获取全球指数快照()
        if data and len(data) > 0:
            return [{"name": d.get("name",""), "price": d.get("price",0), "change_pct": d.get("change_pct",0)} for d in data]
    except Exception:
        pass
    return None

def _try_real_sentiment():
    try:
        import sys, os
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
        from 工具库.情绪周期 import 分析涨停板, 市场温度
        data = 分析涨停板()
        temp = 市场温度(data)
        return {
            "up_down_ratio": f"{data.get('上涨家数',0)} : {data.get('下跌家数',0)}",
            "limit_up": data.get("涨停数", 0),
            "limit_down": data.get("跌停数", 0),
            "max_board_height": data.get("最高连板", 0),
            "volume": f"{data.get('成交额',0)//100000000}亿" if data.get('成交额') else "",
            "market_temp": temp.get("温度", 50),
            "temp_label": temp.get("描述", "中性"),
        }
    except Exception:
        pass
    return None

def _try_real_sectors():
    try:
        import sys, os
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
        from 工具库.热点归因 import get_热点归因器
        return [{"name": s.get("name",""), "count": s.get("count",0), "change_pct": s.get("change_pct",0)} for s in get_热点归因器()[:5]]
    except Exception:
        pass
    return None

def _try_real_news():
    try:
        import sys, os
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
        from 工具库.快讯电报 import 获取最新快讯
        items = 获取最新快讯()
        if items:
            return items[:5]
    except Exception:
        pass
    return None

# ── Route ──

@router.get("/api/overview")
async def get_overview():
    """市场全景：6 组数据聚合"""
    return {
        "indices": _safe_get(_try_real_indices, _mock_indices),
        "global": _safe_get(_try_real_global, _mock_global),
        "sentiment": _safe_get(_try_real_sentiment, _mock_sentiment),
        "sectors": _safe_get(_try_real_sectors, _mock_sectors),
        "news": _safe_get(_try_real_news, _mock_news),
        "ai_logs": _mock_ai_logs(),
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
