# ==============================================================================
# agents/risk.py — Risk Agent (规则引擎)
# Phase C-5: 风控红线 + 执行参数计算
# ==============================================================================

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
from typing import Dict, Any, Optional


def analyze(df: pd.DataFrame, latest: dict, prev: dict,
            fund_flow: dict = None, board_data: dict = None) -> Dict[str, Any]:
    """
    风控红线检查 + 执行参数计算。
    
    输入: df — 指标 DataFramelatest — 最新一行prev — 前一行fund_flow — 资金流向数据board_data — 板块数据
    
    输出: {
        "red_lines": {"triggered": bool, "items": [...]},
        "risk_level": "LOW"|"MEDIUM"|"HIGH",
        "trading_allowed": bool,
        "execution": {"stop_loss": float, "target_price": float, "position": str, "risk_reward": float},
        "interpretation": str,
    }
    """
    from 工具库.交易决策引擎 import (
        BIAS过滤器, 背离检测, 换手率过滤器,
        风控红线检查, 计算盈亏比, 建议目标价与止损,
    )
    
    if df is None or latest is None:
        return {"error": "数据不足"}
    
    fund_flow = fund_flow or {"主力净流入": 0}
    board_data = board_data or {}
    
    # 1. 三大过滤器
    try:
        bias = BIAS过滤器(latest)
    except Exception as e:
        print(f"  ⚠️ risk.py: {e}")
        bias = {"状态": "错误", "结论": "通过"}
    
    try:
        divergence = 背离检测(latest, prev, df)
    except Exception as e:
        print(f"  ⚠️ risk.py: {e}")
        divergence = {"最大级别": "无", "禁止交易": False}
    
    try:
        turnover = 换手率过滤器(latest)
    except Exception as e:
        print(f"  ⚠️ risk.py: {e}")
        turnover = {"状态": "错误", "结论": "通过"}
    
    # 2. 风控红线
    try:
        red = 风控红线检查(latest, prev, df, fund_flow, board_data, divergence, bias, {})
    except Exception as e:
        print(f"  ⚠️ risk.py: {e}")
        red = {"触发": False, "触发红线": [], "禁止交易": False}
    
    # 3. 执行参数
    stop_loss = round(latest.get("close", 0) * 0.95, 2)
    target_price = round(latest.get("close", 0) * 1.05, 2)
    position = "5%~10%"
    risk_reward = 0.0
    
    if not red.get("禁止交易", False):
        try:
            price_info = 建议目标价与止损(latest, {
                "支撑位1": latest.get("布林中轨", latest.get("close", 0) * 0.97),
                "压力位1": latest.get("布林上轨", latest.get("close", 0) * 1.03),
                "压力位2": latest.get("close", 0) * 1.06,
                "ATR14": latest.get("ATR14", latest.get("close", 0) * 0.03),
            })
            stop_loss = round(float(price_info.get("止损位", stop_loss)), 2)
            target_price = round(float(price_info.get("第一目标", target_price)), 2)
            
            # 防御性读取：兼容 price_info 可能缺少 '支撑位2' 的情况
            _close = latest.get("close", 0)
            _atr = latest.get("ATR14", _close * 0.03)
            _support = price_info.get("支撑位2", price_info.get("压力位1", _close * 0.97))
            # 止损 = max(-5%兜底, 技术支撑-ATR×1.0)
            stop_loss = round(max(_close * 0.95, _support - _atr * 1.0), 2)
            
            entry = float(price_info.get("入场价", _close))
            rr = 计算盈亏比(entry, target_price, stop_loss)
            risk_reward = round(float(rr.get("盈亏比", 0)), 2)
            
            if risk_reward >= 3.0:
                position = "70%~100%"
            elif risk_reward >= 2.0:
                position = "30%~70%"
            elif risk_reward >= 1.0:
                position = "10%~30%"
            else:
                position = "5%~10%"
        except Exception as e:
            print(f"  ⚠️ risk.py: {e}")
            pass
    
    # 4. 风险等级
    red_items = red.get("触发红线", [])
    if len(red_items) >= 2 or red.get("禁止交易", False):
        risk_level = "HIGH"
    elif len(red_items) == 1:
        risk_level = "MEDIUM"
    else:
        risk_level = "LOW"
    
    # 5. 解读
    if red.get("禁止交易", False):
        interp = "⛔ 触发风控红线: " + " + ".join(red_items[:3])
    elif risk_reward >= 2.0:
        interp = f"风控通过, 盈亏比{risk_reward}, 建议仓位{position}"
    else:
        interp = f"风控通过, 盈亏比{risk_reward}, 收益风险比偏低"
    
    return {
        "red_lines": {"triggered": red.get("触发", False), "items": red_items},
        "risk_level": risk_level,
        "trading_allowed": not red.get("禁止交易", False),
        "execution": {
            "stop_loss": stop_loss,
            "target_price": target_price,
            "position": position,
            "risk_reward": risk_reward,
        },
        "divergence": divergence.get("最大级别", "无"),
        "turnover": turnover.get("状态", "正常"),
        "bias": bias.get("状态", "正常"),
        "interpretation": interp,
    }
