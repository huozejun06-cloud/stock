# ==============================================================================
# agents/committee.py — 委员会裁决 Agent (LLM 驱动)
# Phase C-9: 汇总 3 派意见 + 4 规则引擎，做出最终决策
# ==============================================================================

import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from typing import Dict, Any, Optional
from server.llm import create_llm_adapter


def finalize(
    trend_follower: Dict[str, Any] = None,
    value_investor: Dict[str, Any] = None,
    sentiment_trader: Dict[str, Any] = None,
    technical: Dict[str, Any] = None,
    chip: Dict[str, Any] = None,
    pattern: Dict[str, Any] = None,
    risk: Dict[str, Any] = None,
    stock_code: str = "",
) -> Dict[str, Any]:
    """
    委员会最终裁决。
    
    输入: 所有 Agent 的输出 (允许部分缺失)
    输出: {
        "final_signal": "BUY"/"WATCH"/"SELL",
        "total_score": 0~100,
        "confidence": 0.0~1.0,
        "consensus": "一致"|"多数一致"|"分歧严重",
        "debate_summary": str,
        "execution": {stop_loss, target_price, position, risk_reward},
        "risk_warning": str|None,
    }
    """
    
    t = trend_follower or {}
    v = value_investor or {}
    s = sentiment_trader or {}
    r = risk or {}
    ex = r.get("execution", {})
    
    # 1. 收集各派观点
    agents_info = [
        ("趋势派", t.get("stance", "未知"), t.get("score", 50), t.get("reasoning", "")[:80]),
        ("价值派", v.get("stance", "未知"), v.get("score", 50), v.get("reasoning", "")[:80]),
        ("情绪派", s.get("stance", "未知"), s.get("score", 50), s.get("reasoning", "")[:80]),
    ]
    
    一致数 = sum(1 for _, st, _, _ in agents_info if st == "看涨")
    看跌数 = sum(1 for _, st, _, _ in agents_info if st == "看跌")
    中性数 = sum(1 for _, st, _, _ in agents_info if st == "中性")
    
    # 2. LLM Prompt
    info_lines = "\n".join([
        f"- {name}: {stance}({sc}分) | {reason}"
        for name, stance, sc, reason in agents_info
    ])
    
    prompt = f"""你是投资总监，正在召开投资决策委员会会议。

各派分析师意见:
{info_lines}

技术指标摘要:
- MA排列: {(technical or {}).get('ma_alignment', '未知')}
- 市场状态: {(technical or {}).get('market_state', '未知')}
- 方向强度: {(technical or {}).get('direction_strength', 0)}

风控状态: {'允许交易' if r.get('trading_allowed', True) else '禁止交易'}

请做出最终裁决，输出 JSON:
{{
    "final_signal": "BUY"或"WATCH"或"SELL",
    "total_score": 0-100,
    "confidence": 0.0-1.0,
    "consensus": "一致"或"多数一致"或"分歧严重",
    "debate_summary": "分歧点分析和最终论断",
    "risk_warning": "主要风险提示或null"
}}"""
    
    # 3. LLM 调用
    try:
        adapter = create_llm_adapter("deepseek")
        result = adapter.safe_generate_decision(prompt)
        content = result.reasoning
        try:
            start = content.index("{")
            end = content.rindex("}") + 1
            parsed = json.loads(content[start:end])
            signal = parsed.get("final_signal", "WATCH")
        except Exception as e:
            print(f"  ⚠️ committee.py: {e}")
            signal = "WATCH"
    except Exception as e:
        print(f"  ⚠️ committee.py: {e}")
        signal = "WATCH"
    
    if signal == "BUY":
        stance = "看涨"
    elif signal == "SELL":
        stance = "看跌"
    else:
        stance = "中性"
    
    # 4. 兜底: 加权投票
    if signal == "WATCH":
        total = 一致数 + 看跌数 + 中性数
        if 一致数 > 看跌数 and 一致数 > 中性数:
            signal = "BUY"
            stance = "看涨"
        elif 看跌数 > 一致数 and 看跌数 > 中性数:
            signal = "SELL"
            stance = "看跌"
    
    # 5. 评分
    scores = [sc for _, _, sc, _ in agents_info]
    avg_score = sum(scores) / len(scores) if scores else 50
    
    # 6. 共识判定
    if 一致数 == 3 or 看跌数 == 3:
        consensus = "一致"
    elif 一致数 >= 2 or 看跌数 >= 2:
        consensus = "多数一致"
    else:
        consensus = "分歧严重"
    
    return {
        "final_signal": signal,
        "total_score": round(avg_score, 1),
        "confidence": round(avg_score / 100, 2),
        "consensus": consensus,
        "debate_summary": f"趋势派{agents_info[0][1]}, 价值派{agents_info[1][1]}, 情绪派{agents_info[2][1]} → 最终裁决: {signal}",
        "execution": {
            "stop_loss": ex.get("stop_loss", 0),
            "target_price": ex.get("target_price", 0),
            "position": ex.get("position", "0%"),
            "risk_reward": ex.get("risk_reward", 0),
        },
        "risk_warning": r.get("interpretation", None),
    }
