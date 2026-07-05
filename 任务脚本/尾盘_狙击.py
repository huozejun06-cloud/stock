"""
任务脚本/尾盘_狙击.py — 尾盘狙击模式
按你的规则找买入标的，出场时机由你自主判断
"""
import sys, os
from datetime import datetime
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def 执行尾盘狙击():
    print("=" * 60)
    print("🎯 尾盘狙击模式 v2.0")
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"   执行时间: {ts}")
    print("=" * 60)

    from 工具库.数据源管理器 import get_manager
    mgr = get_manager()
    
    print("\n📡 全市场扫描...")
    market_df = mgr.get_all_market_stocks()
    hot_boards = mgr.get_hot_boards()

    from 任务脚本.尾盘_决策报告 import screen_candidates
    candidates = screen_candidates(market_df, hot_boards, mgr.BOARD_STOCK_MAP)
    if not candidates:
        print("\n⏸ 今日无候选股，空仓等待")
        return

    print(f"\n🏆 初选 {len(candidates)} 只候选股")
    合格 = []
    for c in candidates:
        code = c['代码']; name = c['名称']
        from 工具库.数据工具 import 采集全量数据
        try:
            数据 = 采集全量数据(code, 使用缓存=True, 快速模式=True)
            last = 数据['最新']
        except:
            continue
        
        close = last['close']; ma20 = last.get('MA20', 0)
        dif = last.get('DIF', 0); dea = last.get('DEA', 0)
        
        if not (dif > dea): continue
        距 = (close - ma20) / ma20 * 100 if ma20 > 0 else 999
        if abs(距) > 2: continue
        亏损 = max(abs(距), 0.5)
        if 3.0 / 亏损 < 3: continue
        
        合格.append({
            '代码': code, '名称': name, '价格': close, 'MA20': ma20,
            '距MA20': round(距, 2), '盈亏比': round(3.0 / 亏损, 1),
        })
    
    if not 合格:
        print("\n🔴 今日无符合入场条件的标的")
        return
    
    合格.sort(key=lambda x: abs(x['距MA20']))
    best = 合格[0]
    
    print(f"\n🎯 狙击目标: {best['代码']} {best['名称']}")
    print(f"   当前价: {best['价格']:.2f}")
    print(f"   20日线: {best['MA20']:.2f} (重要支撑位)")
    print(f"   距MA20: {best['距MA20']:+.2f}%  |  盈亏比: {best['盈亏比']}")
    print()
    print(f"📌 交易模板:")
    print(f"   ├─ 入场价: {best['价格']:.2f}")
    print(f"   ├─ 止损参考: {best['MA20']:.2f} (跌破需警惕)")
    print(f"   └─ 仓位: 单品全仓 | 注意单笔>5000")
    print()
    print(f"⏱ 时间窗口: 14:35-14:55")
    print(f"💡 出场时机由你实时看盘判断")
    print(f"   持仓期间可随时分析:")
    cmd = f"   python3 main.py monitor {best['代码']} {best['价格']:.2f}"
    print(cmd)


if __name__ == "__main__":
    执行尾盘狙击()
