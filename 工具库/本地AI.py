"""
工具库/本地AI.py — 本地规则引擎（代替DeepSeek）
基于已有数据生成自然语言市场解读，不需要任何API
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def 生成解读(温度: dict, 周期: dict, 机会榜: list, 风险警告: list,
            龙头列表: list = None) -> str:
    """从已有数据生成市场解读"""
    lines = []
    temp = 温度.get('温度', 50)
    周期名 = 周期.get('周期', '未知')
    
    # 1. 市场总览
    lines.append("## 📊 市场环境")
    lines.append("")
    if temp >= 75:
        lines.append("今日市场温度**%.0f°C**，处于主升期。涨停家数充裕，赚钱效应明显，适合积极交易。" % temp)
    elif temp >= 55:
        lines.append("今日市场温度**%.0f°C**，处于修复/震荡期。结构性机会为主，精选个股。" % temp)
    elif temp >= 35:
        lines.append("今日市场温度**%.0f°C**，偏弱。控制仓位，减少操作频率。" % temp)
    else:
        lines.append("今日市场温度**%.0f°C**，处于冰点期。空仓或极轻仓，耐心等待。" % temp)
    lines.append("市场状态: **%s** | 建议仓位: **%s**" % (周期名, 温度.get('建议', '')))
    lines.append("")
    
    # 2. 热门板块与龙头
    if 龙头列表:
        lines.append("## 🔥 热门板块与龙头")
        lines.append("")
        for b in 龙头列表[:3]:
            lines.append("- %s 龙一: %s (%s)" % (b.get('板块',''), b.get('龙一',''), b.get('涨幅','')))
        lines.append("")
    
    # 3. 最强机会
    if 机会榜:
        lines.append("## 🏆 今日最强机会")
        lines.append("")
        for s in 机会榜[:3]:
            lines.append("No.%d **%s %s** 总分%s | %s" % (s['排名'], s['代码'], s['名称'], s['总分'], s['原因']))
        lines.append("")
    
    # 4. 风险提示
    if 风险警告:
        lines.append("## ⚠️ 风险提示")
        lines.append("")
        for w in 风险警告:
            lines.append("- %s" % w)
        lines.append("")
    
    # 5. 操作建议
    lines.append("## 💡 操作建议")
    lines.append("")
    if 周期名 in ('冰点',):
        lines.append("当前情绪冰点，不宜开新仓。可关注冰点后修复的反弹机会。")
    elif 周期名 == '退潮':
        lines.append("退潮期建议减仓防御，降低预期。等待情绪企稳。")
    elif 周期名 in ('发酵', '主升'):
        lines.append("市场情绪积极，可围绕主线板块操作，注意高潮分歧风险。")
    else:
        if temp >= 55:
            lines.append("市场正常交易区间，按规则执行即可。")
        else:
            lines.append("市场偏弱，建议降低仓位，多看少动。")
    lines.append("")
    lines.append("---")
    lines.append("*本地AI分析 · 不依赖任何外部API*")
    
    return "\n".join(lines)


def 生成个股解读(代码: str, 名称: str, 评分: float, 信号: str,
               市场温度: int, 仓位: dict, 预案: dict = None) -> str:
    """生成单只个股的解读"""
    lines = []
    lines.append("## %s %s" % (代码, 名称))
    lines.append("")
    lines.append("**信号**: %s | **总分**: %.0f | **建议仓位**: %s" % (信号, 评分, 仓位.get('建议仓位','-')))
    lines.append("")
    if 评分 >= 80:
        lines.append("该股各项指标表现优秀，处于强势区间。")
    elif 评分 >= 60:
        lines.append("该股指标中性偏强，有交易价值但需控制仓位。")
    else:
        lines.append("该股评分偏低，建议观望。")
    
    if 预案:
        lines.append("")
        lines.append("**明日预案**:")
        lines.append(预案.get('预案', ''))
    
    return "\n".join(lines)


if __name__ == "__main__":
    # Test
    from 工具库.情绪周期 import 市场温度, 判断情绪周期, 最强机会榜, 组合风险分析, 龙头识别
    mock_data = {"涨停家数": 86, "跌停家数": 18, "上涨家数": 2800, "下跌家数": 1800, "全市场股票": 4663}
    温度 = 市场温度(mock_data)
    周期 = 判断情绪周期(mock_data)
    解读 = 生成解读(温度, 周期, [{"排名":1,"代码":"002138","名称":"顺络电子","总分":92,"原因":"引擎信号积极"}],
                 ["⚠ PCB板块占比78%，风险集中"])
    print(解读)
