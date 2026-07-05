# ==============================================================================
# 工具库/分钟线数据.py — ⏱ 5分钟K线数据获取与缓存
# 功能：使用腾讯历史K线接口获取5分钟K线，带本地SQLite缓存（TTL=60秒）
# ==============================================================================

import requests
import json
import sqlite3
import os
from datetime import datetime, date

# 腾讯5分钟K线接口
TENCENT_KLINE_API = "http://ifzq.gtimg.cn/appstock/app/kline/mkline?param={market}{code},m5,,320"

# 缓存配置
from config import DB_DIR
缓存路径 = os.path.join(DB_DIR, "分钟线.db")
缓存TTL秒 = 60


def _初始化缓存():
    """内部初始化分钟线缓存表"""
    os.makedirs("cache", exist_ok=True)
    conn = sqlite3.connect(缓存路径, check_same_thread=False)
    try:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS 分钟线缓存 (
                代码 TEXT,
                日期 TEXT,
                数据 TEXT,
                更新时间 TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (代码, 日期)
            )
        """)
        conn.commit()
    finally:
        conn.close()


# 模块加载时自动初始化
_初始化缓存()


def _判断市场(代码: str) -> str:
    """根据股票代码判断市场前缀"""
    代码 = 代码.strip()
    if 代码.startswith(('6', '9', '5')):
        return "sh"
    else:
        return "sz"


def _读取缓存(代码: str, 今日日期: str) -> list:
    """
    从缓存读取5分钟K线数据，检查TTL。
    返回K线列表（如果缓存有效），否则返回None。
    """
    conn = sqlite3.connect(缓存路径, check_same_thread=False)
    try:
        cursor = conn.execute(
            "SELECT 数据, 更新时间 FROM 分钟线缓存 WHERE 代码=? AND 日期=?",
            (代码, 今日日期)
        )
        row = cursor.fetchone()
        if row is None:
            return None

        数据_json, 更新时间_str = row
        # 检查TTL
        try:
            更新时间 = datetime.strptime(更新时间_str, '%Y-%m-%d %H:%M:%S')
        except ValueError:
            更新时间 = datetime.strptime(更新时间_str, '%Y-%m-%d %H:%M:%S.%f')
        
        if (datetime.now() - 更新时间).total_seconds() < 缓存TTL秒:
            # 缓存有效
            return json.loads(数据_json)
        else:
            return None
    except Exception as e:
        print(f"  ⚠️ 读取分钟线缓存失败: {e}")
        return None
    finally:
        conn.close()


def _写入缓存(代码: str, 今日日期: str, kline_list: list):
    """将5分钟K线数据写入缓存"""
    conn = sqlite3.connect(缓存路径, check_same_thread=False)
    try:
        conn.execute("""
            INSERT OR REPLACE INTO 分钟线缓存 (代码, 日期, 数据, 更新时间)
            VALUES (?, ?, ?, ?)
        """, (代码, 今日日期, json.dumps(kline_list, ensure_ascii=False), datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
        conn.commit()
    except Exception as e:
        print(f"  ⚠️ 写入分钟线缓存失败: {e}")
    finally:
        conn.close()


def 获取5分钟K线(代码: str) -> list:
    """
    获取指定股票的当日5分钟K线数据。

    Args:
        代码: 股票代码，纯数字（如 "601138"）

    Returns:
        list: K线列表，每根K线格式：
            {"time": "09:35", "open": 10.0, "high": 10.2, "low": 9.9, "close": 10.1, "volume": 12345}
        获取失败返回空列表
    """
    今日日期 = date.today().strftime('%Y-%m-%d')
    今日日期紧凑 = date.today().strftime('%Y%m%d')  # 腾讯接口使用的格式

    # 1. 尝试读取缓存
    cached = _读取缓存(代码, 今日日期)
    if cached is not None:
        print(f"  ✅ 从缓存读取 {代码} 的5分钟K线 ({len(cached)}根)")
        return cached

    # 2. 缓存未命中或过期，重新请求接口
    市场 = _判断市场(代码)
    url = TENCENT_KLINE_API.format(market=市场, code=代码)

    try:
        print(f"  📡 请求腾讯5分钟K线: {代码}")
        resp = requests.get(url, timeout=10)
        resp.encoding = 'utf-8'
        data = resp.json()
    except Exception as e:
        print(f"  ⚠️ 获取 {代码} 5分钟K线失败: {e}")
        return []

    # 3. 解析返回的数据结构
    try:
        # 数据结构: {"data": {"sh601138": {"m5": [["时间","开","收","高","低","量","额"], ...]}}}
        market_code = f"{市场}{代码}"
        stock_data = data.get("data", {}).get(market_code, {})
        m5_data = stock_data.get("m5", [])

        if not m5_data:
            print(f"  ⚠️ {代码} 5分钟K线数据为空")
            return []

        # 4. 过滤出当日数据并转换为统一格式
        today_kline = []
        for item in m5_data:
            # 腾讯返回格式: ["09:35", 10.0, 10.1, 10.2, 9.9, 12345, 678901]
            if len(item) < 7:
                continue

            time_str = str(item[0]).strip()
            # 时间格式可能是 "09:35" 或 "2025-01-01 09:35"
            # 只保留时间部分
            if ' ' in time_str:
                time_str = time_str.split(' ')[1]
            elif ':' not in time_str:
                continue

            # 只保留当天数据（腾讯接口日期格式为 YYYYMMDD，如 "20260605 09:35"）
            raw_time = str(item[0]).strip()
            if ' ' in raw_time:
                date_part = raw_time.split(' ')[0].strip()
                # 腾讯格式是 YYYYMMDD，而今日日期是 YYYY-MM-DD，比较去掉连字符的版本
                if date_part != 今日日期紧凑 and not date_part.startswith(今日日期.replace('-', '')):
                    continue
            elif ':' not in raw_time:
                continue

            kline = {
                "time": time_str,
                "open": float(item[1]),
                "high": float(item[3]),
                "low": float(item[4]),
                "close": float(item[2]),
                "volume": int(float(item[5])),
            }
            today_kline.append(kline)

        # 按时间排序
        today_kline.sort(key=lambda x: x["time"])

        if today_kline:
            # 5. 写入缓存
            _写入缓存(代码, 今日日期, today_kline)
            print(f"  ✅ 获取 {代码} 5分钟K线成功 ({len(today_kline)}根)")
        else:
            print(f"  ⚠️ {代码} 今日无5分钟K线数据")

        return today_kline

    except Exception as e:
        print(f"  ⚠️ 解析 {代码} 5分钟K线失败: {e}")
        return []
