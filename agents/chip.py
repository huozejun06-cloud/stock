# ==============================================================================
# agents/chip.py — Chip Agent (规则引擎)
# Phase C-3: 筹码分布 + 主力行为分析
# ==============================================================================

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import numpy as np
from typing import Dict, Any, Optional


def analyze(df: pd.DataFrame, current_price: float = None) -> Dict[str, Any]:
    """
    筹码分布 + 主力行为分析。
    
    输入: OHLCV DataFrame (至少 60 行)
    输出: {
        "cost_concentration": 0~100,  # 成本集中度
        "profit_ratio": 0~100,        # 获利盘比例
        "average_cost": float,        # 平均持仓成本
        "support_levels": [float],    # 支撑位
        "resistance_levels": [float], # 压力位
        "capital_behavior": str,     # 主力行为
        "interpretation": str,       # 一句话解读
    }
    """
    if df is None or len(df) < 20:
        return {"error": "数据不足 (至少 20 行)"}
    
    from 工具库.筹码分布 import 计算筹码分布
    
    最新价 = current_price or float(df['close'].iloc[-1])
    
    # 1. 筹码分布计算
    try:
        chip = 计算筹码分布(df, 回看天数=200)
        if "错误" in chip:
            return {"error": chip["错误"]}
    except Exception as e:
        return {"error": f"筹码计算失败: {e}"}
    
    avg_cost = round(float(chip.get("平均成本", 最新价)), 2)
    concentration = round(float(chip.get("成本集中度", 0)), 1)
    profit_ratio = round(float(chip.get("获利盘比例", 0)), 1)
    
    # 解析支撑/压力位
    peaks = chip.get("峰谷分析", "")
    支撑 = chip.get("支撑位", [])
    压力 = chip.get("压力位", [])
    if isinstance(支撑, list) and len(支撑) > 0:
        支撑主 = round(float(支撑[0]), 2)
    else:
        支撑主 = round(最新价 * 0.95, 2)
    if isinstance(压力, list) and len(压力) > 0:
        压力主 = round(float(压力[0]), 2)
    else:
        压力主 = round(最新价 * 1.05, 2)
    
    # 2. 主力行为判断
    try:
        from 工具库.交易决策引擎 import 判断主力行为
        latest = df.iloc[-1].to_dict() if len(df) > 0 else {}
        prev = df.iloc[-2].to_dict() if len(df) > 1 else latest
        behavior = 判断主力行为(latest, prev, df, {"主力净流入": "0"})
        capital_behavior = behavior.get("行为", "数据不足")
    except Exception as e:
        print(f"  ⚠️ chip.py: {e}")
        capital_behavior = "数据不足"
    
    # 3. 解读
    if concentration > 70:
        interp = f"筹码高度集中 ({concentration:.0f}%)，主力控盘度高"
    elif concentration > 40:
        interp = f"筹码适度集中 ({concentration:.0f}%)，存在博弈空间"
    else:
        interp = f"筹码分散 ({concentration:.0f}%)，主力未明显控盘"
    
    if profit_ratio > 80:
        interp += "，获利盘占比高，注意抛压"
    elif profit_ratio < 30:
        interp += "，多数持仓被套，抛压较小"
    
    interp += f"，支撑{支撑主}，压力{压力主}"
    
    return {
        "cost_concentration": concentration,
        "profit_ratio": profit_ratio,
        "average_cost": avg_cost,
        "support_levels": [支撑主],
        "resistance_levels": [压力主],
        "capital_behavior": capital_behavior,
        "current_price": round(最新价, 2),
        "interpretation": interp,
    }
