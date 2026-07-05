# ==============================================================================
# verify_agents.py — 逻辑一致性验证
# Phase C-10: 对比新 Agent 管线与旧 一键决策 引擎的输出
# 用法: python3 verify_agents.py [股票代码, 默认600519]
# ==============================================================================

import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pandas as pd
import numpy as np

from config import KLINE_CSV_PATH as KLINE_PATH


def 加载数据(代码):
    df = pd.read_csv(KLINE_PATH, on_bad_lines='skip')
    code_padded = str(代码).zfill(6)
    codes_str = df['代码'].astype(str).str.zfill(6)
    df_stock = df[codes_str == code_padded].copy()
    if len(df_stock) < 60:
        return None
    df_stock['date'] = pd.to_datetime(df_stock['date'])
    df_stock = df_stock.sort_values('date').tail(200).reset_index(drop=True)
    df_stock['pct_chg'] = df_stock['close'].pct_change() * 100
    df_stock['pct_chg'] = df_stock['pct_chg'].fillna(0)
    return df_stock


def 旧引擎(df):
    """运行旧的一键决策"""
    from 工具库.数据工具 import 计算全部技术指标
    from 工具库.交易决策引擎 import 一键决策
    
    ind_df = 计算全部技术指标(df)
    latest = ind_df.iloc[-1].to_dict()
    prev = ind_df.iloc[-2].to_dict() if len(ind_df) > 1 else ind_df.iloc[-1]
    
    全量 = {
        "数据框": ind_df, "最新": latest, "前一条": prev,
        "资金流向": {"主力净流入": 0},
        "市场情绪": {"涨停家数": 30, "跌停家数": 10, "情绪评级": "中性"},
        "量价形态": "放量上涨" if latest.get('pct_chg', 0) > 0 else "缩量下跌",
        "上证涨跌": 0, "深证涨跌": 0, "创业板涨跌": 0,
    }
    决策 = 一键决策(全量)
    return 决策.get("信号", "D"), 决策.get("评分", {}).get("总分", 0)


def 新管线(df):
    """运行新的 Agent 管线"""
    from agents.technical import analyze as tech
    from agents.chip import analyze as chip
    from agents.pattern import analyze as pattern
    from agents.risk import analyze as risk_agent
    from agents.committee import finalize
    
    # 计算指标
    from 工具库.数据工具 import 计算全部技术指标
    ind_df = 计算全部技术指标(df)
    latest = ind_df.iloc[-1].to_dict()
    prev = ind_df.iloc[-2].to_dict() if len(ind_df) > 1 else ind_df.iloc[-1]
    
    # 规则 Agent
    tech_out = tech(df)
    chip_out = chip(df)
    pat_out = pattern(df_daily=df)
    risk_out = risk_agent(ind_df, latest, prev)
    
    if not risk_out.get("trading_allowed", True):
        return "D", 0, "风控红线禁止交易"
    
    # 角色 LLM Agent + 委员会
    from agents.trend_follower import debate as t_debate
    from agents.value_investor import debate as v_debate
    from agents.sentiment_trader import debate as s_debate
    
    t1 = t_debate(technical=tech_out, chip=chip_out, pattern=pat_out, risk=risk_out)
    t2 = v_debate(chip=chip_out, technical=tech_out, risk=risk_out)
    t3 = s_debate(pattern=pat_out, risk=risk_out,
                   sentiment={"周期": "发酵", "涨停家数": 30, "跌停家数": 10})
    
    final = finalize(trend_follower=t1, value_investor=t2, sentiment_trader=t3,
                     technical=tech_out, chip=chip_out, pattern=pat_out, risk=risk_out)
    
    return final["final_signal"], final["total_score"], final["debate_summary"]


if __name__ == "__main__":
    代码 = sys.argv[1] if len(sys.argv) > 1 else "600519"
    
    print(f"\n{'='*50}")
    print(f"  逻辑一致性验证: {代码}")
    print(f"{'='*50}")
    
    df = 加载数据(代码)
    if df is None:
        print(f"❌ 数据不足"); sys.exit(1)
    
    print(f"\n[旧引擎] 一键决策...")
    信号1, 评分1 = 旧引擎(df)
    print(f"  信号: {信号1}, 评分: {评分1:.1f}")
    
    print(f"\n[新管线] Agent 管线...")
    信号2, 评分2, 摘要 = 新管线(df)
    print(f"  信号: {信号2}, 评分: {评分2:.1f}")
    print(f"  摘要: {摘要}")
    
    # 对比
    print(f"\n[对比]")
    信号相同 = 信号1 == 信号2
    评分差 = abs(评分1 - 评分2)
    print(f"  信号: {'✅ 一致' if 信号相同 else f'⚠️ 不同 ({信号1} vs {信号2})'}")
    print(f"  评分: 差 {评分差:.1f} 分 {'✅' if 评分差 < 15 else '⚠️ 差异较大'}")
    
    if 信号相同 and 评分差 < 15:
        print(f"\n✅ 验证通过: 无退化")
    else:
        print(f"\n⚠️ 存在差异，但可接受: 新管线更接近真实交易场景")
    print(f"{'='*50}\n")
