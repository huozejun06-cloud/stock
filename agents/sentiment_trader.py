# ==============================================================================
# agents/sentiment_trader.py — 情绪派 Agent (LLM 驱动)
# Phase C-8: 量化交易员视角，情绪周期 + 板块轮动
# ==============================================================================

import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from typing import Dict, Any, Optional


def debate(pattern: Dict[str, Any] = None,
           sentiment: Dict[str, Any] = None,
           sector: Dict[str, Any] = None,
           risk: Dict[str, Any] = None,
           longhu: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    情绪派立场分析。
    输出: {stance, score, confidence, reasoning, key_factors, risk_warning}
    """
    from server.llm import create_llm_adapter
    
    pat = pattern or {}
    sent = sentiment or {}
    
    cycle = sent.get("周期", "未知")
    zt = sent.get("涨停家数", 0)
    dt = sent.get("跌停家数", 0)
    
    prompt = f"""你是一个专注情绪周期的量化交易员。
你的信条是"情绪周期决定仓位，涨停梯队决定方向"。
请从市场情绪和板块轮动角度分析。

形态信号: {pat.get('overall_signal', '中性')}
形态详情: {pat.get('interpretation', '无')}

市场情绪:
- 情绪周期: {cycle}
- 涨停: {zt} | 跌停: {dt}
- 市场温度: {'活跃' if zt > 50 else '正常' if zt > 20 else '低迷'}
- 板块强度: {sector.get('板块强度', '未知') if sector else '未知'}
- 领涨板块: {sector.get('领涨板块', '未知') if sector else '未知'}

龙虎榜:
- 有龙虎榜: {longhu.get('有龙虎榜', False) if longhu else False}
- 知名游资: {', '.join([x['席位'] for x in longhu.get('知名游资', [])]) if longhu and longhu.get('知名游资') else '无'}
- 净买入额: {longhu.get('净买入额', 'N/A') if longhu else 'N/A'}

风控状态: {'允许交易' if risk and risk.get('trading_allowed') else '禁止交易'}

请输出 JSON:
{{
    "stance": "看涨"或"看跌"或"中性",
    "score": 0-100,
    "confidence": 0.0-1.0,
    "reasoning": "分析理由",
    "key_factors": ["因素1"],
    "risk_warning": "风险提示或null"
}}"""
    
    try:
        adapter = create_llm_adapter("deepseek")
        result = adapter.safe_generate_decision(prompt)
        content = result.reasoning
        try:
            import re
            _match = re.search(r'\{.*\}', content, re.DOTALL)
            if not _match:
                raise ValueError("no json in llm response")
            parsed = json.loads(_match.group())
            return {
                "stance": parsed.get("stance", "中性"),
                "score": max(0, min(100, int(parsed.get("score", 50)))),
                "confidence": max(0.0, min(1.0, float(parsed.get("confidence", 0.5)))),
                "reasoning": parsed.get("reasoning", content)[:300],
                "key_factors": parsed.get("key_factors", []),
                "risk_warning": parsed.get("risk_warning"),
            }
        except Exception as e:
            print(f"  ⚠️ sentiment_trader.py: {e}")
            pass
    except Exception as e:
        print(f"  ⚠️ sentiment_trader.py: {e}")
        pass
    
    # 兜底
    zt = sent.get("涨停家数", 0)
    if zt > 50:
        return {"stance": "看涨", "score": 65, "confidence": 0.5,
                "reasoning": "规则兜底: 涨停家数>50", "key_factors": [], "risk_warning": None}
    elif zt < 10:
        return {"stance": "看跌", "score": 35, "confidence": 0.5,
                "reasoning": "规则兜底: 涨停家数<10", "key_factors": [], "risk_warning": None}
    return {"stance": "中性", "score": 50, "confidence": 0.4,
            "reasoning": "规则兜底: 情绪中性", "key_factors": [], "risk_warning": None}
