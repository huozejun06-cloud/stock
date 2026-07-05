"""
工具库/快讯电报.py — 东方财富7x24实时快讯 + 财联社电报双源
规则：所有函数纯数据获取，不涉及UI，可在QThread中安全调用
"""
import requests
import json
import time
from datetime import datetime


def _headers():
    """统一请求头"""
    return {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                       "AppleWebKit/537.36 (KHTML, like Gecko) "
                       "Chrome/120.0.0.0 Safari/537.36",
        "Referer": "https://www.eastmoney.com/",
    }


def _格式化时间(时间原始值):
    """
    统一时间格式化：
    - Unix 时间戳(10位数字秒级) → YYYY-MM-DD HH:MM:SS
    - 字符串格式 → 截取前19位
    - 其他 → 原值返回
    """
    from datetime import datetime
    if not 时间原始值:
        return ""
    # 检测是否为 Unix 时间戳（10位纯数字）
    时间_str = str(时间原始值)
    if 时间_str.isdigit() and len(时间_str) >= 10:
        try:
            时间戳 = int(时间_str[:10])
            return datetime.fromtimestamp(时间戳).strftime("%Y-%m-%d %H:%M:%S")
        except Exception as e:
            print(f"  ⚠️ 快讯电报.py: {e}")
            pass
    # 字符串格式，截取前19位
    if len(时间_str) > 19:
        return 时间_str[:19]
    return 时间_str


def 获取东财快讯(数量: int = 50) -> list:
    """
    获取东方财富7x24实时快讯

    Args:
        数量: 获取条数，默认50

    Returns:
        list[dict]: [{时间, 标题, 内容, 来源}, ...]
    """
    url = "https://push2.eastmoney.com/api/qt/content/get/7x24"
    params = {
        "fields": "title,content,showtime,seq",
        "page": 1,
        "pageSize": 数量,
    }
    try:
        resp = requests.get(url, params=params, headers=_headers(), timeout=8)
        resp.encoding = "utf-8"
        data = resp.json()

        快讯列表 = []
        if data and data.get("data") and data["data"].get("list"):
            for item in data["data"]["list"]:
                快讯列表.append({
                    "时间": item.get("showtime", ""),
                    "标题": item.get("title", ""),
                    "内容": item.get("content", ""),
                    "来源": "东方财富",
                })
        return 快讯列表
    except Exception as e:
        print(f"  ⚠️ 东财快讯获取失败: {e}")
        return []


def 获取财联社电报(数量: int = 50) -> list:
    """
    获取财联社电报（东财失败时的备选）

    Args:
        数量: 获取条数，默认50

    Returns:
        list[dict]: [{时间, 标题, 内容, 来源}, ...]
    """
    url = "https://www.cls.cn/api/telegraph/list"
    params = {
        "category": "all",
        "page": 1,
        "pageSize": 数量,
    }
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                       "AppleWebKit/537.36 (KHTML, like Gecko) "
                       "Chrome/120.0.0.0 Safari/537.36",
        "Referer": "https://www.cls.cn/telegraph",
    }
    try:
        resp = requests.get(url, params=params, headers=headers, timeout=8)
        resp.encoding = "utf-8"
        data = resp.json()

        快讯列表 = []
        if data and data.get("data"):
            for item in data["data"]:
                快讯列表.append({
                    "时间": item.get("ctime", ""),
                    "标题": item.get("title", ""),
                    "内容": item.get("content", ""),
                    "来源": "财联社",
                })
        return 快讯列表
    except Exception as e:
        print(f"  ⚠️ 财联社电报获取失败: {e}")
        return []


def 获取东财快讯V2(数量=20):
    """东方财富实时快讯（备用接口路径）"""
    try:
        url = "https://push2.eastmoney.com/api/qt/content/get/7x24"
        params = {
            "fields": "title,content,showtime,seq",
            "page": 1,
            "pageSize": 数量,
            "client": "web",
            "sec": "",
            "device": "web",
            "version": "1.0"
        }
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
            "Referer": "https://www.eastmoney.com/",
            "Origin": "https://www.eastmoney.com"
        }
        resp = requests.get(url, params=params, headers=headers, timeout=8)
        if resp.status_code != 200:
            raise Exception(f"HTTP {resp.status_code}")
        data = resp.json()
        快讯 = []
        for item in data.get("data", {}).get("list", []):
            快讯.append({
                "时间": item.get("showtime", ""),
                "标题": item.get("title", ""),
                "内容": item.get("content", ""),
                "来源": "📰 东财快讯"
            })
        if 快讯:
            print(f"  ✅ 东财快讯V2: {len(快讯)}条")
            return 快讯
    except Exception as e:
        print(f"  ⚠️ 东财快讯V2失败: {e}")
    return []


def 获取腾讯快讯(数量=20):
    """腾讯财经实时快讯"""
    try:
        url = "https://i.news.qq.com/trpc.qqnews_web/kv_srv/topic"
        params = {
            "topic_id": "100018",
            "limit": 数量,
            "page": 1,
        }
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
            "Referer": "https://news.qq.com/",
        }
        resp = requests.get(url, params=params, headers=headers, timeout=8)
        if resp.status_code != 200:
            raise Exception(f"HTTP {resp.status_code}")
        data = resp.json()
        快讯 = []
        for item in data.get("data", {}).get("list", []):
            快讯.append({
                "时间": item.get("publish_time", ""),
                "标题": item.get("title", ""),
                "内容": item.get("abstract", ""),
                "来源": "📱 腾讯新闻"
            })
        if 快讯:
            print(f"  ✅ 腾讯快讯: {len(快讯)}条")
            return 快讯
    except Exception as e:
        print(f"  ⚠️ 腾讯快讯失败: {e}")
    return []


def 获取百度快讯(数量=20):
    """百度财经实时快讯"""
    try:
        url = "https://finance.pae.baidu.com/selfselect/openapi"
        params = {
            "srcid": "5270",
            "code": "",
            "group": "quanbu",
            "page": 1,
            "pageSize": 数量,
        }
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
            "Referer": "https://finance.baidu.com/",
        }
        resp = requests.get(url, params=params, headers=headers, timeout=8)
        if resp.status_code != 200:
            raise Exception(f"HTTP {resp.status_code}")
        data = resp.json()
        快讯 = []
        for item in data.get("data", []):
            快讯.append({
                "时间": item.get("date", ""),
                "标题": item.get("title", ""),
                "内容": item.get("desc", ""),
                "来源": "🔍 百度财经"
            })
        if 快讯:
            print(f"  ✅ 百度快讯: {len(快讯)}条")
            return 快讯
    except Exception as e:
        print(f"  ⚠️ 百度快讯失败: {e}")
    return []


def 获取新浪A股快讯(数量=20):
    """获取新浪财经A股7x24快讯（归档新闻，作为最终兜底）
    🔧 修复：pageid=153→155（153是国际流，155才是A股国内流）
    """
    try:
        url = f"https://feed.mix.sina.com.cn/api/roll/get?pageid=155&lid=2510&num={数量}&page=1"
        headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"}
        resp = requests.get(url, headers=headers, timeout=8)
        data = resp.json()
        快讯 = []
        for item in data.get("result", {}).get("data", []):
            快讯.append({
                "时间": _格式化时间(item.get("ctime", "")),
                "标题": item.get("title", ""),
                "内容": item.get("intro", ""),
                "来源": "🇨🇳 新浪A股"
            })
        if 快讯:
            print(f"  ⚠️ 新浪A股归档新闻: {len(快讯)}条（非实时）")
            return 快讯
    except Exception as e:
        print(f"  ⚠️ 新浪A股快讯失败: {e}")
    return []


def 获取快讯(数量=50):
    """六源降级：东财V2 → 腾讯 → 百度 → 东财V1 → 财联社 → 新浪A股(兜底)"""
    # 源1：东财V2（增强参数）
    try:
        数据 = 获取东财快讯V2(数量)
        if 数据: return 数据
    except Exception as e:
        print(f"  ⚠️ 东财V2失败: {e}")

    # 源2：腾讯新闻
    try:
        数据 = 获取腾讯快讯(数量)
        if 数据: return 数据
    except Exception as e:
        print(f"  ⚠️ 腾讯快讯失败: {e}")

    # 源3：百度财经
    try:
        数据 = 获取百度快讯(数量)
        if 数据: return 数据
    except Exception as e:
        print(f"  ⚠️ 百度快讯失败: {e}")

    # 源4：东财V1（原始）
    try:
        数据 = 获取东财快讯(数量)
        if 数据: return 数据
    except Exception as e:
        print(f"  ⚠️ 东财快讯失败: {e}")

    # 源5：财联社
    try:
        数据 = 获取财联社电报(数量)
        if 数据: return 数据
    except Exception as e:
        print(f"  ⚠️ 财联社失败: {e}")

    # 源6：新浪A股（绝对兜底，归档新闻）
    try:
        数据 = 获取新浪A股快讯(数量)
        if 数据:
            print(f"  ⚠️ 所有实时源均不可用，使用新浪归档新闻(非实时)")
            return 数据
    except Exception as e:
        print(f"  ⚠️ 新浪A股快讯失败: {e}")

    print("  ❌ 所有快讯源不可用（盘后正常）")
    return []


def 获取国际快讯(数量=20):
    """获取国际市场快讯（华尔街见闻 → 新浪美股 → 新浪国际，三源降级+去重）"""
    所有快讯 = []

    # 源1：华尔街见闻 - 全球市场快讯
    try:
        url = "https://api-one.wallstcn.com/apiv1/content/lives?channel=global-channel&limit={}&first_page=true".format(数量)
        headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"}
        resp = requests.get(url, headers=headers, timeout=8)
        data = resp.json()
        华尔街 = []
        for item in data.get("data", {}).get("items", []):
            华尔街.append({
                "时间": str(item.get("display_time", "")),
                "标题": item.get("title", ""),
                "内容": item.get("content_text", ""),
                "来源": "🌐 华尔街见闻"
            })
        if 华尔街:
            print(f"  ✅ 华尔街见闻: {len(华尔街)}条")
            所有快讯.extend(华尔街)
    except Exception as e:
        print(f"  ⚠️ 华尔街见闻失败: {e}")

    # 源2：新浪美股
    try:
        url = f"https://feed.mix.sina.com.cn/api/roll/get?pageid=153&lid=2509&k=&num={数量}&page=1"
        headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"}
        resp = requests.get(url, headers=headers, timeout=8)
        data = resp.json()
        for item in data.get("result", {}).get("data", []):
           所有快讯.append({
                "时间": _格式化时间(item.get("ctime", "")),
                "标题": item.get("title", ""),
                "内容": item.get("intro", ""),
                "来源": "� 新浪国际"
            })
        if 所有快讯:
            print(f"  ✅ 新浪美股: 新增{len(所有快讯)}条")
    except Exception as e:
        print(f"  ⚠️ 新浪美股失败: {e}")

    # 源3：新浪财经国际新闻
    try:
        url = f"https://feed.mix.sina.com.cn/api/roll/get?pageid=153&lid=2511&k=&num={数量}&page=1"
        headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"}
        resp = requests.get(url, headers=headers, timeout=8)
        data = resp.json()
        for item in data.get("result", {}).get("data", []):
            所有快讯.append({
                "时间": _格式化时间(item.get("ctime", "")),
                "标题": item.get("title", ""),
                "内容": item.get("intro", ""),
                "来源": "🌍 新浪国际"
            })
        if 所有快讯:
            print(f"  ✅ 新浪国际: 新增{len(所有快讯)}条")
    except Exception as e:
        print(f"  ⚠️ 新浪国际失败: {e}")

    # 去重+按时间排序
    seen = set()
    去重后 = []
    for 快讯 in 所有快讯:
        if 快讯['标题'] not in seen:
            seen.add(快讯['标题'])
            去重后.append(快讯)

    去重后.sort(key=lambda x: x.get("时间", ""), reverse=True)
    print(f"  ✅ 国际快讯合计: {len(去重后)}条（去重后）")
    return 去重后[:数量]


if __name__ == "__main__":
    快讯 = 获取快讯(5)
    print(f"获取到 {len(快讯)} 条快讯")
    for k in 快讯[:3]:
        print(f"  [{k['时间']}] {k['标题']}")
    print()
    国际 = 获取国际快讯(5)
    print(f"获取到 {len(国际)} 条国际快讯")
    for k in 国际[:3]:
        print(f"  [{k['时间']}] {k['标题']} - {k['来源']}")
