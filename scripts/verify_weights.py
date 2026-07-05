# ==============================================================================
# verify_weights.py — 评分权重 Mini 回测验证
# Phase A Task A-7: 用历史数据验证现有评分权重的有效性
# 用法: python3 verify_weights.py [股票代码, 默认600519]
# ==============================================================================

import sys, os
import pandas as pd, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import KLINE_CSV_PATH as KLINE_PATH

def 加载全局数据(代码: str, 最少天数: int = 120):
    df = pd.read_csv(KLINE_PATH, on_bad_lines='skip')
    code_padded = str(代码).zfill(6)
    codes_str = df['代码'].astype(str).str.zfill(6)
    df_stock = df[codes_str == code_padded].copy()
    if len(df_stock) < 最少天数:
        return None
    df_stock['date'] = pd.to_datetime(df_stock['date'])
    df_stock = df_stock.sort_values('date').reset_index(drop=True)
    # 用收盘价计算涨跌幅（不依赖原始数据列）
    df_stock['pct_chg'] = df_stock['close'].pct_change() * 100
    df_stock['pct_chg'] = df_stock['pct_chg'].fillna(0)
    df_stock['turnover'] = df_stock['turnover'].fillna(0)
    df_stock['volume'] = df_stock['volume'].fillna(0)
    print(f"  ✅ {len(df_stock)} 行, {df_stock['date'].min().date()} → {df_stock['date'].max().date()}")
    return df_stock

def 运行回测(df, 股票名称="未知"):
    from 工具库.数据工具 import 计算全部技术指标
    from 工具库.交易决策引擎 import 一键决策
    
    结果 = {"信号统计": {"A": 0, "B": 0, "C": 0, "D": 0}, "次日收益": [], "总次": 0}
    
    for i in range(60, len(df) - 1):
        窗口 = df.iloc[:i + 1].copy()
        try:
            指标df = 计算全部技术指标(窗口)
            最新 = 指标df.iloc[-1].to_dict()
            前一条 = 指标df.iloc[-2].to_dict()
        except:
            continue
        
        if pd.isna(最新.get('MA5')) or pd.isna(最新.get('ADX')):
            continue
        
        最新['pct_chg'] = 最新.get('pct_chg', 0)  # 确保 pct_chg 存在
        前一条['pct_chg'] = 前一条.get('pct_chg', 0)
        
        全量 = {
            "数据框": 指标df, "最新": 最新, "前一条": 前一条,
            "资金流向": {"主力净流入": 0},
            "市场情绪": {"涨停家数": 30, "跌停家数": 10, "情绪评级": "中性"},
            "量价形态": "放量上涨" if 最新.get('pct_chg', 0) > 0 else "缩量下跌",
            "上证涨跌": 0, "深证涨跌": 0, "创业板涨跌": 0,
        }
        
        try:
            决策 = 一键决策(全量)
            信号 = 决策.get("信号", "D")
            结果["信号统计"][信号] = 结果["信号统计"].get(信号, 0) + 1
            结果["总次"] += 1
            
            # 次日涨跌幅（用重新计算的 pct_chg）
            次日涨跌 = df.iloc[i + 1]['pct_chg']
            结果["次日收益"].append({
                "信号": 信号,
                "涨跌幅": 次日涨跌,
                "评分": 决策.get("评分", {}).get("总分", 0),
                "日期": str(df.iloc[i]['date'])[:10]
            })
        except:
            continue
    
    return 结果

def 报告(结果, 股票名称):
    统计 = 结果["信号统计"]
    收益 = 结果["次日收益"]
    总次 = 结果["总次"]
    
    if not 收益:
        print("\n❌ 无有效信号")
        return
    
    print(f"\n{'='*55}")
    print(f"  📊 评分权重验证报告")
    print(f"{'='*55}")
    print(f"  测试标的: {股票名称}")
    print(f"  测试周期: {收益[0]['日期']} → {收益[-1]['日期']}")
    print(f"  总信号数: {总次}")
    
    for s in ['A', 'B', 'C', 'D']:
        cnt = 统计.get(s, 0)
        if cnt > 0:
            sr = [r['涨跌幅'] for r in 收益 if r['信号'] == s]
            wr = sum(1 for r in sr if r > 0) / len(sr) * 100 if sr else 0
            avg = np.mean(sr) if sr else 0
            print(f"  {s}信号: {cnt}次 | 胜率{wr:5.1f}% | 平均{avg:+7.3f}%")
    
    涨幅 = [r['涨跌幅'] for r in 收益]
    非零涨幅 = [v for v in 涨幅 if abs(v) > 0.001]
    
    print(f"  {'─'*50}")
    整体胜率 = sum(1 for v in 涨幅 if v > 0) / len(涨幅) * 100
    平均收益 = np.mean(涨幅)
    收益std = np.std(涨幅)
    夏普 = (平均收益 / 收益std) * np.sqrt(244) if 收益std > 0 else 0
    最大回撤 = min(涨幅)
    
    print(f"  整体胜率:   {整体胜率:6.1f}%")
    print(f"  平均盈亏:   {平均收益:+7.3f}%")
    print(f"  夏普比率:   {夏普:6.2f}")
    print(f"  最大单日回撤: {最大回撤:7.2f}%")
    print(f"  非零样本:   {len(非零涨幅)}/{len(涨幅)}")
    
    if 夏普 >= 1.0:
        print(f"\n  ✅ 结论: 当前权重表现优秀 (夏普≥1.0)")
    elif 夏普 >= 0.5:
        print(f"\n  🟡 结论: 当前权重表现可接受 (夏普≥0.5)")
    else:
        print(f"\n  ⚠️ 结论: 当前权重表现一般 (夏普<0.5), 建议调整")
    print(f"{'='*55}\n")

if __name__ == "__main__":
    股票代码 = sys.argv[1] if len(sys.argv) > 1 else "600519"
    print(f"\n📂 加载数据: {股票代码}")
    df = 加载全局数据(股票代码)
    if df is None:
        print("❌ 数据不足"); sys.exit(1)
    
    df = df.tail(500).reset_index(drop=True)
    股票名称 = f"{股票代码}"
    结果 = 运行回测(df, 股票名称)
    报告(结果, 股票名称)
