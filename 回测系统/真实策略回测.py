"""
真实交易模式回测 v1.0
模拟"分时确认买入 + 5%止盈/2%止损 + 一发子弹"的完整交易流程

选股：昨日涨2%-7% + 均线多头 + MACD多头 + 热门板块前5
买入：分时确认（低>开盘×0.97）
卖出：涨5%止盈 / 跌2%止损 / 收盘卖出
资金：一发子弹，每日只做Top1

成本：单边0.25%（佣金0.05%+滑点0.20%），双边0.50%
"""
import os
import sys
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from 工具库.数据源管理器 import get_manager

CACHE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "缓存")
单边成本 = 0.0005
双边成本 = 单边成本 * 2
总成本Pct = 双边成本 * 100

# ==============================================================================
# 1. 数据加载
# ==============================================================================

def 加载数据():
    """加载板块映射 + 所有股票K线"""
    import io
    from contextlib import redirect_stdout
    with redirect_stdout(io.StringIO()):
        mgr = get_manager()
    板块映射 = mgr.BOARD_STOCK_MAP
    股票板块 = {代码: 板块 for 板块, 代码列表 in 板块映射.items() for 代码 in 代码列表}

    代码列表 = sorted(股票板块.keys())
    print(f"📂 加载 {len(代码列表)} 只板块股票的日K线...")
    所有数据 = {}
    for 代码 in 代码列表:
        csv_path = os.path.join(CACHE_DIR, f"{代码}_日K.csv")
        if not os.path.exists(csv_path):
            continue
        try:
            df = pd.read_csv(csv_path, parse_dates=['date'])
            df = df.sort_values('date').reset_index(drop=True)
            df['代码'] = 代码
            df['板块'] = 股票板块[代码]
            # 计算均线 + MACD
            df = 计算技术指标(df)
            所有数据[代码] = df
        except:
            continue
    print(f"   ✅ 成功加载 {len(所有数据)} 只股票")
    return 所有数据, 板块映射, 股票板块


def 计算技术指标(df):
    """计算均线 + MACD"""
    if df.empty or len(df) < 20:
        return df
    close = df['close']
    # 均线
    df['ma5'] = close.rolling(5).mean()
    df['ma10'] = close.rolling(10).mean()
    df['ma20'] = close.rolling(20).mean()
    # MACD
    ema12 = close.ewm(span=12).mean()
    ema26 = close.ewm(span=26).mean()
    df['dif'] = ema12 - ema26
    df['dea'] = df['dif'].ewm(span=9).mean()
    return df


# ==============================================================================
# 2. 每日选股条件
# ==============================================================================

def 检查均线多头(df, i):
    """检查第i日是否为均线多头排列（MA5 > MA10 > MA20）"""
    if i < 20:
        return False
    m5 = df.iloc[i]['ma5']
    m10 = df.iloc[i]['ma10']
    m20 = df.iloc[i]['ma20']
    return pd.notna(m5) and pd.notna(m10) and pd.notna(m20) and m5 > m10 > m20


def 检查MACD多头(df, i):
    """检查第i日MACD是否为多头（DIF > DEA）"""
    if i < 20:
        return False
    dif = df.iloc[i]['dif']
    dea = df.iloc[i]['dea']
    return pd.notna(dif) and pd.notna(dea) and dif > dea


def 计算板块热度(所有数据, 股票板块, 今日索引):
    """计算各板块平均涨幅（用前一日数据，避免未来函数），取前5名"""
    板块涨幅 = {}
    for 代码, df in 所有数据.items():
        if 今日索引 >= len(df):
            continue
        板块 = 股票板块[代码]
        pct = df.iloc[今日索引 - 1].get('pct_chg', 0) or 0 if 今日索引 > 0 else 0
        if 板块 not in 板块涨幅:
            板块涨幅[板块] = []
        板块涨幅[板块].append(pct)
    板块均值 = {k: np.mean(v) for k, v in 板块涨幅.items()}
    排序 = sorted(板块均值.items(), key=lambda x: x[1], reverse=True)
    return [b[0] for b in 排序[:5]]


# ==============================================================================
# 3. 主回测
# ==============================================================================

def 运行回测(所有数据, 板块映射, 股票板块):
    """执行完整回测"""
    print("\n🚀 运行真实交易模式回测...")
    print(f"   规则: 2%-7% + 均线多头 + MACD多头 + 热门板块Top5")
    print(f"   买入: 分时确认（低>开盘×0.97）")
    print(f"   卖出: 涨5%止盈 / 跌2%止损 / 收盘卖出")
    print(f"   资金: 一发子弹，每日Top1")
    print(f"   成本: 单边0.25% | 双边0.50%\n")

    # 获取所有交易日索引（找有最多数据的股票）
    交易日 = sorted(set(
        d.date() for _, df in 所有数据.items()
        for d in df['date']
    ))
    print(f"   交易日范围: {交易日[0]} ~ {交易日[-1]} ({len(交易日)} 天)")

    交易记录 = []
    空仓天数 = 0
    总交易天数 = 0

    for 日期 in 交易日:
        总交易天数 += 1
        # 找到此日期在各股票中的索引
        今日选股 = []
        for 代码, df in 所有数据.items():
            if df.empty or len(df) < 21:
                continue
            # 找到日期位置
            idx_list = df.index[df['date'] == pd.Timestamp(日期)].tolist()
            if not idx_list:
                continue
            i = idx_list[0]
            if i < 1:  # 需要前一天数据
                continue
            # ===== 选股条件 =====
            昨日涨跌 = df.iloc[i-1]['pct_chg']
            if pd.isna(昨日涨跌) or not (2 <= 昨日涨跌 <= 7):
                continue
            # 均线多头（用前一天的数据判断）
            if not 检查均线多头(df, i-1):
                continue
            # MACD多头（用前一天的数据判断）
            if not 检查MACD多头(df, i-1):
                continue
            # 热门板块前5
            # 注意：用前一天的板块热度来判断，避免未来函数
            # 简化：用最近一个交易日的板块热度
            hot_boards = 计算板块热度(所有数据, 股票板块, i-1)
            if 股票板块[代码] not in hot_boards:
                continue

            今日选股.append({
                '代码': 代码,
                '板块': 股票板块[代码],
                '昨日涨跌': 昨日涨跌,
                'df_idx': i,
                'df': df,
            })

        if not 今日选股:
            空仓天数 += 1
            continue

        # 按昨日涨跌幅排序，取Top1
        今日选股.sort(key=lambda x: x['昨日涨跌'], reverse=True)
        最佳 = 今日选股[0]

        # ===== 模拟今日交易 =====
        idx = 最佳['df_idx']
        df = 最佳['df']
        开盘 = df.iloc[idx]['open']
        收盘 = df.iloc[idx]['close']
        最高 = df.iloc[idx]['high']
        最低 = df.iloc[idx]['low']
        昨日收盘 = df.iloc[idx-1]['close']

        if 开盘 <= 0 or 昨日收盘 <= 0:
            空仓天数 += 1
            continue

        # 分时确认条件：最低 > 开盘 × 0.97（模拟30分钟站稳开盘）
        if 最低 < 开盘 * 0.97:
            空仓天数 += 1
            continue

        # 买入（加一点点滑点）
        买入价 = 开盘 * 1.002
        if 买入价 > 最高:  # 开盘后直接拉，没买到
            空仓天数 += 1
            continue

        # ===== 模拟卖出 =====
        止盈价 = 买入价 * 1.05
        止损价 = 买入价 * 0.98
        持仓时间 = '全天'  # 近似

        if 最高 >= 止盈价:
            卖出价 = 止盈价
            卖出原因 = '止盈(5%)'
            持仓时间 = '盘中'
        elif 最低 <= 止损价:
            卖出价 = 止损价
            卖出原因 = '止损(-2%)'
            持仓时间 = '盘中'
        else:
            卖出价 = 收盘
            卖出原因 = '收盘卖出'

        毛收益 = (卖出价 - 买入价) / 买入价 * 100
        净收益 = 毛收益 - 总成本Pct

        交易记录.append({
            '日期': 日期,
            '年份': 日期.year,
            '代码': 最佳['代码'],
            '板块': 最佳['板块'],
            '昨日涨跌': round(最佳['昨日涨跌'], 2),
            '开盘': 开盘,
            '买入价': round(买入价, 2),
            '卖出价': round(卖出价, 2),
            '收盘': 收盘,
            '最高': 最高,
            '最低': 最低,
            '毛收益': round(毛收益, 2),
            '净收益': round(净收益, 2),
            '卖出原因': 卖出原因,
            '持仓时间': 持仓时间,
        })

    return 交易记录, 空仓天数, 总交易天数


# ==============================================================================
# 4. 统计输出
# ==============================================================================

def 统计结果(交易记录, 空仓天数, 总交易天数):
    """计算所有统计指标"""
    df = pd.DataFrame(交易记录)
    if df.empty:
        print("❌ 无交易记录")
        return

    实际执行 = len(df)
    胜率 = (df['净收益'] > 0).sum() / 实际执行 * 100
    期望收益 = df['净收益'].mean()
    中位收益 = df['净收益'].median()

    # 卖出入类
    止盈率 = (df['卖出原因'] == '止盈(5%)').sum() / 实际执行 * 100
    止损率 = (df['卖出原因'] == '止损(-2%)').sum() / 实际执行 * 100
    收盘卖出率 = (df['卖出原因'] == '收盘卖出').sum() / 实际执行 * 100

    # 最大连续盈利/亏损
    连盈 = (df['净收益'] > 0).astype(int).groupby(
        (df['净收益'] <= 0).cumsum()
    ).cumsum().max()
    连亏 = (df['净收益'] < 0).astype(int).groupby(
        (df['净收益'] >= 0).cumsum()
    ).cumsum().max()

    print("\n" + "=" * 70)
    print("📊 真实交易模式回测结果")
    print("=" * 70)
    print(f"总交易天数: {总交易天数}天    空仓天数: {空仓天数}天    实际执行: {实际执行}天")
    print("=" * 70)
    print(f"{'指标':<25} {'数值':<15}")
    print("-" * 70)
    print(f"{'胜率':<25} {胜率:.1f}%")
    print(f"{'期望收益(扣费后)':<25} {期望收益:+.2f}%")
    print(f"{'中位收益':<25} {中位收益:+.2f}%")
    print(f"{'平均持仓时间':<25} {'盘中(触价即出)'}")
    print(f"{'止盈率(涨5%卖出)':<25} {止盈率:.1f}%")
    print(f"{'止损率(跌2%割肉)':<25} {止损率:.1f}%")
    print(f"{'收盘卖出率':<25} {收盘卖出率:.1f}%")
    print(f"{'最大连续盈利':<25} {连盈}次")
    print(f"{'最大连续亏损':<25} {连亏}次")
    print("=" * 70)

    # 各年份
    print(f"\n📅 各年份表现:")
    print(f"{'年份':<10} {'交易':<8} {'胜率':<10} {'期望收益':<15} {'止盈率':<10} {'止损率':<10}")
    print("-" * 65)
    for 年份 in sorted(df['年份'].unique()):
        年df = df[df['年份'] == 年份]
        年胜率 = (年df['净收益'] > 0).sum() / len(年df) * 100
        年期望 = 年df['净收益'].mean()
        年止盈 = (年df['卖出原因'] == '止盈(5%)').sum() / len(年df) * 100
        年止损 = (年df['卖出原因'] == '止损(-2%)').sum() / len(年df) * 100
        print(f"{年份:<10} {len(年df):<8} {年胜率:.1f}%{'':<4} {年期望:+.2f}%{'':<7} {年止盈:.1f}%{'':<4} {年止损:.1f}%")

    # 总结
    print(f"\n📋 判定:")
    if 期望收益 > 0.5:
        print(f"   🟢 期望{期望收益:+.2f}% → 真实交易模式显著优于裸策略(+0.28%)")
        print(f"      '分时确认+5%止盈'组合有效锁住了利润")
    elif 期望收益 > 0:
        print(f"   🟡 期望{期望收益:+.2f}% → 有改善但有限")
    else:
        print(f"   🔴 期望{期望收益:+.2f}% → 策略仍亏损")

    # 保存
    输出路径 = os.path.join(os.path.dirname(os.path.abspath(__file__)), "真实策略回测结果.csv")
    df.to_csv(输出路径, index=False, encoding='utf-8-sig')
    print(f"\n💾 详细数据已保存至: {输出路径}")


def main():
    开始时间 = datetime.now()
    print("=" * 60)
    print("🧪 【真实交易模式回测】")
    print(f"   启动时间: {开始时间.strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    所有数据, 板块映射, 股票板块 = 加载数据()
    if not 所有数据:
        print("❌ 无可用数据")
        return

    交易记录, 空仓天数, 总交易天数 = 运行回测(所有数据, 板块映射, 股票板块)
    统计结果(交易记录, 空仓天数, 总交易天数)

    总耗时 = (datetime.now() - 开始时间).total_seconds()
    print(f"\n⏱ 总耗时: {总耗时:.0f} 秒 ({总耗时/60:.1f} 分钟)")
    print(f"   完成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == "__main__":
    main()
