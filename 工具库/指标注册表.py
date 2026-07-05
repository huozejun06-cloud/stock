# ==============================================================================
# 工具库/指标注册表.py — 轻量指标注册表 + 决策缓存
# Phase C-1: 集中管理所有可用技术指标，Agent 按需查询
# ==============================================================================

import time
from typing import Optional, Dict, Any, List, Tuple

# ==============================================================================
# 指标注册表（轻量 dataclass 列表）
# ==============================================================================

# (名称, 分组, 描述, 依赖列)
INDICATORS: List[Tuple[str, str, str, List[str]]] = [
    # 趋势
    ("MA5",     "trend",     "5日均线",         ["close"]),
    ("MA10",    "trend",     "10日均线",        ["close"]),
    ("MA20",    "trend",     "20日均线",        ["close"]),
    ("MA30",    "trend",     "30日均线",        ["close"]),
    ("MA60",    "trend",     "60日均线",        ["close"]),
    ("DIF",     "trend",     "MACD快线",        ["close"]),
    ("DEA",     "trend",     "MACD慢线",        ["close"]),
    ("MACD柱",  "trend",     "MACD柱线",        ["close"]),
    ("ADX",     "trend",     "趋势强度",        ["high","low","close"]),
    ("正DI",    "trend",     "正向动向指标",     ["high","low","close"]),
    ("负DI",    "trend",     "负向动向指标",     ["high","low","close"]),
    
    # 动量
    ("RSI14",   "momentum",  "14日相对强弱",    ["close"]),
    ("BIAS20",  "momentum",  "20日乖离率",      ["close"]),
    ("OBV",     "momentum",  "能量潮",          ["close","volume"]),
    
    # 波动性
    ("ATR14",   "volatility","平均真实波幅",    ["high","low","close"]),
    ("布林中轨","volatility","布林带中轨",      ["close"]),
    ("布林上轨","volatility","布林带上轨",      ["close"]),
    ("布林下轨","volatility","布林带下轨",      ["close"]),
    
    # 成交量
    ("量MA5",   "volume",    "5日均量",         ["volume"]),
    ("量MA10",  "volume",    "10日均量",        ["volume"]),
    ("量MA20",  "volume",    "20日均量",        ["volume"]),
    ("换手率",  "volume",    "换手率",          ["volume","outstanding_share"]),
]


def get_by_group(group: str) -> List[str]:
    """按分组查询指标名"""
    return [name for name, g, _, _ in INDICATORS if g == group]


def get_all() -> List[str]:
    """获取所有指标名"""
    return [name for name, _, _, _ in INDICATORS]


# ==============================================================================
# 决策缓存（LRU + TTL)
# ==============================================================================

class DecisionCache:
    """同一股票指定时间内不重复计算"""
    
    def __init__(self, maxsize: int = 128, ttl: int = 30):
        self._cache: Dict[str, dict] = {}
        self._maxsize = maxsize
        self._ttl = ttl
    
    def get(self, key: str) -> Optional[dict]:
        """命中且未过期 → 返回缓存"""
        entry = self._cache.get(key)
        if entry and time.time() - entry["time"] < self._ttl:
            return entry["data"]
        return None
    
    def set(self, key: str, data: dict):
        """写入缓存（超 maxsize 时淘汰最旧一半）"""
        if len(self._cache) >= self._maxsize:
            for k in list(self._cache)[:self._maxsize // 2]:
                del self._cache[k]
        self._cache[key] = {"data": data, "time": time.time()}
    
    def clear(self):
        self._cache.clear()


# 全局单例
decision_cache = DecisionCache(maxsize=128, ttl=30)
