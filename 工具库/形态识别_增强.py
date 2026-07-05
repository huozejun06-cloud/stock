"""
工具库/形态识别_增强.py — K线形态识别（增强版）
包含：早晨之星、黄昏之星、红三兵、三只乌鸦、吞没形态、锤子线、十字星
"""
import sys, os
import pandas as pd
import numpy as np
from config import BASE_DIR, CACHE_DIR
sys.path.insert(0, BASE_DIR)


def _body(open, close): return abs(close - open)
def _upper_shadow(open, close, high): return high - max(open, close)
def _lower_shadow(open, close, low): return min(open, close) - low
def _is_bullish(open, close): return close > open
def _is_bearish(open, close): return close < open
def _body_pct(open, close): return abs(close - open) / max(open, close, 0.01) * 100
def _total_range(open, close, high, low): return high - low


def 识别早晨之星(df: pd.DataFrame) -> dict:
    """早晨之星（底部反转信号）"""
    if len(df) < 3: return {'生效': False, '评分': 0}
    d1, d2, d3 = df.iloc[-3], df.iloc[-2], df.iloc[-1]
    if not (_is_bearish(d1['open'], d1['close']) and _body_pct(d1['open'], d1['close']) > 2): return {'生效': False}
    if _body_pct(d2['open'], d2['close']) > 2: return {'生效': False}  # 中间小实体
    if not (_is_bullish(d3['open'], d3['close']) and _body_pct(d3['open'], d3['close']) > 2): return {'生效': False}
    if d3['close'] <= (d1['close'] + d1['open']) / 2: return {'生效': False}
    return {'生效': True, '形态': '早晨之星', '评分': 80, '方向': '看涨'}


def 识别黄昏之星(df: pd.DataFrame) -> dict:
    """黄昏之星（顶部反转信号）"""
    if len(df) < 3: return {'生效': False, '评分': 0}
    d1, d2, d3 = df.iloc[-3], df.iloc[-2], df.iloc[-1]
    if not (_is_bullish(d1['open'], d1['close']) and _body_pct(d1['open'], d1['close']) > 2): return {'生效': False}
    if _body_pct(d2['open'], d2['close']) > 2: return {'生效': False}
    if not (_is_bearish(d3['open'], d3['close']) and _body_pct(d3['open'], d3['close']) > 2): return {'生效': False}
    if d3['close'] >= (d1['close'] + d1['open']) / 2: return {'生效': False}
    return {'生效': True, '形态': '黄昏之星', '评分': 80, '方向': '看跌'}


def 识别红三兵(df: pd.DataFrame) -> dict:
    """红三兵（持续上涨信号）"""
    if len(df) < 3: return {'生效': False, '评分': 0}
    for i in range(-3, 0):
        r = df.iloc[i]
        if not (_is_bullish(r['open'], r['close']) and _body_pct(r['open'], r['close']) > 1):
            return {'生效': False}
    c1, c2, c3 = df.iloc[-3]['close'], df.iloc[-2]['close'], df.iloc[-1]['close']
    if not (c2 > c1 and c3 > c2): return {'生效': False}
    return {'生效': True, '形态': '红三兵', '评分': 70, '方向': '看涨'}


def 识别三只乌鸦(df: pd.DataFrame) -> dict:
    """三只乌鸦（持续下跌信号）"""
    if len(df) < 3: return {'生效': False, '评分': 0}
    for i in range(-3, 0):
        r = df.iloc[i]
        if not (_is_bearish(r['open'], r['close']) and _body_pct(r['open'], r['close']) > 1):
            return {'生效': False}
    c1, c2, c3 = df.iloc[-3]['close'], df.iloc[-2]['close'], df.iloc[-1]['close']
    if not (c2 < c1 and c3 < c2): return {'生效': False}
    return {'生效': True, '形态': '三只乌鸦', '评分': 70, '方向': '看跌'}


def 识别看涨吞没(df: pd.DataFrame) -> dict:
    """看涨吞没（反转信号）"""
    if len(df) < 2: return {'生效': False, '评分': 0}
    d1, d2 = df.iloc[-2], df.iloc[-1]
    if not _is_bearish(d1['open'], d1['close']): return {'生效': False}
    if not _is_bullish(d2['open'], d2['close']): return {'生效': False}
    if not (d2['open'] < d1['close'] and d2['close'] > d1['open']): return {'生效': False}
    return {'生效': True, '形态': '看涨吞没', '评分': 75, '方向': '看涨'}


def 识别看跌吞没(df: pd.DataFrame) -> dict:
    """看跌吞没（反转信号）"""
    if len(df) < 2: return {'生效': False, '评分': 0}
    d1, d2 = df.iloc[-2], df.iloc[-1]
    if not _is_bullish(d1['open'], d1['close']): return {'生效': False}
    if not _is_bearish(d2['open'], d2['close']): return {'生效': False}
    if not (d2['open'] > d1['close'] and d2['close'] < d1['open']): return {'生效': False}
    return {'生效': True, '形态': '看跌吞没', '评分': 75, '方向': '看跌'}


def 识别锤子线(df: pd.DataFrame) -> dict:
    """锤子线（底部反转信号）"""
    if len(df) < 1: return {'生效': False, '评分': 0}
    r = df.iloc[-1]
    body = _body(r['open'], r['close'])
    lower = _lower_shadow(r['open'], r['close'], r['low'])
    upper = _upper_shadow(r['open'], r['close'], r['high'])
    if body <= 0: return {'生效': False}
    if lower / body < 2: return {'生效': False}
    if upper > body * 0.3: return {'生效': False}
    评分 = 60 if _is_bullish(r['open'], r['close']) else 50
    return {'生效': True, '形态': '锤子线', '评分': 评分, '方向': '看涨'}


def 识别十字星(df: pd.DataFrame) -> dict:
    """十字星（变盘信号）"""
    if len(df) < 1: return {'生效': False, '评分': 0}
    r = df.iloc[-1]
    if _body_pct(r['open'], r['close']) > 0.5: return {'生效': False}
    total = _total_range(r['open'], r['close'], r['high'], r['low'])
    if total <= 0: return {'生效': False}
    评分 = 55
    return {'生效': True, '形态': '十字星', '评分': 评分, '方向': '变盘'}


def 识别所有形态(df: pd.DataFrame) -> list:
    """运行所有形态识别，返回活跃形态列表"""
    patterns = [
        识别早晨之星, 识别黄昏之星, 识别红三兵, 识别三只乌鸦,
        识别看涨吞没, 识别看跌吞没, 识别锤子线, 识别十字星
    ]
    results = []
    for func in patterns:
        try:
            r = func(df)
            if r['生效']:
                results.append(r)
        except Exception as e:
            print(f"  ⚠️ 形态识别_增强.py: {e}")
            pass
    # 按评分排序
    results.sort(key=lambda x: -x['评分'])
    return results


def 形态综合评分(形态列表: list) -> dict:
    """根据识别的形态给出综合评分和方向"""
    看涨 = sum(r['评分'] for r in 形态列表 if r.get('方向') == '看涨')
    看跌 = sum(r['评分'] for r in 形态列表 if r.get('方向') == '看跌')
    
    if 看涨 > 看跌 * 1.5:
        方向, 强度 = '看涨', 看涨
    elif 看跌 > 看涨 * 1.5:
        方向, 强度 = '看跌', 看跌
    else:
        方向, 强度 = '震荡', 0
    
    return {
        '方向': 方向,
        '强度': 强度,
        '形态数': len(形态列表),
        '活跃形态': [r['形态'] for r in 形态列表[:3]],
    }


if __name__ == "__main__":
    import pandas as pd
    df = pd.read_csv(os.path.join(CACHE_DIR, "002138_日K.csv"), parse_dates=['date'])
    results = 识别所有形态(df.tail(50))
    print(f"识别到 {len(results)} 个形态:")
    for r in results:
        print(f"  {r['形态']}: 评分{r['评分']} | {r['方向']}")
    print(f"\n综合: {形态综合评分(results)}")
