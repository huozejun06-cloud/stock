"""
最小可执行隔夜策略基础生存率测试
问一个最底层的问题：A股隔夜买入强势股（5%-7%），到底能不能赚钱？

策略：
  1. 选出昨日涨幅在 5%-7% 的股票
  2. 第二天开盘买入
  3. 统计：开盘买入收盘卖出 vs 开盘即卖

成本：单边0.05% + 滑点0.20% = 单边0.25%，双边0.50%
"""
import os
import sys
import pandas as pd
import numpy as np
from datetime import datetime

CACHE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "缓存")

# 成本参数
单边成本 = 0.0005   # 佣金0.05% + 滑点0.20% = 0.25%
双边成本 = 单边成本 * 2  # 0.50%


def 加载所有股票数据():
    """从缓存加载所有有日线数据的股票"""
    print("📂 扫描缓存数据...")
    股票列表 = []
    for f in os.listdir(CACHE_DIR):
        if f.endswith('_日K.csv'):
            代码 = f.replace('_日K.csv', '')
            股票列表.append(代码)
    print(f"   找到 {len(股票列表)} 只有缓存数据的股票")
    return sorted(股票列表)


def 分析单只股票(代码, df):
    """对单只股票执行策略信号检测"""
    if df.empty or len(df) < 10:
        return []
    
    结果 = []
    for i in range(1, len(df) - 1):  # 从第2行开始（需昨日数据），留1天算结果
        昨日涨跌 = df.iloc[i-1]['pct_chg']
        # 条件：昨日涨幅 5%-7%
        if pd.isna(昨日涨跌):
            continue
        if 5 <= 昨日涨跌 <= 7:
            row = df.iloc[i]
            开盘 = row['open']
            收盘 = row['close']
            日期 = row['date']
            
            if 开盘 <= 0:
                continue
            
            # 开盘涨幅 = (开盘/昨日收盘 - 1)
            昨日收盘 = df.iloc[i-1]['close']
            开盘涨幅 = (开盘 / 昨日收盘 - 1) * 100 if 昨日收盘 > 0 else 0
            
            # 当日收益（扣除成本）
            毛收益 = (收盘 - 开盘) / 开盘 * 100
            净收益 = 毛收益 - 双边成本 * 100
            
            # 高开低走判断：开盘涨幅 > 0 且 收盘 < 开盘
            是否高开低走 = 开盘 > 昨日收盘 and 收盘 < 开盘
            
            # 年份
            年份 = pd.Timestamp(日期).year
            
            结果.append({
                '代码': 代码,
                '日期': 日期,
                '年份': 年份,
                '昨日涨跌': round(昨日涨跌, 2),
                '开盘涨幅': round(开盘涨幅, 2),
                '当日毛收益': round(毛收益, 2),
                '当日净收益': round(净收益, 2),
                '开盘价': 开盘,
                '收盘价': 收盘,
                '高开低走': 是否高开低走,
            })
    
    return 结果


def 打印结果(所有结果):
    """输出格式化统计"""
    df = pd.DataFrame(所有结果)
    if df.empty:
        print("\n❌ 无任何交易信号")
        return
    
    总交易 = len(df)
    覆盖股票 = df['代码'].nunique()
    
    print("\n" + "=" * 60)
    print("📊 隔夜策略基础生存率测试")
    print("=" * 60)
    
    print(f"\n📈 总览")
    print(f"   数据范围: {df['日期'].min()} ~ {df['日期'].max()}")
    print(f"   总交易次数: {总交易}")
    print(f"   覆盖股票: {覆盖股票} 只")
    print(f"   策略: 昨日涨幅 5%-7% → 次日开盘买入收盘卖出")
    print(f"   交易成本: 单边0.25% | 双边0.50%（含佣金+滑点）")
    
    # 核心指标
    胜率 = (df['当日净收益'] > 0).sum() / 总交易 * 100
    期望收益 = df['当日净收益'].mean()
    中位收益 = df['当日净收益'].median()
    
    # 高开率
    高开数 = (df['开盘涨幅'] > 0).sum()
    高开率 = 高开数 / 总交易 * 100
    高开低走数 = df['高开低走'].sum()
    高开低走率 = 高开低走数 / 高开数 * 100 if 高开数 > 0 else 0
    
    # 最大连续亏损
    连亏序列 = (df['当日净收益'] < 0).astype(int).groupby(
        (df['当日净收益'] >= 0).cumsum()
    ).cumsum()
    最大连续亏损 = 连亏序列.max()
    
    print(f"\n🎯 核心指标")
    print(f"   胜率(扣费后): {胜率:.1f}%")
    print(f"   期望收益(扣费后): {期望收益:.2f}%")
    print(f"   中位收益(扣费后): {中位收益:.2f}%")
    print(f"   高开率: {高开率:.1f}%")
    print(f"   高开低走率: {高开低走率:.1f}%")
    print(f"   最大连续亏损次数: {最大连续亏损}")
    
    # 判定
    print(f"\n📋 判定")
    if 期望收益 > 0:
        print(f"   🟢 期望收益 > 0 → 隔夜策略有基础生存价值")
        if 胜率 > 55:
            print(f"   🟢 胜率 {胜率:.1f}% > 55% → 策略有Alpha")
        else:
            print(f"   🟡 胜率 {胜率:.1f}% → 虽正期望但接近随机，需做A-H优化")
    else:
        print(f"   🔴 期望收益 < 0 → 隔夜策略本身不存在Alpha")
        print(f"   🔴 建议放弃隔夜策略，改做趋势策略(5-10日持有)")
    
    # 各年度统计
    print(f"\n📅 各年度统计")
    print(f"{'年份':<8} {'交易次数':<10} {'胜率':<10} {'期望收益':<12} {'高开率':<10} {'高开低走率':<12}")
    print(f"{'-'*60}")
    for 年份 in sorted(df['年份'].unique()):
        年df = df[df['年份'] == 年份]
        年交易 = len(年df)
        年胜率 = (年df['当日净收益'] > 0).sum() / 年交易 * 100
        年期望 = 年df['当日净收益'].mean()
        年高开率 = (年df['开盘涨幅'] > 0).sum() / 年交易 * 100
        年高高走 = 年df[年df['开盘涨幅'] > 0]
        年高开低走率 = (年高高走[年高高走['高开低走'] == True].shape[0]) / (年高高走.shape[0]) * 100 if len(年高高走) > 0 else 0
        print(f"{年份:<8} {年交易:<10} {年胜率:.1f}%{'':<4} {年期望:+.2f}%{'':<6} {年高开率:.1f}%{'':<4} {年高开低走率:.1f}%")
    
    # 保存
    输出路径 = os.path.join(os.path.dirname(os.path.abspath(__file__)), "生存率测试结果.csv")
    df.to_csv(输出路径, index=False, encoding='utf-8-sig')
    print(f"\n💾 详细数据已保存至: {输出路径}")


def main():
    开始时间 = datetime.now()
    print("=" * 60)
    print("🧪 【隔夜策略基础生存率测试】")
    print(f"   启动时间: {开始时间.strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    股票列表 = 加载所有股票数据()
    if not 股票列表:
        print("❌ 无可用缓存数据")
        return
    
    所有结果 = []
    for i, 代码 in enumerate(股票列表):
        csv_path = os.path.join(CACHE_DIR, f"{代码}_日K.csv")
        try:
            df = pd.read_csv(csv_path, parse_dates=['date'])
            df = df.sort_values('date').reset_index(drop=True)
            单只结果 = 分析单只股票(代码, df)
            所有结果.extend(单只结果)
        except:
            pass
        
        # 进度
        if (i + 1) % 10 == 0 or i == len(股票列表) - 1:
            print(f"   📊 进度: {i+1}/{len(股票列表)} | 已发现 {len(所有结果)} 个信号")
    
    总耗时 = (datetime.now() - 开始时间).total_seconds()
    print(f"\n⏱ 耗时: {总耗时:.0f} 秒")
    
    打印结果(所有结果)
    
    print(f"\n   完成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == "__main__":
    main()
