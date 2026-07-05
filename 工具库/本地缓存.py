# ==============================================================================
# 工具库/本地缓存.py — SQLite 本地缓存历史技术指标（线程安全版）
# 功能：将计算好的技术指标缓存到本地 SQLite，避免重复网络请求
# 线程安全：每个线程独立打开/关闭连接，加 check_same_thread=False
# ==============================================================================

import sqlite3
import pandas as pd
import os
import os.path
from config import DB_DIR

缓存路径 = os.path.join(DB_DIR, "技术指标.db")


def 初始化缓存():
    """
    主线程初始化时调用一次（只建表，不持有连接）。
    每个线程后续独立打开连接。
    """
    os.makedirs(DB_DIR, exist_ok=True)
    # 每个线程独立打开连接，必须加 check_same_thread=False
    conn = sqlite3.connect(缓存路径, check_same_thread=False)
    try:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS 技术指标 (
                代码 TEXT,
                日期 TEXT,
                MA5 REAL, MA10 REAL, MA20 REAL, MA60 REAL,

                DIF REAL, DEA REAL, MACD柱 REAL,
                RSI6 REAL, RSI14 REAL,
                BIAS20 REAL,
                ATR14 REAL,
                量MA5 REAL, 量MA10 REAL, 量MA20 REAL,
                K REAL, D REAL, J REAL,
                布林中轨 REAL, 布林上轨 REAL, 布林下轨 REAL,
                ADX REAL, 正DI REAL, 负DI REAL,
                OBV REAL,
                PRIMARY KEY (代码, 日期)
            )
        """)
        conn.commit()
    finally:
        conn.close()


def 批量缓存指标(代码: str, df指标: pd.DataFrame):
    """
    将计算好的技术指标写入本地缓存（在子线程中调用）。
    每个线程独立打开连接。
    """
    conn = sqlite3.connect(缓存路径, check_same_thread=False)
    try:
        # 确保日期列存在
        if 'date' in df指标.columns:
            df指标 = df指标.rename(columns={'date': '日期'})
        elif '日期' not in df指标.columns:
            raise ValueError("DataFrame 缺少日期列")

        # 只保留需要的列
        需要列 = ['日期', 'MA5', 'MA10', 'MA20', 'MA60',
                  'DIF', 'DEA', 'MACD柱',
                  'RSI6', 'RSI14',
                  'BIAS20',
                  'ATR14',
                  '量MA5', '量MA10', '量MA20',
                  '布林中轨', '布林上轨', '布林下轨',
                  'ADX', '正DI', '负DI', 'OBV']
        实际列 = [c for c in 需要列 if c in df指标.columns]

        if not 实际列:
            print(f"    ⚠️ 缓存 {代码}: 没有可缓存的技术指标列")
            return

        # 添加代码列
        df_to_save = df指标[实际列].copy()
        df_to_save.insert(0, '代码', 代码)

        # 写入数据库（replace模式）
        df_to_save.to_sql("技术指标", conn, if_exists="append", index=False)
        conn.commit()
        print(f"  💾 已缓存 {代码} 的技术指标 ({len(df_to_save)}行)")
    except Exception as e:
        print(f"  ⚠️ 缓存 {代码} 失败: {e}")
    finally:
        conn.close()


def 读取缓存指标(代码: str, 开始日期: str = "20240101", 结束日期: str = "20991231") -> pd.DataFrame:
    """
    从本地缓存读取历史技术指标（在子线程中调用）。
    每个线程独立打开连接。
    """
    conn = sqlite3.connect(缓存路径, check_same_thread=False)
    try:
        # 确保日期格式统一（去除可能的横线）
        开始日期_清理 = 开始日期.replace("-", "")
        结束日期_清理 = 结束日期.replace("-", "")

        # 兼容两种日期格式（YYYY-MM-DD 和 YYYYMMDD）
        df = pd.read_sql(f"""
            SELECT * FROM 技术指标 
            WHERE 代码=? AND (
                REPLACE(日期, '-', '') >= ? AND REPLACE(日期, '-', '') <= ?
            )
            ORDER BY 日期
        """, conn, params=(代码, 开始日期_清理, 结束日期_清理))

        if not df.empty:
            print(f"  ✅ 从本地缓存读取 {代码} 的技术指标 ({len(df)}行)")

        return df
    except Exception as e:
        print(f"  ⚠️ 读取缓存 {代码} 失败: {e}")
        return pd.DataFrame()
    finally:
        conn.close()


def 清除缓存():
    """清除所有缓存数据"""
    conn = sqlite3.connect(缓存路径, check_same_thread=False)
    try:
        conn.execute("DELETE FROM 技术指标")
        conn.commit()
        print("  🗑️ 已清除所有技术指标缓存")
    except Exception as e:
        print(f"  ⚠️ 清除缓存失败: {e}")
    finally:
        conn.close()


def 获取缓存统计() -> dict:
    """获取缓存统计信息"""
    conn = sqlite3.connect(缓存路径, check_same_thread=False)
    try:
        总行数 = pd.read_sql("SELECT COUNT(*) as cnt FROM 技术指标", conn)['cnt'][0]
        股票数 = pd.read_sql("SELECT COUNT(DISTINCT 代码) as cnt FROM 技术指标", conn)['cnt'][0]
        最早日期 = pd.read_sql("SELECT MIN(日期) as dt FROM 技术指标", conn)['dt'][0] if 总行数 > 0 else "N/A"
        最晚日期 = pd.read_sql("SELECT MAX(日期) as dt FROM 技术指标", conn)['dt'][0] if 总行数 > 0 else "N/A"
        return {
            "总行数": int(总行数),
            "股票数": int(股票数),
            "最早日期": str(最早日期),
            "最晚日期": str(最晚日期),
        }
    except Exception as e:
        return {"错误": str(e)}
    finally:
        conn.close()
