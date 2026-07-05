"""
工具库/基本面数据.py — 股票基本面财务数据获取
数据源：腾讯(PE/PB/市值) → mootdx(财务明细) → 新浪(补充) → 兜底中性分
评分：EPS增速、ROE、毛利率、营收增速、PE分位
"""
import sys, os, json, re, time, requests
from datetime import datetime
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def 获取基本面评分(股票代码: str, 腾讯行情: dict = None) -> dict:
    """获取股票的基本面评分
    输入：股票代码，腾讯行情数据（可选，包含PE/PB/市值）
    返回：{EPS: float, ROE: float, 营收增速: float, 净利润增速: float, 评分: int, 来源: str}
    """
    # 0. 从腾讯行情提取已有数据
    基本面 = {"EPS": None, "ROE": None, "营收增速": None, "净利润增速": None, "市盈率": None, "市净率": None}
    
    if 腾讯行情:
        基本面["市盈率"] = 腾讯行情.get("市盈率")
        基本面["市净率"] = 腾讯行情.get("市净率")

    # 1. 尝试 mootdx（需要正常配置）
    try:
        import os as _os
        if _os.path.exists(_os.path.expanduser("~/.mootdx/config.json")):
            from mootdx.financial import FinancialFiles
            ff = FinancialFiles()
            # 尝试获取最近一期财务数据
            data = ff.financial(股票代码, year=datetime.now().year - 1, quarter=4)
            if data is not None and not data.empty:
                cols = [str(c).lower() for c in data.columns]
                for c in data.columns:
                    cs = str(c).lower()
                    if "eps" in cs and 基本面["EPS"] is None:
                        基本面["EPS"] = float(data[c].iloc[0]) if data[c].iloc[0] is not None else None
                    elif "roe" in cs and 基本面["ROE"] is None:
                        基本面["ROE"] = float(data[c].iloc[0]) if data[c].iloc[0] is not None else None
                基本面["来源"] = "mootdx"
    except Exception:
        pass

    # 2. 尝试新浪财经
    if not any(v for v in 基本面.values()):
        try:
            prefix = "sh" if str(股票代码).startswith(("6", "9", "5")) else "sz"
            url = f"http://vip.stock.finance.sina.com.cn/corp/go.php/vCI_CorpManager/stockid/{股票代码}.phtml"
            resp = requests.get(url, headers={"User-Agent": "Mozilla/5.0", "Referer": "https://finance.sina.com.cn"}, timeout=8)
            resp.encoding = "gbk"
            html = resp.text
            # 提取EPS
            for m in re.finditer(r'每股收益[：:]\s*([-\d.]+)', html):
                基本面["EPS"] = float(m.group(1))
            for m in re.finditer(r'净资产收益率[：:]\s*([-\d.]+)', html):
                基本面["ROE"] = float(m.group(1))
            for m in re.finditer(r'营业收入增长率[：:]\s*([-\d.]+)', html):
                基本面["营收增速"] = float(m.group(1))
            基本面["来源"] = "新浪"
        except Exception:
            pass

    # 3. 腾讯已包含的数据
    if 基本面["市盈率"] or 基本面["市净率"]:
        if not 基本面.get("来源"):
            基本面["来源"] = "腾讯行情"

    # 4. 计算基本面评分（0-100分）
    评分 = 计算基本面分数(基本面)

    return {
        **基本面,
        "评分": 评分,
        "评级": "优秀" if 评分 >= 70 else ("良好" if 评分 >= 50 else ("一般" if 评分 >= 30 else "较差")),
    }


def 计算基本面分数(基本面: dict) -> int:
    """从基本面数据计算分数"""
    得分 = 50  # 基准分

    # EPS越高越好
    eps = 基本面.get("EPS")
    if eps is not None and eps > 0:
        得分 += min(eps * 10, 15)
    elif eps is not None and eps < 0:
        得分 -= 10

    # ROE越高越好（15%以上优秀）
    roe = 基本面.get("ROE")
    if roe is not None:
        if roe > 20: 得分 += 15
        elif roe > 15: 得分 += 10
        elif roe > 10: 得分 += 5
        elif roe < 0: 得分 -= 10

    # 营收增速
    增速 = 基本面.get("营收增速")
    if 增速 is not None:
        if 增速 > 20: 得分 += 10
        elif 增速 > 10: 得分 += 5
        elif 增速 < -10: 得分 -= 10

    return max(0, min(100, 得分))


def 获取腾讯行情基本面(股票代码: str) -> dict:
    """通过腾讯接口获取基本市盈率/市净率等"""
    try:
        prefix = "sh" if str(股票代码).startswith(("6", "9", "5")) else "sz"
        url = f"http://qt.gtimg.cn/q={prefix}{股票代码}"
        resp = requests.get(url, timeout=5)
        resp.encoding = "gbk"
        if "~" not in resp.text:
            return {}
        parts = resp.text.split("~")
        return {
            "市盈率": float(parts[39]) if len(parts) > 39 and parts[39] else None,
            "市净率": None,  # 腾讯不直接提供PB
            "总市值": float(parts[45]) if len(parts) > 45 and parts[45] else None,
            "流通市值": float(parts[44]) if len(parts) > 44 and parts[44] else None,
        }
    except Exception as e:
        print(f"  ⚠️ 基本面数据.py: {e}")
        return {}


if __name__ == "__main__":
    for code in ["002138", "000063", "600985"]:
        result = 获取基本面评分(code)
        print(f"\n{code}:")
        for k, v in result.items():
            if v is not None:
                print(f"  {k}: {v}")
