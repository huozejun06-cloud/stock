"""
回测引擎 v2.0
修复未来函数陷阱 + 加入手续费滑点

核心改动：
  1. 选股条件：用昨日涨跌幅（模式A），而非今日涨跌幅（修复未来函数）
  2. 买入价格：今日开盘价（模拟9:25竞价后，根据昨日涨跌幅决策）
  3. 交易成本：佣金万三 + 印花税万二 + 滑点千分之一
"""
import os
import sys
import pandas as pd
import numpy as np
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from 工具库.数据源管理器 import get_manager

# ==============================================================================
# 交易成本配置
# ==============================================================================
手续费率 = 0.0003   # 佣金万三
印花税率 = 0.0002   # 印花税万二
滑点 = 0.001        # 滑点千分之一（买卖各一次）
单边成本 = 手续费率 + 滑点
总成本 = 单边成本 * 2 + 印花税率  # 买入+卖出+印花税

CACHE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "缓存")


# ==============================================================================
# 1. 数据加载
# ==============================================================================

def 获取候选股列表() -> list:
    """从数据源管理器获取所有可回测的股票代码列表"""
    mgr = get_manager()
    codes = set()
    for board_codes in mgr.BOARD_STOCK_MAP.values():
        for c in board_codes:
            codes.add(c)
    return sorted(list(codes))


def 加载单只股票数据(代码: str) -> pd.DataFrame:
    """从缓存加载单只股票日K线数据"""
    csv_path = os.path.join(CACHE_DIR, f"{代码}_日K.csv")
    if not os.path.exists(csv_path):
        return pd.DataFrame()
    try:
        df = pd.read_csv(csv_path, parse_dates=['date'], dtype={
            'open': float, 'high': float, 'low': float, 'close': float,
            'volume': float, 'amount': float, 'pct_chg': float,
        })
        df = df.sort_values('date').reset_index(drop=True)
        return df
    except Exception as e:
        print(f"  ⚠️ 加载{代码}失败: {e}")
        return pd.DataFrame()


# ==============================================================================
# 2. 核心计算函数
# ==============================================================================

def _获取昨日涨跌幅(df: pd.DataFrame, idx: int) -> float:
    """获取前一日涨跌幅"""
    if idx < 1:
        return None
    return df.iloc[idx - 1]['pct_chg']


def _获取开盘涨幅(df: pd.DataFrame, idx: int) -> float:
    """获取今日开盘涨幅（用于模式B，本引擎用模式A）"""
    if idx < 1:
        return None
    昨日收盘 = df.iloc[idx - 1]['close']
    if 昨日收盘 <= 0:
        return None
    今日开盘 = df.iloc[idx]['open']
    return (今日开盘 / 昨日收盘 - 1) * 100


def _计算后续收益(df: pd.DataFrame, idx: int, 入场价: float) -> dict:
    """计算候选股后续N日收益（扣除手续费和滑点）"""
    收益 = {}
    for 天数, 键 in [(1, '1日'), (3, '3日'), (5, '5日'), (10, '10日')]:
        未来索引 = idx + 天数
        if 未来索引 < len(df):
            未来收盘 = df.iloc[未来索引]['close']
            毛收益 = (未来收盘 - 入场价) / 入场价 * 100
            # 扣除交易成本
            净收益 = 毛收益 - 总成本 * 100
            收益[键] = round(净收益, 2)
        else:
            收益[键] = None
    return 收益


def 筛选当日候选股(df: pd.DataFrame, idx: int) -> list:
    """
    筛选当日候选股
    模式A：用昨日涨跌幅筛选（避免未来函数）
    条件：2% ≤ 昨日涨跌幅 ≤ 7%
    """
    candidates = []

    昨日涨跌幅 = _获取昨日涨跌幅(df, idx)
    if 昨日涨跌幅 is None:
        return candidates

    # ✅ 用昨日涨幅筛选（模拟9:25竞价结束后，基于昨日数据选股）
    if 2 <= 昨日涨跌幅 <= 7:
        今日开盘 = df.iloc[idx]['open']
        今日日期 = df.iloc[idx]['date']
        后续收益 = _计算后续收益(df, idx, 今日开盘)

        candidates.append({
            '日期': 今日日期,
            '昨日涨跌幅': 昨日涨跌幅,
            '开盘涨幅': _获取开盘涨幅(df, idx),
            '入场价': 今日开盘,
            '入场原因': f"昨日涨跌幅{昨日涨跌幅:+.2f}%，符合2%-7%区间",
            '收益': 后续收益,
        })

    return candidates


def 单只股票回测(df: pd.DataFrame, 代码: str) -> pd.DataFrame:
    """对单只股票进行全周期回测"""
    if df.empty or len(df) < 30:
        return pd.DataFrame()

    records = []
    # 从第2天开始（需要前一天数据做判断），留10天给未来计算
    for idx in range(1, len(df) - 10):
        candidates = 筛选当日候选股(df, idx)
        for c in candidates:
            c['代码'] = 代码
            records.append(c)

    return pd.DataFrame(records)


# ==============================================================================
# 3. 回测统计
# ==============================================================================

def 统计回测结果(结果_df: pd.DataFrame) -> dict:
    """统计回测结果，计算各维度胜率"""
    if 结果_df.empty:
        return {'错误': '无回测结果'}

    stats = {}
    总交易次数 = len(结果_df)
    stats['总交易次数'] = 总交易次数
    stats['涉及股票数'] = 结果_df['代码'].nunique()

    # 按天数统计胜率和平均收益
    for 天数 in ['1日', '3日', '5日', '10日']:
        列名 = f'收益_{天数}'
        if 列名 not in 结果_df.columns:
            continue
        有效数据 = 结果_df[结果_df[列名].notna()]
        if 有效数据.empty:
            continue

        胜率 = len(有效数据[有效数据[列名] > 0]) / len(有效数据) * 100
        平均收益 = 有效数据[列名].mean()
        中位数收益 = 有效数据[列名].median()
        最大收益 = 有效数据[列名].max()
        最大亏损 = 有效数据[列名].min()

        stats[f'{天数}_胜率(%)'] = round(胜率, 1)
        stats[f'{天数}_平均收益(%)'] = round(平均收益, 2)
        stats[f'{天数}_中位数收益(%)'] = round(中位数收益, 2)
        stats[f'{天数}_最大收益(%)'] = round(最大收益, 2)
        stats[f'{天数}_最大亏损(%)'] = round(最大亏损, 2)

    # 额外统计：按涨跌幅区间分析胜率
    if '昨日涨跌幅' in 结果_df.columns:
        结果_df['涨跌幅区间'] = pd.cut(
            结果_df['昨日涨跌幅'],
            bins=[2, 3, 4, 5, 7],
            labels=['2%~3%', '3%~4%', '4%~5%', '5%~7%']
        )
        for 区间 in ['2%~3%', '3%~4%', '4%~5%', '5%~7%']:
            子集 = 结果_df[结果_df['涨跌幅区间'] == 区间]
            if len(子集) < 5:
                continue
            胜率 = len(子集[子集['收益_1日'] > 0]) / len(子集) * 100
            stats[f'{区间}_交易次数'] = len(子集)
            stats[f'{区间}_1日胜率(%)'] = round(胜率, 1)

    return stats


def 打印回测结果(stats: dict):
    """格式化打印回测结果"""
    print("\n" + "=" * 60)
    print("📊 回测结果统计")
    print("=" * 60)

    print(f"\n📈 总交易次数: {stats.get('总交易次数', 'N/A')}")
    print(f"📈 涉及股票数: {stats.get('涉及股票数', 'N/A')}")

    print(f"\n{'='*40}")
    print(f"{'周期':<10} {'胜率':<10} {'平均收益':<12} {'中位数':<12}")
    print(f"{'='*40}")

    for 天数 in ['1日', '3日', '5日', '10日']:
        胜率 = stats.get(f'{天数}_胜率(%)', 'N/A')
        平均 = stats.get(f'{天数}_平均收益(%)', 'N/A')
        中位 = stats.get(f'{天数}_中位数收益(%)', 'N/A')
        if 胜率 != 'N/A':
            print(f"{天数 + '收益':<10} {str(胜率)+'%':<10} {str(平均)+'%':<12} {str(中位)+'%':<12}")

    print(f"\n{'='*40}")
    print(f"{'昨日涨幅区间':<12} {'交易次数':<10} {'1日胜率':<12}")
    print(f"{'='*40}")
    for 区间 in ['2%~3%', '3%~4%', '4%~5%', '5%~7%']:
        次数 = stats.get(f'{区间}_交易次数', None)
        胜率 = stats.get(f'{区间}_1日胜率(%)', None)
        if 次数 and 次数 > 0:
            print(f"{区间:<12} {次数:<10} {str(胜率)+'%' if 胜率 else 'N/A':<12}")


# ==============================================================================
# 4. 主回测入口
# ==============================================================================

def 运行回测(股票列表: list = None, 进度回调=None) -> dict:
    """
    运行全市场回测

    参数:
        股票列表: 若为None则从数据源管理器获取
        进度回调: 可选回调函数，用于进度显示 progress(已完成, 总数)

    返回:
        stats: 回测统计结果字典
    """
    if 股票列表 is None:
        股票列表 = 获取候选股列表()

    print(f"🚀 启动回测: {len(股票列表)} 只股票")
    print(f"   交易成本: 佣金{手续费率*100:.2f}% + 印花税{印花税率*100:.2f}% + 滑点{滑点*100:.1f}%")
    print(f"   单次交易总成本: {总成本*100:.3f}%")
    print(f"   筛选模式: 模式A（昨日涨跌幅 2%-7%）")
    print(f"   入场价: 今日开盘价")
    print(f"   开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    全部结果 = []
    总股票数 = len(股票列表)

    for i, 代码 in enumerate(股票列表):
        df = 加载单只股票数据(代码)
        单只结果 = 单只股票回测(df, 代码)
        if not 单只结果.empty:
            全部结果.append(单只结果)

        if 进度回调:
            进度回调(i + 1, 总股票数)

    if 全部结果:
        结果_df = pd.concat(全部结果, ignore_index=True)
        # 拆分收益字典为独立列
        收益_df = 结果_df['收益'].apply(pd.Series).add_prefix('收益_')
        结果_df = pd.concat([结果_df.drop(columns=['收益']), 收益_df], axis=1)

        print(f"\n✅ 回测完成! 共产生 {len(结果_df)} 次交易信号")
        print(f"   完成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        stats = 统计回测结果(结果_df)

        # 保存详细结果
        输出路径 = os.path.join(os.path.dirname(os.path.abspath(__file__)), "回测结果.csv")
        结果_df.to_csv(输出路径, index=False, encoding='utf-8-sig')
        print(f"   详细结果已保存至: {输出路径}")

        return stats
    else:
        print("❌ 无任何交易信号产生")
        return {'错误': '无交易信号'}


if __name__ == "__main__":
    # 测试运行
    stats = 运行回测(股票列表=['002138', '600563', '603267', '300285', '601138'])
    打印回测结果(stats)
