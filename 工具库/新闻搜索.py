"""
新闻搜索模块 — 搜索A股 + 全球金融新闻，情绪反转测试
新增：国际财经新闻搜索（英文关键词）
"""
import requests
import json
import re
import time

def 搜索新闻(关键词, 来源="baidu"):
    """搜索指定关键词的中文新闻"""
    print(f"  🔍 搜索: {关键词}")
    try:
        url = "https://news.baidu.com/s"
        params = {'tn': 'news', 'word': 关键词, 'ie': 'utf-8'}
        headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36', 'Accept': 'text/html'}
        resp = requests.get(url, params=params, headers=headers, timeout=8)
        resp.encoding = 'utf-8'
        新闻列表 = []
        if resp.status_code == 200:
            html = resp.text
            for m in re.finditer(r'<h3[^>]*>.*?<a[^>]*href="([^"]*)"[^>]*>(.*?)</a>', html, re.DOTALL):
                title = re.sub(r'<[^>]+>', '', m.group(2)).strip()
                if title and len(title) > 5:
                    新闻列表.append({'标题': title, '来源': '百度新闻', '链接': m.group(1) if m.group(1).startswith('http') else f'https://news.baidu.com{m.group(1)}'})
        if not 新闻列表:
            新闻列表.append({'标题': f'{关键词}相关新闻', '来源': '搜索摘要'})
        return 新闻列表
    except Exception as e:
        print(f"    ⚠️ 新闻搜索失败: {e}")
        return []

def 搜索国际财经新闻(关键词="", 数量=10):
    """搜索国际财经新闻（英文关键词，免费源多源降级）
    优先级：新浪国际新闻 > 华尔街见闻 > 雅虎财经RSS转换
    """
    print(f"  🌐 搜索国际财经: {关键词 or '最新国际财经'}")
    所有新闻 = []

    # 源1：新浪财经国际新闻流（中文）
    try:
        url = f"https://feed.mix.sina.com.cn/api/roll/get?pageid=153&lid=2511&k=&num={数量}&page=1"
        headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"}
        resp = requests.get(url, headers=headers, timeout=8)
        data = resp.json()
        for item in data.get("result", {}).get("data", []):
            标题 = item.get("title", "").strip()
            if 标题 and len(标题) > 5:
                if not 关键词 or 关键词.lower() in 标题.lower() or 关键词.lower() in item.get("intro","").lower():
                    所有新闻.append({"时间":item.get("ctime",""),"标题":标题,"内容":item.get("intro",""),"来源":"新浪国际"})
    except Exception as e:
        print(f"  ⚠️ 新闻搜索.py: {e}")

    # 源2：华尔街见闻全球快讯
    try:
        url = f"https://api-one.wallstcn.com/apiv1/content/lives?channel=global-channel&limit={数量}&first_page=true"
        headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"}
        resp = requests.get(url, headers=headers, timeout=8)
        for item in resp.json().get("data",{}).get("items",[]):
            标题 = item.get("title","").strip()
            if 标题 and len(标题) > 5:
                if not 关键词 or 关键词.lower() in 标题.lower() or 关键词.lower() in item.get("content_text","").lower():
                    所有新闻.append({"时间":str(item.get("display_time","")),"标题":标题,"内容":item.get("content_text",""),"来源":"华尔街见闻"})
    except Exception as e:
        print(f"  ⚠️ 新闻搜索.py: {e}")

    # 去重
    seen = set()
    去重 = []
    for n in 所有新闻:
        if n['标题'] not in seen:
            seen.add(n['标题'])
            去重.append(n)
    return 去重[:数量]

def 情绪反转测试(新闻列表):
    """新闻情绪反转测试：一致利好=警惕开盘即顶"""
    标题文本 = ' '.join([n.get('标题', '') for n in 新闻列表])
    乐观词数 = sum(1 for 词 in ['暴涨','涨停','龙头','重大利好','突破','新高','领涨','爆发','大涨','强势'] if 词 in 标题文本)
    悲观词数 = sum(1 for 词 in ['风险','下跌','减持','利空','监管','回调','跌停','亏损','立案','警告'] if 词 in 标题文本)
    新闻数 = max(len(新闻列表), 1)
    乐观密度 = 乐观词数 / 新闻数
    if 乐观密度 > 0.3:
        return {'反转概率':'高','警告':'市场一致乐观，警惕利好兑现高开低走','乐观密度':乐观密度,'悲观密度':悲观词数/新闻数}
    elif 乐观密度 > 0.1:
        return {'反转概率':'中','警告':'情绪偏热，需警惕','乐观密度':乐观密度,'悲观密度':悲观词数/新闻数}
    else:
        return {'反转概率':'低','警告':'情绪中性，无一致性预期','乐观密度':乐观密度,'悲观密度':悲观词数/新闻数}

def 批量搜索候选股新闻(候选股列表):
    """为多只候选股搜索新闻并做情绪反转测试"""
    结果 = []
    for 股票 in 候选股列表:
        code = 股票['代码'] if isinstance(股票, dict) else 股票
        name = 股票['名称'] if isinstance(股票, dict) else code
        新闻 = 搜索新闻(f"{name} {code}")
        time.sleep(0.5)
        情绪 = 情绪反转测试(新闻)
        结果.append({'代码':code,'名称':name,'新闻数':len(新闻),'情绪反转':情绪,'新闻':新闻[:3]})
    return 结果

if __name__ == "__main__":
    新闻 = 搜索国际财经新闻("S&P 500", 5)
    print(f"国际财经新闻: {len(新闻)}条")
    for n in 新闻[:3]:
        print(f"  [{n['来源']}] {n['标题'][:60]}")
