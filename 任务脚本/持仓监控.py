"""
任务脚本/持仓监控.py — 持仓实时监控分析
你持仓期间随时跑，系统分析技术面、资金面、量价关系
输出建议但最终由你决策卖出
用法：python3 main.py monitor 002138 [入场价]
"""
import sys, os, json, time, re
from datetime import datetime
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def 监控持仓(股票代码=None, 入场价=None):
    """持仓实时监控"""
    # 处理参数
    if not 股票代码 and len(sys.argv) > 2:
        股票代码 = sys.argv[2]
    if not 入场价 and len(sys.argv) > 3:
        try: 入场价 = float(sys.argv[3])
        except: 入场价 = None
    
    if not 股票代码 or len(str(股票代码)) < 6:
        print("❌ 用法: python3 main.py monitor 股票代码 [入场价]")
        print("   示例: python3 main.py monitor 002138 50.00")
        return
    
    股票代码 = str(股票代码).zfill(6)
    name = ""
    
    print("=" * 60)
    print(f"📡 持仓监控: {股票代码}")
    print(f"   时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    if 入场价:
        try: 入场价 = float(入场价)
        except: pass
        print(f"   入场: {float(入场价):.2f}")
    print("=" * 60)
    
    # 1. 实时行情 + 技术数据
    print("\n📥 获取数据...")
    try:
        from 工具库.数据工具 import 采集全量数据
        数据 = 采集全量数据(股票代码, 使用缓存=True, 快速模式=True)
        df = 数据['数据框']
        last = 数据['最新']
        name = 数据.get('股票名称', '')
        print(f"   {name}({股票代码}) | 最新价: {last['close']:.2f}")
    except Exception as e:
        print(f"   ❌ 数据获取失败: {e}")
        return
    
    close = last['close']
    high = last.get('high', close)
    low = last.get('low', close)
    volume = last.get('volume', 0)
    turnover = last.get('turnover', 0)
    
    # 2. 入场盈亏计算
    print(f"\n💰 盈亏状况:")
    if 入场价 and 入场价 > 0:
        盈亏比 = (close - 入场价) / 入场价 * 100
        入场标记 = "🟢" if 盈亏比 > 0 else ("🔴" if 盈亏比 < 0 else "⚪")
        print(f"   {入场标记} 入场: {入场价:.2f} → 现价: {close:.2f} | 盈亏: {盈亏比:+.2f}%")
    else:
        print(f"   现价: {close:.2f} (未录入入场价)")
    
    # 3. 多维度分析
    print(f"\n📊 技术分析:")
    
    # 均线
    ma5 = last.get('MA5', 0); ma10 = last.get('MA10', 0)
    ma20 = last.get('MA20', 0); ma60 = last.get('MA60', 0)
    if ma5 > ma10 > ma20:
        均线状态 = "多头排列 📈"
        趋势分 = 1
    elif ma5 < ma10 < ma20:
        均线状态 = "空头排列 📉"
        趋势分 = -1
    else:
        均线状态 = "震荡缠绕 ➡️"
        趋势分 = 0
    print(f"   均线: {均线状态}")
    
    # MACD
    dif = last.get('DIF', 0); dea = last.get('DEA', 0)
    macd_col = last.get('MACD柱', 0)
    if dif > dea and macd_col > 0:
        macd状态 = "多头+柱线放大 ✅"
        动能分 = 2
    elif dif > dea:
        macd状态 = "多头但柱线缩小 ⚠️"
        动能分 = 1
    elif dif < dea and macd_col < 0:
        macd状态 = "空头+柱线放大 ❌"
        动能分 = -2
    else:
        macd状态 = "空头但柱线缩小 🔄"
        动能分 = -1
    print(f"   MACD: {macd状态} (DIF={dif:.2f}, DEA={dea:.2f})")
    
    # RSI
    rsi14 = last.get('RSI14', 50)
    if rsi14 > 70:
        rsi状态 = f"超买区({rsi14:.0f}) 🔴"
        动量分 = -1
    elif rsi14 > 50:
        rsi状态 = f"偏强({rsi14:.0f}) 🟢"
        动量分 = 1
    elif rsi14 > 30:
        rsi状态 = f"偏弱({rsi14:.0f}) 🟡"
        动量分 = 0
    else:
        rsi状态 = f"超卖区({rsi14:.0f}) 📈"
        动量分 = 1
    print(f"   RSI14: {rsi状态}")
    
    # 布林
    bol_mid = last.get('布林中轨', 0)
    bol_up = last.get('布林上轨', 0)
    bol_down = last.get('布林下轨', 0)
    if bol_up > 0:
        if close > bol_up:
            布林状态 = "突破上轨 🔴(超买)"
        elif close > bol_mid:
            布林状态 = "上轨附近 📈"
        elif close > bol_down:
            布林状态 = "中下轨间 📉"
        else:
            布林状态 = "跌破下轨 🔴(超卖)"
        print(f"   布林: {布林状态}")
    
    # BIAS
    bias20 = last.get('BIAS20', 0)
    if bias20 > 15:
        bias状态 = f"过热({bias20:.1f}%) 🔴"
    elif bias20 > 8:
        bias状态 = f"偏强({bias20:.1f}%) 🟡"
    elif bias20 > -8:
        bias状态 = f"正常({bias20:.1f}%) ✅"
    else:
        bias状态 = f"超跌({bias20:.1f}%) 📈"
    print(f"   BIAS20: {bias状态}")
    
    # 4. 量价分析
    print(f"\n📊 量价分析:")
    volume_ma5 = last.get('量MA5', 0)
    if volume_ma5 and volume_ma5 > 0 and volume > 0:
        量比 = volume / volume_ma5
        if 量比 > 2: 量价 = f"放量({量比:.1f}倍) 🔴"
        elif 量比 > 1.2: 量价 = f"温和放量({量比:.1f}倍) 🟡"
        else: 量价 = f"缩量({量比:.1f}倍) ✅"
        print(f"   量比: {量价}")
    print(f"   换手: {turnover:.1f}%")
    
    # 5. 综合评分与建议
    总分 = 趋势分 * 30 + 动能分 * 20 + 动量分 * 15 + rsi14/100 * 10
    
    print(f"\n🚦 综合信号:")
    if 总分 > 20:
        信号 = "继续持有 ✅"
        建议 = "趋势健康，可继续持有观察"
    elif 总分 > 0:
        信号 = "谨慎持有 ⚠️"
        建议 = "动能减弱，建议密切关注，考虑减部分仓位锁利"
    elif 总分 > -20:
        信号 = "考虑减仓 🟡"
        建议 = "技术面偏弱，建议减仓保护利润"
    else:
        信号 = "建议卖出 🔴"
        建议 = "多项指标转空，建议止盈/止损"
    
    print(f"   信号: {信号} (总分{总分:.0f})")
    print(f"   建议: {建议}")
    
    # 6. 关键价位
    print(f"\n📌 关键价位参考:")
    if 入场价:
        profit_target_3 = round(入场价 * 1.03, 2)
        print(f"   止盈参考: +3% = {profit_target_3}")
    print(f"   均线支撑: MA20={ma20:.2f}, MA60={ma60:.2f}")
    print(f"   布林阻力: {bol_up:.2f}" if bol_up > 0 else "")
    
    print(f"\n{'='*60}")
    print(f"💡 最终由你决策 — 系统只提供分析参考")
    print(f"{'='*60}")
    
    # 保存结果
    out = f"/Users/harris/Documents/Codex/2026-06-07/stockquant/outputs/持仓监控_{股票代码}.json"
    try:
        with open(out, 'w') as f:
            json.dump({
                '时间': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                '代码': 股票代码, '名称': name, '现价': close,
                '入场价': 入场价, '盈亏': 盈亏比 if 入场价 else None,
                '信号': 信号, '建议': 建议,
            }, f, ensure_ascii=False, indent=2)
        print(f"\n✅ 已保存")
    except: pass


def main():
    if len(sys.argv) > 2:
        监控持仓(sys.argv[2], float(sys.argv[3]) if len(sys.argv) > 3 else None)
    else:
        print("❌ 用法: python3 main.py monitor 股票代码 [入场价]")

if __name__ == '__main__':
    main()
