# ==============================================================================
# agents/value_investor.py — 价值派 Agent (LLM 驱动)
# Phase C-7: 私募研究员视角，好公司好价格
# ==============================================================================

import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from typing import Dict, Any, Optional


def debate(chip: Dict[str, Any] = None,
           technical: Dict[str, Any] = None,
           risk: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    价值派立场分析。
    输出: {stance, score, confidence, reasoning, key_factors, risk_warning}
    """
    from server.llm import create_llm_adapter
    
    ch = chip or {}
    ind = (technical or {}).get("indicators", {})
    
    prompt = f"""你是一个有5年经验的私募研究员。
你的信条是"好公司好价格，估值合理才是硬道理"。
请从价值和估值角度分析以下数据。

筹码结构:
- 成本集中度: {ch.get('cost_concentration', 0)} (越高越好)
- 获利盘比例: {ch.get('profit_ratio', 0)}%
- 平均成本: {ch.get('average_cost', 0)}
- 当前价: {ch.get('current_price', 0)}
- 主力行为: {ch.get('capital_behavior', '未知')}

技术参考:
- MA20: {ind.get('MA20', 0)} (价值参考线)
- BIAS20: {ind.get('BIAS20', 0)} (乖离率)
- 布林中轨: {ind.get('布林中轨', 0)}

风控状态: {'允许交易' if risk and risk.get('trading_allowed') else '禁止交易'}

请输出 JSON 格式:
{{
    "stance": "看涨"或"看跌"或"中性",
    "score": 0-100,
    "confidence": 0.0-1.0,
    "reasoning": "分析理由",
    "key_factors": ["因素1", "因素2"],
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
            print(f"  ⚠️ value_investor.py: {e}")
            pass
    except Exception as e:
        print(f"  ⚠️ value_investor.py: {e}")
        pass
    
    # 兜底: 筹码集中度 + 获利盘
    conc = ch.get("cost_concentration", 0)
    profit = ch.get("profit_ratio", 50)
    if conc > 60 and profit < 70:
        return {"stance": "看涨", "score": 60, "confidence": 0.5,
                "reasoning": "规则兜底: 筹码集中且获利盘适中", "key_factors": [], "risk_warning": None}
    elif profit > 85:
        return {"stance": "看跌", "score": 35, "confidence": 0.5,
                "reasoning": "规则兜底: 获利盘过高，抛压风险", "key_factors": [], "risk_warning": None}
    return {"stance": "中性", "score": 50, "confidence": 0.4,
            "reasoning": "规则兜底: 无明显价值信号", "key_factors": [], "risk_warning": None}
