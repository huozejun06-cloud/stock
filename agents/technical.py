# ==============================================================================
# agents/technical.py — Technical Agent (规则引擎)
# Phase C-2: 趋势分析 Agent，处理 MA/MACD/ADX/BIAS/BOLL
# ==============================================================================

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import numpy as np
from typing import Dict, Any


def analyze(df: pd.DataFrame) -> Dict[str, Any]:
    """
    全量趋势分析。
    
    输入: OHLCV DataFrame (至少 60 行)
    输出: {
        "indicators": {...},        # 关键指标值
        "ma_alignment": str,        # 多头/空头/缠绕
        "macd_signal": str,         # 金叉/死叉/多头运行/空头运行
        "adx_description": str,     # 强趋势/中等/无趋势
        "boll_status": str,         # 突破上轨/跌破下轨/轨道内
        "direction_strength": int,  # -100 ~ 100
        "market_state": str,        # 市场状态描述
        "market_confidence": int,   # 置信度 0~100
    }
    """
    from 工具库.数据工具 import 计算全部技术指标, 判断均线排列, 判断MACD信号
    from 工具库.数据工具 import 判断ADX描述, 判断布林形态
    from 工具库.交易决策引擎 import level2_方向判断, 判断市场状态
    
    if df is None or len(df) < 60:
        return {"error": "数据不足 (至少 60 行)"}
    
    # 1. 计算全部指标
    indicator_df = 计算全部技术指标(df.copy())
    if indicator_df is None or len(indicator_df) < 2:
        return {"error": "指标计算失败"}
    
    最新 = indicator_df.iloc[-1].to_dict()
    前一条 = indicator_df.iloc[-2] if len(indicator_df) > 1 else indicator_df.iloc[-1]
    
    # 2. 提取关键指标
    indicators = {
        "MA5": round(float(最新.get("MA5", 0)), 2),
        "MA10": round(float(最新.get("MA10", 0)), 2),
        "MA20": round(float(最新.get("MA20", 0)), 2),
        "MA60": round(float(最新.get("MA60", 0)), 2),
        "DIF": round(float(最新.get("DIF", 0)), 4),
        "DEA": round(float(最新.get("DEA", 0)), 4),
        "MACD柱": round(float(最新.get("MACD柱", 0)), 4),
        "ADX": round(float(最新.get("ADX", 0)), 1),
        "正DI": round(float(最新.get("正DI", 0)), 1),
        "负DI": round(float(最新.get("负DI", 0)), 1),
        "BIAS20": round(float(最新.get("BIAS20", 0)), 2),
        "RSI14": round(float(最新.get("RSI14", 0)), 1),
        "ATR14": round(float(最新.get("ATR14", 0)), 2),
        "布林中轨": round(float(最新.get("布林中轨", 0)), 2),
        "布林上轨": round(float(最新.get("布林上轨", 0)), 2),
        "布林下轨": round(float(最新.get("布林下轨", 0)), 2),
    }
    
    # 3. 趋势解读
    try:
        ma_align = 判断均线排列(最新)
    except Exception as e:
        print(f"  ⚠️ technical.py: {e}")
        ma_align = "数据不足"
    
    try:
        macd_sig = 判断MACD信号(最新, 前一条)
    except Exception as e:
        print(f"  ⚠️ technical.py: {e}")
        macd_sig = "数据不足"
    
    try:
        adx_desc = 判断ADX描述(indicators["ADX"])
    except Exception as e:
        print(f"  ⚠️ technical.py: {e}")
        adx_desc = "数据不足"
    
    try:
        boll = 判断布林形态(最新)
    except Exception as e:
        print(f"  ⚠️ technical.py: {e}")
        boll = "数据不足"
    
    # 4. 方向强度
    try:
        l2 = level2_方向判断(最新)
        direction = l2.get("方向", "震荡")
        strength = l2.get("强度", 0)
    except Exception as e:
        print(f"  ⚠️ technical.py: {e}")
        direction = "未知"
        strength = 0
    
    # 5. 市场状态
    try:
        ms = 判断市场状态(indicator_df, 最新)
        state = ms.get("状态", "未知")
        confidence = ms.get("置信度", 0)
    except Exception as e:
        print(f"  ⚠️ technical.py: {e}")
        state = "未知"
        confidence = 0
    
    return {
        "indicators": indicators,
        "ma_alignment": ma_align,
        "macd_signal": macd_sig,
        "adx_description": adx_desc,
        "boll_status": boll,
        "direction": direction,
        "direction_strength": strength,
        "market_state": state,
        "market_confidence": confidence,
    }
