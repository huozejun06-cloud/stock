"""工具库/精准选股.py — 8重标准筛选 + 概率评分"""
import os, sys, pandas as pd
from config import BASE_DIR, CACHE_DIR
sys.path.insert(0, BASE_DIR)

def 加载K线(代码):
    path = os.path.join(CACHE_DIR, f"{代码}_日K.csv")
    if not os.path.exists(path): return None
    return pd.read_csv(path, parse_dates=["date"])

def 精准选股(候选股列表, 市场温度=50, 板块生命周期={}):
    """
    8重标准筛选候选股
    输入: 候选股列表 [{代码,名称,板块}]
    输出: [{代码,名称,通过数,总标准,通过率,理由,风险,概率,仓位建议}]
    """
    结果 = []
    for c in 候选股列表:
        code = c.get('代码','')
        name = c.get('名称','')
        板块 = c.get('板块','')
        df = 加载K线(code)
        if df is None or len(df) < 20: continue
        
        last = df.iloc[-1]
        close = last['close']
        volume = last['volume']
        amount = last['amount']
        
        通过 = 0; total = 8; 理由 = []; 风险 = []
        
        # 1. 站上MA20（趋势向上）
        ma20 = df['close'].rolling(20).mean().iloc[-1]
        if close > ma20:
            通过 += 1; 理由.append("站上MA20")
        else:
            风险.append("跌破MA20")
        
        # 2. 均线多头 (MA5 > MA10)
        ma5 = df['close'].rolling(5).mean().iloc[-1]
        ma10 = df['close'].rolling(10).mean().iloc[-1]
        if ma5 > ma10:
            通过 += 1; 理由.append("均线多头")
        else:
            风险.append("均线空头")
        
        # 3. MACD多头
        ema12 = df['close'].ewm(span=12, adjust=False).mean().iloc[-1]
        ema26 = df['close'].ewm(span=26, adjust=False).mean().iloc[-1]
        dif = ema12 - ema26
        dea = df['close'].ewm(span=12, adjust=False).mean().iloc[-1] - df['close'].ewm(span=26, adjust=False).mean().iloc[-1]
        # simplified MACD check
        if len(df) >= 26:
            ema12_s = df['close'].ewm(span=12, adjust=False).mean()
            ema26_s = df['close'].ewm(span=26, adjust=False).mean()
            dif_v = ema12_s.iloc[-1] - ema26_s.iloc[-1]
            dea_v = (dif_v - (ema12_s.iloc[-2] - ema26_s.iloc[-2]))  # simplified
            if dif_v > dea_v: 通过 += 1; 理由.append("MACD多头")
            else: 风险.append("MACD空头")
        else: 通过 += 1  # 数据不足时默认通过
        
        # 4. BIAS20不过热
        if ma20 > 0:
            bias20 = (close / ma20 - 1) * 100
            if abs(bias20) < 15:
                通过 += 1
            else:
                风险.append("BIAS过热(%.1f%%)" % bias20)
        else: 通过 += 1
        
        # 5. 量价确认（放量上涨或缩量回调）
        avg5 = df['volume'].tail(5).mean()
        avg20 = df['volume'].tail(20).mean()
        vol_ratio = volume / avg5 if avg5 > 0 else 0
        prev_close = df['close'].iloc[-2]
        price_up = close > prev_close
        
        if price_up and vol_ratio > 1.1:
            通过 += 1; 理由.append("放量上涨")
        elif price_up and vol_ratio < 0.7:
            风险.append("缩量上涨(诱多)")
        elif not price_up and vol_ratio > 1.2:
            风险.append("放量下跌(危险)")
        else: 通过 += 1; 理由.append("量价正常")
        
        # 6. 成交额足够（防僵尸股）
        avg_amount = df['amount'].tail(20).mean()
        if avg_amount > 5e7:  # 5000万
            通过 += 1
        else:
            风险.append("成交额过低(%.0f万)" % (avg_amount/1e4))
        
        # 7. 市场温度
        if 市场温度 >= 35: 通过 += 1; 理由.append("市场温度%d°C" % 市场温度)
        else: 风险.append("市场温度过低(%d°C)" % 市场温度)
        
        # 8. 板块生命周期
        板块阶段 = 板块生命周期.get(板块, "未知")
        if 板块阶段 not in ("退潮期", "未知"):
            通过 += 1; 理由.append("板块%s" % 板块阶段)
        else:
            风险.append("板块退潮期")
        
        # 概率计算
        概率 = 通过 / total * 100
        if 概率 >= 87: 评级 = "强烈推荐"
        elif 概率 >= 75: 评级 = "推荐"
        elif 概率 >= 62: 评级 = "可关注"
        else: 评级 = "观望"
        
        # 仓位建议
        if 概率 >= 87: 仓位 = "50-70%%"
        elif 概率 >= 75: 仓位 = "30-50%%"
        elif 概率 >= 62: 仓位 = "10-30%%"
        else: 仓位 = "0-10%%"
        
        结果.append({
            '代码': code, '名称': name, '板块': 板块,
            '通过数': 通过, '总标准': total,
            '通过率': "%.0f%%%%" % (通过/total*100),
            '买入概率': 概率, '评级': 评级,
            '建议仓位': 仓位,
            '入选理由': '; '.join(理由) if 理由 else '无',
            '风险提示': '; '.join(风险) if 风险 else '无',
        })
    
    结果.sort(key=lambda x: -x['买入概率'])
    return 结果


def 精选Top(候选股列表, 市场温度=50, 板块生命周期={}, 取前几名=5):
    """返回精选Top N"""
    all_ = 精准选股(候选股列表, 市场温度, 板块生命周期)
    # 只保留通过数 >= 5 的
    filtered = [r for r in all_ if r['通过数'] >= 5]
    return filtered[:取前几名]


if __name__ == "__main__":
    # 测试
    mock = [{"代码":"002138","名称":"顺络电子","板块":"元件"},
            {"代码":"000063","名称":"中兴通讯","板块":"通信设备"}]
    top = 精选Top(mock, 70, {"元件":"发酵期","通信设备":"启动期"})
    for s in top:
        print("%s %s | 概率%.0f%% | %s | %s" % (s['代码'],s['名称'],s['买入概率'],s['评级'],s['入选理由'][:40]))
