"""
工具库/作战预案.py — 明日作战预案生成器
根据今日分析生成明日具体操作计划：高开/平开/低开/跌破 四种应对
"""
import sys, os, numpy as np, pandas as pd
from config import BASE_DIR, CACHE_DIR
sys.path.insert(0, BASE_DIR)

def 生成预案(代码: str, 名称: str, 当前价: float, df: pd.DataFrame) -> dict:
    """生成单只股票的明日作战预案"""
    if df is None or len(df) < 20:
        return {"错误": "数据不足"}
    
    close = df['close'].values
    high = df['high'].values
    low = df['low'].values
    
    # 关键价位
    ma20 = df['MA20'].iloc[-1] if 'MA20' in df.columns else np.mean(close[-20:])
    ma10 = df['MA10'].iloc[-1] if 'MA10' in df.columns else np.mean(close[-10:])
    ma5 = df['MA5'].iloc[-1] if 'MA5' in df.columns else np.mean(close[-5:])
    
    # 支撑位: MA20, 前低
    支撑1 = round(ma20, 2)
    支撑2 = round(min(low[-20:]), 2)
    
    # 压力位: 前高, 布林上轨
    压力1 = round(max(high[-20:]), 2)
    bol_up = df['布林上轨'].iloc[-1] if '布林上轨' in df.columns else 压力1 * 1.05
    压力2 = round(bol_up, 2)
    
    # 趋势判断
    if ma5 > ma10 > ma20:
        趋势 = "多头排列 📈"
    elif ma5 < ma10 < ma20:
        趋势 = "空头排列 📉"
    else:
        趋势 = "震荡整理 ➡️"
    
    # 距支撑/压力距离
    距支撑1 = (当前价 - 支撑1) / 支撑1 * 100
    距压力1 = (压力1 - 当前价) / 当前价 * 100
    盈亏比_short = round(距压力1 / max(abs(距支撑1), 0.5), 1)
    
    # 四种应对方案
    预案 = []
    预案.append(f"【高开 ＞{压力1}】→ {'追涨（放量突破确认）' if 距压力1 < 2 else '等回踩确认'}")
    预案.append(f"【平开 {当前价}附近】→ {'持有观察，跌破{支撑1}止损'}")
    预案.append(f"【低开 {当前价}~{支撑1}】→ {'可低吸加仓' if 距支撑1 < 3 else '等待企稳'}")
    预案.append(f"【跌破 ＜{支撑1}】→ {'⚠️ 无条件止损'}")
    
    return {
        "代码": 代码, "名称": 名称, "当前价": 当前价,
        "趋势": 趋势,
        "均线": f"MA5={ma5:.2f} MA10={ma10:.2f} MA20={ma20:.2f}",
        "支撑位": f"一档{支撑1} / 二档{支撑2}",
        "压力位": f"一档{压力1} / 二档{压力2}",
        "盈亏比": f"止损{支撑1}→目标{压力1} = {盈亏比_short}:1",
        "预案": "\n".join(预案),
    }


if __name__ == "__main__":
    path = os.path.join(CACHE_DIR, "002138_日K.csv")
    df = pd.read_csv(path, parse_dates=['date'])
    for n in [5,10,20,60]:
        df[f'MA{n}'] = df['close'].rolling(n).mean()
    df['布林上轨'] = df['close'].rolling(20).mean() + 2*df['close'].rolling(20).std()
    预案 = 生成预案("002138","顺络电子", 55.61, df.tail(60))
    for k,v in 预案.items():
        print(f"{k}: {v}")
