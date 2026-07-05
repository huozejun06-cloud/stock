"""工具库/辩论机制.py — 多Agent投票系统"""
def 辩论(理由, 风险, 技术概率, 市场温度, 板块阶段):
    """5个Agent辩论: Bull/Bear/Tech/News/Macro"""
    bull = min(100, 60 + len(理由 or '') * 0.5)
    bear = min(100, 50 + len(风险 or '') * 0.5)
    tech = 技术概率
    macro = 70 if 市场温度 >= 60 else (50 if 市场温度 >= 40 else 30)
    news = 40 if "退潮" in 板块阶段 or "未知" in 板块阶段 else 60
    买入 = bull * 0.3 + tech * 0.3 + macro * 0.2 + news * 0.1
    卖出 = bear * 0.1
    prob = min(100, round(买入 / (买入 + 卖出 + 0.01) * 100, 1))
    共识 = "看多一致" if prob>80 else "偏多" if prob>60 else "分歧" if prob>40 else "偏空" if prob>20 else "看空一致"
    return {"概率":prob,"共识":共识}

if __name__ == "__main__":
    print(辩论("站上MA20;均线多头;MACD多头","", 88, 70, "发酵期"))
