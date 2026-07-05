# ==============================================================================
# update_kline_cache.py — 批量更新 K 线缓存（带日期校验，只升不降）
# 用法: python3 scripts/update_kline_cache.py
# ==============================================================================

import sys, os, time, concurrent.futures
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import pandas as pd
import requests, json

from config import CACHE_DIR



def _fetch_kline(code: str, start_date: str = "20260101") -> "pd.DataFrame":
    """多源回退获取历史日K线：新浪 → 数据工具 → 腾讯"""
    market = "sh" if code.startswith('6') else "sz"
    
    # 源1: 新浪财经K线API（已验证可用 2026-07-03）
    try:
        symbol = f"{market}{code}"
        url = (f"http://money.finance.sina.com.cn/quotes_service/api/json_v2.php/"
               f"CN_MarketData.getKLineData?symbol={symbol}&scale=240&ma=no&datalen=200")
        resp = requests.get(url, timeout=8)
        klines = resp.json()
        if klines and isinstance(klines, list) and len(klines) > 20:
            rows = []
            for k in klines:
                rows.append({"date": k["day"], "open": float(k["open"]),
                             "close": float(k["close"]), "high": float(k["high"]),
                             "low": float(k["low"]), "volume": float(k["volume"])})
            df = pd.DataFrame(rows)
            df['date'] = pd.to_datetime(df['date'])
            return df.sort_values('date')
    except Exception as e:
        print(f"  ⚠️ 新浪K线失败({code}): {str(e)[:50]}")
    
    # 源2: 数据工具获取日K线（akshare → 新浪备用）
    try:
        symbol = f"{market}{code}"
        url = (f"http://money.finance.sina.com.cn/quotes_service/api/json_v2.php/"
               f"CN_MarketData.getKLineData?symbol={symbol}&scale=240&ma=no&datalen=200")
        resp = requests.get(url, timeout=8)
        klines = resp.json()
        if klines and isinstance(klines, list) and len(klines) > 20:
            rows = []
            for k in klines:
                rows.append({"date": k["day"], "open": float(k["open"]),
                             "close": float(k["close"]), "high": float(k["high"]),
                             "low": float(k["low"]), "volume": float(k["volume"])})
            df = pd.DataFrame(rows)
            df['date'] = pd.to_datetime(df['date'])
            return df.sort_values('date')
    except Exception as e:
        print(f"  ⚠️ 新浪K线失败({code}): {str(e)[:50]}")
    
    # 源2续: 数据工具获取日K线
    try:
        from 工具库.数据工具 import 获取日K线数据
        df = 获取日K线数据(code, 起始日期=start_date, 使用缓存=False)
        if df is not None and len(df) >= 60:
            return df
    except Exception as e:
        print(f"  ⚠️ 数据工具失败({code}): {str(e)[:50]}")
    
    return pd.DataFrame()


def update_stock(code: str) -> tuple:
    """下载并更新单只股票的K线缓存（使用腾讯历史K线API）"""
    cache_path = os.path.join(CACHE_DIR, f"{code}_日K.csv")
    
    # 检查现有缓存日期
    existing_date = None
    if os.path.exists(cache_path):
        try:
            existing = pd.read_csv(cache_path, usecols=["date"], parse_dates=['date'])
            existing_date = existing['date'].max()
        except:
            pass
    
    # 从腾讯历史K线API下载
    try:
        df = _fetch_kline(code, start_date="20260101")
        if df is None or len(df) < 60:
            return ("FAIL", code, "数据不足", existing_date)
        
        new_date = df['date'].max()
        
        # 只升不降
        if existing_date is not None and new_date <= existing_date:
            return ("SKIP", code, f"缓存已最新({existing_date.date()})", existing_date)
        
        df.to_csv(cache_path, index=False)
        return ("OK", code, str(new_date.date()), existing_date)
    except Exception as e:
        return ("FAIL", code, str(e)[:40], existing_date)


print("=" * 55)
print("  更新 K 线缓存")
print("=" * 55)

# 获取候选股列表
print("\n[1/3] 实时扫描候选股...")
from 工具库.数据源管理器 import DataSourceManager
mgr = DataSourceManager()
stocks = mgr.get_all_market_stocks()
hot = stocks[stocks['涨跌幅'].between(2, 7)].copy()
hot = hot[~hot['名称'].str.contains('ST|退', na=False)]
codes = [str(c).zfill(6) for c in hot['代码']]
print(f"  候选股: {len(codes)} 只")

# 并行下载
print(f"\n[2/3] 并行下载 (10线程)...")
t0 = time.time()
ok = fail = skip = 0

with concurrent.futures.ThreadPoolExecutor(max_workers=10) as pool:
    futures = {pool.submit(update_stock, c): c for c in codes}
    done = 0
    for f in concurrent.futures.as_completed(futures):
        done += 1
        status, code, info, old = f.result()
        if status == "OK":
            ok += 1
        elif status == "FAIL":
            fail += 1
        else:
            skip += 1
        if done % 50 == 0:
            elapsed = round(time.time() - t0)
            print(f"  进度: {done}/{len(codes)} (OK={ok} FAIL={fail} SKIP={skip}) {elapsed}s")

t = round(time.time() - t0)

# 验证结果
print(f"\n[3/3] 完成! OK={ok} FAIL={fail} SKIP={skip} 耗时:{t}s")

# 检查新鲜度
dates = []
for f in os.listdir(CACHE_DIR):
    if not f.endswith('_日K.csv'):
        continue
    try:
        df = pd.read_csv(os.path.join(CACHE_DIR, f), usecols=["date"], parse_dates=['date'])
        if 'date' in df.columns:
            dates.append(df['date'].max())
    except:
        pass

jul = sum(1 for d in dates if d >= pd.Timestamp('2026-07-01'))
jun = sum(1 for d in dates if d >= pd.Timestamp('2026-06-08') and d < pd.Timestamp('2026-07-01'))
print(f"\n  缓存文件: {len(dates)} 个")
print(f"  最新日期: {max(dates).strftime('%Y-%m-%d')}")
print(f"  7月数据: {jul} 个")
print(f"  6月8日后: {jul+jun} 个")
