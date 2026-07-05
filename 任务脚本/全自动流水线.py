"""
任务脚本/全自动流水线.py — 全自动选股分析流水线
合并：扫描→精准选股→辩论→概率输出
"""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def 运行流水线(取前几名=5):
    """全自动流水线主流程"""
    print("="*60); print("🚀 全自动选股流水线"); print("="*60)
    data = {}
    
    # Step 1: 扫描
    print("\n1/4 📡 全市场扫描...")
    from 工具库.数据源管理器 import get_manager
    m = get_manager(); df = m.get_all_market_stocks()
    hot = m.get_hot_boards(); 情绪 = m.get_market_emotion()
    from 任务脚本.尾盘_决策报告 import screen_candidates
    cand = screen_candidates(df, hot, m.BOARD_STOCK_MAP)
    print("   候选: %d只" % len(cand))
    if not cand: return {"精选":[],"错误":"无候选股"}
    data['候选股'] = cand
    
    # Step 2: 市场温度+板块生命周期
    print("2/4 🌡️ 市场温度+板块周期...")
    from 工具库.情绪周期 import 市场温度, 判断情绪周期
    from 工具库.热点生命周期 import 批量生命周期
    temp = 市场温度(情绪)
    cycle = 判断情绪周期(情绪)
    lifecycle = 批量生命周期(m.BOARD_STOCK_MAP)
    板块周期映射 = {r['板块']:r['阶段'] for r in lifecycle}
    data['温度'] = temp.get('温度',50)
    data['周期'] = cycle.get('周期','')
    print("   温度: %d°C | %s" % (数据['温度'], 周期['周期']))
    
    # Step 3: 精准选股
    print("3/4 🔍 精准选股(8重标准)...")
    from 工具库.精准选股 import 精准选股
    results = 精准选股(cand, data['温度'], 板块周期映射)
    
    # Step 4: 辩论+概率
    print("4/4 🗳️ AI辩论(多Agent投票)...")
    from 工具库.辩论机制 import 辩论
    for s in results:
        辩 = 辩论(s.get('入选理由',''), s.get('风险提示',''), 
                  s.get('买入概率',50), data['温度'], 板块周期映射.get(s.get('板块',''),'未知'))
        s['辩论概率'] = 辩.get('概率',50)
        s['辩论共识'] = 辩.get('共识','')
    
    results.sort(key=lambda x: -x.get('辩论概率', x.get('买入概率',0)))
    精选 = [r for r in results if r['通过数'] >= 5][:取前几名]
    data['精选'] = 精选
    
    print("\n"+"="*60)
    print("🏆 精选Top%d" % len(精选))
    for s in 精选:
        print("  %s %s | 概率%.0f%% | %s | 仓位%s" % (
            s.get('代码',''),s.get('名称',''),s.get('辩论概率',s.get('买入概率',0)),
            s.get('评级',''),s.get('建议仓位','')))
        print("    理由: %s" % s.get('入选理由','')[:50])
        print("    风险: %s" % s.get('风险提示','')[:50])
        print("    共识: %s" % s.get('辩论共识',''))
    
    return data

def main():
    r = 运行流水线(5)
    if '错误' in r: print("错误: %s" % r['错误'])

if __name__ == "__main__":
    main()
