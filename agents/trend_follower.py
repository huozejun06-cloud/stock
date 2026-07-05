# ==============================================================================
# agents/trend_follower.py — 趋势派 Agent (LLM 驱动)
# Phase C-6: 游资操盘手视角，顺势而为
# ==============================================================================

import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from typing import Dict, Any, Optional


def _fmt(items):
    """格式化列表"""
    if not items: return "无"
    return ", ".join(items[:3])

def _fmt_notice(notice):
    if not notice: return "无"
    risk = notice.get("有风险公告")
    return f"有风险公告" if risk else "无风险"

def _format_flow(flow):
    """格式化资金流向数据"""
    if flow is None:
        return "N/A (非交易时段)"
    try:
        v = float(flow.get("主力净流入", 0))
        if v > 0:
            return f"+{v/10000:.0f}万 (净流入)"
        elif v < 0:
            return f"{v/10000:.0f}万 (净流出)"
        return "0 (持平)"
    except Exception as e:
        print(f"  ⚠️ trend_follower.py: {e}")
        return "N/A"


def _format_longhu(lh):
    """格式化龙虎榜数据"""
    if not lh or not lh.get("有龙虎榜"):
        return "无 (今日无上榜)"
    youzi = lh.get("知名游资", [])
    if youzi:
        names = ", ".join([y.get("席位", "")[:8] for y in youzi[:3]])
        return f"✅ 有知名游资: {names}"
    return f"有龙虎榜, 净买额: {lh.get('净买入额', 'N/A')}"


def _format_flow(flow):
    """格式化资金流向数据"""
    if flow is None:
        return "N/A (非交易时段)"
    try:
        v = float(flow.get("主力净流入", 0))
        if v > 0:
            return f"+{v/10000:.0f}万 (净流入)"
        elif v < 0:
            return f"{v/10000:.0f}万 (净流出)"
        return "0 (持平)"
    except Exception as e:
        print(f"  ⚠️ trend_follower.py: {e}")
        return "N/A"


def debate(technical: Dict[str, Any] = None,
           chip: Dict[str, Any] = None,
           pattern: Dict[str, Any] = None,
           risk: Dict[str, Any] = None,
           fund_flow: Dict[str, Any] = None,
           longhu: Dict[str, Any] = None,
           news_count: int = 0,
           topics: list = None,
           notice: dict = None) -> Dict[str, Any]:
    """
    趋势派立场分析。
    
    输入: 4 个规则 Agent 的结构化输出
    输出: {
        "stance": "看涨"|"看跌"|"中性",
        "score": 0~100,
        "confidence": 0.0~1.0,
        "reasoning": str,
        "key_factors": [str],
        "risk_warning": str|None,
    }
    """
    from config import DEEPSEEK_API_KEY
    from server.llm import create_llm_adapter
    
    tech = technical or {}
    ind = tech.get("indicators", {})
    
    # 1. 构建 LLM Prompt
    prompt = f"""你是一个有10年经验的游资操盘手。
你的信条是"顺势而为，强者恒强，只做主升浪"。
请从趋势交易的角度分析以下股票数据。

技术指标:
- MA排列: {tech.get('ma_alignment', '未知')}
- MACD信号: {tech.get('macd_signal', '未知')}
- ADX: {ind.get('ADX', 0)} ({tech.get('adx_description', '未知')})
- 方向强度: {tech.get('direction_strength', 0)} (-100~100)
- 市场状态: {tech.get('market_state', '未知')}
- RSI14: {ind.get('RSI14', 50)}
- BIAS20: {ind.get('BIAS20', 0)}

筹码数据:
- 主力行为: {chip.get('capital_behavior', '未知') if chip else '未知'}

形态信号: {pattern.get('overall_signal', '中性') if pattern else '中性'}

风控状态: {'允许交易' if risk and risk.get('trading_allowed') else '禁止交易'}

请输出 JSON 格式 (不要其他文字):
{{
    "stance": "看涨"或"看跌"或"中性",
    "score": 0-100的数值评分,
    "confidence": 0.0-1.0的置信度,
    "reasoning": "你的分析理由",
    "key_factors": ["关键因素1", "关键因素2"],
    "risk_warning": "风险提示或null"
}}"""
    
    # 2. 调用 LLM
    try:
        adapter = create_llm_adapter("deepseek")
        result = adapter.safe_generate_decision(prompt)
        content = result.reasoning
        
        # 尝试从回复中提取 JSON
        try:
            # 找第一个 { 和最后一个 }
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
            print(f"  ⚠️ trend_follower.py: {e}")
            pass
    except Exception as e:
        print(f"  ⚠️ trend_follower.py: {e}")
        pass
    
    # 3. 兜底: 用规则引擎评分
    strength = tech.get("direction_strength", 0)
    if strength > 20:
        return {"stance": "看涨", "score": 65, "confidence": 0.6,
                "reasoning": "规则兜底: 方向强度为正，MACD多头", "key_factors": [], "risk_warning": None}
    elif strength < -20:
        return {"stance": "看跌", "score": 35, "confidence": 0.6,
                "reasoning": "规则兜底: 方向强度为负，趋势偏空", "key_factors": [], "risk_warning": None}
    return {"stance": "中性", "score": 50, "confidence": 0.5,
            "reasoning": "规则兜底: 无明显趋势信号", "key_factors": [], "risk_warning": None}
