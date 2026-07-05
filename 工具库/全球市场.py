"""
工具库/全球市场.py — 全球金融市场实时数据模块
美/日/韩/港 股指 + 核心个股 + 汇率 + 大宗商品
数据源：Yahoo Finance 公开API（无需API Key，自动降级）
"""
import requests, json, time, re
from datetime import datetime
from typing import Optional

# ===== 全球指数列表 =====
全球指数列表 = {
    "^GSPC":  ("S&P 500",  "US", "美国"),  "^IXIC":  ("纳斯达克", "US", "美国"),
    "^DJI":   ("道琼斯",   "US", "美国"),  "^N225":  ("日经225",  "JP", "日本"),
    "^KS11":  ("KOSPI",    "KR", "韩国"),  "^HSI":   ("恒生指数", "HK", "香港"),
}
核心美股列表 = {"AAPL":"苹果","MSFT":"微软","GOOGL":"谷歌","AMZN":"亚马逊","META":"Meta","TSLA":"特斯拉","NVDA":"英伟达","AMD":"AMD","TSM":"台积电","AVGO":"博通","QQQ":"纳斯达克100ETF","SPY":"标普500ETF"}
日韩核心股 = {"9984.T":("软银集团","JP"),"6758.T":("索尼","JP"),"7203.T":("丰田","JP"),"005930.KS":("三星电子","KR"),"000660.KS":("SK海力士","KR")}
港股核心 = {"0700.HK":"腾讯控股","9988.HK":"阿里巴巴","1810.HK":"小米集团","9618.HK":"京东集团"}
汇率对 = {"CNY=X":"美元/人民币","JPY=X":"美元/日元","KRW=X":"美元/韩元","HKD=X":"美元/港币"}
大宗商品 = {"GC=F":"黄金","SI=F":"白银","CL=F":"原油","BTC-USD":"比特币"}

def _查询Yahoo单只(代码):
    """查询单只Yahoo Finance行情"""
    try:
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{requests.utils.quote(代码)}"
        resp = requests.get(url, params={"range":"1d","interval":"1d"}, timeout=8,
            headers={"User-Agent":"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36"})
        if resp.status_code != 200: return None
        meta = resp.json().get("chart",{}).get("result",[{}])[0].get("meta",{})
        当前价 = meta.get("regularMarketPrice")
        前收价 = meta.get("chartPreviousClose")
        涨跌幅 = round((当前价-前收价)/前收价*100,2) if 当前价 and 前收价 and 前收价>0 else None
        return {"代码":代码,"当前价":当前价,"涨跌幅":涨跌幅,"数据源":"Yahoo"}
    except Exception as e:
        print(f"  ⚠️ 全球市场.py: {e}")
        return None

# ===== 数据组装 =====
def _组装指数数据(y):
    r=[]
    for c,(n,fl,市) in 全球指数列表.items():
        d=y.get(c)
        if d and d.get("当前价"):
            f=d.get("涨跌幅") or 0; t="+" if f>0 else("-" if f<0 else" ")
            r.append({"代码":c,"名称":f"{fl} {n}","当前价":d["当前价"],"涨跌幅":f,"涨跌标记":t,"市场":市})
    return r

def _组装美股数据(y):
    r=[]
    for c,n in 核心美股列表.items():
        d=y.get(c)
        if d and d.get("当前价"):
            f=d.get("涨跌幅") or 0; t="+" if f>0 else("-" if f<0 else" ")
            r.append({"代码":c,"名称":n,"当前价":d["当前价"],"涨跌幅":f,"涨跌标记":t})
    return r

def _判断全球趋势(指数数据):
    上涨 = sum(1 for i in 指数数据 if (i.get("涨跌幅") or 0) > 0)
    下跌 = sum(1 for i in 指数数据 if (i.get("涨跌幅") or 0) < 0)
    总数 = 上涨 + 下跌
    if 总数 == 0: return {"方向":"数据不足","描述":"全球市场数据不足"}
    方向 = "强势" if 上涨/总数>=0.7 else ("偏强" if 上涨/总数>=0.5 else ("偏弱" if 上涨/总数>=0.3 else "弱势"))
    return {"方向":方向,"描述":f"全球市场{方向} | {上涨}/{总数}指数上涨"}

def _生成市场摘要(数据):
    指数 = 数据.get("全球指数",[])
    趋势 = 数据.get("全球市场趋势",{})
    lines = [f"全球市场摘要 ({数据['获取时间']})", f"趋势: {趋势.get('描述','数据不足')}", ""]
    if 指数:
        lines.append("━━━ 全球指数 ━━━")
        for i in 指数:
            涨跌 = f"{i['涨跌幅']:+.2f}%" if i['涨跌幅'] is not None else "--"
            lines.append(f"  {i['涨跌标记']} {i['名称']:12s} {i['当前价']:>10.2f} {涨跌}")
    return "\n".join(lines)

# ===== 对外接口 =====
def 获取全球市场快照():
    """获取全球金融市场完整快照"""
    print("\n" + "="*60 + "\n全球获取全球金融数据...\n" + "="*60)
    yahoo_结果 = {}
    for 代码 in list(全球指数列表.keys())+list(核心美股列表.keys())+list(日韩核心股.keys())+list(港股核心.keys())+list(汇率对.keys())+list(大宗商品.keys()):
        d = _查询Yahoo单只(代码)
        if d: yahoo_结果[代码] = d
        time.sleep(0.5)
    结果 = {"获取时间":datetime.now().strftime("%Y-%m-%d %H:%M:%S"),"全球指数":_组装指数数据(yahoo_结果),"核心美股":_组装美股数据(yahoo_结果),"_raw":yahoo_结果}
    结果["全球市场趋势"] = _判断全球趋势(结果["全球指数"])
    结果["市场相关摘要"] = _生成市场摘要(结果)
    return 结果

def 获取全球指数快照():
    """轻量版：仅获取全球主要指数"""
    yahoo_结果 = {}
    for 代码 in 全球指数列表:
        d = _查询Yahoo单只(代码)
        if d: yahoo_结果[代码] = d
        time.sleep(0.5)
    return _组装指数数据(yahoo_结果)

def 获取全球市场决策上下文():
    """生成Markdown格式全球市场上下文（供DeepSeek提示词使用）"""
    try:
        数据 = 获取全球市场快照()
    except Exception as e:
        return f"\n## 🌐 全球市场\n> 数据获取失败: {e}\n"
    lines = ["\n## 🌐 全球金融市场参考", f"> 更新时间: {数据['获取时间']}", f"> 整体趋势: {数据.get('全球市场趋势',{}).get('描述','N/A')}", ""]
    if 数据.get("全球指数"):
        lines.append("### 📊 全球主要指数")
        lines.append("| 指数 | 最新价 | 涨跌幅 |")
        lines.append("|------|--------|--------|")
        for i in 数据["全球指数"]:
            涨跌 = f"{i['涨跌幅']:+.2f}%" if i['涨跌幅'] is not None else "--"
            lines.append(f"| {i['涨跌标记']} {i['名称']} | {i['当前价']:.2f} | {涨跌} |")
        lines.append("")
    if 数据.get("核心美股"):
        lines.append("### 🇺🇸 核心美股")
        lines.append("| 代码 | 名称 | 最新价 | 涨跌幅 |")
        lines.append("|------|------|--------|--------|")
        for s in 数据["核心美股"]:
            涨跌 = f"{s['涨跌幅']:+.2f}%" if s['涨跌幅'] is not None else "--"
            lines.append(f"| {s['代码']} | {s['名称']} | {s['当前价']:.2f} | {涨跌} |")
        lines.append("")
    return "\n".join(lines)

def 获取全球市场文本摘要():
    try:
        return 获取全球市场快照().get("市场相关摘要","获取失败")
    except Exception as e:
        return f"获取失败: {e}"
