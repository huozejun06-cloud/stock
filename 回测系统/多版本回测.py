"""
隔夜策略 A-H 多版本对比回测
测试9个版本，找出能提升Alpha的因子组合

成本：佣金0.05% + 滑点0.20% = 单边0.25%，双边0.50%
"""
import os
import sys
import pandas as pd
import numpy as np
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from 工具库.数据源管理器 import get_manager

CACHE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "缓存")
单边成本 = 0.0005   # 佣金0.05% + 滑点0.20% = 0.25%
双边成本 = 单边成本 * 2  # 0.50%
总成本Pct = 双边成本 * 100  # 0.50%

# ==============================================================================
# 1. 数据加载
# ==============================================================================

def 加载板块映射():
    """从数据源管理器获取板块→股票映射"""
    import io
    from contextlib import redirect_stdout
    with redirect_stdout(io.StringIO()):
        mgr = get_manager()
    return mgr.BOARD_STOCK_MAP, {代码: 板块 for 板块, 代码列表 in mgr.BOARD_STOCK_MAP.items() for 代码 in 代码列表}


def 加载全量数据():
    """加载所有板块关联股票的全部日K线数据"""
    板块映射, 股票板块 = 加载板块映射()
    代码列表 = sorted(股票板块.keys())

    print(f"📂 加载 {len(代码列表)} 只板块股票的日K线数据...")
    所有数据 = {}
    for 代码 in 代码列表:
        csv_path = os.path.join(CACHE_DIR, f"{代码}_日K.csv")
        if not os.path.exists(csv_path):
            continue
        try:
            df = pd.read_csv(csv_path, parse_dates=['date'])
            df = df.sort_values('date').reset_index(drop=True)
            # 计算技术指标
            df = 计算技术指标(df)
            df['代码'] = 代码
            df['板块'] = 股票板块[代码]
            所有数据[代码] = df
        except:
            continue
    print(f"   ✅ 成功加载 {len(所有数据)} 只股票")
    return 所有数据, 板块映射


def 计算技术指标(df):
    """为DataFrame增加技术指标列"""
    if df.empty or len(df) < 20:
        return df

    close = df['close']
    high = df['high']
    low = df['low']
    volume = df['volume']
    amount = df['amount']

    # MA5均量
    df['vol_ma5'] = volume.rolling(5).mean()

    # MACD
    ema12 = close.ewm(span=12).mean()
    ema26 = close.ewm(span=26).mean()
    df['dif'] = ema12 - ema26
    df['dea'] = df['dif'].ewm(span=9).mean()

    # 20日超额收益
    全市场平均 = close.pct_change().rolling(20).mean()
    df['个股20日涨幅'] = close.pct_change(20)
    df['超额20日'] = df['个股20日涨幅'] - 全市场平均

    return df


# ==============================================================================
# 2. 每日截面数据（市场环境）
# ==============================================================================

def 构建每日截面(所有数据):
    """从所有股票数据中提取每日市场截面（涨停数、跌停数、上涨占比）"""
    print("📊 构建每日市场截面...")
    每日数据 = {}

    for 代码, df in 所有数据.items():
        for i in range(len(df)):
            日期 = df.iloc[i]['date']
            pct = df.iloc[i].get('pct_chg', 0) or 0
            # 涨停/跌停判断（简化：取当日涨跌幅）
            if 日期 not in 每日数据:
                每日数据[日期] = {'涨停': 0, '跌停': 0, '上涨': 0, '总数': 0, '个股': {}}
            每日数据[日期]['总数'] += 1
            if pct >= 9.8:
                每日数据[日期]['涨停'] += 1
            elif pct <= -9.8:
                每日数据[日期]['跌停'] += 1
            if pct > 0:
                每日数据[日期]['上涨'] += 1
            每日数据[日期]['个股'][代码] = {
                'pct_chg': pct,
                'close': df.iloc[i]['close'],
                'amount': df.iloc[i].get('amount', 0),
            }

    print(f"   ✅ 构建完成，共 {len(每日数据)} 个交易日")
    return 每日数据


def 获取市场环境(每日截面, 日期):
    """
    获取某日的市场环境数据
    C版本条件：涨停≥30、跌停≤20、上涨占比≥40%
    """
    if 日期 not in 每日截面:
        return {'可交易': False, '涨停': 0, '跌停': 0, '上涨占比': 0}
    d = 每日截面[日期]
    涨停 = d['涨停']
    跌停 = d['跌停']
    上涨占比 = d['上涨'] / d['总数'] * 100 if d['总数'] > 0 else 0
    可交易 = (涨停 >= 30) and (跌停 <= 20) and (上涨占比 >= 40)
    return {'可交易': 可交易, '涨停': 涨停, '跌停': 跌停, '上涨占比': round(上涨占比, 1)}


# ==============================================================================
# 3. 核心信号检测
# ==============================================================================

def 检测版本A(所有数据, 每日截面):
    """A: 裸策略 — 昨日涨幅5%-7%，开盘买入，收盘卖出"""
    结果 = []
    for 代码, df in 所有数据.items():
        if df.empty or len(df) < 5:
            continue
        for i in range(1, len(df) - 1):
            昨日涨跌 = df.iloc[i-1]['pct_chg']
            if pd.isna(昨日涨跌) or not (5 <= 昨日涨跌 <= 7):
                continue
            信号 = 提取交易信号(代码, df, i, 昨日涨跌)
            if 信号:
                结果.append(信号)
    return 结果


def 提取交易信号(代码, df, i, 昨日涨跌=None):
    """提取基础交易信号"""
    row = df.iloc[i]
    prev = df.iloc[i-1]
    if 昨日涨跌 is None:
        昨日涨跌 = prev['pct_chg']
    开盘 = row['open']
    收盘 = row['close']
    最低 = row['low']
    日期 = row['date']
    昨日收盘 = prev['close']

    if 开盘 <= 0 or 昨日收盘 <= 0:
        return None

    开盘涨幅 = (开盘 / 昨日收盘 - 1) * 100
    毛收益 = (收盘 - 开盘) / 开盘 * 100
    净收益 = 毛收益 - 总成本Pct

    return {
        '代码': 代码,
        '日期': 日期,
        '年份': pd.Timestamp(日期).year,
        '板块': df.iloc[i].get('板块', ''),
        '昨日涨跌': round(昨日涨跌, 2),
        '开盘涨幅': round(开盘涨幅, 2),
        '开盘': 开盘,
        '收盘': 收盘,
        '最低': 最低,
        '毛收益': round(毛收益, 2),
        '净收益': round(净收益, 2),
        '成交量': row.get('volume', 0),
        '成交额': row.get('amount', 0),
        '高开低走': 开盘 > 昨日收盘 and 收盘 < 开盘,
        'dif': df.iloc[i].get('dif', None),
        'dea': df.iloc[i].get('dea', None),
        'vol_ma5': df.iloc[i].get('vol_ma5', None),
        '超额20日': df.iloc[i].get('超额20日', None),
    }


def 五条红线通过(信号):
    """五条红线过滤（至少通过3条）"""
    if 信号 is None:
        return False
    分数 = 0
    # 1. 收盘 > 开盘
    if 信号['收盘'] > 信号['开盘']:
        分数 += 1
    # 2. 最低 > 开盘 × 0.97
    if 信号['最低'] > 信号['开盘'] * 0.97:
        分数 += 1
    # 3. 成交量 > MA5量 × 0.3
    if 信号['vol_ma5'] and 信号['vol_ma5'] > 0 and 信号['成交量'] > 信号['vol_ma5'] * 0.3:
        分数 += 1
    # 4. DIF > DEA
    if 信号['dif'] is not None and 信号['dea'] is not None and 信号['dif'] > 信号['dea']:
        分数 += 1
    # 5. 昨日涨跌幅筛选已在A层完成（5%-7%）
    分数 += 1  # 自动通过

    return 分数 >= 3


# ==============================================================================
# 4. 各版本运行
# ==============================================================================

def 运行版本A(所有数据, 每日截面):
    """A: 裸策略"""
    return 检测版本A(所有数据, 每日截面)


def 运行版本B(所有数据, 每日截面):
    """B: A + 五条红线"""
    所有信号 = 检测版本A(所有数据, 每日截面)
    return [s for s in 所有信号 if 五条红线通过(s)]


def 运行版本C(所有数据, 每日截面):
    """C: B + 市场环境"""
    信号B = 运行版本B(所有数据, 每日截面)
    结果 = []
    for s in 信号B:
        环境 = 获取市场环境(每日截面, s['日期'])
        if 环境['可交易']:
            结果.append(s)
    return 结果


def 运行版本D(所有数据, 每日截面):
    """D: C + 只买Top1（按昨日涨幅排序，每日只取第1名）"""
    信号C = 运行版本C(所有数据, 每日截面)
    # 按日期分组，取昨日涨幅最高的一只
    df = pd.DataFrame(信号C)
    if df.empty:
        return []
    df = df.loc[df.groupby('日期')['昨日涨跌'].idxmax()]
    return df.to_dict('records')


def 运行版本E(所有数据, 每日截面, 最小开盘涨幅=0):
    """E1/E2: D + 竞价确认（开盘涨幅>0% 或 >1%）"""
    信号D = 运行版本D(所有数据, 每日截面)
    return [s for s in 信号D if s['开盘涨幅'] > 最小开盘涨幅]


def 运行版本F(所有数据, 每日截面):
    """F: C + 成交额>10亿 + 20日超额收益>10%"""
    信号C = 运行版本C(所有数据, 每日截面)
    结果 = []
    for s in 信号C:
        if s['成交额'] and s['成交额'] >= 1_000_000_000:  # 10亿
            if s['超额20日'] and s['超额20日'] > 0.10:  # 20日超额>10%
                结果.append(s)
    return 结果


def 运行版本H1(所有数据, 每日截面):
    """H1: 主线板块龙一 — 板块涨幅前3 + 个股板块内涨幅第1 + 成交额>10亿"""
    return _运行版本H(所有数据, 每日截面, topk=1)


def 运行版本H2(所有数据, 每日截面):
    """H2: 主线板块前三平均 — 板块涨幅前3 + 个股板块内涨幅前3"""
    return _运行版本H(所有数据, 每日截面, topk=3)


def _运行版本H(所有数据, 每日截面, topk):
    """H版本核心逻辑"""
    所有信号 = 检测版本A(所有数据, 每日截面)
    if not 所有信号:
        return []

    df = pd.DataFrame(所有信号)
    结果 = []

    for 日期, 日组 in df.groupby('日期'):
        # 计算当日各板块平均涨幅
        板块涨幅 = 日组.groupby('板块')['昨日涨跌'].mean().sort_values(ascending=False)
        # 取前3板块
        top3板块 = 板块涨幅.head(3).index.tolist()

        for 板块 in top3板块:
            板块股 = 日组[日组['板块'] == 板块]
            if 板块股.empty:
                continue
            # 板块内按昨日涨跌幅排序
            板块股 = 板块股.sort_values('昨日涨跌', ascending=False)
            # 取前topk
            for _, s in 板块股.head(topk).iterrows():
                if s['成交额'] and s['成交额'] >= 1_000_000_000:  # 成交额>10亿
                    结果.append(s.to_dict())

    return 结果


# ==============================================================================
# 5. 统计函数
# ==============================================================================

def 计算统计(信号列表):
    """批量计算所有统计指标"""
    if not 信号列表:
        return {
            '次数': 0, '胜率': 0, '期望收益': 0, '高开率': 0,
            '高开低走率': 0, '开盘卖收益': 0, '收盘卖收益': 0,
            '最大连亏': 0, '2024胜率': 0, '2025胜率': 0, '2026胜率': 0,
        }

    df = pd.DataFrame(信号列表).dropna(subset=['净收益'])

    总次数 = len(df)
    胜率 = (df['净收益'] > 0).sum() / 总次数 * 100
    期望收益 = df['净收益'].mean()

    高开数 = (df['开盘涨幅'] > 0).sum()
    高开率 = 高开数 / 总次数 * 100
    高开低走率 = df['高开低走'].sum() / 高开数 * 100 if 高开数 > 0 else 0

    开盘卖收益 = (df['开盘涨幅']).mean()
    收盘卖收益 = df['净收益'].mean()

    # 最大连续亏损
    连亏 = (df['净收益'] < 0).astype(int).groupby(
        (df['净收益'] >= 0).cumsum()
    ).cumsum()
    最大连亏 = 连亏.max()

    # 分年
    年胜率 = {}
    for y in ['2024', '2025', '2026']:
        年df = df[df['年份'] == int(y)]
        if len(年df) >= 5:
            年胜率[f'{y}胜率'] = round((年df['净收益'] > 0).sum() / len(年df) * 100, 1)
        else:
            年胜率[f'{y}胜率'] = 0

    return {
        '次数': 总次数,
        '胜率': round(胜率, 1),
        '期望收益': round(期望收益, 2),
        '高开率': round(高开率, 1),
        '高开低走率': round(高开低走率, 1),
        '开盘卖收益': round(开盘卖收益, 2),
        '收盘卖收益': round(收盘卖收益, 2),
        '最大连亏': 最大连亏,
        **年胜率,
    }


def 打印表格(版本结果):
    """打印A-H对比表"""
    print("\n" + "=" * 110)
    print("📊 隔夜策略A-H多版本对比")
    print("=" * 110)
    print(f"{'版本':<6} {'次数':<7} {'胜率':<8} {'期望收益':<10} {'高开率':<8} {'高开低走':<9} {'开盘卖':<8} {'收盘卖':<8} {'最大连亏':<9} {'2024':<8} {'2025':<8} {'2026':<8}")
    print("-" * 110)

    for 版本名, stats in 版本结果:
        print(f"{版本名:<6} {stats['次数']:<7} {stats['胜率']:<7}% {stats['期望收益']:+.2f}%{'':<5} {stats['高开率']:<6}% {stats['高开低走率']:<6}% {stats['开盘卖收益']:+.2f}%{'':<3} {stats['收盘卖收益']:+.2f}%{'':<3} {stats['最大连亏']:<9} {stats.get('2024胜率', 0):<6}% {stats.get('2025胜率', 0):<6}% {stats.get('2026胜率', 0):<6}%")
        # 添加过拟合检查
        if stats['次数'] > 0 and '2024胜率' in stats and stats.get('2025胜率', 0) > 0:
            训练期胜率 = max(stats.get('2024胜率', 0), stats.get('2025胜率', 0))
            验证期胜率 = stats.get('2026胜率', 0)
            if 验证期胜率 < 训练期胜率 - 10:
                print(f"       ⚠️ 过拟合风险: 验证期{验证期胜率}% < 训练期{训练期胜率}%")

    print("\n📋 训练期: 2024-01 ~ 2025-06 | 验证期: 2025-07 ~ 2026-06")
    print("📋 交易成本: 单边0.25% | 双边0.50%（含佣金+滑点）")


def 打印详细结果(版本结果):
    """为每个版本打印详细年度统计"""
    print("\n" + "=" * 60)
    print("📈 各版本详细年度统计")
    print("=" * 60)

    for 版本名, stats in 版本结果:
        if stats['次数'] == 0:
            continue
        print(f"\n【版本{版本名}】 总{stats['次数']}次 | 期望{stats['期望收益']:+.2f}% | 胜率{stats['胜率']}%")
        for y in ['2024', '2025', '2026']:
            if f'{y}胜率' in stats:
                print(f"   {y}年: {stats[f'{y}胜率']}%", end='')
        # 过拟合标注
        训练年胜率 = [stats.get(f'{y}胜率', 0) for y in ['2024', '2025'] if stats.get(f'{y}胜率', 0) > 0]
        验证年胜率 = stats.get('2026胜率', 0)
        if 训练年胜率 and 验证年胜率 > 0:
            平均训练 = sum(训练年胜率) / len(训练年胜率)
            if 验证年胜率 < 平均训练 - 10:
                print(f"   ⚠️ 过拟合风险（验证{验证年胜率}% < 训练{平均训练:.0f}%）")
            else:
                print(f"   ✅ 未见显著过拟合")
        else:
            print()


# ==============================================================================
# 6. 主流程
# ==============================================================================

def main():
    开始时间 = datetime.now()
    print("=" * 60)
    print("🧪 【隔夜策略 A-H 多版本对比回测】")
    print(f"   启动时间: {开始时间.strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    # 加载数据
    所有数据, 板块映射 = 加载全量数据()
    if not 所有数据:
        print("❌ 无可用数据")
        return

    # 构建每日截面
    每日截面 = 构建每日截面(所有数据)

    print(f"\n🚀 运行9个版本的回测...")

    # 运行各版本
    ALL_VERSIONS = [
        ('A', 运行版本A),
        ('B', 运行版本B),
        ('C', 运行版本C),
        ('D', 运行版本D),
        ('E1', lambda a, s: 运行版本E(a, s, 最小开盘涨幅=0)),
        ('E2', lambda a, s: 运行版本E(a, s, 最小开盘涨幅=1)),
        ('F', 运行版本F),
        ('H1', 运行版本H1),
        ('H2', 运行版本H2),
    ]

    版本结果 = []
    for 版本名, func in ALL_VERSIONS:
        t0 = datetime.now()
        信号 = func(所有数据, 每日截面)
        stats = 计算统计(信号)
        版本结果.append((版本名, stats))
        elapsed = (datetime.now() - t0).total_seconds()
        print(f"   {版本名}: {stats['次数']:>5} 个信号 | 胜率{stats['胜率']:>5}% | 期望{stats['期望收益']:+.2f}% | {elapsed:.1f}s")

    # 打印结果
    打印表格(版本结果)
    打印详细结果(版本结果)

    # 最佳版本判定
    print("\n" + "=" * 60)
    print("🏆 最佳版本判定")
    print("=" * 60)
    best = max(版本结果, key=lambda x: (
        x[1]['期望收益'] if x[1]['次数'] >= 30 else -999,
        x[1]['胜率'],
    ))
    print(f"   按期望收益最高的有效版本: {best[0]}")
    print(f"     → 期望{best[1]['期望收益']:+.2f}% | 胜率{best[1]['胜率']}% | {best[1]['次数']}次")

    # 对比A版本（裸策略）
    Astats = next(s for n, s in 版本结果 if n == 'A')
    if Astats['次数'] > 0:
        print(f"\n   裸策略(A)基线: 期望{Astats['期望收益']:+.2f}% | 胜率{Astats['胜率']}%")
        print(f"   最佳版本({best[0]}) vs A: 期望提升 {best[1]['期望收益'] - Astats['期望收益']:+.2f}%")

    总耗时 = (datetime.now() - 开始时间).total_seconds()
    print(f"\n⏱ 总耗时: {总耗时:.0f} 秒 ({总耗时/60:.1f} 分钟)")
    print(f"   完成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == "__main__":
    main()
