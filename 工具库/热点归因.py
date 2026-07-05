"""
工具库/热点归因.py — 同花顺热点归因（替代硬编码板块映射表）
动态获取每只股票的概念/题材标签，支持多标签评分
"""
import sys, os, json, time, re, requests
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class 热点归因器:
    """股票热点/题材标签获取器，替代硬编码BOARD_STOCK_MAP"""
    
    def __init__(self):
        self._缓存 = {}
        self._全部概念 = None
    
    def 获取股票题材(self, 股票代码: str) -> list:
        """获取单只股票的题材标签列表
        优先级：iwencai(同花顺问财) → 新浪 → 本地缓存
        """
        if 股票代码 in self._缓存:
            return self._缓存[股票代码]
        
        # 源1：iwencai 同花顺问财
        tags = self._通过iwencai获取(股票代码)
        if tags:
            self._缓存[股票代码] = tags
            return tags
        
        # 源2：新浪财经
        tags = self._通过新浪获取(股票代码)
        if tags:
            self._缓存[股票代码] = tags
            return tags
        
        return []
    
    def _通过iwencai获取(self, 股票代码: str) -> list:
        """通过同花顺问财接口获取题材标签"""
        try:
            url = "http://www.iwencai.com/stockpick/search"
            params = {
                "w": f"{股票代码} 所属概念板块",
                "querytype": "stock",
                "addSource": "thsi",
            }
            headers = {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
                "Referer": "http://www.iwencai.com/",
            }
            resp = requests.get(url, params=params, headers=headers, timeout=8)
            if resp.status_code != 200:
                return []
            
            # 解析结果：iwencai返回HTML，概念板块在特定标签内
            html = resp.text
            tags = []
            
            # 尝试多种提取方式
            # 方式1：JSON数据
            for m in re.finditer(r'"ConceptName":"([^"]+)"', html):
                tags.append(m.group(1))
            
            # 方式2：普通HTML提取
            if not tags:
                for m in re.finditer(r'概念[：:]\s*([^<]+)', html):
                    parts = re.split(r'[,，、]', m.group(1))
                    tags.extend(p.strip() for p in parts if p.strip())
            
            # 方式3：美股/A股通用板块
            if not tags:
                for m in re.finditer(r'所属行业[：:]\s*([^<]+)', html):
                    tags.append(m.group(1).strip())
            
            return list(set(tags))[:10]  # 最多10个标签去重
        except Exception as e:
            return []
    
    def _通过新浪获取(self, 股票代码: str) -> list:
        """通过新浪财经获取概念标签"""
        try:
            # 新浪股票概念页面
            前缀 = "sh" if 股票代码.startswith(('6','9','5')) else "sz"
            url = f"http://vip.stock.finance.sina.com.cn/corp/go.php/vCI_CorpOtherInfo/stockid/{股票代码}.phtml"
            headers = {"User-Agent": "Mozilla/5.0"}
            resp = requests.get(url, headers=headers, timeout=8)
            resp.encoding = "gbk"
            
            tags = []
            for m in re.finditer(r'(?:概念|板块|题材)[：:]\s*([^<]+)', resp.text):
                parts = re.split(r'[,，、\s]+', m.group(1))
                tags.extend(p.strip() for p in parts if p.strip())
            return list(set(tags))[:10]
        except Exception as e:
            print(f"  ⚠️ 热点归因.py: {e}")
            return []
    
    def 获取全部热门板块(self, 全市场数据: list = None) -> list:
        """获取所有活跃板块及其成分股涨跌（动态计算）
        替代：数据源管理器.get_hot_boards()
        """
        # 使用已有热点数据 + 概念标签增强
        # 如果没有传入全市场数据，返回空列表
        if not 全市场数据:
            return []
        
        # 动态计算板块强度（基于个股涨跌幅聚合）
        板块热度 = {}
        for 股 in 全市场数据:
            tags = self.获取股票题材(股.get('代码',''))
            for tag in tags:
                if tag not in 板块热度:
                    板块热度[tag] = {"涨跌幅": [], "股票": []}
                板块热度[tag]["涨跌幅"].append(股.get("涨跌幅", 0))
                板块热度[tag]["股票"].append(股.get("代码",""))
        
        结果 = []
        for 板块名, 数据 in 板块热度.items():
            if len(数据["涨跌幅"]) < 2:  # 少于2只股票的不算板块
                continue
            avg_pct = sum(数据["涨跌幅"]) / len(数据["涨跌幅"])
            结果.append({
                "名称": 板块名,
                "涨跌幅": round(avg_pct, 2),
                "成分股数": len(数据["涨跌幅"]),
                "领涨股": 数据["股票"][数据["涨跌幅"].index(max(数据["涨跌幅"]))] if 数据["涨跌幅"] else "",
            })
        
        结果.sort(key=lambda x: x["涨跌幅"], reverse=True)
        return 结果[:20]  # Top20板块


# 全局单例
_热点归因器 = None

def get_热点归因器():
    global _热点归因器
    if _热点归因器 is None:
        _热点归因器 = 热点归因器()
    return _热点归因器


def 获取股票题材(代码: str) -> list:
    """快捷接口"""
    return get_热点归因器().获取股票题材(代码)


def 测试():
    """快速测试"""
    r = 热点归因器()
    for code in ["002138", "000063", "600985"]:
        tags = r.获取股票题材(code)
        print(f"{code}: {', '.join(tags) if tags else '无数据'}")

if __name__ == "__main__":
    测试()
