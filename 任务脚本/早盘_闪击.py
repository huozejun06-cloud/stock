# ==============================================================================
# 任务脚本/早盘_闪击.py — ⚡ 早盘闪击买入（9:30-9:35运行）
# 功能：判断预选池个股是否出现早盘闪击买入机会
# 条件：股价突破压力位1 + 放量(>昨日5分均量×2) + 主力资金净流入
# 运行：python3 main.py shanjied
# ★ 铁律1：跨进程状态持久化（读/写 缓存/预选池.json）
# ★ 铁律2：昨日成交量分母安全熔断
# ★ 铁律3：5分钟K线空列表保护（防 IndexError）
# ==============================================================================

import sys
import os
import json
from config import CACHE_DIR
import time
from datetime import datetime
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from 工具库.分钟线数据 import 获取5分钟K线
from 工具库.数据源管理器 import get_manager


def 更新预选池状态(代码: str, 新状态: str, 附加数据: dict = None):
    """
    ★ 铁律1：跨进程状态持久化
    读取 JSON → 修改该股 status → 写回文件
    """
    try:
        with open(os.path.join(CACHE_DIR, '预选池.json'), 'r', encoding='utf-8') as f:
            预选池 = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"  ⚠️ 读取预选池失败: {e}")
        return

    for 股 in 预选池['预选股']:
        if 股['代码'] == 代码:
            股['status'] = 新状态
            if 附加数据:
                股.update(附加数据)
            break
    else:
        print(f"  ⚠️ 未在预选池中找到 {代码}")
        return

    with open(os.path.join(CACHE_DIR, '预选池.json'), 'w', encoding='utf-8') as f:
        json.dump(预选池, f, ensure_ascii=False, indent=2)

    print(f"  ✅ 预选池状态更新: {代码} → {新状态}")


def 判断早盘闪击(代码: str, 关键价位: dict, 昨日成交量: int) -> dict:
    """
    判断早盘闪击买入

    条件：
    1. 股价突破压力位1
    2. 成交量 > 昨日5分均量 × 2
    3. 主力资金净流入 > 0

    ★ 铁律3：空列表保护
    ★ 铁律2：分母安全熔断
    """
    # ★ 铁律3：空列表保护
    分时数据 = 获取5分钟K线(代码)
    if not 分时数据 or len(分时数据) < 2:
        return {'闪击': False, '原因': '等待9:35分第一根K线生成'}

    第一根 = 分时数据[0]  # 9:35
    第二根 = 分时数据[1] if len(分时数据) > 1 else 第一根

    当前价 = 第二根['close']
    开盘价 = 第一根['open']
    成交量 = 第二根['volume']

    压力位1 = 关键价位.get('压力位1', 0)

    if 压力位1 <= 0:
        return {'闪击': False, '原因': '关键价位数据无效（压力位1=0）'}

    # ★ 铁律2：分母安全熔断
    昨日5分均量 = 昨日成交量 / 48 if 昨日成交量 > 0 else 1

    # 条件1：突破压力位
    突破压力 = 当前价 > 压力位1

    # 条件2：放量（成交量 > 昨日5分均量 × 2）
    放量 = 成交量 > 昨日5分均量 * 2

    # 条件3：主力资金净流入
    mgr = get_manager()
    df = mgr.get_stock_realtime([代码])
    主力净流入 = df.iloc[0].get('主力净流入', 0) if not df.empty else 0
    资金为正 = 主力净流入 > 0

    if 突破压力 and 放量 and 资金为正:
        return {
            '闪击': True,
            '建议买入价': round(当前价, 2),
            '止损位': 关键价位.get('支撑位1', 0),
            '当前价': round(当前价, 2),
            '成交量': 成交量,
            '昨日5分均量': round(昨日5分均量, 0),
            '量比': round(成交量 / 昨日5分均量, 2) if 昨日5分均量 > 0 else 0,
            '主力净流入': 主力净流入,
            '突破压力位': 压力位1,
        }
    else:
        失败原因 = []
        if not 突破压力:
            失败原因.append(f'未突破压力位{压力位1}(当前价{当前价:.2f})')
        if not 放量:
            失败原因.append(f'成交量不足({成交量}<{昨日5分均量*2:.0f})')
        if not 资金为正:
            失败原因.append(f'主力资金未流入({主力净流入})')
        return {
            '闪击': False,
            '原因': ' + '.join(失败原因),
            '当前价': round(当前价, 2),
            '开盘价': round(开盘价, 2),
            '成交量': 成交量,
            '昨日5分均量': round(昨日5分均量, 0),
            '量比': round(成交量 / 昨日5分均量, 2) if 昨日5分均量 > 0 else 0,
            '压力位1': 压力位1,
            '主力净流入': 主力净流入,
        }


def 执行早盘闪击():
    """
    早盘闪击主流程
    遍历预选池，对status='pending'的个股执行闪击判断
    """
    print("=" * 60)
    print("⚡ 【早盘闪击】9:30-9:35 判断预选股早盘闪击买入机会")
    print(f"   执行时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    # 读取预选池
    try:
        with open(os.path.join(CACHE_DIR, '预选池.json'), 'r', encoding='utf-8') as f:
            预选池 = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"  ❌ 读取预选池失败: {e}")
        print("  💡 请先执行 python3 main.py night 生成预选池")
        return

    if not 预选池['预选股']:
        print("  ⚠️ 预选池为空")
        return

    print(f"  📋 预选池日期: {预选池.get('日期', 'N/A')}")
    print(f"  📋 预选股数量: {len(预选池['预选股'])} 只")

    待处理 = [股 for 股 in 预选池['预选股'] if 股['status'] == 'pending']
    if not 待处理:
        print("  ⏭️ 所有预选股均已处理过，无需再执行闪击")
        return

    print(f"  🎯 待处理预选股: {len(待处理)} 只")
    for 股 in 待处理:
        print(f"    {股['代码']} {股['名称']} | 当前价{股['当前价']:.2f}")

    print()

    闪击结果列表 = []
    for 股 in 待处理:
        代码 = 股['代码']
        名称 = 股['名称']
        关键价位 = 股.get('关键价位', {})
        昨日成交量 = 股.get('昨日成交量', 0)

        print(f"  📡 分析 {代码} {名称} ...")

        结果 = 判断早盘闪击(代码, 关键价位, 昨日成交量)

        print(f"     {'🚀 闪击触发!' if 结果['闪击'] else '⏸ 未触发'}")
        print(f"     原因: {结果['原因'] if '原因' in 结果 else '无'}")

        if 结果['闪击']:
            # ★ 铁律1：跨进程状态回写
            更新预选池状态(代码, 'shanjied', {
                '闪击买入价': 结果['建议买入价'],
                '止损位': 结果['止损位'],
                '闪击时间': datetime.now().strftime('%H:%M'),
            })

            print(f"     ✅ 建议买入价: {结果['建议买入价']}")
            print(f"     🛑 止损位: {结果['止损位']}")
            print(f"     📊 量比: {结果['量比']}")
            print(f"     💰 主力净流入: {结果['主力净流入']}")

        else:
            print(f"     当前价: {结果.get('当前价', 'N/A')}")
            print(f"     量比: {结果.get('量比', 'N/A')}")
            print(f"     压力位1: {结果.get('压力位1', 'N/A')}")
            print(f"     主力净流入: {结果.get('主力净流入', 'N/A')}")

        闪击结果列表.append({
            '代码': 代码,
            '名称': 名称,
            **结果,
        })

        print()

    # 汇总
    闪击数 = sum(1 for r in 闪击结果列表 if r.get('闪击'))
    print("=" * 60)
    print(f"⚡ 早盘闪击完成: {闪击数}/{len(闪击结果列表)} 只触发")
    for r in 闪击结果列表:
        status = "🚀 闪击" if r.get('闪击') else "⏸ 等待"
        print(f"  {status} {r['代码']} {r['名称']}: {r.get('原因', r.get('建议买入价', 'N/A'))}")
    print("=" * 60)

    return 闪击结果列表


if __name__ == "__main__":
    执行早盘闪击()
