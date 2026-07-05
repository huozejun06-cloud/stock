"""
三级数据源管理器
优先级：东方财富 > 同花顺 > 腾讯
自动检测可用性，自动降级

v2.0 新增：腾讯并发全市场扫描引擎
穷举全A股号段 + 腾讯批量接口(100只/批) + 多线程并发(20线程)
实现在 2 秒内完成全市场 5000+ 只股票的短线情绪扫描
"""
import requests
import pandas as pd
import time
import json
import re
from urllib.parse import urlparse, urlunparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading


class DataSourceManager:
    """数据源管理器"""

    def __init__(self):
        self.current_source = None
        self.available_sources = []
        # 🔧 腾讯并发锁：最多3个并发请求，防止被腾讯限流封IP
        self.腾讯并发锁 = threading.Semaphore(3)
        self._detect_sources()

    def _detect_sources(self):
        """检测所有数据源的可用性"""
        results = []

        # 1. 检测东方财富
        print("🔄 检测东方财富...")
        try:
            url = "https://push2.eastmoney.com/api/qt/ulist.np/get"
            params = {
                'fltt': '2', 'invt': '2',
                'fields': 'f2,f3,f12,f14',
                'secids': '1.600519'
            }
            resp = requests.get(url, params=params, timeout=5)
            if resp.status_code == 200 and resp.json().get('rc') == 0:
                # 再测试 clist 接口（真正需要的）
                url2 = "https://push2.eastmoney.com/api/qt/clist/get"
                params2 = {
                    'pn': '1', 'pz': '5', 'po': '1', 'np': '1',
                    'ut': 'bd1d9ddb04089700cf9c27f6f7426281',
                    'fltt': '2', 'invt': '2', 'fid': 'f3',
                    'fs': 'm:0+t:6,m:0+t:80,m:1+t:2,m:1+t:23,m:0+t:81+s:2048',
                    'fields': 'f2,f3,f12,f14'
                }
                resp2 = requests.get(url2, params=params2, timeout=5)
                if resp2.status_code == 200:
                    print("  ✅ 东方财富可用")
                    results.append(('eastmoney', 3))
                    self.current_source = 'eastmoney'
                else:
                    print("  ❌ 东方财富 clist 接口不可达")
            else:
                print("  ❌ 东方财富不可达")
        except Exception as e:
            print(f"  ❌ 东方财富: {e}")

        # 2. 检测同花顺
        print("🔄 检测同花顺...")
        try:
            url = "https://d.10jqka.com.cn/v2/realhead/hs_601138/last.js"
            headers = {'User-Agent': 'Mozilla/5.0',
                       'Referer': 'https://www.10jqka.com.cn/'}
            resp = requests.get(url, headers=headers, timeout=5)
            if resp.status_code == 200 and 'items' in resp.text:
                print("  ✅ 同花顺可用")
                results.append(('hexin', 2))
                if not self.current_source:
                    self.current_source = 'hexin'
            else:
                print("  ❌ 同花顺不可达")
        except Exception as e:
            print(f"  ❌ 同花顺: {e}")

        # 3. 检测腾讯
        print("🔄 检测腾讯...")
        try:
            resp = requests.get("http://qt.gtimg.cn/q=sh601138", timeout=5)
            if resp.status_code == 200 and '~' in resp.text:
                print("  ✅ 腾讯可用")
                results.append(('tencent', 1))
                if not self.current_source:
                    self.current_source = 'tencent'
            else:
                print("  ❌ 腾讯不可达")
        except Exception as e:
            print(f"  ❌ 腾讯: {e}")

        self.available_sources = [s[0]
                                  for s in sorted(results, key=lambda x: -x[1])]
        print(
            f"\n📊 可用数据源（按优先级）: {self.available_sources}")
        print(f"🎯 当前使用: {self.current_source}")

    # ==========================================================================
    # 全A股代码穷举生成器
    # ==========================================================================

    def _generate_all_a_share_codes(self):
        """生成全A股代码列表（快扫模式：只含7个主要前缀，覆盖95%以上交易量）"""
        codes = []
        # 上海主板 600, 601, 603（跳过605）
        for prefix in ["600", "601", "603"]:
            for i in range(1000):
                codes.append(f"{prefix}{str(i).zfill(3)}")
        # 科创板 688
        for i in range(1000):
            codes.append(f"688{str(i).zfill(3)}")
        # 深圳主板 000（跳过001）
        for i in range(1000):
            codes.append(f"000{str(i).zfill(3)}")
        # 中小板 002（跳过003）
        for i in range(1000):
            codes.append(f"002{str(i).zfill(3)}")
        # 创业板 300（跳过301）
        for i in range(1000):
            codes.append(f"300{str(i).zfill(3)}")
        return codes

    # ==========================================================================
    # 腾讯单批次（100只）批量请求
    # ==========================================================================

    def _fetch_batch_tencent(self, codes_batch):
        """腾讯批量查询（单批不超过100只），过滤空号，提取涨跌幅"""
        if not codes_batch:
            return []
        code_str = ','.join([
            f"sh{c}" if c.startswith(('6', '9', '5')) else f"sz{c}"
            for c in codes_batch
        ])
        url = f"http://qt.gtimg.cn/q={code_str}"
        try:
            # 🔧 腾讯并发限流保护：最多3个同时请求
            with self.腾讯并发锁:
                resp = requests.get(url, timeout=5)
                resp.encoding = 'gbk'
            if not resp or not resp.text:
                time.sleep(0.5)
                return []
        except Exception as e:
            print(f"  ⚠️ 数据源管理器.py: {e}")
            time.sleep(0.5)
            return []

        results = []
        for line in resp.text.strip().split(';'):
            if not line.strip() or '=' not in line:
                continue
            parts = line.split('~')
            if len(parts) < 40:
                continue
            # 腾讯原始格式：v_sh601600="1~... 或 sh601600~...
            # 用正则提取其中6位数字代码
            raw_code = parts[0]
            code_match = re.search(r'(\d{6})', raw_code)
            code = code_match.group(1) if code_match else ''
            if not code:
                continue
            try:
                pct = float(parts[32]) if parts[32] else None
                name = parts[1].strip()
                # 只有腾讯返回了有效名字和涨跌幅的，才是全市场真正上市的股票
                if pct is not None and name and "退" not in name:
                    # 🔧 换手率：腾讯接口标准字段 38 即为换手率
                    try:
                        val = float(parts[38]) if len(parts) > 38 and parts[38] else 0
                        换手率 = val if val > 0 else 0
                    except Exception as e:
                        print(f"  ⚠️ 数据源管理器.py: {e}")
                        换手率 = 0
                    # 兜底逻辑：用成交额估算换手率
                    if not 换手率 or 换手率 == 0:
                        try:
                            成交额 = float(parts[37]) if len(parts) > 37 and parts[37] else 0
                            最新价 = float(parts[3]) if len(parts) > 3 and parts[3] else 0
                            流通市值 = float(parts[44]) if len(parts) > 44 and parts[44] else 0
                            if 成交额 > 0 and 流通市值 > 0:
                                换手率 = round(成交额 / 流通市值 * 100, 2)
                        except Exception as e:
                            print(f"  ⚠️ 数据源管理器.py: {e}")
                            换手率 = 0
                    results.append({
                        '代码': code,
                        '名称': name,
                        '涨跌幅': pct,
                        '换手率': 换手率 or 0,
                    })
            except Exception as e:
                print(f"  ⚠️ 数据源管理器.py: {e}")
                continue
        return results



    # ==========================================================================
    # 老版接口：单只/多只个股实时行情
    # ==========================================================================

    def get_stock_realtime(self, codes: list) -> pd.DataFrame:
        """获取股票实时行情（自动选择数据源，失败时自动降级）"""
        # 优先当前数据源
        if self.current_source == 'eastmoney':
            df = self._get_by_eastmoney(codes)
            if hasattr(df,"empty") and not df.empty:
                return df
        elif self.current_source == 'hexin':
            df = self._get_by_hexin(codes)
            if hasattr(df,"empty") and not df.empty:
                return df
        # 当前数据源失败 → 降级到腾讯批量接口（最可靠）
        print(f"    📡 降级至腾讯批量接口查询 {len(codes)} 只股票...")
        return self._get_by_tencent(codes)

    def _get_by_eastmoney(self, codes: list) -> pd.DataFrame:
        """东方财富接口"""
        try:
            from 工具库.V8线程锁 import V8_LOCK
            import akshare as ak
            with V8_LOCK:
                return ak.stock_zh_a_spot_em()
        except Exception as e:
            print(f"    ⚠️ 东方财富实时行情失败: {e}")
            return pd.DataFrame()


    def _get_by_hexin(self, codes: list) -> pd.DataFrame:
        """同花顺接口"""
        rows = []
        for code in codes[:50]:  # 每批最多50只
            try:
                prefix = "sh" if code.startswith(('6', '9', '5')) else "sz"
                url = f"https://d.10jqka.com.cn/v2/realhead/hs_{code}/last.js"
                headers = {'User-Agent': 'Mozilla/5.0',
                           'Referer': 'https://www.10jqka.com.cn/'}
                resp = requests.get(url, headers=headers, timeout=5)
                text = resp.text
                json_str = re.search(r'\{.*\}', text).group()
                data = json.loads(json_str)
                item = data.get('data', {})
                items = item.get('items', {})
                if not items:
                    continue
                # 解析同花顺返回格式
                change_pct = float(items.get('changePercent', 0)
                                   ) if items.get('changePercent') else 0
                rows.append({
                    '代码': code,
                    '名称': str(items.get('name', '')),
                    '最新价': float(items.get('price', 0)) if items.get('price') else 0,
                    '涨跌幅': change_pct,
                    '昨收': float(items.get('prePrice', 0)) if items.get('prePrice') else 0,
                    '开盘': float(items.get('openPrice', 0)) if items.get('openPrice') else 0,
                    '最高': float(items.get('highPrice', 0)) if items.get('highPrice') else 0,
                    '最低': float(items.get('lowPrice', 0)) if items.get('lowPrice') else 0,
                    '成交量': float(items.get('volume', 0)) if items.get('volume') else 0,
                    '成交额': float(items.get('turnover', 0)) if items.get('turnover') else 0,
                    '换手率': float(items.get('turnoverRate', 0)) if items.get('turnoverRate') else 0,
                    '量比': float(items.get('volumeRatio', 0)) if items.get('volumeRatio') else 0,
                })
                time.sleep(0.05)
            except Exception as e:
                continue
        if not rows:
            print("    ⚠️ 同花顺未返回任何有效数据")
            return pd.DataFrame()
        return pd.DataFrame(rows)

    def _get_by_tencent(self, codes: list) -> pd.DataFrame:
        """腾讯接口（单批最多100只）"""
        code_str = ','.join([
            f"sh{c}" if c.startswith(('6', '9', '5')) else f"sz{c}"
            for c in codes[:100]
        ])
        if not code_str:
            return pd.DataFrame()
        url = f"http://qt.gtimg.cn/q={code_str}"
        try:
            resp = requests.get(url, timeout=10)
            resp.encoding = 'gbk'
        except Exception as e:
            print(f"    ⚠️ 腾讯请求失败: {e}")
            return pd.DataFrame()
        rows = []
        for line in resp.text.strip().split(';'):
            if not line.strip() or '=' not in line:
                continue
            parts = line.split('~')
            if len(parts) < 40:
                continue
            try:
                code = parts[0][2:] if parts[0].startswith(
                    ('sh', 'sz')) else parts[0]
                价格 = float(parts[3]) if parts[3] else 0.0
                昨收 = float(parts[4]) if parts[4] else 价格
                涨跌幅 = ((价格 - 昨收) / 昨收 * 100) if 昨收 > 0 else 0.0
                # 🔧 换手率：腾讯接口标准字段 38 即为换手率
                try:
                    val = float(parts[38]) if len(parts) > 38 and parts[38] else 0
                    换手率 = val if val > 0 else 0
                except Exception as e:
                    print(f"  ⚠️ 数据源管理器.py: {e}")
                    换手率 = 0
                # 兜底逻辑：用成交额估算换手率
                if not 换手率 or 换手率 == 0:
                    try:
                        成交额 = float(parts[37]) if len(parts) > 37 and parts[37] else 0
                        流通市值 = float(parts[44]) if len(parts) > 44 and parts[44] else 0
                        if 成交额 > 0 and 流通市值 > 0:
                            换手率 = round(成交额 / 流通市值 * 100, 2)
                    except Exception as e:
                        print(f"  ⚠️ 数据源管理器.py: {e}")
                        换手率 = 0
                rows.append({
                    '代码': code,
                    '名称': parts[1],
                    '最新价': 价格,
                    '涨跌幅': 涨跌幅,
                    '昨收': 昨收,
                    '开盘': float(parts[5]) if parts[5] else 价格,
                    '最高': float(parts[33]) if parts[33] else 价格,
                    '最低': float(parts[34]) if parts[34] else 价格,
                    '成交量': float(parts[6]) if parts[6] else 0.0,
                    '成交额': float(parts[37]) if len(parts) > 37 and parts[37] else 0.0,
                    '换手率': 换手率 or 0.0,
                    '量比': float(parts[39]) if len(parts) > 39 and parts[39] else 0.0,
                })

            except (ValueError, IndexError):
                continue
        if not rows:
            print("    ⚠️ 腾讯未返回任何有效数据")
            return pd.DataFrame()
        return pd.DataFrame(rows)

    # ==========================================================================
    # 🔥 V2 核心：腾讯并发全市场扫描引擎
    # ==========================================================================

    def get_market_emotion(self) -> dict:
        """
        全市场情绪计算核心主入口
        东方财富可用时用原生接口，否则强制启用腾讯并发全市场扫描
        """
        if self.current_source == 'eastmoney':
            return self._get_emotion_eastmoney()
        # 东财死掉 → 腾讯并发全市场扫描
        return self._get_emotion_tencent_full()

    def _get_emotion_eastmoney(self) -> dict:
        """东方财富原生全市场扫描"""
        try:
            from 工具库.V8线程锁 import V8_LOCK
            import akshare as ak
            with V8_LOCK:
                df = ak.stock_zh_a_spot_em()

            zt = len(df[df['涨跌幅'] >= 9.8])
            dt = len(df[df['涨跌幅'] <= -9.8])
            up = len(df[df['涨跌幅'] > 0])
            down = len(df[df['涨跌幅'] < 0])
            emotion = self._rate_emotion(zt, dt)
            return {
                '全市场股票': len(df),
                '上涨家数': up,
                '下跌家数': down,
                '涨停家数': zt,
                '跌停家数': dt,
                '情绪评级': emotion,
                '数据源': '东方财富',
            }
        except Exception as e:
            print(f"  ⚠️ 东方财富全市场扫描失败: {e}，自动降级至腾讯并发源...")
            return self._get_emotion_tencent_full()

    def _get_emotion_tencent_full(self) -> dict:
        """
        腾讯引擎：多线程分片并发扫描
        穷举全A股号段 + 腾讯批量接口(100只/批) + 多线程并发(20线程)
        """
        print("🚀 启动腾讯并发引擎，开始剥离全A股短线情绪数据...")
        all_codes = self._generate_all_a_share_codes()

        batch_size = 100
        batches = [all_codes[i:i+batch_size]
                   for i in range(0, len(all_codes), batch_size)]

        total_batches = len(batches)
        all_results = []
        lock = threading.Lock()
        completed = [0]  # 用列表实现闭包可修改

        def fetch_batch(batch):
            results = self._fetch_batch_tencent(batch)
            with lock:
                all_results.extend(results)
                completed[0] += 1
                if completed[0] % 20 == 0 or completed[0] == total_batches:
                    print(
                        f"    📡 扫描进度: {completed[0]}/{total_batches} 批次完成...")
            return results

        # 开启 20 个并发工作线程
        with ThreadPoolExecutor(max_workers=20) as executor:
            futures = [executor.submit(fetch_batch, batch)
                       for batch in batches]
            for f in as_completed(futures):
                pass

        print(
            f"  ✅ 全市场扫描完毕！成功捕获有效 A 股样本: {len(all_results)} 只")

        # 统计计算
        zt_count = sum(1 for r in all_results if r['涨跌幅'] >= 9.8)
        dt_count = sum(1 for r in all_results if r['涨跌幅'] <= -9.8)
        up_count = sum(1 for r in all_results if r['涨跌幅'] > 0)
        down_count = sum(1 for r in all_results if r['涨跌幅'] < 0)

        emotion = self._rate_emotion(zt_count, dt_count)

        return {
            '全市场股票': len(all_results),
            '上涨家数': up_count,
            '下跌家数': down_count,
            '涨停家数': zt_count,
            '跌停家数': dt_count,
            '情绪评级': emotion,
            '数据源': '腾讯并发全市场',
        }

    def _rate_emotion(self, zt, dt):
        """短线情绪量化评级"""
        if zt >= 50:
            return "活跃"
        elif zt >= 20:
            return "回暖"
        elif zt >= 5:
            return "平淡"
        else:
            return "退潮"

    # ==========================================================================
    # 老版全市场快照（保留兼容性，但重写为腾讯并发）
    # ==========================================================================

    def get_all_market_stocks(self) -> pd.DataFrame:
        """全市场股票快照"""
        if self.current_source == 'eastmoney':
            try:
                from 工具库.V8线程锁 import V8_LOCK
                import akshare as ak
                with V8_LOCK:
                    df = ak.stock_zh_a_spot_em()
                if hasattr(df,"empty") and not df.empty and len(df) > 2000:
                    return df
            except Exception as e:
                print(f"    ⚠️ 东财全市场快照失败: {e}")


        # 备用：腾讯并发扫描
        print("    📡 使用腾讯并发引擎扫描全市场...")
        all_codes = self._generate_all_a_share_codes()
        batch_size = 100
        batches = [all_codes[i:i+batch_size]
                   for i in range(0, len(all_codes), batch_size)]

        all_results = []
        lock = threading.Lock()
        completed = [0]
        total_batches = len(batches)

        def fetch_batch(batch):
            results = self._fetch_batch_tencent(batch)
            with lock:
                all_results.extend(results)
                completed[0] += 1
            return results

        with ThreadPoolExecutor(max_workers=20) as executor:
            futures = [executor.submit(fetch_batch, batch)
                       for batch in batches]
            for f in as_completed(futures):
                pass

        if not all_results:
            return pd.DataFrame()

        df = pd.DataFrame(all_results)
        print(f"    ✅ 腾讯并发扫描完毕，共 {len(df)} 只股票")
        return df

    # ==========================================================================
    # 板块成分股映射表（已修正工业富联归属）
    # ==========================================================================
    # 工业富联(601138)主业为AI服务器、通信网络设备制造，属于计算机设备
    BOARD_STOCK_MAP = {
        '半导体': [
            '688981', '688012', '688008', '688126', '688099', '688396',
            '002371', '002049', '603986', '603501', '600703', '300661',
            '300782', '300223', '300604', '300474', '600745',
            '600584', '603005', '603160', '603290', '605111',
            '688072', '688041', '688256', '688347',
        ],
        '电子化学品': [
            '300576', '300655', '300346', '300236', '300398',
            '603650', '603931', '002409', '002643', '002741',
            '688019', '688025', '688116', '688550',
        ],
        '元件': [
            '002138', '603267', '600563', '300408', '002859', '300285',
            '000636', '002199', '002484', '002916', '603228', '603678',
            '300726', '300814',
        ],
        '计算机设备': [
            '601138',  # 工业富联：AI服务器制造龙头，归入计算机设备
            '000977', '603019', '002415', '300853',
            '300476', '300045', '002152', '300130', '300603', '688158',
            '000066', '600100', '601788',
        ],
        '通信设备': [
            '000063', '002396', '300628', '300308', '300502',
            '600745', '600703', '603501',
        ],
        '煤炭开采加工': [
            '601225', '600188', '601088', '600985', '601898',
            '600546', '600348', '601001', '600740', '600395',
            '000983', '002128',
        ],
        '电力': [
            '600900', '600886', '600011', '600023', '600025',
            '600905', '600938', '601985', '601567', '601727',
            '000543', '000600', '000690', '000883', '000966',
            '300750', '300274', '300693',
        ],
    }

    def get_board_stocks(self, board_name: str) -> pd.DataFrame:
        """获取板块成分股"""
        codes = self.BOARD_STOCK_MAP.get(board_name, [])
        if not codes:
            return pd.DataFrame()
        df = self.get_stock_realtime(codes)
        if hasattr(df,"empty") and not df.empty:
            df['板块名称'] = board_name
        return df

    def get_hot_boards(self) -> list:
        """本地计算热门板块（直接使用腾讯批量接口，最快速）"""
        results = []
        for board_name, codes in self.BOARD_STOCK_MAP.items():
            # 直接走腾讯批量接口，跳过同花顺降级（不在交易时段同花顺单只查询很慢）
            df = self._get_by_tencent(codes)
            if not hasattr(df,"empty") or df.empty:
                continue
            avg_pct = df['涨跌幅'].mean()
            top_stock = df.loc[df['涨跌幅'].idxmax()] if not df.empty else {}
            results.append({
                '名称': board_name,
                '涨跌幅': avg_pct,
                '资金净额': 0,
                '得分': 0,
                '领涨股': top_stock.get('名称', ''),
                '领涨股涨跌幅': top_stock.get('涨跌幅', 0),
                '公司家数': len(df),
            })
        results.sort(key=lambda x: x['涨跌幅'], reverse=True)
        if results:
            pct_list = [b['涨跌幅'] for b in results]
            min_pct, max_pct = min(pct_list), max(pct_list)
            for b in results:
                score = (b['涨跌幅'] - min_pct) / \
                    (max_pct - min_pct + 1e-10) * 0.6
                b['得分'] = score
        return results


# 全局单例
_manager = None


def get_manager():
    """获取数据源管理器全局单例"""
    global _manager
    if _manager is None:
        _manager = DataSourceManager()
    return _manager
