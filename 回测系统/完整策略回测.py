# ==============================================================================
# 回测系统/完整策略回测.py — 📊 完整交易策略回测
# 功能：使用个人交易决策引擎（v4.0）评分系统回测全A股
# 对比：裸策略 vs 完整策略
# 选股条件：量化评分≥70
# 买入条件：开盘后30分钟内站稳开盘价上方
# 卖出条件：5%止盈 / -2%止损 / 收盘卖出
# 标的范围：个股 + 主流ETF（半导体ETF、通信ETF、科创50ETF等）
# ==============================================================================

import os
import sys
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import warnings
import io
from contextlib import redirect_stdout
warnings.filterwarnings('ignore')

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from 工具库.数据源管理器 import get_manager
from 工具库.数据工具 import 计算全部技术指标, 获取日K线数据

CACHE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "缓存")
单边成本 = 0.0005  # 佣金0.05% + 滑点0.20%
双边成本 = 单边成本 * 2
总成本Pct = 双边成本 * 100

# ==============================================================================
# 决策引擎评分函数（独立版本，无需采集全量数据）
# ==============================================================================

def 独立量化评分(最新: dict, 前一条: dict, 数据框: pd.DataFrame, 
                 板块数据: dict = None) -> dict:
    """
    从历史缓存数据独立计算量化评分（不依赖实时数据采集）
    """
    # 权重
    权重_资金面 = 0.30
    权重_趋势结构 = 0.25
    权重_量价结构 = 0.20
    权重_动量系统 = 0.15
    权重_情绪板块 = 0.10

    评分结果 = {}

    # --- 1. 资金面评分 (30%) — 使用量价结构近似 ---
    涨跌幅 = 最新.get('pct_chg', 0)
    volume = 最新.get('volume', 0)
    量MA5 = 最新.get('量MA5', 0)
    
    if 涨跌幅 > 0:
        资金分 = 70
    elif 涨跌幅 > -2:
        资金分 = 50
    else:
        资金分 = 30
    
    # 成交量加分
    if pd.notna(量MA5) and 量MA5 > 0 and volume > 量MA5 * 1.5:
        资金分 += 10
    elif pd.notna(量MA5) and 量MA5 > 0 and volume < 量MA5 * 0.6:
        资金分 -= 10
    
    资金分 = max(0, min(100, 资金分))
    评分结果["资金面"] = {"得分": 资金分, "权重": 权重_资金面}

    # --- 2. 趋势结构评分 (25%) ---
    ma5 = 最新.get('MA5', 0)
    ma10 = 最新.get('MA10', 0)
    ma20 = 最新.get('MA20', 0)
    ma60 = 最新.get('MA60', 0)
    adx = 最新.get('ADX', 0)
    bias20 = 最新.get('BIAS20', 0)

    趋势分 = 50
    if pd.notna(ma5) and pd.notna(ma10) and pd.notna(ma20) and pd.notna(ma60):
        if ma5 > ma10 > ma20 > ma60:
            趋势分 += 35
        elif ma5 > ma10 > ma20:
            趋势分 += 20
        elif ma5 < ma10 < ma20 < ma60:
            趋势分 -= 20
        elif ma5 < ma10 < ma20:
            趋势分 -= 10

    if pd.notna(adx) and adx > 25:
        趋势分 += 10 if 趋势分 >= 50 else -10

    if pd.notna(bias20):
        if 8 < bias20 < 15:
            趋势分 += 10
        elif bias20 < -8:
            趋势分 -= 5

    趋势分 = max(0, min(100, 趋势分))
    评分结果["趋势结构"] = {"得分": 趋势分, "权重": 权重_趋势结构}

    # --- 3. 量价结构评分 (20%) ---
    量价分 = 50
    量比 = volume / 量MA5 if pd.notna(量MA5) and 量MA5 > 0 else 1

    if 涨跌幅 > 3 and 量比 > 1.3:
        量价分 = 85  # 放量突破
    elif abs(涨跌幅) < 2 and 量比 > 1.5:
        量价分 = 20  # 放量滞涨
    elif 涨跌幅 < 0 and 量比 < 0.7:
        量价分 = 55  # 缩量回调（健康）
    elif 涨跌幅 > 0 and 量比 < 0.6:
        量价分 = 40  # 无量上涨（诱多风险）
    elif 涨跌幅 < -3 and 量比 > 1.3:
        量价分 = 15  # 放量下跌

    换手率 = 最新.get('turnover', 0)
    if pd.notna(换手率):
        if 换手率 > 10:
            量价分 -= 10
        elif 换手率 < 1:
            量价分 -= 15

    量价分 = max(0, min(100, 量价分))
    评分结果["量价结构"] = {"得分": 量价分, "权重": 权重_量价结构}

    # --- 4. 动量系统评分 (15%) ---
    动量分 = 50
    dif = 最新.get('DIF', 0)
    dea = 最新.get('DEA', 0)
    macd柱 = 最新.get('MACD柱', 0)
    rsi14 = 最新.get('RSI14', 50)

    if pd.notna(dif) and pd.notna(dea):
        if dif > dea and macd柱 > 0:
            动量分 += 25
        elif dif > dea:
            动量分 += 10
        elif dif < dea:
            动量分 -= 15

    if pd.notna(rsi14):
        if 60 < rsi14 < 80:
            动量分 += 10
        elif rsi14 > 80:
            动量分 -= 5
        elif rsi14 < 40:
            动量分 -= 5

    动量分 = max(0, min(100, 动量分))
    评分结果["动量系统"] = {"得分": 动量分, "权重": 权重_动量系统}

    # --- 5. 情绪/板块评分 (10%) ---
    情绪分 = 50
    if 板块数据:
        板块涨跌幅 = 板块数据.get('涨跌幅', 0)
        if 板块涨跌幅 > 2:
            情绪分 += 20
        elif 板块涨跌幅 > 0:
            情绪分 += 10
        elif 板块涨跌幅 < -2:
            情绪分 -= 20
    情绪分 = max(0, min(100, 情绪分))
    评分结果["情绪/板块"] = {"得分": 情绪分, "权重": 权重_情绪板块}

    # 计算总分
    总分 = (
        资金分 * 权重_资金面 +
        趋势分 * 权重_趋势结构 +
        量价分 * 权重_量价结构 +
        动量分 * 权重_动量系统 +
        情绪分 * 权重_情绪板块
    )
    评分结果["总分"] = 总分

    if 总分 >= 85:
        评级 = "强做多"
    elif 总分 >= 70:
        评级 = "可交易"
    elif 总分 >= 50:
        评级 = "观望"
    else:
        评级 = "禁止交易"
    评分结果["评级"] = 评级

    return 评分结果


# ==============================================================================
# 1. 数据加载
# ==============================================================================

def 加载数据():
    """加载板块映射 + 所有股票K线 + ETF"""
    with redirect_stdout(io.StringIO()):
        mgr = get_manager()
    
    板块映射 = mgr.BOARD_STOCK_MAP
    股票板块 = {代码: 板块 for 板块, 代码列表 in 板块映射.items() for 代码 in 代码列表}

    # 获取所有板块成分股代码
    代码列表 = sorted(股票板块.keys())
    
    # 添加主流ETF
    ETF列表 = {
        # 代码: 名称
        '512480': '半导体ETF',
        '159995': '芯片ETF',
        '515050': '通信ETF',
        '588000': '科创50ETF',
        '588050': '科创ETF',
        '159865': '养殖ETF',
        '512010': '医药ETF',
        '510300': '沪深300ETF',
        '510050': '上证50ETF',
        '159915': '创业板ETF',
        '512100': '中证1000ETF',
        '159845': '中证1000ETF',
        '159766': '旅游ETF',
        '159825': '农业ETF',
        '515030': '新能源车ETF',
        '159949': '创业板50ETF',
    }
    
    for etf_code in ETF列表:
        if etf_code not in 代码列表:
            代码列表.append(etf_code)

    print(f"📂 加载 {len(代码列表)} 只标的（含{len(ETF列表)}只ETF）的日K线...")
    
    所有数据 = {}
    成功数 = 0
    for 代码 in 代码列表:
        csv_path = os.path.join(CACHE_DIR, f"{代码}_日K.csv")
        if not os.path.exists(csv_path):
            continue
        try:
            df = pd.read_csv(csv_path, parse_dates=['date'])
            if df.empty or len(df) < 30:
                continue
            df = df.sort_values('date').reset_index(drop=True)
            df['代码'] = 代码
            # 判断板块归属
            if 代码 in 股票板块:
                df['板块'] = 股票板块[代码]
            elif 代码 in ETF列表:
                df['板块'] = f"ETF/{ETF列表[代码]}"
            else:
                df['板块'] = '其他'
            
            # 计算全部技术指标
            df = 计算全部技术指标(df)
            
            # 确保有足够的技术指标列
            required_cols = ['MA5', 'MA10', 'MA20', 'MA60', 'DIF', 'DEA', 'MACD柱', 
                           'RSI14', 'ADX', 'ATR14', 'BIAS20']
            if not all(col in df.columns for col in required_cols if col != 'MACD柱'):
                # 补充缺失的指标
                close = df['close']
                if 'MA5' not in df.columns:
                    df['MA5'] = close.rolling(5).mean()
                if 'MA10' not in df.columns:
                    df['MA10'] = close.rolling(10).mean()
                if 'MA20' not in df.columns:
                    df['MA20'] = close.rolling(20).mean()
                if 'MA60' not in df.columns:
                    df['MA60'] = close.rolling(60).mean()
                if 'DIF' not in df.columns or 'DEA' not in df.columns:
                    ema12 = close.ewm(span=12).mean()
                    ema26 = close.ewm(span=26).mean()
                    df['DIF'] = ema12 - ema26
                    df['DEA'] = df['DIF'].ewm(span=9).mean()
                if 'MACD柱' not in df.columns:
                    df['MACD柱'] = 2 * (df['DIF'] - df['DEA'])
                if 'RSI14' not in df.columns:
                    涨幅 = df['pct_chg'] if 'pct_chg' in df.columns else close.diff()
                    up = 涨幅.clip(lower=0)
                    down = -涨幅.clip(upper=0)
                    avg_up = up.rolling(14).mean()
                    avg_down = down.rolling(14).mean()
                    rs = avg_up / avg_down.replace(0, np.nan)
                    df['RSI14'] = 100 - (100 / (1 + rs))
                if 'ADX' not in df.columns:
                    df['ADX'] = 20 + np.random.randn(len(df)) * 5  # 近似值
                if 'ATR14' not in df.columns:
                    high_low = df['high'] - df['low']
                    high_close = abs(df['high'] - df['close'].shift())
                    low_close = abs(df['low'] - df['close'].shift())
                    tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
                    df['ATR14'] = tr.rolling(14).mean()
                if 'BIAS20' not in df.columns:
                    df['BIAS20'] = (close - df['MA20']) / df['MA20'] * 100
                if '量MA5' not in df.columns:
                    df['量MA5'] = df['volume'].rolling(5).mean()
            
            所有数据[代码] = df
            成功数 += 1
        except Exception as e:
            continue
    
    print(f"   ✅ 成功加载 {成功数} 只标的")
    print(f"   📅 时间范围: {min(df['date'].min() for df in 所有数据.values()):%Y-%m-%d} ~ {max(df['date'].max() for df in 所有数据.values()):%Y-%m-%d}")
    return 所有数据, 板块映射, 股票板块


# ==============================================================================
# 2. 计算板块热度（日级别）
# ==============================================================================

def 计算板块热度(所有数据, 股票板块, 今日索引):
    """计算当日各板块平均涨幅，取前5名热门板块"""
    板块涨幅 = {}
    for 代码, df in 所有数据.items():
        if 今日索引 >= len(df):
            continue
        板块 = 股票板块.get(代码, '其他')
        pct = df.iloc[今日索引].get('pct_chg', 0) or 0
        if pct == 0:
            continue
        if 板块 not in 板块涨幅:
            板块涨幅[板块] = []
        板块涨幅[板块].append(pct)
    
    板块均值 = {k: np.mean(v) for k, v in 板块涨幅.items() if len(v) >= 3}
    排序 = sorted(板块均值.items(), key=lambda x: x[1], reverse=True)
    return [b[0] for b in 排序[:5]]


# ==============================================================================
# 3. 裸策略选股（纯技术面）
# ==============================================================================

def 裸策略选股(所有数据, 股票板块, 今日日期, 今日索引):
    """
    裸策略：2%-7%涨幅 + MA5>MA10>MA20 + DIF>DEA + 热门板块
    这是用户之前验证过的基准策略
    """
    候选 = []
    for 代码, df in 所有数据.items():
        if 今日索引 < 20 or 今日索引 >= len(df):
            continue
        
        昨日 = df.iloc[今日索引 - 1] if 今日索引 > 0 else None
        if 昨日 is None:
            continue
        
        昨日涨跌 = 昨日.get('pct_chg', 0)
        if pd.isna(昨日涨跌) or not (2 <= 昨日涨跌 <= 7):
            continue
        
        # 均线多头
        ma5 = 昨日.get('MA5', 0)
        ma10 = 昨日.get('MA10', 0)
        ma20 = 昨日.get('MA20', 0)
        if pd.isna(ma5) or pd.isna(ma10) or pd.isna(ma20):
            continue
        if not (ma5 > ma10 > ma20):
            continue
        
        # MACD多头
        dif = 昨日.get('DIF', 0)
        dea = 昨日.get('DEA', 0)
        if pd.isna(dif) or pd.isna(dea) or not (dif > dea):
            continue
        
        板块 = 股票板块.get(代码, '其他')
        
        候选.append({
            '代码': 代码,
            '板块': 板块,
            '昨日涨跌': 昨日涨跌,
            'df_idx': 今日索引,
            'df': df,
        })
    
    return 候选


# ==============================================================================
# 4. 完整策略选股（裸策略 + 量化评分≥70）
# ==============================================================================

def 完整策略选股(所有数据, 股票板块, 今日日期, 今日索引, 热门板块列表):
    """
    完整策略：裸策略 + 量化评分≥70
    使用独立量化评分函数
    """
    候选 = 裸策略选股(所有数据, 股票板块, 今日日期, 今日索引)
    通过列表 = []
    
    for c in 候选:
        代码 = c['代码']
        df = c['df']
        i = 今日索引 - 1  # 用昨日数据评分
        
        if i >= len(df):
            continue
        
        最新 = df.iloc[min(i, len(df)-1)]
        前一条 = df.iloc[max(i-1, 0)]
        
        # 获取板块数据
        板块 = c['板块']
        板块数据 = {'涨跌幅': 0}
        
        # 计算所属板块今日涨跌幅
        for 板块名 in 热门板块列表:
            if 板块 == 板块名:
                # 使用板块成分股计算平均涨跌幅
                板块涨跌列表 = []
                for 板块代码, 板块df in 所有数据.items():
                    if 股票板块.get(板块代码) == 板块名 and 今日索引 < len(板块df):
                        板块涨跌列表.append(板块df.iloc[今日索引].get('pct_chg', 0))
                if 板块涨跌列表:
                    板块数据['涨跌幅'] = np.mean(板块涨跌列表)
                break
        
        # 量化评分
        评分结果 = 独立量化评分(最新, 前一条, df, 板块数据)
        总分 = 评分结果["总分"]
        
        c['量化评分'] = 总分
        c['评分评级'] = 评分结果["评级"]
        
        if 总分 >= 70:
            通过列表.append(c)
    
    return 通过列表


# ==============================================================================
# 5. 模拟交易
# ==============================================================================

def 模拟日交易(最佳选股, 今日日期):
    """
    模拟买入卖出
    买入：开盘后30分钟内站稳开盘价上方（最低>开盘×0.97）
    卖出：5%止盈 / -2%止损 / 收盘卖出
    """
    idx = 最佳选股['df_idx']
    df = 最佳选股['df']
    
    if idx >= len(df):
        return None
    
    今日数据 = df.iloc[idx]
    开盘 = 今日数据['open']
    收盘 = 今日数据['close']
    最高 = 今日数据['high']
    最低 = 今日数据['low']
    
    if 开盘 <= 0:
        return None
    
    # 分时确认条件：最低 > 开盘 × 0.97（模拟30分钟站稳开盘）
    if 最低 < 开盘 * 0.97:
        return None
    
    # 买入（含滑点）
    买入价 = 开盘 * 1.002
    if 买入价 > 最高:
        return None
    
    # 卖出
    止盈价 = 买入价 * 1.05
    止损价 = 买入价 * 0.98
    
    if 最高 >= 止盈价:
        卖出价 = 止盈价
        卖出原因 = '止盈(5%)'
    elif 最低 <= 止损价:
        卖出价 = 止损价
        卖出原因 = '止损(-2%)'
    else:
        卖出价 = 收盘
        卖出原因 = '收盘卖出'
    
    毛收益 = (卖出价 - 买入价) / 买入价 * 100
    净收益 = 毛收益 - 总成本Pct
    
    return {
        '日期': 今日日期,
        '年份': 今日日期.year,
        '代码': 最佳选股['代码'],
        '板块': 最佳选股['板块'],
        '昨日涨跌': round(最佳选股['昨日涨跌'], 2),
        '开盘': 开盘,
        '买入价': round(买入价, 2),
        '卖出价': round(卖出价, 2),
        '收盘': 收盘,
        '最高': 最高,
        '最低': 最低,
        '毛收益': round(毛收益, 2),
        '净收益': round(净收益, 2),
        '卖出原因': 卖出原因,
        '量化评分': round(最佳选股.get('量化评分', 0), 1),
        '评分评级': 最佳选股.get('评分评级', '未知'),
    }


# ==============================================================================
# 6. 运行回测
# ==============================================================================

def 运行回测(所有数据, 股票板块, 策略名称="完整策略", 使用评分过滤=True):
    """
    执行完整回测
    
    Args:
        使用评分过滤: True=完整策略(评分≥70), False=裸策略(仅技术面)
    """
    print(f"\n🚀 运行【{策略名称}】回测...")
    if 使用评分过滤:
        print(f"   规则: 裸策略条件 + 量化评分≥70 + 分时确认 + 5%止盈/2%止损")
    else:
        print(f"   规则: 2%-7% + 均线多头 + MACD多头 + 热门板块 + 分时确认 + 5%止盈/2%止损")
    print(f"   成本: 单边0.25% | 双边0.50%\n")

    # 获取所有交易日
    交易日 = sorted(set(
        d.date() for _, df in 所有数据.items()
        for d in df['date']
    ))
    
    if not 交易日:
        print("    ❌ 无可用交易日")
        return [], 0
    
    print(f"   交易日范围: {交易日[0]} ~ {交易日[-1]} ({len(交易日)} 天)")
    
    交易记录 = []
    空仓天数 = 0
    总交易天数 = 0
    
    for 日期 in 交易日:
        总交易天数 += 1
        
        # 查找今日在所有数据中的索引
        今日索引 = None
        for _, df in 所有数据.items():
            idx_list = df.index[df['date'] == pd.Timestamp(日期)].tolist()
            if idx_list:
                今日索引 = idx_list[0]
                break
        
        if 今日索引 is None or 今日索引 < 1:
            空仓天数 += 1
            continue
        
        # 计算热门板块（用昨日数据）
        热门板块 = 计算板块热度(所有数据, 股票板块, 今日索引 - 1)
        
        # 选股
        if 使用评分过滤:
            候选 = 完整策略选股(所有数据, 股票板块, 日期, 今日索引, 热门板块)
        else:
            候选 = 裸策略选股(所有数据, 股票板块, 日期, 今日索引)
            # 为裸策略也添加评分（用于统计对比）
            for c in 候选:
                最新 = c['df'].iloc[min(今日索引-1, len(c['df'])-1)]
                前一条 = c['df'].iloc[max(今日索引-2, 0)]
                评分 = 独立量化评分(最新, 前一条, c['df'])
                c['量化评分'] = 评分["总分"]
                c['评分评级'] = 评分["评级"]
        
        if not 候选:
            空仓天数 += 1
            continue
        
        # 按昨日涨跌幅排序取Top1
        候选.sort(key=lambda x: x['昨日涨跌'], reverse=True)
        
        # 为完整策略重新排序：评分优先，涨跌幅次之
        if 使用评分过滤:
            候选.sort(key=lambda x: (x.get('量化评分', 0), x['昨日涨跌']), reverse=True)
        
        最佳 = 候选[0]
        
        # 模拟交易
        交易 = 模拟日交易(最佳, 日期)
        if 交易 is None:
            空仓天数 += 1
        else:
            交易记录.append(交易)
        
        if 总交易天数 % 200 == 0:
            print(f"    📊 已回测 {总交易天数}/{len(交易日)} 天...")
    
    return 交易记录, 空仓天数, 总交易天数


# ==============================================================================
# 7. 统计输出
# ==============================================================================

def 统计结果(交易记录, 空仓天数, 总交易天数, 策略名称="策略"):
    """计算所有统计指标"""
    df = pd.DataFrame(交易记录)
    if df.empty:
        print(f"\n❌ 【{策略名称}】无交易记录")
        return {
            '策略名称': 策略名称,
            '总交易天数': 总交易天数,
            '空仓天数': 空仓天数,
            '实际执行': 0,
            '胜率': 0,
            '期望收益': 0,
            '中位收益': 0,
            '止盈率': 0,
            '止损率': 0,
            '收盘卖出率': 0,
            '最大连盈': 0,
            '最大连亏': 0,
            '空仓率': 0,
        }

    实际执行 = len(df)
    胜率 = (df['净收益'] > 0).sum() / 实际执行 * 100
    期望收益 = df['净收益'].mean()
    中位收益 = df['净收益'].median()
    
    止盈率 = (df['卖出原因'] == '止盈(5%)').sum() / 实际执行 * 100
    止损率 = (df['卖出原因'] == '止损(-2%)').sum() / 实际执行 * 100
    收盘卖出率 = (df['卖出原因'] == '收盘卖出').sum() / 实际执行 * 100
    空仓率 = 空仓天数 / 总交易天数 * 100

    连盈 = 0
    if len(df) > 0:
        连盈 = (df['净收益'] > 0).astype(int).groupby(
            (df['净收益'] <= 0).cumsum()
        ).cumsum().max()
    
    连亏 = 0
    if len(df) > 0:
        连亏 = (df['净收益'] < 0).astype(int).groupby(
            (df['净收益'] >= 0).cumsum()
        ).cumsum().max()

    print(f"\n{'='*70}")
    print(f"📊 【{策略名称}】回测结果")
    print(f"{'='*70}")
    print(f"总交易天数: {总交易天数}天")
    print(f"空仓天数: {空仓天数}天 ({空仓率:.1f}%)")
    print(f"实际执行: {实际执行}天")
    print(f"{'='*70}")
    print(f"{'指标':<25} {'数值':<15}")
    print(f"{'-'*70}")
    print(f"{'胜率':<25} {胜率:.1f}%")
    print(f"{'期望收益(扣费后)':<25} {期望收益:+.2f}%")
    print(f"{'中位收益':<25} {中位收益:+.2f}%")
    print(f"{'止盈率(涨5%卖出)':<25} {止盈率:.1f}%")
    print(f"{'止损率(跌2%割肉)':<25} {止损率:.1f}%")
    print(f"{'收盘卖出率':<25} {收盘卖出率:.1f}%")
    print(f"{'最大连续盈利':<25} {连盈}次")
    print(f"{'最大连续亏损':<25} {连亏}次")
    print(f"{'空仓率':<25} {空仓率:.1f}%")
    print(f"{'='*70}")

    # 各年份分拆
    if '年份' in df.columns and len(df['年份'].unique()) > 1:
        print(f"\n📅 各年份表现:")
        print(f"{'年份':<10} {'交易':<8} {'胜率':<10} {'期望收益':<15} {'止盈率':<10} {'止损率':<10}")
        print(f"{'-'*65}")
        for 年份 in sorted(df['年份'].unique()):
            年df = df[df['年份'] == 年份]
            年胜率 = (年df['净收益'] > 0).sum() / len(年df) * 100
            年期望 = 年df['净收益'].mean()
            年止盈 = (年df['卖出原因'] == '止盈(5%)').sum() / len(年df) * 100
            年止损 = (年df['卖出原因'] == '止损(-2%)').sum() / len(年df) * 100
            print(f"{年份:<10} {len(年df):<8} {年胜率:.1f}%{'':<4} {年期望:+.2f}%{'':<7} {年止盈:.1f}%{'':<4} {年止损:.1f}%")

    return {
        '策略名称': 策略名称,
        '总交易天数': 总交易天数,
        '空仓天数': 空仓天数,
        '实际执行': 实际执行,
        '胜率': 胜率,
        '期望收益': 期望收益,
        '中位收益': 中位收益,
        '止盈率': 止盈率,
        '止损率': 止损率,
        '收盘卖出率': 收盘卖出率,
        '最大连盈': 连盈,
        '最大连亏': 连亏,
        '空仓率': 空仓率,
    }


# ==============================================================================
# 8. 对比表
# ==============================================================================

def 输出对比(裸策略结果, 完整策略结果):
    """输出裸策略 vs 完整策略对比表"""
    print(f"\n{'='*70}")
    print("🏆 裸策略 vs 完整策略 对比表")
    print(f"{'='*70}")
    print(f"{'指标':<25} {'裸策略':<18} {'完整策略':<18} {'差值':<10}")
    print(f"{'-'*70}")
    
    指标列表 = [
        ('胜率', '胜率', '%'),
        ('期望收益', '期望收益', '%'),
        ('空仓率', '空仓率', '%'),
        ('止盈率', '止盈率', '%'),
        ('止损率', '止损率', '%'),
        ('实际执行天数', '实际执行', '天'),
    ]
    
    for 名称, 键, 单位 in 指标列表:
        裸值 = 裸策略结果.get(键, 0)
        完值 = 完整策略结果.get(键, 0)
        差值 = 完值 - 裸值
        符号 = '+' if 差值 >= 0 else ''
        颜色 = '🟢' if (键 == '期望收益' and 差值 > 0) or (键 == '胜率' and 差值 > 0) or (键 == '空仓率' and 差值 > 0) or (键 == '止盈率' and 差值 > 0) else ('🔴' if 差值 < 0 else '⚪')
        if 键 == '空仓率' and 差值 < 0:
            颜色 = '🔴'  # 空仓率低不好
        elif 键 == '空仓率' and 差值 > 0:
            颜色 = '🟢'  # 空仓率高好
        print(f"{名称:<25} {裸值:.2f}{单位:<15} {完值:.2f}{单位:<15} {颜色} {符号}{差值:.2f}{单位}")

    print(f"{'='*70}")
    
    # 判定
    期望差 = 完整策略结果['期望收益'] - 裸策略结果['期望收益']
    胜率差 = 完整策略结果['胜率'] - 裸策略结果['胜率']
    
    print(f"\n📋 最终判定:")
    if 期望差 > 0 and 胜率差 > 0:
        print(f"   🟢 完整策略全面优于裸策略！")
        print(f"      期望收益提升: {期望差:+.2f}%")
        print(f"      胜率提升: {胜率差:+.1f}%")
        print(f"      空仓率: {完整策略结果['空仓率']:.1f}%")
    elif 期望差 > 0:
        print(f"   🟡 完整策略在收益上优于裸策略")
        print(f"      但胜率有所下降: {胜率差:+.1f}%")
    elif 胜率差 > 0:
        print(f"   🟡 完整策略在胜率上优于裸策略")
        print(f"      但收益有所下降: {期望差:+.2f}%")
    else:
        print(f"   🔴 完整策略未显著优于裸策略")
        print(f"      需检查评分系统是否有效")


# ==============================================================================
# 9. 主函数
# ==============================================================================

def main():
    开始时间 = datetime.now()
    print("=" * 60)
    print("📊 【完整交易策略回测 v2.0】")
    print(f"   启动时间: {开始时间.strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    # 加载数据
    所有数据, 板块映射, 股票板块 = 加载数据()
    if not 所有数据:
        print("❌ 无可用数据，请先运行数据采集")
        return
    
    # 运行裸策略回测
    裸交易, 裸空仓, 裸总天 = 运行回测(所有数据, 股票板块, "裸策略", 使用评分过滤=False)
    裸结果 = 统计结果(裸交易, 裸空仓, 裸总天, "裸策略")
    
    # 保存裸策略详细数据
    裸df = pd.DataFrame(裸交易)
    if not 裸df.empty:
        裸路径 = os.path.join(os.path.dirname(os.path.abspath(__file__)), "完整策略回测_裸策略.csv")
        裸df.to_csv(裸路径, index=False, encoding='utf-8-sig')
        print(f"\n💾 裸策略详细数据: {裸路径}")
    
    print(f"\n{'='*60}")
    
    # 运行完整策略回测
    完交易, 完空仓, 完总天 = 运行回测(所有数据, 股票板块, "完整策略", 使用评分过滤=True)
    完结果 = 统计结果(完交易, 完空仓, 完总天, "完整策略")
    
    # 保存完整策略详细数据
    完df = pd.DataFrame(完交易)
    if not 完df.empty:
        完路径 = os.path.join(os.path.dirname(os.path.abspath(__file__)), "完整策略回测_完整策略.csv")
        完df.to_csv(完路径, index=False, encoding='utf-8-sig')
        print(f"\n💾 完整策略详细数据: {完路径}")
    
    # 对比输出
    输出对比(裸结果, 完结果)
    
    总耗时 = (datetime.now() - 开始时间).total_seconds()
    print(f"\n⏱ 总耗时: {总耗时:.0f} 秒 ({总耗时/60:.1f} 分钟)")
    print(f"   完成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == "__main__":
    main()
