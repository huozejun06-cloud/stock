# ==============================================================================
# agents/pattern.py — Pattern Agent (规则引擎)
# Phase C-4: 6 种 K 线形态识别
# ==============================================================================

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
from typing import Dict, Any, Optional, List


def analyze(df_daily: pd.DataFrame = None, df_5min: list = None) -> Dict[str, Any]:
    """
    K 线形态识别。
    
    输入: df_daily — 日 K 线 DataFrame (用于形态识别_增强)
          df_5min — 5 分钟 K 线 list (用于 W 底检测，可选)
    输出: {
        "patterns_detected": [...],
        "bullish_count": int,     # 看涨形态数
        "bearish_count": int,     # 看跌形态数
        "overall_signal": str,    # 看涨/看跌/中性
        "interpretation": str,
    }
    """
    from 工具库.形态识别_增强 import (
        识别早晨之星, 识别黄昏之星,
        识别红三兵, 识别三只乌鸦,
        识别看涨吞没,
    )
    
    patterns = []
    
    if df_daily is not None and len(df_daily) >= 5:
        for detector, name in [
            (识别早晨之星, "早晨之星"),
            (识别黄昏之星, "黄昏之星"),
            (识别红三兵, "红三兵"),
            (识别三只乌鸦, "三只乌鸦"),
            (识别看涨吞没, "看涨吞没"),
        ]:
            try:
                result = detector(df_daily)
                if result.get("生效"):
                    patterns.append({
                        "name": result.get("形态", name),
                        "direction": result.get("方向", "未知"),
                        "score": result.get("评分", 0),
                    })
            except Exception as e:
                print(f"  ⚠️ pattern.py: {e}")
                continue
    
    # W 底检测（需要 5 分钟线，可选）
    if df_5min:
        try:
            from 工具库.形态识别 import detect_w_bottom
            w = detect_w_bottom(df_5min)
            if w.get("is_w_bottom"):
                patterns.append({
                    "name": "W底",
                    "direction": "看涨",
                    "score": w.get("score", 0),
                })
        except Exception as e:
            print(f"  ⚠️ pattern.py: {e}")
            pass
    
    bullish = sum(1 for p in patterns if p["direction"] == "看涨")
    bearish = sum(1 for p in patterns if p["direction"] == "看跌")
    
    if bullish > bearish:
        overall = "看涨"
    elif bearish > bullish:
        overall = "看跌"
    else:
        overall = "中性"
    
    if patterns:
        desc = f"检测到 {len(patterns)} 个形态: "
        desc += ", ".join([f"{p['name']}({p['direction']},{p['score']}分)" for p in patterns])
    else:
        desc = "未检测到明确形态"
    
    return {
        "patterns_detected": patterns,
        "bullish_count": bullish,
        "bearish_count": bearish,
        "overall_signal": overall,
        "interpretation": desc,
    }
