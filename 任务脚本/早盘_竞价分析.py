"""
早盘集合竞价分析
在 9:25-9:30 之间运行，分析竞价结果
"""
import requests
import pandas as pd
from datetime import datetime
import sys
import os
from config import CACHE_DIR
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from 工具库.数据源管理器 import get_manager


def 分析预选股竞价():
    """读取预选池，对比集合竞价数据（9:25后可调用）"""
    import json

    try:
        with open(os.path.join(CACHE_DIR, '预选池.json'), 'r') as f:
            预选池 = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []

    mgr = get_manager()
    结果 = []

    for 股 in 预选池['预选股']:
        if 股['status'] != 'pending':
            continue  # 已处理的不再重复分析

        代码 = 股['代码']
        df = mgr.get_stock_realtime([代码])
        if df.empty:
            continue

        row = df.iloc[0]
        开盘涨幅 = row.get('涨跌幅', 0)
        竞价量 = row.get('成交量', 0)
        当前价 = row.get('最新价', 0)
        压力位1 = 股.get('关键价位', {}).get('压力位1', 0)

        # 判定类型
        if 当前价 > 压力位1 and 开盘涨幅 > 3:
            判定 = "🚀 超预期突破（早盘可追）"
        elif 开盘涨幅 > 0:
            判定 = "🟢 正常高开（观察）"
        elif 开盘涨幅 > -2:
            判定 = "🟡 小幅低开（等尾盘）"
        else:
            判定 = "🔴 大幅低开（放弃）"

        结果.append({
            '代码': 代码,
            '名称': 股['名称'],
            '开盘涨幅': 开盘涨幅,
            '竞价量': 竞价量,
            '当前价': 当前价,
            '压力位': 压力位1,
            '判定': 判定,
        })

    return 结果


def 获取竞价数据():
    """获取全市场集合竞价结果"""
    print("📡 获取集合竞价数据...")
    mgr = get_manager()
    df = mgr.get_all_market_stocks()
    if df.empty:
        print("  ❌ 获取全市场数据失败")
        return {'涨幅前30': [], '量比前30': []}

    # 按涨跌幅排序取前30
    涨幅前30 = df.nlargest(30, '涨跌幅').to_dict('records')
    # 如果数据有量比字段则按量比排序，否则按涨跌幅
    量比前30 = df.nlargest(30, '涨跌幅').to_dict('records')

    print(f"  ✅ 获取成功，全市场 {len(df)} 只股票")
    print(f"  📊 涨幅前3: {[(r.get('名称',''), r.get('涨跌幅',0)) for r in 涨幅前30[:3]]}")

    return {
        '涨幅前30': 涨幅前30,
        '量比前30': 量比前30,
        '全市场': df,
        '时间': datetime.now().strftime('%H:%M'),
    }


def 竞价反向审计(竞价数据):
    """竞价对抗审计：高开不等于买入"""
    问题列表 = []

    for 股票 in 竞价数据.get('涨幅前30', []):
        代码 = 股票.get('代码', '')
        名称 = 股票.get('名称', '')
        涨幅 = 股票.get('涨跌幅', 0)
        量比 = 股票.get('量比', 0)

        # 问题1：非龙头高换手需警惕
        if 量比 > 3:
            问题列表.append(f"⚠️ {代码} {名称} 量比异常({量比})，非龙头高换手需警惕")

        # 问题2：主力流出却高开，警惕诱多
        主力净流入 = 股票.get('主力净流入', 0)
        if 主力净流入 < 0 and 涨幅 > 3:
            问题列表.append(f"⚠️ {代码} {名称} 主力流出({主力净流入})却高开{涨幅:+.2f}%，警惕诱多")

    return {
        '审计通过': len(问题列表) == 0,
        '具体警告': 问题列表[:5],
        '警告数': len(问题列表),
    }


def 分析候选股竞价(候选股列表):
    """分析昨日候选股今日竞价表现"""
    结果 = []
    mgr = get_manager()
    codes = [s['代码'] if isinstance(s, dict) else s for s in 候选股列表]
    df = mgr.get_stock_realtime(codes)
    for s in 候选股列表:
        code = s['代码'] if isinstance(s, dict) else s
        name = s['名称'] if isinstance(s, dict) else code
        row = df[df['代码'] == code]
        if not row.empty:
            r = row.iloc[0]
            结果.append({
                '代码': code,
                '名称': name,
                '竞价涨幅': r.get('涨跌幅', 0),
                '竞价量比': r.get('量比', 0),
                '竞价成交额': r.get('成交额', 0),
            })
        else:
            结果.append({'代码': code, '名称': name, '竞价涨幅': 0, '竞价量比': 0, '竞价成交额': 0})
    return 结果


def 执行竞价分析(候选股列表=None):
    """竞价分析主入口"""
    print("=" * 60)
    print("🌅 【早盘竞价分析】9:25-9:30 集合竞价审计")
    print(f"   执行时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    竞价数据 = 获取竞价数据()
    if not 竞价数据['涨幅前30']:
        print("  ⚠️ 竞价数据为空，跳过审计")
        return {'审计通过': False, '具体警告': ['无竞价数据'], '候选股表现': []}

    审计结果 = 竞价反向审计(竞价数据)
    print(f"\n📊 竞价反向审计结果：{'✅ 通过' if 审计结果['审计通过'] else '❌ 有警告'}")
    for w in 审计结果['具体警告']:
        print(f"  {w}")

    候选股表现 = []
    if 候选股列表:
        候选股表现 = 分析候选股竞价(候选股列表)
        print(f"\n📊 昨日候选股竞价表现:")
        for c in 候选股表现:
            print(f"  {c['代码']} {c['名称']}: {c['竞价涨幅']:+.2f}% 量比{c['竞价量比']}")

    审计结果['候选股表现'] = 候选股表现
    return 审计结果


if __name__ == "__main__":
    执行竞价分析()
