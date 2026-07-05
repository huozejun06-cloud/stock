"""
工具库/公告检查.py — 巨潮公告风险检查
在选股流程中检查候选股是否有：ST/退市/减持/立案/诉讼等风险公告
"""
import sys, os, json, re, time, requests
from datetime import datetime, timedelta
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 风险关键词（公告标题匹配）
风险关键词 = {
    "退市风险": ["退市", "终止上市", "暂停上市", "ST", "*ST"],
    "减持风险": ["减持", "减仓", "套现", "转让股份"],
    "监管风险": ["立案", "调查", "监管措施", "警示函", "行政处罚", "责令改正"],
    "业绩风险": ["预亏", "亏损", "业绩下滑", "利润下降", "营收下滑"],
    "法律风险": ["诉讼", "仲裁", "查封", "冻结", "失信", "被执行"],
    "财务风险": ["债务违约", "逾期", "资金占用", "违规担保", "财务造假"],
}

# 正面关键词（公告标题匹配）
正面关键词 = {
    "业绩利好": ["预增", "扭亏", "大幅增长", "创新高"],
    "分红利好": ["分红", "送转", "回购", "增持"],
    "订单利好": ["中标", "合同", "订单", "签约", "重大合同"],
}


def 检查巨潮公告(股票代码: str) -> dict:
    """通过巨潮资讯网查询股票近期公告并检查风险
    返回：{有风险: bool, 风险等级: str, 公告: [...], 摘要: str}
    """
    try:
        # 巨潮公告查询API
        url = "http://www.cninfo.com.cn/new/hisAnnouncement/query"
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "Referer": "http://www.cninfo.com.cn/new/commonUrl?url=disclosure/list/notice",
        }
        页码 = 1
        data = {
            "pageNum": 页码,
            "pageSize": 30,
            "column": "szse_latest",
            "tabName": "fulltext",
            "plate": "sz" if 股票代码.startswith(("0","3","2")) else "sh",
            "stock": 股票代码,
            "category": "",
            "trade": "",
            "seDate": (datetime.now() - timedelta(days=90)).strftime("%Y-%m-%d") + "~" + datetime.now().strftime("%Y-%m-%d"),
            "sortName": "",
            "sortType": "",
            "isHLtitle": True,
        }
        
        resp = requests.post(url, headers=headers, data=data, timeout=10)
        if resp.status_code != 200:
            return {"有风险": False, "风险等级": "无", "公告": [], "摘要": "无法访问巨潮资讯"}
        
        result = resp.json()
        公告列表 = result.get("announcements", []) if "announcements" in result else []
        if not 公告列表 and "totalAnnouncement" in result:
            # 另一种返回格式
            公告列表 = result.get("announcements", [])
        
        风险公告 = []
        正面公告 = []
        
        for ann in 公告列表[:20]:
            标题 = ann.get("announcementTitle", "") or ann.get("title", "")
            if not 标题:
                continue
            
            # 检查风险关键词
            for 风险类型, 关键词列表 in 风险关键词.items():
                for kw in 关键词列表:
                    if kw in 标题:
                        风险公告.append({
                            "标题": 标题.replace("<em>", "").replace("</em>", ""),
                            "类型": 风险类型,
                            "日期": str(ann.get("announcementDate", ann.get("date", "")))[:10],
                        })
                        break
            
            # 检查正面关键词
            for 利好类型, 关键词列表 in 正面关键词.items():
                for kw in 关键词列表:
                    if kw in 标题:
                        正面公告.append({
                            "标题": 标题.replace("<em>", "").replace("</em>", ""),
                            "类型": 利好类型,
                            "日期": str(ann.get("announcementDate", ann.get("date", "")))[:10],
                        })
                        break
        
        # 判定风险等级
        风险等级 = "无"
        高危风险 = [r for r in 风险公告 if r["类型"] in ("退市风险", "监管风险", "财务风险")]
        if 高危风险:
            风险等级 = "高危"
        elif 风险公告:
            风险等级 = "中风险"
        
        return {
            "有风险": 风险等级 != "无",
            "风险等级": 风险等级,
            "风险公告数": len(风险公告),
            "风险公告": 风险公告[:5],
            "利好公告数": len(正面公告),
            "利好公告": 正面公告[:3],
            "摘要": _生成摘要(风险等级, 风险公告, 正面公告),
        }
    except Exception as e:
        return {"有风险": False, "风险等级": "无", "公告": [], "摘要": f"检查失败: {e}"}


def _生成摘要(风险等级: str, 风险公告: list, 正面公告: list) -> str:
    """生成可读的公告摘要"""
    lines = []
    if 风险等级 == "高危":
        lines.append(f"🔴 高危风险公告 {len(风险公告)}条")
    elif 风险等级 == "中风险":
        lines.append(f"🟡 风险公告 {len(风险公告)}条")
    
    for r in 风险公告[:2]:
        lines.append(f"   ⚠️ [{r['日期']}] {r['类型']}: {r['标题'][:50]}")
    
    for r in 正面公告[:1]:
        lines.append(f"   ✅ {r['类型']}: {r['标题'][:50]}")
    
    return "\n".join(lines) if lines else "⚪ 90天内无重大公告"


if __name__ == "__main__":
    for code in ["002138", "300346", "600985"]:
        result = 检查巨潮公告(code)
        print(f"\n{code}:")
        print(f"  风险等级: {result['风险等级']}")
        print(f"  摘要: {result['摘要']}")
