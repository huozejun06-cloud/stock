# ==============================================================================
# 任务脚本/夜盘_复盘.py — 🌙 夜盘复盘（前夜任务）
# 功能：收盘后运行，全市场扫描生成预选池 → 计算关键价位 → 保存到缓存/预选池.json
# 运行：python3 main.py night
# 产出：缓存/预选池.json（含昨日成交量 + status字段）
# ==============================================================================

import sys
import os
import json
from config import CACHE_DIR
import time
import pandas as pd
from datetime import datetime
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from 工具库.数据源管理器 import get_manager
from 工具库.数据工具 import 获取日K线数据


# ==============================================================================
# 1. 全市场扫描生成预选池（精选3-5只）
# ==============================================================================

def 生成预选池() -> list:
    """
    复用尾盘_决策报告的选股逻辑，在Top10基础上增加精选条件：
    - 评分 ≥ 70
    - 红线通过数 ≥ 3
    - 排除换手率 < 0.1% 的低流动性股
    """
    print("\n🔍 夜盘复盘：全市场扫描生成预选池...")
    
    mgr = get_manager()
    
    # 获取全市场数据
    market_df = mgr.get_all_market_stocks()
    hot_boards = mgr.get_hot_boards()
    
    if market_df.empty or not hot_boards:
        print("  ❌ 全市场扫描失败")
        return []
    
    print(f"  📊 全市场股票: {len(market_df)} 只 | 热点板块: {len(hot_boards)} 个")
    
    # 复用尾盘的选股逻辑
    from 任务脚本.尾盘_决策报告 import screen_candidates, 单只股票全维度分析, 判断今日是否可交易
    
    # 市场环境判断
    情绪数据 = mgr.get_market_emotion()
    可交易, 原因 = 判断今日是否可交易(情绪数据)
    print(f"\n📊 市场环境: {原因}")
    
    if not 可交易:
        print("  ⏸ 今日不满足交易条件，跳过选股")
        return []
    
    # 候选股筛选（Top10）
    candidates = screen_candidates(market_df, hot_boards, mgr.BOARD_STOCK_MAP)
    if not candidates:
        print("  ⚠️ 今日无符合条件的候选股")
        return []
    
    print(f"\n⚡ 并行分析 {len(candidates)} 只候选股（全维度采集）...")
    
    # 并行分析（复用尾盘逻辑）
    from concurrent.futures import ThreadPoolExecutor, as_completed
    
    候选股分析列表 = []
    with ThreadPoolExecutor(max_workers=min(10, len(candidates))) as executor:
        future_map = {}
        for c in candidates:
            future = executor.submit(
                单只股票全维度分析,
                股票代码=c['代码'],
                股票名称=c['名称'],
                板块=c.get('板块', '未知'),
                涨跌幅=c['涨跌幅'],
                rs=c.get('RS', 0),
                已扫描情绪=情绪数据,
            )
            future_map[future] = c
        
        for future in as_completed(future_map):
            c = future_map[future]
            try:
                result = future.result(timeout=300)
                if result:
                    候选股分析列表.append(result)
                else:
                    print(f"  ⚠️ {c['代码']} {c['名称']} 分析返回空")
            except Exception as e:
                print(f"  ❌ {c['代码']} {c['名称']} 分析异常: {e}")
    
    print(f"  ✅ 完成分析: {len(候选股分析列表)}/{len(candidates)} 只")
    
    if not 候选股分析列表:
        return []
    
    # ★ 用腾讯接口覆盖实时换手率（全维度分析走日K缓存，换手率可能为0）
    print("\n  📡 通过腾讯接口补充实时换手率...")
    for d in 候选股分析列表:
        try:
            df = mgr.get_stock_realtime([d['代码']])
            if not df.empty:
                实时换手率 = float(df.iloc[0].get('换手率', 0))
                if 实时换手率 > 0:
                    d['换手率'] = 实时换手率  # 覆盖缓存值
                    print(f"    {d['代码']} {d['名称']}: 缓存换手率→{实时换手率:.2f}%")
        except Exception as e:
            print(f"    ⚠️ {d['代码']} 实时换手率获取失败: {e}")

    # ★ 精选条件：评分≥65 & 红线通过数≥3 & 换手率≥0.05%
    精选股 = []
    for d in 候选股分析列表:
        评分 = d.get('决策总分', 0)
        红线数 = d.get('红线通过数', 0)
        换手率 = abs(d.get('换手率', 0))
        
        if 评分 >= 65 and 红线数 >= 3 and 换手率 >= 0.05:
            精选股.append(d)
            print(f"  ✅ 精选: {d['代码']} {d['名称']} | 评分{评分:.0f} | 红线{红线数} | 换手率{换手率:.2f}%")
        else:
            print(f"  ⏭️ 淘汰: {d['代码']} {d['名称']} | 评分{评分:.0f}(需≥65) | 红线{红线数}(需≥3) | 换手率{换手率:.2f}%(需≥0.05%)")
    
    # 最多取5只
    精选股 = 精选股[:5]
    print(f"\n  🏆 最终精选 {len(精选股)} 只")
    for i, d in enumerate(精选股, 1):
        print(f"    {i}. {d['代码']} {d['名称']}: {d['涨跌幅']:+.2f}% | 评分{d['决策总分']:.0f} | 红线{d['红线通过数']}/{d['红线总规则']}")
    
    return 精选股


# ==============================================================================
# 2. 计算关键价位（压力位/支撑位）
# ==============================================================================

def 计算关键价位(df_日K: pd.DataFrame) -> dict:
    """
    基于日K线数据计算压力位和支撑位
    
    Returns:
        dict: {
            '压力位1': MA5,
            '压力位2': 前高(20日最高),
            '支撑位1': MA20,
            '支撑位2': 前低(20日最低),
            '筹码密集区': (close*volume).rolling(10).sum() / volume.rolling(10).sum(),
            '当前价': latest close,
            '距压力位1%': (压力位1 - 当前价)/当前价 * 100,
            '距支撑位1%': (支撑位1 - 当前价)/当前价 * 100,
        }
    """
    if df_日K is None or df_日K.empty or len(df_日K) < 20:
        return {
            '压力位1': 0, '压力位2': 0,
            '支撑位1': 0, '支撑位2': 0,
            '筹码密集区': 0, '当前价': 0,
            '距压力位1%': 0, '距支撑位1%': 0,
        }
    
    latest = df_日K.iloc[-1]
    close_series = df_日K['close']
    high_series = df_日K['high']
    low_series = df_日K['low']
    volume_series = df_日K['volume']
    
    MA5 = close_series.rolling(5).mean().iloc[-1]
    前高 = high_series.rolling(20).max().iloc[-1]
    MA20 = close_series.rolling(20).mean().iloc[-1]
    前低 = low_series.rolling(20).min().iloc[-1]
    
    # 筹码密集区 = VWAP 10日
    vwap = (close_series * volume_series).rolling(10).sum() / volume_series.rolling(10).sum()
    筹码密集区 = vwap.iloc[-1] if not vwap.empty else latest['close']
    
    当前价 = latest['close']
    
    距压力位1 = ((MA5 - 当前价) / 当前价 * 100) if 当前价 > 0 else 0
    距支撑位1 = ((MA20 - 当前价) / 当前价 * 100) if 当前价 > 0 else 0
    
    return {
        '压力位1': round(MA5, 2),
        '压力位2': round(前高, 2),
        '支撑位1': round(MA20, 2),
        '支撑位2': round(前低, 2),
        '筹码密集区': round(筹码密集区, 2),
        '当前价': round(当前价, 2),
        '距压力位1%': round(距压力位1, 2),
        '距支撑位1%': round(距支撑位1, 2),
    }


# ==============================================================================
# 3. 保存预选池到缓存/预选池.json
# ==============================================================================

def 保存预选池(预选股列表: list):
    """
    保存预选池到JSON文件（含昨日总成交量 + status跨进程状态字段）
    
    ★ 铁律1：跨进程状态持久化
    ★ 铁律2：昨日成交量分母安全熔断 → 在JSON中固化昨日总成交量
    """
    import json
    from datetime import datetime
    
    数据 = {
        '日期': datetime.now().strftime('%Y-%m-%d'),
        '生成时间': datetime.now().strftime('%H:%M'),
        '预选股': []
    }
    
    for 股 in 预选股列表:
        代码 = 股['代码']
        
        # 获取日K线数据从缓存
        日K数据 = None
        昨日成交量 = 0
        try:
            日K数据 = 获取日K线数据(代码, 使用缓存=True)
            if 日K数据 is not None and not 日K数据.empty:
                昨日成交量 = int(日K数据['volume'].iloc[-1])
        except Exception as e:
            print(f"  ⚠️ 获取{代码}日K线失败: {e}")
            日K数据 = None
        
        # ★ 计算关键价位
        关键价位 = 计算关键价位(日K数据)
        
        数据['预选股'].append({
            '代码': 代码,
            '名称': 股['名称'],
            '板块': 股.get('板块', ''),
            '评分': 股.get('决策总分', 0),
            '当前价': 股.get('最新价', 0),
            '关键价位': 关键价位,
            '昨日成交量': 昨日成交量,  # ★ 必须固化，供早盘闪击使用
            'status': 'pending',      # ★ 跨进程状态
            '入选理由': str(股.get('决策理由', ''))[:100] if 股.get('决策理由') else '',
        })
    
    # 确保缓存目录存在
    os.makedirs('缓存', exist_ok=True)
    
    with open(os.path.join(CACHE_DIR, '预选池.json'), 'w', encoding='utf-8') as f:
        json.dump(数据, f, ensure_ascii=False, indent=2)
    
    print(f"\n  ✅ 预选池已保存: {len(预选股列表)}只")
    print(f"     📄 缓存/预选池.json")
    for 股 in 数据['预选股']:
        关键 = 股['关键价位']
        print(f"     {股['代码']} {股['名称']} | "
              f"当前价{股['当前价']:.2f} | "
              f"压力位1={关键['压力位1']} | "
              f"支撑位1={关键['支撑位1']} | "
              f"昨量={股['昨日成交量']} | "
              f"status={股['status']}")


# ==============================================================================
# 4. 主流程
# ==============================================================================

def 执行夜盘复盘():
    """
    夜盘复盘主流程
    """
    print("=" * 60)
    print("🌙 【夜盘复盘】全市场扫描 → 精选预选池 → 关键价位计算")
    print(f"   执行时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # 1. 生成预选池
    预选股列表 = 生成预选池()
    
    if not 预选股列表:
        print("\n⚠️ 今日无符合条件的预选股")
        # 保存空预选池
        保存预选池([])
        print("=" * 60)
        return
    
    # 2. 保存预选池
    保存预选池(预选股列表)
    
    print("\n" + "=" * 60)
    print(f"🌙 夜盘复盘完成！预选 {len(预选股列表)} 只个股")
    print("=" * 60)


if __name__ == "__main__":
    执行夜盘复盘()
