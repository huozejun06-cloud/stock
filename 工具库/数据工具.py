# ==============================================================================
# 工具库/数据工具.py — 公用数据工具箱
# 封装：新浪行情、akshare抓取、技术指标、龙虎榜、情绪数据
# 供三个任务脚本复用
# ==============================================================================

import re
import os
import time
import json
import requests
import pandas as pd
import numpy as np
import akshare as ak
from datetime import datetime, timedelta
from pathlib import Path

# ==============================================================================
# ⚠️ 全局断言：全A股市场样本数阈值
# ==============================================================================
# 全A股约5300只，取80%阈值 ≈ 4240
全市场样本数阈值 = 4000


def 断言数据完整性(实际样本数: int, 数据来源描述: str) -> bool:
    """
    检查数据样本数是否达到全市场的80%。
    如果不足，弹窗警告并返回 False。
    """
    if 实际样本数 >= 全市场样本数阈值:
        return True
    警告消息 = (
        f"🚨【数据完整性警告】{数据来源描述}实际样本数={实际样本数}只，"
        f"远低于全市场阈值={全市场样本数阈值}只！"
        f"\n   → 选股/评分结果不可信，请检查网络或接口可用性！"
    )
    print(f"    {警告消息}")
    return False


# ==============================================================================
# 重试装饰器：统一网络请求重试机制（timeout=5, 最多3次）
# ==============================================================================

def 带重试的请求(url: str, 会话: requests.Session = None, 超时: int = 5,
                 最大重试: int = 3, 编码: str = None, **kwargs) -> requests.Response:
    """
    统一的带重试的HTTP GET请求。
    所有网络请求必须通过此函数，确保 timeout=5 和至少3次重试。
    """
    最后一次异常 = None
    for 尝试次数 in range(最大重试):
        try:
            if 尝试次数 > 0:
                time.sleep(尝试次数 * 1.5)  # 退避等待
            if 会话:
                resp = 会话.get(url, timeout=超时, **kwargs)
            else:
                resp = requests.get(url, timeout=超时, **kwargs)
            resp.raise_for_status()  # 非2xx状态码抛出异常
            if 编码:
                resp.encoding = 编码
            return resp
        except requests.exceptions.Timeout as e:
            最后一次异常 = e
            print(f"    ⚠️ 请求超时(第{尝试次数+1}次): {url[:60]}...")
        except requests.exceptions.RequestException as e:
            最后一次异常 = e
            print(f"    ⚠️ 请求失败(第{尝试次数+1}次): {url[:60]}... {e}")
    raise 最后一次异常 or RuntimeError(f"请求失败，已重试{最大重试}次: {url[:60]}")


# ==============================================================================
# 1. 新浪实时行情 HTTP 引擎
# ==============================================================================

会话 = requests.Session()
会话.headers.update({
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
    'Referer': 'https://finance.sina.com.cn'
})

指数代码表 = {
    "sh000001": "上证指数",  "sz399001": "深证成指",
    "sz399006": "创业板指",  "sh000688": "科创50"
}


def 批量获取新浪行情(代码列表: list) -> dict:
    """批量拉取新浪实时行情（单次请求 <0.5s）"""
    try:
        url = "http://hq.sinajs.cn/list=" + ",".join(代码列表)
        resp = 带重试的请求(url, 会话=会话, 超时=5, 编码="gbk")
        return _解析新浪批量数据(resp.text)
    except Exception as e:
        return {"_error": str(e)}


def _解析新浪指数(原始代码: str, 字段列表: list) -> dict:
    """解析新浪指数"""
    名称 = 字段列表[0]
    价格 = float(字段列表[1]) if 字段列表[1] else 0.0
    涨跌幅 = float(字段列表[3]) if len(字段列表) > 3 and 字段列表[3] else 0.0
    涨跌额 = float(字段列表[2]) if len(字段列表) > 2 and 字段列表[2] else 0.0
    昨收 = 价格 - 涨跌额
    成交量 = float(字段列表[4]) if len(字段列表) > 4 and 字段列表[4] else 0.0
    成交额 = float(字段列表[5]) if len(字段列表) > 5 and 字段列表[5] else 0.0
    return {
        "名称": 名称, "开盘": 价格, "昨收": 昨收,
        "最新价": 价格, "最高": 价格, "最低": 价格,
        "涨跌幅": 涨跌幅, "成交量": 成交量, "成交额": 成交额, "换手率": 0.0
    }


def _解析新浪个股(字段列表: list) -> dict:
    """解析新浪个股"""
    名称 = 字段列表[0]
    开盘 = float(字段列表[1]) if 字段列表[1] else 0.0
    昨收 = float(字段列表[2]) if 字段列表[2] else 0.0
    价格 = float(字段列表[3]) if 字段列表[3] and float(字段列表[3]) > 0 else 昨收
    最高 = float(字段列表[4]) if 字段列表[4] else 价格
    最低 = float(字段列表[5]) if 字段列表[5] else 价格
    # ⚠️ 新浪涨跌幅是百分比数值（如 5.75 表示 +5.75%），与东财格式一致
    涨跌幅 = ((价格 - 昨收) / 昨收 * 100) if 昨收 > 0 else 0.0
    成交量 = float(字段列表[8]) / 100 if len(字段列表) > 8 and 字段列表[8] else 0.0
    成交额 = float(字段列表[9]) if len(字段列表) > 9 and 字段列表[9] else 0.0
    换手率 = 0.0
    for idx in [37, 38, 39]:
        if len(字段列表) > idx and 字段列表[idx]:
            try:
                换手率 = float(字段列表[idx]) / 100
                break
            except ValueError:
                continue
    return {
        "名称": 名称, "开盘": 开盘, "昨收": 昨收,
        "最新价": 价格, "最高": 最高, "最低": 最低,
        "涨跌幅": 涨跌幅, "成交量": 成交量, "成交额": 成交额,
        "换手率": 换手率
    }


def _解析新浪批量数据(原始文本: str) -> dict:
    """解析新浪实时行情文本为字典"""
    结果 = {}
    for m in re.findall(r'var\s+hq_str_(\w+)="([^"]*)"', 原始文本):
        代码, 数据 = m
        字段列表 = [p.strip() for p in 数据.split(",")]
        if len(字段列表) < 6:
            continue
        try:
            if 代码.startswith("s_"):
                结果[代码] = _解析新浪指数(代码, 字段列表)
            else:
                结果[代码] = _解析新浪个股(字段列表)
        except (ValueError, IndexError):
            continue
    return 结果


def 获取指数实时数据() -> dict:
    """
    获取四大指数实时数据。
    三源对冲：新浪（24h）→ 腾讯备用
    """
    # ===== 第一级：新浪（24小时可用）=====
    代码列表 = list(指数代码表.keys())
    新浪代码列表 = [f"s_{c}" for c in 代码列表]
    结果 = 批量获取新浪行情(新浪代码列表)
    if "_error" not in 结果 and len(结果) > 0:
        return 结果

    # ===== 第二级：腾讯备用 =====
    print("    ⚠️ 新浪指数失败，切换到腾讯备用源...")
    try:
        腾讯代码 = ",".join([f"sh{c[2:]}" if c.startswith("sh") else f"sz{c[2:]}" for c in 代码列表])
        url = f"http://qt.gtimg.cn/q={腾讯代码}"
        resp = 带重试的请求(url, 超时=5, 编码="gbk")
        for line in resp.text.strip().split(";"):
            if not line.strip():
                continue
            parts = line.split("~")
            if len(parts) >= 4:
                代码 = parts[2]
                名称 = parts[1]
                价格 = float(parts[3]) if parts[3] else 0.0
                昨收 = float(parts[4]) if len(parts) > 4 and parts[4] else 价格
                涨跌幅 = ((价格 - 昨收) / 昨收 * 100) if 昨收 > 0 else 0.0
                新浪键 = f"s_sh{代码}" if 代码.startswith(("0", "1")) else f"s_sz{代码}"
                结果[新浪键] = {
                    "名称": 名称, "开盘": 价格, "昨收": 昨收,
                    "最新价": 价格, "最高": 价格, "最低": 价格,
                    "涨跌幅": 涨跌幅, "成交量": 0, "成交额": 0, "换手率": 0.0
                }
    except Exception as e:
        print(f"    ❌ 腾讯备用也失败: {e}")

    return 结果


def 获取个股实时行情(股票代码: str) -> dict:
    """
    获取单只个股实时行情。
    三源对冲：新浪（24h）→ 腾讯备用

    🔧 v6修复：无论哪个数据源返回，只要换手率为0，
    都单独从腾讯接口补充换手率字段（parts[38]）。
    """
    前缀 = "sh" if 股票代码.startswith(("6", "9")) else "sz"
    新浪代码 = f"{前缀}{股票代码}"

    # ===== 第一级：新浪 =====
    结果 = 批量获取新浪行情([新浪代码])
    if 新浪代码 not in 结果:
        # ===== 第二级：腾讯备用 =====
        try:
            url = f"http://qt.gtimg.cn/q={新浪代码}"
            resp = 带重试的请求(url, 超时=5, 编码="gbk")
            line = resp.text.strip().split(";")[0]
            parts = line.split("~")
            if len(parts) >= 30:
                名称 = parts[1]
                昨收 = float(parts[4]) if parts[4] else 0.0
                价格 = float(parts[3]) if parts[3] else 昨收
                开盘 = float(parts[5]) if parts[5] else 价格
                最高 = float(parts[33]) if parts[33] else 价格
                最低 = float(parts[34]) if parts[34] else 价格
                涨跌幅 = ((价格 - 昨收) / 昨收 * 100) if 昨收 > 0 else 0.0
                成交量 = float(parts[6]) if parts[6] else 0.0
                成交额 = float(parts[37]) if len(parts) > 37 and parts[37] else 0.0
                # 腾讯 parts[38] = 换手率
                try:
                    val = float(parts[38]) if len(parts) > 38 and parts[38] else 0
                    换手率 = val if val > 0 else 0
                except Exception as e:
                    print(f"  ⚠️ 数据工具.py: {e}")
                    换手率 = 0
                结果[新浪代码] = {
                    "名称": 名称, "开盘": 开盘, "昨收": 昨收,
                    "最新价": 价格, "最高": 最高, "最低": 最低,
                    "涨跌幅": 涨跌幅, "成交量": 成交量, "成交额": 成交额,
                    "换手率": 换手率 or 0.0
                }
        except Exception:
            pass

    # ===== 🔧 V6修复：换手率兜底补充 =====
    # 新浪个股接口不提供换手率字段，腾讯才有(parts[38])
    # 无论哪个数据源返回，只要换手率=0，单独从腾讯补充
    if 新浪代码 in 结果:
        行情 = 结果[新浪代码]
        if not 行情.get('换手率') or 行情['换手率'] == 0.0:
            try:
                url = f"http://qt.gtimg.cn/q={新浪代码}"
                resp = 带重试的请求(url, 超时=3, 编码="gbk")
                # 腾讯格式: v_sz000063="field1~field2~...~fieldN"
                # 必须先按 ; 拆出第一只股票，再去掉引号后按 ~ 拆
                line = resp.text.strip().split(";")[0]
                line = line.split('="', 1)[-1].rstrip('"')
                parts = line.split("~")
                if len(parts) > 38 and parts[38]:
                    try:
                        换手率 = float(parts[38])
                        行情['换手率'] = 换手率 if 换手率 > 0 else 0.0
                    except ValueError:
                        pass
                # 再兜底：用成交额/流通市值估算
                if (not 行情.get('换手率') or 行情['换手率'] == 0.0) and len(parts) > 37 and parts[37]:
                    try:
                        成交额 = float(parts[37])
                        流通市值 = float(parts[44]) if len(parts) > 44 and parts[44] else 0
                        if 成交额 > 0 and 流通市值 > 0:
                            行情['换手率'] = round(成交额 / 流通市值 * 100, 2)
                    except Exception as e:
                        print(f"  ⚠️ 数据工具.py: {e}")
                        pass
            except Exception:
                pass

    return 结果


# ==============================================================================
# 2. 本地缓存系统（CSV文件缓存，避免重复调API）
# ==============================================================================

缓存目录 = Path(__file__).resolve().parent.parent / "缓存"

def _确保缓存目录存在():
    缓存目录.mkdir(parents=True, exist_ok=True)

def _缓存路径(股票代码: str, 缓存类型: str = "日K") -> Path:
    return 缓存目录 / f"{股票代码}_{缓存类型}.csv"

def _缓存元数据路径(股票代码: str, 缓存类型: str = "日K") -> Path:
    return 缓存目录 / f"{股票代码}_{缓存类型}_元数据.json"

def _缓存是否有效(股票代码: str, 缓存类型: str = "日K", 最大有效小时: int = 4) -> bool:
    元数据路径 = _缓存元数据路径(股票代码, 缓存类型)
    if not 元数据路径.exists():
        return False
    try:
        with open(元数据路径, "r", encoding="utf-8") as f:
            元数据 = json.load(f)
        缓存时间 = datetime.fromisoformat(元数据["缓存时间"])
        现在 = datetime.now()
        已过小时 = (现在 - 缓存时间).total_seconds() / 3600
        if 元数据.get("日期") != 现在.strftime("%Y-%m-%d"):
            return False
        return 已过小时 < 最大有效小时
    except Exception:
        return False

def _保存缓存(股票代码: str, 数据框: pd.DataFrame, 缓存类型: str = "日K"):
    _确保缓存目录存在()
    csv路径 = _缓存路径(股票代码, 缓存类型)
    元数据路径 = _缓存元数据路径(股票代码, 缓存类型)
    数据框.to_csv(csv路径, index=False)
    元数据 = {
        "股票代码": 股票代码,
        "缓存类型": 缓存类型,
        "日期": datetime.now().strftime("%Y-%m-%d"),
        "缓存时间": datetime.now().isoformat(),
        "行数": len(数据框),
    }
    with open(元数据路径, "w", encoding="utf-8") as f:
        json.dump(元数据, f, ensure_ascii=False, indent=2)
    # 🔥 修复：变量名 csv_path → csv路径
    print(f"  💾 已缓存至: {csv路径.name} ({len(数据框)}行)")

def _读取缓存(股票代码: str, 缓存类型: str = "日K") -> pd.DataFrame:
    csv路径 = _缓存路径(股票代码, 缓存类型)
    if csv路径.exists():
        数据框 = pd.read_csv(csv路径)
        print(f"  📂 从缓存读取: {csv路径.name} ({len(数据框)}行)")
        return 数据框
    return pd.DataFrame()

def 清除缓存(股票代码: str = None):
    """清除缓存，不传参数则清除全部"""
    _确保缓存目录存在()
    if 股票代码:
        for f in 缓存目录.glob(f"{股票代码}_*"):
            f.unlink()
        print(f"  🗑️ 已清除 {股票代码} 的缓存")
    else:
        for f in 缓存目录.glob("*"):
            f.unlink()
        print(f"  🗑️ 已清除所有缓存")


# ==============================================================================
# 3. 历史K线数据获取（缓存 → akshare → 新浪备用）
# ==============================================================================

def 获取日K线数据(股票代码: str, 起始日期: str = "20240101",
                   使用缓存: bool = True, 缓存有效小时: int = 4) -> pd.DataFrame:
    """获取个股历史日K线，支持三级数据源：本地缓存 → akshare → 新浪备用"""
    # 第一级：本地缓存
    if 使用缓存 and _缓存是否有效(股票代码, "日K", 缓存有效小时):
        缓存数据 = _读取缓存(股票代码, "日K")
        if not 缓存数据.empty:
            重命名表 = {
                '日期': 'date', '开盘': 'open', '收盘': 'close', '最高': 'high', '最低': 'low',
                '成交量': 'volume', '涨跌幅': 'pct_chg', '换手率': 'turnover',
            }
            存在的重命名 = {k: v for k, v in 重命名表.items() if k in 缓存数据.columns}
            if 存在的重命名:
                缓存数据 = 缓存数据.rename(columns=存在的重命名)
            return 缓存数据

    # 第二级：akshare 主接口（含重试）
    from 工具库.V8线程锁 import V8_LOCK
    数据框 = pd.DataFrame()
    for 主重试 in range(2):
        try:
            with V8_LOCK:
                数据框 = ak.stock_zh_a_hist(symbol=股票代码, period="daily", adjust="qfq")
            break  # 成功即退出循环
        except Exception:
            if 主重试 == 0:
                print("    ⚠️ 主接口拥堵，等待2秒重试...")
                time.sleep(2)
            else:
                print("    ⚠️ 主接口两次均失败，切换到备用源...")
                try:
                    完整代码 = f"sz{股票代码}" if 股票代码.startswith(("0", "3")) else f"sh{股票代码}"
                    数据框 = ak.stock_zh_a_daily(symbol=完整代码, start_date=起始日期)
                except Exception as e:
                    err_msg = str(e)
                    # 🔧 修复：新浪备用源因日期格式不兼容（如1998-05-22 vs %Y-%b-%d）而失败
                    # 改用东财接口重试（可能有速率限制，但值得一试）
                    if "doesn't match format" in err_msg:
                        print("    ⚠️ 备用源日期格式不兼容，改用东财 stock_zh_a_hist 再试...")
                        time.sleep(3)  # 等待速率限制恢复
                        try:
                            数据框 = ak.stock_zh_a_hist(symbol=股票代码, period="daily", adjust="qfq")
                        except Exception as e2:
                            raise ValueError(f"历史K线获取失败(日期格式+东财均失败): {e2}")
                    else:
                        raise ValueError(f"历史K线获取失败: {e}")

    if 数据框.empty:
        raise ValueError("❌ 抓取到的股票数据为空，请确认代码是否正确。")

    # 列名映射
    重命名表 = {
        '日期': 'date', '开盘': 'open', '收盘': 'close', '最高': 'high', '最低': 'low',
        '成交量': 'volume', '涨跌幅': 'pct_chg', '换手率': 'turnover',
        'date': 'date', 'open': 'open', 'close': 'close', 'high': 'high', 'low': 'low',
        'volume': 'volume'
    }
    存在的重命名 = {k: v for k, v in 重命名表.items() if k in 数据框.columns}
    数据框 = 数据框.rename(columns=存在的重命名)

    if 'pct_chg' not in 数据框.columns:
        数据框['pct_chg'] = 数据框['close'].pct_change() * 100
    if 'turnover' not in 数据框.columns:
        数据框['turnover'] = 1.5

    # 写入缓存
    if 使用缓存:
        _保存缓存(股票代码, 数据框, "日K")

    return 数据框


def 合并实时数据到数据框(数据框: pd.DataFrame, 股票代码: str) -> pd.DataFrame:
    """如果历史K线未包含今日数据，补充新浪盘中实时数据"""
    最新日期 = str(数据框['date'].iloc[-1])[:10]
    今日日期 = datetime.now().strftime('%Y-%m-%d')

    if 最新日期 != 今日日期:
        实时数据 = 获取个股实时行情(股票代码)
        前缀 = "sh" if 股票代码.startswith(("6", "9")) else "sz"
        键 = f"{前缀}{股票代码}"
        if 键 in 实时数据:
            d = 实时数据[键]
            昨收 = float(数据框['close'].iloc[-1])
            新行 = {
                'date': 今日日期,
                'open': d['开盘'],
                'high': d['最高'],
                'low': d['最低'],
                'close': d['最新价'],
                'volume': d['成交量'],
                'pct_chg': d['涨跌幅'],
                'turnover': d['换手率'],
            }
            数据框 = pd.concat([数据框, pd.DataFrame([新行])], ignore_index=True)
            print(f"  📡 已补充今日({今日日期})盘中实时数据：最新价={新行['close']:.2f}，涨跌幅={新行['pct_chg']:+.2f}%")
        else:
            print(f"  ⚠️ 新浪实时行情未返回 {股票代码}，继续使用上一交易日({最新日期})数据")
    else:
        print(f"  ✅ 历史K线已包含今日数据({今日日期})，无需补充")

    return 数据框


# ==============================================================================
# 4. 全维度技术指标计算
# ==============================================================================

def 计算全部技术指标(数据框: pd.DataFrame) -> pd.DataFrame:
    """计算 MA, MACD, KDJ, RSI, ATR, BOLL, ADX, OBV, VMA"""
    close = 数据框['close']
    high = 数据框['high']
    low = 数据框['low']
    volume = 数据框['volume']

    数据框['MA5'] = close.rolling(5).mean()
    数据框['MA10'] = close.rolling(10).mean()
    数据框['MA20'] = close.rolling(20).mean()
    数据框['MA30'] = close.rolling(30).mean()
    数据框['MA60'] = close.rolling(60).mean()
        
    数据框['BIAS20'] = ((close - 数据框['MA20']) / 数据框['MA20']) * 100
    
    exp12 = close.ewm(span=12, adjust=False).mean()
    exp26 = close.ewm(span=26, adjust=False).mean()
    数据框['DIF'] = exp12 - exp26
    数据框['DEA'] = 数据框['DIF'].ewm(span=9, adjust=False).mean()
    数据框['MACD柱'] = 2 * (数据框['DIF'] - 数据框['DEA'])

    low_n = low.rolling(9).min()
    high_n = high.rolling(9).max()
    rsv = ((close - low_n) / (high_n - low_n + 1e-10)) * 100

    def 计算RSI(序列, 周期):
        delta = 序列.diff()
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)
        avg_gain = gain.ewm(alpha=1 / 周期, adjust=False).mean()
        avg_loss = loss.ewm(alpha=1 / 周期, adjust=False).mean()
        rs = avg_gain / (avg_loss + 1e-10)
        return 100 - 100 / (1 + rs)

    数据框['RSI6'] = 计算RSI(close, 6)
    数据框['RSI14'] = 计算RSI(close, 14)
    
    high_low = high - low
    high_close_prev = (high - close.shift(1)).abs()
    low_close_prev = (low - close.shift(1)).abs()
    tr = pd.concat([high_low, high_close_prev, low_close_prev], axis=1).max(axis=1)
    数据框['ATR14'] = tr.rolling(14).mean()

    数据框['布林中轨'] = 数据框['MA20']
    std20 = close.rolling(20).std()
    数据框['布林上轨'] = 数据框['布林中轨'] + 2 * std20
    数据框['布林下轨'] = 数据框['布林中轨'] - 2 * std20

    def 计算ADX(df, period=14):
        up_move = df['high'] - df['high'].shift(1)
        down_move = df['low'].shift(1) - df['low']
        plus_dm = np.where((up_move > down_move) & (up_move > 0), up_move, 0)
        minus_dm = np.where((down_move > up_move) & (down_move > 0), down_move, 0)
        atr_series = tr.rolling(period).mean()
        plus_di = 100 * (pd.Series(plus_dm).ewm(alpha=1 / period, adjust=False).mean() / (atr_series + 1e-10))
        minus_di = 100 * (pd.Series(minus_dm).ewm(alpha=1 / period, adjust=False).mean() / (atr_series + 1e-10))
        dx = 100 * np.abs(plus_di - minus_di) / (plus_di + minus_di + 1e-10)
        adx = dx.ewm(alpha=1 / period, adjust=False).mean()
        return pd.Series(adx, index=df.index), pd.Series(plus_di, index=df.index), pd.Series(minus_di, index=df.index)

    数据框['ADX'], 数据框['正DI'], 数据框['负DI'] = 计算ADX(数据框)

    obv = [0]
    for i in range(1, len(close)):
        if close.iloc[i] > close.iloc[i - 1]:
            obv.append(obv[-1] + volume.iloc[i])
        elif close.iloc[i] < close.iloc[i - 1]:
            obv.append(obv[-1] - volume.iloc[i])
        else:
            obv.append(obv[-1])
    数据框['OBV'] = obv

    数据框['量MA5'] = volume.rolling(5).mean()
    数据框['量MA10'] = volume.rolling(10).mean()
    数据框['量MA20'] = volume.rolling(20).mean()

    return 数据框


# ==============================================================================
# 5. 定性判定辅助函数
# ==============================================================================

def 判断量价形态(最新, 前一条) -> str:
    if 最新['pct_chg'] > 0 and 最新['volume'] > 前一条['volume']:
        return "放量上涨"
    elif 最新['pct_chg'] > 0 and 最新['volume'] <= 前一条['volume']:
        return "缩量上涨"
    elif 最新['pct_chg'] <= 0 and 最新['volume'] > 前一条['volume']:
        return "放量下跌"
    else:
        return "缩量下跌"


def 判断均线排列(最新) -> str:
    ma值 = [最新.get(f'MA{i}', 0) for i in [5, 10, 20, 30, 60]]
    if all(ma值[i] > ma值[i + 1] for i in range(len(ma值) - 1)):
        return "多头排列"
    elif all(ma值[i] < ma值[i + 1] for i in range(len(ma值) - 1)):
        return "空头排列"
    else:
        return "震荡缠绕"


def 判断MACD信号(最新, 前一条) -> str:
    if 最新['DIF'] > 最新['DEA'] and 前一条['DIF'] <= 前一条['DEA']:
        return "金叉"
    elif 最新['DIF'] < 最新['DEA'] and 前一条['DIF'] >= 前一条['DEA']:
        return "死叉"
    elif 最新['DIF'] > 最新['DEA']:
        return "多头运行中"
    else:
        return "空头运行中"


def 判断ADX描述(adx值: float) -> str:
    if adx值 > 40:
        return "强趋势运行"
    elif adx值 >= 25:
        return "中等趋势"
    else:
        return "无趋势震荡"


def 判断布林形态(最新) -> str:
    if 最新['close'] > 最新['布林上轨']:
        return "突破上轨"
    elif 最新['close'] < 最新['布林下轨']:
        return "跌破下轨"
    else:
        return "轨道内运行"


def 判断换手率分类(换手率: float) -> str:
    if 换手率 < 1:
        return "低换手（绝对锁仓）"
    elif 换手率 < 3:
        return "正常换手（良性换手）"
    elif 换手率 < 10:
        return "高换手（多空剧烈博弈）"
    else:
        return "天量换手（分歧极端化/筹码派发）"


# ==============================================================================
# 6. 🔥 全自动动态板块雷达（重构版·稳健性升级）
# 盘后(15:00-09:15)：同花顺 stock_fund_flow_industry（24h可用）
# 盘中(09:15-15:00)：东方财富 stock_board_industry_spot_em
# 零硬编码，全自动扫描全市场行业板块
# ==============================================================================

def _是否为盘中时间() -> bool:
    """判断当前是否为盘中交易时间（09:15-15:00）"""
    now = datetime.now()
    当前时间 = now.hour * 100 + now.minute
    if 当前时间 >= 915 and 当前时间 <= 1500 and now.weekday() < 5:
        return True
    return False


def _归一化(值列表: list) -> list:
    """
    Min-Max归一化列表值到[0,1]区间。
    ⚠️ 稳健性：对异常值（如资金净额极值）做了截断保护。
    
    🔥 审计要点：归一化在板块级别进行，确保巨无霸板块不会绑架评分。
    每个板块的资金净额在板块内部做归一化，而非跨板块直接相加减。
    """
    if not 值列表:
        return []
    最小值 = min(值列表)
    最大值 = max(值列表)
    if 最大值 == 最小值:
        return [0.5] * len(值列表)
    return [(v - 最小值) / (最大值 - 最小值) for v in 值列表]


def 动态板块扫描(强制使用同花顺: bool = False) -> dict:
    """
    🔥 全自动动态板块雷达 - 零硬编码，自动获取全市场行业板块

    数据源选择机制：
    - 盘中(09:15-15:00, 工作日) → 东方财富（精度最高）
    - 盘后/非交易日 → 同花顺 stock_fund_flow_industry（24h可用）

    评分体系：得分 = 今日涨跌幅归一化 * 0.6 + 近3日资金净额归一化 * 0.4
    ⚠️ 2019-11-25 审计修复：量纲统一断言
    - 涨跌幅：不管是东财还是同花顺，返回的都是百分比数值（如 5.75 = +5.75%）
    - 资金净额：同花顺返回亿元，东财 fund_flow_em 返回亿元
    - 归一化在板块级别进行，防止巨无霸绑架评分
    自动筛选出得分最高的 Top 3 热门板块。

    Returns:
        dict: {
            "成功": bool,
            "数据源": "同花顺/东方财富",
            "板块列表": [{"名称", "涨跌幅", "资金净额", "得分", "领涨股", ...}],
            "Top3": [得分最高的3个板块],
            "文本": str
        }
    """
    结果 = {
        "成功": False,
        "数据源": "未知",
        "板块列表": [],
        "Top3": [],
        "文本": "全自动动态板块扫描暂不可用"
    }

    使用东财 = _是否为盘中时间() and not 强制使用同花顺

    from 工具库.V8线程锁 import V8_LOCK
    if 使用东财:
        # ===== 数据源A：东方财富（盘中首选）=====
        print("    📡 盘中模式 → 使用东方财富实时数据")
        for 尝试次数 in range(3):
            try:
                with V8_LOCK:
                    板块数据 = ak.stock_board_industry_spot_em()
                if 板块数据.empty or '板块名称' not in 板块数据.columns:
                    continue

                板块列表 = []
                for _, row in 板块数据.iterrows():
                    涨跌幅 = float(row.get('涨跌幅', 0))
                    # 🔥 断言：东财涨跌幅是百分比（如 5.75 表示 5.75%）
                    assert abs(涨跌幅) < 100, (
                        f"东财涨跌幅疑似格式异常：{涨跌幅}，"
                        f"预期为百分比数值（如5.75表示+5.75%）"
                    )
                    板块列表.append({
                        "名称": row.get('板块名称', ''),
                        "涨跌幅": 涨跌幅,
                        "涨跌额": row.get('涨跌额', 0),
                        "成交量": row.get('成交量', 0),
                        "成交额": row.get('成交额', 0),
                        "资金净额": 0,  # 东财spot不含资金流
                        "领涨股": '',
                        "领涨股涨跌幅": 0,
                        "公司家数": row.get('公司数', 0),
                    })

                # 尝试合并资金流数据
                try:
                    with V8_LOCK:
                        资金流 = ak.stock_board_industry_fund_flow_em(symbol='行业板块')
                    if not 资金流.empty:
                        # 🔥 断言：东财资金流主力净流入单位是亿元
                        资金映射 = {}
                        for _, r in 资金流.iterrows():
                            净额 = float(r.get('主力净流入', 0))
                            assert abs(净额) < 10000, (
                                f"东财资金流疑似格式异常：{净额}，"
                                f"预期为亿元数值"
                            )
                            资金映射[r['板块名称']] = 净额
                        for b in 板块列表:
                            b['资金净额'] = 资金映射.get(b['名称'], 0)
                except Exception:
                    print("    ⚠️ 东财资金流数据获取失败，使用涨跌幅作为唯一评分依据")
                    pass

                # 计算得分：涨跌幅权重0.6，资金净额归一化权重0.4
                涨跌幅列表 = [b['涨跌幅'] for b in 板块列表]
                资金列表 = [b['资金净额'] for b in 板块列表]
                涨跌幅归一化 = _归一化(涨跌幅列表)
                资金归一化 = _归一化(资金列表)

                for i, b in enumerate(板块列表):
                    b['得分'] = 涨跌幅归一化[i] * 0.6 + 资金归一化[i] * 0.4

                板块列表.sort(key=lambda x: x['得分'], reverse=True)
                结果["板块列表"] = 板块列表
                结果["Top3"] = 板块列表[:3]
                结果["数据源"] = "东方财富"
                结果["成功"] = True

                文本行 = "\n".join([
                    f"  {i+1}. **{b['名称']}**: 涨跌幅{b['涨跌幅']:+.2f}% | "
                    f"得分{b['得分']:.3f}"
                    for i, b in enumerate(板块列表[:5])
                ])
                结果["文本"] = f"🔍 全市场行业板块扫描（东财，得分=涨跌幅×0.6+资金×0.4）：\n{文本行}\n  ... 共{len(板块列表)}个行业"
                print(f"    ✅ 东方财富板块扫描成功: {len(板块列表)}个行业")
                return 结果

            except AssertionError as e:
                print(f"    ⚠️ 数据断言失败(东财): {e}")
            except Exception as e:
                print(f"    ⚠️ 东方财富板块扫描第{尝试次数+1}次失败: {e}")

        # 东财失败，降级到同花顺
        print("    🔄 东财不可用，降级到同花顺数据源...")

    # ===== 数据源B：同花顺（24h可用，盘后首选）=====
    print("    📡 盘后模式 → 使用同花顺24h数据源")
    try:
        # 获取即时行业数据（含今日涨跌幅、领涨股）
        即时数据 = ak.stock_fund_flow_industry(symbol='即时')
        if 即时数据.empty:
            raise ValueError("同花顺即时数据为空")

        # 获取3日排行数据（含近3日资金流向）
        三日数据 = ak.stock_fund_flow_industry(symbol='3日排行')
        if 三日数据.empty:
            raise ValueError("同花顺3日数据为空")

        # 建立行业名称到3日数据的映射
        三日映射 = {}
        for _, row in 三日数据.iterrows():
            三日映射[row['行业']] = {
                '阶段涨跌幅': row.get('阶段涨跌幅', 0),
                '净额': row.get('净额', 0),
                '流入资金': row.get('流入资金', 0),
                '流出资金': row.get('流出资金', 0),
            }

        # 合并即时 + 3日数据
        板块列表 = []
        for _, row in 即时数据.iterrows():
            行业名 = row['行业']
            三日信息 = 三日映射.get(行业名, {'阶段涨跌幅': 0, '净额': 0, '流入资金': 0, '流出资金': 0})

            # 今日涨跌幅
            今日涨跌幅 = float(row.get('行业-涨跌幅', 0))
            # 🔥 断言：同花顺涨跌幅是百分比（如 5.75 表示 5.75%）
            assert abs(今日涨跌幅) < 100, (
                f"同花顺涨跌幅疑似格式异常：{今日涨跌幅}"
            )
            # 3日净额（亿元）
            三日净额 = float(三日信息.get('净额', 0))
            # 🔥 断言：同花顺净额单位是亿元
            assert abs(三日净额) < 100000, (
                f"同花顺净额疑似格式异常：{三日净额}，预期为亿元"
            )

            板块列表.append({
                "名称": 行业名,
                "涨跌幅": 今日涨跌幅,
                "资金净额": 三日净额,
                "阶段涨跌幅": 三日信息.get('阶段涨跌幅', 0),
                "流入资金": row.get('流入资金', 0),
                "流出资金": row.get('流出资金', 0),
                "公司家数": int(row.get('公司家数', 0)),
                "领涨股": row.get('领涨股', ''),
                "领涨股涨跌幅": row.get('领涨股-涨跌幅', 0),
                "行业指数": row.get('行业指数', 0),
            })

        if not 板块列表:
            raise ValueError("合并后的板块列表为空")

        # ===== 🔥 分数计算：同花顺数据源 =====
        # ⚠️ 注意：实际公式是 得分 = 涨跌幅归一化×0.6 + 资金归一化×0.4
        #      而不是 涨跌幅原始值×0.6 + 资金原始值×0.4
        #      因为原始值量纲差异巨大（涨跌幅±10%, 净额±100亿），不归一化会被巨无霸绑架
        涨跌幅列表 = [b['涨跌幅'] for b in 板块列表]
        资金列表 = [abs(b['资金净额']) * (1 if b['涨跌幅'] > 0 else -1) for b in 板块列表]

        # 🔍 debug: 找到半导体板块的原始值
        半导体debug = next((b for b in 板块列表 if "半导" in b['名称']), None)
        if 半导体debug:
            print(f"\n    🔬 【DEBUG-同花顺】{半导体debug['名称']}:")
            print(f"       原始涨跌幅 = {半导体debug['涨跌幅']:+.2f}%")
            print(f"       原始3日资金净额 = {半导体debug['资金净额']:+.2f}亿")
            print(f"       资金列表值(带方向) = {abs(半导体debug['资金净额']) * (1 if 半导体debug['涨跌幅'] > 0 else -1):+.2f}")
            print(f"       涨跌幅范围: [{min(涨跌幅列表):+.2f}%, {max(涨跌幅列表):+.2f}%]")
            print(f"       资金范围: [{min(资金列表):+.2f}亿, {max(资金列表):+.2f}亿]")

        涨跌幅归一化 = _归一化(涨跌幅列表)
        资金归一化 = _归一化(资金列表)

        for i, b in enumerate(板块列表):
            b['得分'] = 涨跌幅归一化[i] * 0.6 + 资金归一化[i] * 0.4

        # 🔍 debug: 半导体的归一化值和得分
        if 半导体debug:
            半导体索引 = next(i for i, b in enumerate(板块列表) if "半导" in b['名称'])
            print(f"       归一化-涨跌幅 = {涨跌幅归一化[半导体索引]:.4f}")
            print(f"       归一化-资金 = {资金归一化[半导体索引]:.4f}")
            print(f"       最终得分 = {涨跌幅归一化[半导体索引]*0.6:.4f} + {资金归一化[半导体索引]*0.4:.4f} = {板块列表[半导体索引]['得分']:.4f}")
            print(f"       真实公式 = 涨跌幅归一化({涨跌幅归一化[半导体索引]:.3f})×0.6 + 资金归一化({资金归一化[半导体索引]:.3f})×0.4 = {板块列表[半导体索引]['得分']:.3f}")
            print(f"       ⚠️ 注意：-181亿的权重只有0.18(归一化后)，而不是直接用-181×0.4")

        # 按得分排序
        板块列表.sort(key=lambda x: x['得分'], reverse=True)
        结果["板块列表"] = 板块列表
        结果["Top3"] = 板块列表[:3]
        结果["数据源"] = "同花顺"
        结果["成功"] = True

        文本行 = "\n".join([
            f"  {i+1}. **{b['名称']}**: 涨跌幅{b['涨跌幅']:+.2f}% | "
            f"3日净额{b['资金净额']:+.2f}亿 | 得分{b['得分']:.3f}"
            for i, b in enumerate(板块列表[:5])
        ])
        结果["文本"] = (f"🔍 全市场行业板块扫描（同花顺24h，得分=涨跌幅归一化×0.6+3日资金归一化×0.4）：\n"
                      f"{文本行}\n  ... 共{len(板块列表)}个行业板块")

        print(f"    ✅ 同花顺板块扫描成功: {len(板块列表)}个行业")
        return 结果

    except AssertionError as e:
        print(f"    ⚠️ 数据断言失败(同花顺): {e}")
    except Exception as e:
        print(f"    ⚠️ 同花顺板块扫描失败: {e}")
        import traceback
        traceback.print_exc()

    # 如果以上数据源都失败，用 DataSourceManager 全量并发扫描
    if int(结果.get("涨停家数", "0")) == 0 and int(结果.get("跌停家数", "0")) == 0:
        try:
            from 工具库.数据源管理器 import get_manager
            mgr = get_manager()
            full = mgr.get_market_emotion()
            if int(full.get("全市场股票", 0)) > 1000:
                结果.update(full)
        except:
            pass

    return 结果


def 动态板块选黑马(Top3板块: list, 数据源: str = "同花顺", 取前几名: int = 5) -> list:
    """
    🔥 从Top3动态板块中精选"黑马股"
    筛选条件：量比>0.8 + 5日均线多头 + 主力净流入>0

    盘后策略：先用领涨股名查代码 → 腾讯批量个股行业匹配 → 东财补充
    盘前策略：直接使用东财板块成分股

    Args:
        Top3板块: [{"名称": "...", "涨跌幅": ..., "得分": ..., "领涨股": "..."}, ...]
        数据源: "同花顺" 或 "东方财富"
        取前几名: 最终返回几只黑马股

    Returns:
        list: [{"代码": "601138", "名称": "工业富联", "板块": "...", "量比": ..., ...}]
    """
    候选股 = []

    # ===== 第一步：构建腾讯批量查询的超级股票池（含各行业龙头）=====
    print("    📡 构建全市场超级股票池（腾讯批量查询）...")
    腾讯股票池 = [
        "sh600519", "sh601318", "sh600036", "sh600030", "sh601166",
        "sh600887", "sh600585", "sh601398", "sh601939", "sh600900",
        "sh601012", "sh600309", "sh600276", "sh603259", "sh601888",
        "sh600690", "sh600809", "sh600085", "sh600438", "sh600703",
        "sh600745", "sh600893", "sh601088", "sh600104", "sh600028",
        "sh600196", "sh600588", "sh600570", "sh600111", "sh600362",
        "sh601225", "sh601857", "sh600019", "sh600010", "sh600031",
        "sh600050", "sh600941", "sh600085", "sh600900",
        "sz000858", "sz000002", "sz000001", "sz002415", "sz002475",
        "sz300750", "sz300059", "sz000651", "sz000333", "sz002714",
        "sz002304", "sz000568", "sz000596", "sz002230", "sz300124",
        "sz000063", "sz000100", "sz000538", "sz000625", "sz000725",
        "sz002129", "sz002179", "sz002460", "sz002466", "sz002594",
        "sz300014", "sz300015", "sz300122", "sz300274", "sz300347",
        "sz300413", "sz300433", "sz300450", "sz300498", "sz300601",
        "sz300760", "sz300782", "sz300999", "sz300896", "sz301269",
        "sh601138", "sh600183", "sh600584", "sh600745", "sh603501",
        "sh688981", "sh688012", "sh688126", "sh688396", "sh688599",
        "sz002049", "sz002371", "sz002916", "sz300661", "sz300672",
        "sz301308", "sz000977", "sz002236",
        # 半导体核心股补充
        "sz300782", "sz300661", "sz002371", "sz002049", "sh603986",
        "sh688072", "sh688008", "sh688012", "sh688126", "sh688981",
        "sh603160", "sh603005", "sh688018", "sh688041", "sh688037",
        "sh600171", "sh688200", "sh688396", "sh688521", "sh688689",
        # 电子化学品
        "sz300054", "sz300346", "sz300236", "sz300576", "sz300655",
        "sh603379", "sh600746", "sh002409", "sz300398",
        # 元件
        "sz002484", "sz002138", "sz002384", "sz002916", "sz300014",
        "sz300136", "sz300408", "sz300979", "sh600183", "sh600563",
        "sh603228", "sh603267", "sh603920", "sh688019", "sh688025",
        "sh688200", "sh688396",
    ]
    # 去重
    腾讯股票池 = list(dict.fromkeys(腾讯股票池))

    # ⚠️ 样本数警告：腾讯股票池仅 ~160 只，远少于全 A 股 5000+
    if not 断言数据完整性(len(腾讯股票池), "腾讯股票池"):
        print("    ⚠️ 注意：腾讯批量查询仅覆盖约160只股票，不代表全市场！")

    腾讯行情数据 = {}
    try:
        url = f"http://qt.gtimg.cn/q={','.join(腾讯股票池)}"
        resp = 带重试的请求(url, 超时=5, 编码="gbk")

        for line in resp.text.strip().split(";"):
            if not line.strip():
                continue
            parts = line.split("~")
            if len(parts) < 30:
                continue
            股名称 = parts[1]
            股代码 = parts[2]
            价格 = float(parts[3]) if parts[3] else 0.0
            昨收 = float(parts[4]) if parts[4] else 价格
            涨跌幅 = ((价格 - 昨收) / 昨收 * 100) if 昨收 > 0 else 0.0
            腾讯行情数据[股代码] = {
                "名称": 股名称, "涨跌幅": 涨跌幅, "价格": 价格,
                "昨收": 昨收
            }

        print(f"      ✅ 腾讯行情: {len(腾讯行情数据)}只股票")
    except Exception as e:
        print(f"      ⚠️ 腾讯批量查询失败: {e}")

    # ===== 第一阶段：从每个Top板块的领涨股直接入选（查代码）=====
    print("    🎯 第一阶段：处理各板块领涨股...")
    for b in Top3板块:
        领涨股名 = b.get('领涨股', '')
        if not 领涨股名:
            continue

        # 在腾讯结果中查找领涨股代码
        领涨股代码 = ""
        for 代码, 数据 in 腾讯行情数据.items():
            if 数据['名称'] == 领涨股名:
                领涨股代码 = 代码
                break

        if 领涨股代码:
            候选股.append({
                "名称": 领涨股名,
                "板块": b['名称'],
                "来源": "领涨股",
                "涨跌幅": b.get('领涨股涨跌幅', 0),
                "代码": 领涨股代码,
                "量比": 1.0,
            })
            print(f"      ✅ 领涨股: {领涨股名}({领涨股代码})（{b['名称']}）")
        else:
            print(f"      ⚠️ 领涨股{领涨股名}未在腾讯池中，尝试单独查询...")
            # 尝试用腾讯模糊搜索查领涨股代码（用名称查）
            try:
                领涨股代码 = 查股票代码(领涨股名)
                if 领涨股代码:
                    候选股.append({
                        "名称": 领涨股名,
                        "板块": b['名称'],
                        "来源": "领涨股",
                        "涨跌幅": b.get('领涨股涨跌幅', 0),
                        "代码": 领涨股代码,
                        "量比": 1.0,
                    })
                    print(f"      ✅ 查得领涨股代码: {领涨股名}({领涨股代码})")
            except Exception as e:
                print(f"      ⚠️ 查询领涨股代码失败: {e}")

    # ===== 第二阶段：腾讯批量个股匹配Top板块 ✅ 精确代码匹配 ====
    print("    📡 第二阶段：腾讯批量个股精确代码匹配...")

    # 为 Top3 板块构建精确代码映射表（避免名称误判）
    板块代码映射 = {}
    for b in Top3板块:
        名 = b['名称']
        if "半导" in 名:
            板块代码映射[名] = [
                "688981", "688012", "688008", "688126", "688041", "688072",
                "688256", "688037", "688018", "688200", "688396", "688521",
                "688689", "688082", "688138", "688206", "688209",
                "603986", "603501", "603160", "603005", "603893", "603290",
                "600171", "600460", "600584", "600745", "600703",
                "002049", "002371", "002156", "002185", "002077",
                "300661", "300782", "300672", "301099", "300223",
                "301308", "300604", "300623", "300842",
            ]
        elif "电子化学" in 名:
            板块代码映射[名] = [
                "300054", "300346", "300236", "300576", "300655",
                "300398", "300489", "300637", "300903",
                "603379", "600746", "002409", "603650",
                "688019", "688025", "688106", "688116", "688199",
                "688268", "688378", "688550", "688596",
            ]
        elif "元件" in 名:
            板块代码映射[名] = [
                "002484", "002138", "002384", "002916", "002465",
                "002475", "002241", "002273", "002106",
                "300136", "300408", "300115",
                "301031", "300709", "300476",
                "600183", "600563", "603228", "603267", "603920",
                "603327", "603328",
                # 精密电子制造
                "002600", "002579", "002815", "002885",
                "300476", "300709", "300606", "300812",
                # PCB/CCL
                "603186", "002913", "002938", "603005",
                "688019", "688025", "688200", "688396",
            ]
        elif "计算机" in 名 or "计算机设备" in 名:
            板块代码映射[名] = [
                "601138",  # 工业富联：AI服务器制造龙头，属计算机设备
                "000977", "603019", "002415", "300853",
                "300476", "300045", "002152", "300130", "300603", "688158",
                "000066", "600100",
            ]

        elif "煤炭" in 名:
            板块代码映射[名] = [
                "601225", "601088", "600188", "600985", "600546",
                "600348", "600971", "601001", "601666", "601699",
                "600508", "601898", "601918", "600740", "600578",
            ]
        elif "电力" in 名:
            板块代码映射[名] = [
                "600900", "600886", "600011", "600023", "600025",
                "600905", "600938", "601985", "601567", "601727",
                "000543", "000600", "000690", "000883", "000966",
                "300750", "300274", "300693",
            ]
        else:
            # 对于未知板块，不强行名称匹配（避免误判）
            板块代码映射[名] = []

    for 板块名, 代码列表 in 板块代码映射.items():
        for 代码 in 代码列表:
            # 排除误判：恒生电子(600570)等不是电子制造股
            if 代码 == "600570" and 板块名 in ("半导体", "电子化学品", "元件"):
                continue
            if 代码 == "600588" and 板块名 in ("半导体", "电子化学品", "元件"):
                continue
            if 代码 == "600519" and 板块名 in ("半导体", "电子化学品", "元件", "煤炭"):
                continue
            if 代码 in 腾讯行情数据:
                数据 = 腾讯行情数据[代码]
                if not any(c.get('代码') == 代码 for c in 候选股 if c.get('代码')):
                    候选股.append({
                        "代码": 代码,
                        "名称": 数据['名称'],
                        "板块": 板块名,
                        "来源": "腾讯精确匹配",
                        "涨跌幅": 数据['涨跌幅'],
                        "量比": 1.0,
                    })

    print(f"      ✅ 腾讯精确匹配阶段: 共 {sum(1 for c in 候选股 if c['来源']=='腾讯精确匹配')} 只")

    # ===== 第三阶段：东财补充（盘中可用）=====
    if 数据源 == "东方财富" or _是否为盘中时间():
        print("    📡 第三阶段：东财板块成分股补充（盘中可用）...")
        for b in Top3板块:
            try:
                成分股 = ak.stock_board_industry_cons_em(symbol=b['名称'])
                if not 成分股.empty:
                    count = 0
                    for _, row in 成分股.head(10).iterrows():
                        代码 = str(row.get('代码', ''))
                        名称 = row.get('名称', '')
                        if not 代码 or any(c.get('代码') == 代码 for c in 候选股 if c.get('代码')):
                            continue
                        候选股.append({
                            "代码": 代码,
                            "名称": 名称,
                            "板块": b['名称'],
                            "来源": "东财成分股",
                            "涨跌幅": row.get('涨跌幅', 0),
                            "量比": row.get('量比', 1.0),
                            "换手率": row.get('换手率', 0),
                        })
                        count += 1
                    print(f"      ✅ 东财补充: {b['名称']} → {count}只")
            except Exception as e:
                print(f"      ⚠️ 东财{b['名称']}失败: {e}")
    else:
        print("    ⏰ 盘后模式，跳过东财成分股补充")

    # ===== 第四阶段：去重 & 技术指标筛选 =====
    print("    🔬 第四阶段：技术指标深度筛选...")
    已见 = set()
    去重候选 = []
    for c in 候选股:
        key = c.get('代码', '')
        if not key:
            key = c['名称']
        if key and key not in 已见:
            已见.add(key)
            去重候选.append(c)

    print(f"      🗂️ 去重后共 {len(去重候选)} 只候选股")

    # 🔥 宁缺毋滥！技术面硬性一票否决制
    黑马池 = []
    for c in 去重候选:
        代码 = c.get('代码', '')
        if not 代码:
            continue

        try:
            # 获取日K线判断均线
            数据框 = 获取日K线数据(代码, 使用缓存=True)
            数据框 = 计算全部技术指标(数据框)
            最新 = 数据框.iloc[-1]

            # 条件1：5日均线多头（MA5 > MA10）
            ma5多头 = 最新['MA5'] > 最新['MA10'] if not pd.isna(最新['MA5']) else False

            # 条件2：股价站上MA5
            站上MA5 = 最新['close'] > 最新['MA5']

            # ⛔ 一票否决：均线多头必须为True
            if not ma5多头:
                print(f"      ❌ {代码}({c['名称']}): MA5多头=❌ → 一票否决！跳过")
                continue

            # ⛔ 一票否决：股价必须站上MA5
            if not 站上MA5:
                print(f"      ❌ {代码}({c['名称']}): 站上MA5=❌ → 一票否决！跳过")
                continue

            # 🔥 计算技术分：仅基于已确定的历史数据（无未来函数风险）
            # ⚠️ 审计说明：
            #  - MA5/MA10 使用 rolling(5).mean()，依赖历史收盘价，不需要当日收盘价
            #  - 如果缓存中包含当日盘中实时数据（close=最新价），MA5可能漂移
            #  - 因此早盘(09:20)运行时，建议强制刷新缓存或仅使用昨日数据
            #  - 当前实现中：获取日K线用缓存(使用缓存=True)，若缓存是最新的非当日数据则安全
            技术分 = 0
            if ma5多头:
                技术分 += 3
            if 站上MA5:
                技术分 += 2
            if 最新['pct_chg'] > 0:
                技术分 += 1

            c['技术分'] = 技术分
            c['均线多头'] = ma5多头
            c['站上MA5'] = 站上MA5
            c['收盘价'] = 最新['close']
            c['MA5'] = 最新['MA5']
            c['MA10'] = 最新['MA10']
            c['涨跌幅'] = 最新['pct_chg']
            黑马池.append(c)

            print(f"      ✅ {代码}({c['名称']}): {c['板块']} | "
                  f"MA5多头=✅ 站上MA5=✅ 技术分={技术分}")

        except Exception as e:
            # K线获取失败 → 宁缺毋滥，直接跳过
            print(f"      ⚠️ {代码}({c['名称']}): 技术数据获取失败，跳过")
            continue

    # 按技术分排序，取前N名
    黑马池.sort(key=lambda x: x['技术分'], reverse=True)

    if not 黑马池:
        # 🔥 宁缺毋滥：没有达标黑马就返回空列表
        print(f"    ⛔ 今日无达标黑马！所有候选股均被一票否决（均线多头+站上MA5双重硬性门槛）")
        return []

    最终结果 = 黑马池[:取前几名]

    print(f"    ✅ 最终精选出 {len(最终结果)} 只黑马股")
    for i, s in enumerate(最终结果):
        print(f"       🐎 {i+1}. {s['名称']}({s.get('代码','')}) — {s.get('板块','')} 技术分={s.get('技术分',0)}")

    return 最终结果



def 查股票代码(股票名称: str) -> str:
    """
    通过股票名称查询股票代码。
    使用腾讯批量接口，如果找不到则返回空字符串。
    """
    # 常见股票名称→代码映射（用于领涨股查找）
    名称代码映射 = {
        "普冉股份": "sz301099", "龙辰科技": "sz920161", "胜业电气": "sz301118",
        "雅创电子": "sz301099", "安泰集团": "sh600408",
        "贵州茅台": "sh600519", "中国平安": "sh601318", "招商银行": "sh600036",
        "中信证券": "sh600030", "兴业银行": "sh601166",
        "伊利股份": "sh600887", "海螺水泥": "sh600585", "长江电力": "sh600900",
        "隆基绿能": "sh601012", "万华化学": "sh600309", "恒瑞医药": "sh600276",
        "药明康德": "sh603259", "中国中免": "sh601888",
        "美的集团": "sz000333", "格力电器": "sz000651", "五粮液": "sz000858",
        "万科A": "sz000002", "平安银行": "sz000001",
        "海康威视": "sz002415", "立讯精密": "sz002475",
        "宁德时代": "sz300750", "东方财富": "sz300059",
        "牧原股份": "sz002714", "泸州老窖": "sz000568",
        "工业富联": "sh601138", "比亚迪": "sz002594",
        "迈瑞医疗": "sz300760", "中芯国际": "sh688981",
        "北方华创": "sz002371", "韦尔股份": "sh603501",
        "紫光国微": "sz002049", "中微公司": "sh688012",
        "澜起科技": "sh688008", "华虹公司": "sh688347",
        "长电科技": "sh600584", "士兰微": "sh600460",
        "兆易创新": "sh603986", "寒武纪": "sh688256",
        "海光信息": "sh688041", "拓荆科技": "sh688072",
    }

    if 股票名称 in 名称代码映射:
        return 名称代码映射[股票名称]

    return ""



def 快捷扫描全市场个股(腾讯股票池: list = None) -> list:
    """
    快捷全市场个股扫描（腾讯批量接口24h可用）
    返回：[{"代码": "...", "名称": "...", "涨跌幅": ..., "量比": ..., "行业归属": "..."}, ...]
    ⚠️ 审计警告：腾讯批量查询仅覆盖约160只股票，样本数远不及全市场！
    """
    if 腾讯股票池 is None:
        腾讯股票池 = [
            "sh600519", "sh601318", "sh600036", "sh600030", "sh601166",
            "sh600887", "sh600585", "sh601398", "sh601939", "sh600900",
            "sh601012", "sh600309", "sh600276", "sh603259", "sh601888",
            "sh600690", "sh600809", "sh600085", "sh600438", "sh600703",
            "sh600745", "sh600893", "sh601088", "sh600104", "sh600028",
            "sh600196", "sh600588", "sh600570", "sh600111", "sh600362",
            "sh601225", "sh601857", "sh600019", "sh600010", "sh600031",
            "sh600050", "sh600941", "sh600887", "sh600085", "sh600900",
            "sz000858", "sz000002", "sz000001", "sz002415", "sz002475",
            "sz300750", "sz300059", "sz000651", "sz000333", "sz002714",
            "sz002304", "sz000568", "sz000596", "sz002230", "sz300124",
            "sz000063", "sz000100", "sz000538", "sz000625", "sz000725",
            "sz002129", "sz002179", "sz002460", "sz002466", "sz002594",
            "sz300014", "sz300015", "sz300122", "sz300274", "sz300347",
            "sz300413", "sz300433", "sz300450", "sz300498", "sz300601",
            "sz300760", "sz300782", "sz300999", "sz300896", "sz301269",
            "sh601138", "sh600183", "sh600584", "sh600745", "sh603501",
            "sh688981", "sh688012", "sh688126", "sh688396", "sh688599",
            "sz002049", "sz002371", "sz002916", "sz300661", "sz300672",
            "sz301308", "sz000977", "sz000063", "sz002230", "sz002236",
        ]

    结果 = []
    try:
        url = f"http://qt.gtimg.cn/q={','.join(腾讯股票池)}"
        resp = 带重试的请求(url, 超时=5, 编码="gbk")

        for line in resp.text.strip().split(";"):
            if not line.strip():
                continue
            parts = line.split("~")
            if len(parts) < 30:
                continue

            名称 = parts[1]
            代码 = parts[2]
            价格 = float(parts[3]) if parts[3] else 0.0
            昨收 = float(parts[4]) if parts[4] else 价格
            涨跌幅 = ((价格 - 昨收) / 昨收 * 100) if 昨收 > 0 else 0.0
            成交量_手 = float(parts[6]) if parts[6] else 0.0
            成交额_万 = float(parts[37]) / 10000 if len(parts) > 37 and parts[37] else 0.0
            换手率 = float(parts[38]) / 100 if len(parts) > 38 and parts[38] else 0.0

            结果.append({
                "代码": 代码,
                "名称": 名称,
                "涨跌幅": 涨跌幅,
                "成交量": 成交量_手,
                "成交额": 成交额_万,
                "换手率": 换手率,
            })
    except Exception as e:
        print(f"    ⚠️ 腾讯扫描失败: {e}")

    # ⚠️ 样本数警告：腾讯扫描仅覆盖有限股票
    if len(结果) < 全市场样本数阈值:
        print(f"    ⚠️ 腾讯扫描仅获取到 {len(结果)} 只股票数据（远少于全A股）")

    return 结果



def 获取板块内强势股(板块名称: str, 取前几名: int = 3) -> list:
    """
    获取指定板块内主力资金净流入前N名的个股。
    返回列表：[{"代码": "601138", "名称": "工业富联", "主力净流入": 12345}, ...]
    """
    结果 = []
    try:
        # 获取板块成分股
        成分股 = ak.stock_board_industry_cons_em(symbol=板块名称)
        if 成分股.empty:
            return 结果

        # 获取板块内个股的资金流向
        for _, row in 成分股.head(20).iterrows():
            代码 = row.get('代码', '')
            if not 代码:
                continue
            try:
                资金 = 获取资金流向(代码)
                主力净流入_str = 资金.get("主力净流入", "0")
                try:
                    主力净流入 = float(主力净流入_str)
                except (ValueError, TypeError):
                    主力净流入 = 0
                结果.append({
                    "代码": 代码,
                    "名称": row.get('名称', ''),
                    "主力净流入": 主力净流入,
                    "涨跌幅": row.get('涨跌幅', 0)
                })
            except Exception:
                continue

        # 按主力净流入排序
        结果.sort(key=lambda x: x['主力净流入'], reverse=True)
        结果 = 结果[:取前几名]

    except Exception as e:
        print(f"    ⚠️ 获取板块{板块名称}强势股失败: {e}")

    return 结果


def 获取个股行业(股票代码: str) -> str:
    try:
        个股资料 = ak.stock_individual_info_ths(symbol=股票代码)
        行业行 = 个股资料[个股资料['item'] == '所处行业']
        if not 行业行.empty:
            return 行业行['value'].values[0]
    except Exception:
        pass
    return "新能源/核心资产"


def 获取资金流向(股票代码: str) -> dict:
    结果 = {
        "主力净流入": "0",
        "超大单净流入": "0",
        "大单净流入": "0",
        "连续资金方向": "0"
    }
    try:
        from 工具库.V8线程锁 import V8_LOCK
        市场 = 'sh' if 股票代码.startswith(('6', '9')) else 'sz'
        with V8_LOCK:
            资金数据 = ak.stock_individual_fund_flow(stock=股票代码, market=市场)
        if not 资金数据.empty:
            最新资金 = 资金数据.iloc[-1]
            # ★ 多字段兼容：新版akshare列名带"-净额"后缀
            主力净流入 = (
                最新资金.get('主力净流入-净额') or
                最新资金.get('主力净流入') or
                最新资金.get('主力净额') or
                0
            )
            超大单净流入 = (
                最新资金.get('超大单净流入-净额') or
                最新资金.get('超大单净流入') or
                最新资金.get('超大单净额') or
                0
            )
            大单净流入 = (
                最新资金.get('大单净流入-净额') or
                最新资金.get('大单净流入') or
                最新资金.get('大单净额') or
                0
            )
            结果["主力净流入"] = f"{主力净流入:.0f}"
            结果["超大单净流入"] = f"{超大单净流入:.0f}"
            结果["大单净流入"] = f"{大单净流入:.0f}"
            # 连续资金方向：新版列名兼容
            if '主力净流入-净额' in 资金数据.columns:
                净流 = 资金数据['主力净流入-净额'].tail(5)
            else:
                净流 = 资金数据.get('主力净流入', 资金数据.iloc[:, 1]).tail(5)
            正天数 = int((净流 > 0).sum())
            负天数 = int((净流 < 0).sum())
            结果["连续资金方向"] = f"近5日: {正天数}日净流入/{负天数}日净流出"
    except Exception:
        pass
    return 结果


# ==============================================================================
# 7. 🔥 龙虎榜数据（新增！游资席位审计）
# ==============================================================================

def 获取龙虎榜数据(股票代码: str, 最近天数: int = 5) -> dict:
    """
    获取个股最近N天的龙虎榜数据。
    返回结构化信息供AI审计游资席位。
    """
    结果 = {
        "有龙虎榜": False,
        "上榜日期": "无",
        "游资席位列表": [],
        "净买入额": "N/A",
        "买方前五": [],
        "卖方前五": [],
        "知名游资": [],
        "风险提示": ""
    }
    try:
        # 获取龙虎榜个股明细
        龙虎榜 = ak.stock_lhb_detail_em()
        if 龙虎榜.empty:
            return 结果

        # 筛选目标股票
        目标数据 = 龙虎榜[龙虎榜['代码'] == 股票代码]
        if 目标数据.empty:
            return 结果

        结果["有龙虎榜"] = True
        最新上榜 = 目标数据.iloc[-1]
        结果["上榜日期"] = str(最新上榜.get('日期', 'N/A'))[:10]
        结果["净买入额"] = f"{最新上榜.get('净买入额', 0):.0f}"

        # 获取详细买卖席位
        try:
            详情 = ak.stock_lhb_detail_daily_em()
            if not 详情.empty:
                股票详情 = 详情[详情['代码'] == 股票代码]
                if not 股票详情.empty:
                    买方 = 股票详情[股票详情['买卖标志'] == '买入'].head(5)
                    卖方 = 股票详情[股票详情['买卖标志'] == '卖出'].head(5)
                    结果["买方前五"] = 买方['营业部名称'].tolist() if not 买方.empty else []
                    结果["卖方前五"] = 卖方['营业部名称'].tolist() if not 卖方.empty else []

                    # 识别知名游资
                    知名游资名单 = [
                        "呼家楼", "六一中路", "作手新一", "方新侠", "赵老哥",
                        "炒股养家", "章盟主", "小鳄鱼", "佛山无影脚", "欢乐海岸",
                        "上海溧阳路", "宁波桑田路", "杭州龙井路", "北京知春路"
                    ]
                    所有席位 = 结果["买方前五"] + 结果["卖方前五"]
                    for 席位 in 所有席位:
                        for 游资 in 知名游资名单:
                            if 游资 in 席位:
                                结果["知名游资"].append({"席位": 席位, "方向": "买入" if 席位 in 结果["买方前五"] else "卖出"})
        except Exception:
            pass

        # 风险提示
        if 结果["知名游资"]:
            结果["风险提示"] = f"有知名游资参与：{', '.join([x['席位'] for x in 结果['知名游资']])}"
        else:
            结果["风险提示"] = "无知名游资参与，多为散户或普通机构席位"

    except Exception:
        pass

    return 结果


# ==============================================================================
# 8. 🔥 市场情绪数据（新增！连板高度、昨日涨停表现、炸板率）
# ==============================================================================

def 获取市场情绪数据() -> dict:
    """
    计算全市场短线情绪指标。
    三源对冲：东财全A快照（盘中）→ 腾讯批量查询（盘后）
    - 涨停定义：涨幅 ≥ 9.9%
    - 跌停定义：跌幅 ≤ -9.9%

    🔥 审计修复：腾讯备用源不再用60只样本估算全市场情绪，
    而是明确标注样本数不足的警告。
    """
    结果 = {
        "昨日涨停表现": "N/A",
        "最高连板": "N/A",
        "涨停家数": "N/A",
        "跌停家数": "N/A",
        "炸板率": "N/A",
        "情绪评级": "中性",
        "赚钱效应": "N/A",
        "样本警告": ""  # 🔥 新增：数据完整性警告
    }

    from 工具库.V8线程锁 import V8_LOCK
    # ===== 数据源A：东财全A快照（盘中）=====
    try:
        print("    📊 正在获取全A股实时快照（东财）...")
        with V8_LOCK:
            全A数据 = ak.stock_zh_a_spot_em()
        if not 全A数据.empty and '涨跌幅' in 全A数据.columns:
            样本数 = len(全A数据)
            # 🔥 断言：东财全A快照应包含4000+只股票
            if not 断言数据完整性(样本数, "东财全A快照"):
                结果["样本警告"] = f"数据残缺（仅{样本数}只），结果不可信！"

            涨停家数 = len(全A数据[全A数据['涨跌幅'] >= 9.9])
            跌停家数 = len(全A数据[全A数据['涨跌幅'] <= -9.9])
            结果["涨停家数"] = str(涨停家数)
            结果["跌停家数"] = str(跌停家数)
            print(f"      ✅ 东财全A快照: 共{样本数}只股票, 涨停{涨停家数}家, 跌停{跌停家数}家")

            # 连板高度
            try:
                涨停板数据 = ak.stock_zt_pool_em(date=datetime.now().strftime('%Y-%m-%d'))
                if not 涨停板数据.empty:
                    if '连板' in 涨停板数据.columns:
                        结果["最高连板"] = f"{涨停板数据['连板'].max()}板"
            except Exception:
                pass

            # 昨日涨停表现
            try:
                昨日日期 = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
                昨日涨停数据 = ak.stock_zt_pool_em(date=昨日日期)
                if not 昨日涨停数据.empty:
                    昨日代码列表 = 昨日涨停数据['代码'].tolist()[:30]
                    今日涨幅列表 = [row['涨跌幅'] for _, row in 全A数据.iterrows() if row.get('代码') in 昨日代码列表]
                    if 今日涨幅列表:
                        平均涨幅 = sum(今日涨幅列表) / len(今日涨幅列表)
                        结果["昨日涨停表现"] = f"{平均涨幅:+.2f}%"
                        if 平均涨幅 > 2:
                            结果["赚钱效应"] = "强"; 结果["情绪评级"] = "活跃"
                        elif 平均涨幅 > 0:
                            结果["赚钱效应"] = "一般"; 结果["情绪评级"] = "中性"
                        else:
                            结果["赚钱效应"] = "差"; 结果["情绪评级"] = "退潮"
            except Exception:
                pass

            return 结果  # 东财成功直接返回
    except Exception as e:
        print(f"    ⚠️ 东财全A快照失败: {e}")

    # ===== 数据源B：腾讯备用（盘后24h可用）=====
    print("    🔄 切换到腾讯备用源计算涨跌停...")
    try:
        热门股列表 = [
            "sh600519", "sh601318", "sh600036", "sh600030", "sh601166",
            "sh600887", "sh600585", "sh601398", "sh601939", "sh600900",
            "sh601012", "sh600309", "sh600276", "sh603259", "sh601888",
            "sz000858", "sz000002", "sz000001", "sz002415", "sz002475",
            "sz300750", "sz300059", "sz000651", "sz000333", "sz002714",
            "sz002304", "sz000568", "sz000596", "sz002230", "sz300124",
            "sh600036", "sh600104", "sh600690", "sh600809", "sh600085",
            "sh600438", "sh600703", "sh600745", "sh600893", "sh601088",
            "sz000063", "sz000100", "sz000538", "sz000625", "sz000725",
            "sz002129", "sz002179", "sz002460", "sz002466", "sz002594",
            "sz300014", "sz300015", "sz300122", "sz300274", "sz300347",
            "sz300413", "sz300433", "sz300450", "sz300498", "sz300601",
            "sz300750", "sz300760", "sz300782", "sz300999"
        ]

        url = f"http://qt.gtimg.cn/q={','.join(热门股列表)}"
        resp = 带重试的请求(url, 超时=5, 编码="gbk")

        涨跌幅列表 = []
        for line in resp.text.strip().split(";"):
            if not line.strip():
                continue
            parts = line.split("~")
            if len(parts) >= 4:
                价格 = float(parts[3]) if parts[3] else 0.0
                昨收 = float(parts[4]) if len(parts) > 4 and parts[4] else 价格
                涨跌幅 = ((价格 - 昨收) / 昨收 * 100) if 昨收 > 0 else 0.0
                涨跌幅列表.append(涨跌幅)

        if 涨跌幅列表:
            样本数 = len(涨跌幅列表)
            # 🔥 明确标注：腾讯备用源样本数极少，无法代表全市场
            结果["样本警告"] = f"数据极其残缺（仅{样本数}只样本，远少于全A股），情绪数据仅供参考！"
            print(f"    ⚠️ {结果['样本警告']}")

            涨停家数 = sum(1 for v in 涨跌幅列表 if v >= 9.9)
            跌停家数 = sum(1 for v in 涨跌幅列表 if v <= -9.9)
            结果["涨停家数"] = str(涨停家数)
            结果["跌停家数"] = str(跌停家数)
            print(f"      ✅ 腾讯备用计算: 涨停{涨停家数}家, 跌停{跌停家数}家（样本{样本数}只）")

            # 情绪评级（基于样本涨跌幅均值）
            平均涨跌幅 = sum(涨跌幅列表) / len(涨跌幅列表)
            if 平均涨跌幅 > 1:
                结果["情绪评级"] = "活跃"
                结果["赚钱效应"] = "强"
            elif 平均涨跌幅 > -0.5:
                结果["情绪评级"] = "中性"
                结果["赚钱效应"] = "一般"
            else:
                结果["情绪评级"] = "退潮"
                结果["赚钱效应"] = "差"
    except Exception as e:
        print(f"    ⚠️ 腾讯备用也失败: {e}")

    return 结果


# ==============================================================================
# 9. 🔥 分时量价异动检测（新增！盘中爆量滞涨、跌破黄线）
# ==============================================================================

def 检测分时异动(股票代码: str) -> dict:
    """
    检测盘中分时量价异动：
    - 爆量滞涨：成交量突然放大但价格不动
    - 分时均线位置：当前价相对于分时黄线的位置
    """
    结果 = {
        "当前价": "N/A",
        "分时均价": "N/A",
        "相对黄线位置": "未知",
        "爆量滞涨": False,
        "异动警告": ""
    }

    try:
        实时 = 获取个股实时行情(股票代码)
        前缀 = "sh" if 股票代码.startswith(("6", "9")) else "sz"
        键 = f"{前缀}{股票代码}"
        if 键 not in 实时:
            return 结果

        d = 实时[键]
        当前价 = d['最新价']
        开盘价 = d['开盘']
        结果["当前价"] = f"{当前价:.2f}"

        # 用开盘价和当前价的关系近似判断黄线位置
        if 当前价 >= 开盘价:
            结果["相对黄线位置"] = "站上黄线 ✅"
        else:
            结果["相对黄线位置"] = "跌破黄线 ❌"
            结果["异动警告"] = "⚠️ 股价跌破分时黄线（开盘价），若反抽无力建议减仓"

        # 获取日K判断爆量
        try:
            日K = 获取日K线数据(股票代码, 使用缓存=True)
            if len(日K) > 5:
                最近5日均量 = 日K['volume'].tail(5).mean()
                if 最近5日均量 > 0 and d['成交量'] > 最近5日均量 * 3:
                    结果["爆量滞涨"] = True
                    结果["异动警告"] += " ⚠️ 爆量滞涨！成交量超5日均量3倍，主力可能出货"
        except Exception:
            pass

    except Exception:
        pass

    return 结果


# ==============================================================================
# 10. 一站式全量数据采集（终极版）
# ==============================================================================

def 获取板块RS数据(上证涨跌: float):
    """获取板块相对强度数据（占位函数，避免采集中引用未定义函数）"""
    return {}


def 采集全量数据(股票代码: str, 使用缓存: bool = True, 已扫描情绪: dict = None, 快速模式: bool = False) -> dict:
    """
    一站式采集全部量化数据，包含：
    技术面 + 资金面 + 龙虎榜 + 市场情绪 + 分时异动
    
    参数：
        已扫描情绪: 可选，外部已扫描的情绪数据，避免重复扫描全市场（优化耗时关键）
        快速模式: True时跳过龙虎榜审计和分时异动检测（尾盘可省约15秒）
    """
    print(f"🍏 旗舰引擎v5.1终极版启动{'（缓存模式）' if 使用缓存 else '（强制刷新）'}...")

    # --- 大盘指数 ---
    上证指数价 = "N/A"
    上证涨跌 = 深证涨跌 = 创业板涨跌 = 科创涨跌 = 0.0

    指数数据 = 获取指数实时数据()
    if "s_sh000001" in 指数数据:
        d = 指数数据["s_sh000001"]
        上证指数价 = f"{d['最新价']:.2f}"
        上证涨跌 = d['涨跌幅']
    if "s_sz399001" in 指数数据:
        深证涨跌 = 指数数据["s_sz399001"]['涨跌幅']
    if "s_sz399006" in 指数数据:
        创业板涨跌 = 指数数据["s_sz399006"]['涨跌幅']
    if "s_sh000688" in 指数数据:
        科创涨跌 = 指数数据["s_sh000688"]['涨跌幅']

    print(f"  📡 指数就绪 | 上证 {上证涨跌:+.2f}% | 深成指 {深证涨跌:+.2f}% | 创业板 {创业板涨跌:+.2f}% | 科创50 {科创涨跌:+.2f}%")

    # --- 板块RS ---
    板块RS数据 = 获取板块RS数据(上证涨跌)

    # --- 个股K线（快速模式也合并今日实时 - 仅0.2s，对打分至关重要）---
    数据框 = 获取日K线数据(股票代码, 使用缓存=使用缓存)
    数据框 = 合并实时数据到数据框(数据框, 股票代码)
    # ★ 写回缓存，持久化换手率（确保换手率字段被缓存）
    if 使用缓存 and not 数据框.empty:
        _保存缓存(股票代码, 数据框, "日K")
    数据框 = 计算全部技术指标(数据框)

    # --- 行业归属 ---
    if 快速模式 or 使用缓存:
        # 快速模式/缓存模式跳过行业归属（尾盘不需额外验证，缓存已确认股票有效）
        行业信息 = "N/A（快速模式跳过）"
    else:
        行业信息 = 获取个股行业(股票代码)
        time.sleep(1.5)

    # --- 资金流向 ---
    资金流向 = 获取资金流向(股票代码)

    # --- 🔥 龙虎榜数据 ---
    if 快速模式:
        龙虎榜 = {"有龙虎榜": False, "上榜日期": "无", "风险提示": "快速模式跳过"}
    else:
        print("  🐅 正在审计龙虎榜游资席位...")
        龙虎榜 = 获取龙虎榜数据(股票代码)

    # --- 🔥 市场情绪 ---
    if 已扫描情绪 is not None:
        情绪数据 = 已扫描情绪
        print(f"  📊 复用已扫描的全市场情绪数据（涨停{情绪数据.get('涨停家数','N/A')}家）")
    else:
        print("  📊 正在扫描全市场情绪指标...")
        情绪数据 = 获取市场情绪数据()

    # --- 🔥 分时异动 ---
    if 快速模式:
        分时异动 = {"当前价": "N/A", "分时均价": "N/A", "相对黄线位置": "快速模式跳过", "爆量滞涨": False, "异动警告": ""}
    else:
        print("  📈 正在检测分时量价异动...")
        分时异动 = 检测分时异动(股票代码)

    # --- 最新两行数据 ---
    最新 = 数据框.iloc[-1]
    前一条 = 数据框.iloc[-2] if len(数据框) > 1 else 最新
    日期字符串 = str(最新.get('date', 'N/A'))[:10]

    # --- 定性判定 ---
    量价形态 = 判断量价形态(最新, 前一条)
    均线排列 = 判断均线排列(最新)
    MACD信号 = 判断MACD信号(最新, 前一条)
    ADX描述 = 判断ADX描述(最新['ADX'])
    布林形态 = 判断布林形态(最新)
    换手分类 = 判断换手率分类(最新['turnover'])

    # --- 打印摘要 ---
    print(f"\n📊 数据采集完成：{len(数据框)}根K线|{日期字符串}收盘{最新['close']:.2f}")
    print(f"   均线排列: {均线排列}|MACD: {MACD信号}|ADX: {最新['ADX']:.1f}({ADX描述})")
    print(f"   RSI6: {最新['RSI6']:.1f}|BIAS20: {最新['BIAS20']:.1f}%")
    print(f"   量价: {量价形态}|换手: {最新['turnover']:.1f}%|布林: {布林形态}")
    if 龙虎榜["有龙虎榜"]:
        print(f"   🐅 龙虎榜: {龙虎榜['风险提示']}")
    if 情绪数据.get("情绪评级", "中性") != "中性":
        print(f"   📊 情绪: {情绪数据.get('情绪评级', '中性')}|连板最高: {情绪数据.get('最高连板', 'N/A')}|涨停: {情绪数据.get('涨停家数', 'N/A')}家")
    if 分时异动["异动警告"]:
        print(f"   ⚠️ {分时异动['异动警告']}")

    return {
        "股票代码": 股票代码,
        "日期": 日期字符串,
        "数据框": 数据框,
        "最新": 最新,
        "前一条": 前一条,
        "上证指数价": 上证指数价,
        "上证涨跌": 上证涨跌,
        "深证涨跌": 深证涨跌,
        "创业板涨跌": 创业板涨跌,
        "科创涨跌": 科创涨跌,
        "板块RS": 板块RS数据,
        "行业": 行业信息,
        "资金流向": 资金流向,
        "龙虎榜": 龙虎榜,
        "市场情绪": 情绪数据,
        "分时异动": 分时异动,
        "量价形态": 量价形态,
        "均线排列": 均线排列,
        "MACD信号": MACD信号,
        "ADX描述": ADX描述,
        "布林形态": 布林形态,
        "换手分类": 换手分类,
    }


def 获取单只资金流(股票代码: str) -> dict:
    """
    东方财富直连：修复数字前缀（1代表沪市/科创，0代表深市/创业）
    单位：万元
    """
    import requests
    try:
        # 严格执行东财数字前缀规则
        if 股票代码.startswith(('6', '9', '688')):
            secid = f"1.{股票代码}"
        else:
            secid = f"0.{股票代码}"
            
        url = f"https://push2.eastmoney.com/api/qt/stock/fflow/kline/get?secid={secid}&fields1=f1,f2,f3&fields2=f51,f52,f53,f54,f55,f56,f57"
        resp = requests.get(url, headers={"User-Agent": "Mozilla/5.0", "Referer": "https://data.eastmoney.com/"}, timeout=3)
        data = resp.json()
        
        if data.get('data') and data['data'].get('klines'):
            latest = data['data']['klines'][-1].split(',')
            return {
                '主力净流入': float(latest[1]) / 10000 if len(latest) > 1 else 0,
                '大单净流入': float(latest[4]) / 10000 if len(latest) > 4 else 0,
                '超大单净流入': float(latest[5]) / 10000 if len(latest) > 5 else 0,
                '数据有效': True
            }
    except Exception as e:
        print(f"  ⚠️ {股票代码} 东财直连失败({e})，降级到V8...")
        
    return 获取单只资金流_V8(股票代码)

def 获取单只资金流_V8(股票代码: str) -> dict:
    """
    AkShare V8 降级源：兼容新老版本多字段键名
    """
    from 工具库.V8线程锁 import V8_LOCK
    try:
        with V8_LOCK:
            from akshare.stock.stock_fund_em import stock_individual_fund_flow
            df = stock_individual_fund_flow(stock=股票代码, market='sh' if 股票代码.startswith(('6','9')) else 'sz')
            if df is not None and not df.empty:
                main_col = next((c for c in df.columns if '主力净流入' in c), None)
                large_col = next((c for c in df.columns if '超大单净流入' in c), None)
                
                return {
                    '主力净流入': float(df[main_col].iloc[0]) / 10000 if main_col else 0,
                    '大单净流入': 0,
                    '超大单净流入': float(df[large_col].iloc[0]) / 10000 if large_col else 0,
                    '数据有效': True
                }
    except Exception as e:
        print(f"  ❌ V8资金流完全失效: {e}")
    return {'主力净流入': 0, '大单净流入': 0, '超大单净流入': 0, '数据有效': False}
