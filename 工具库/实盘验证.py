# ==============================================================================
# 工具库/实盘验证.py — 📊 实盘验证日志模块
# 功能：记录每日信号和次日验证数据到 SQLite，支持验证报告生成
# 复用 工具库/本地缓存.py 的模式：check_same_thread=False，函数级别打开关闭连接
# ==============================================================================

import sqlite3
import os
import copy
from datetime import datetime, timedelta

from config import DB_DIR
数据库路径 = os.path.join(DB_DIR, "实盘验证.db")


def _初始化数据库():
    """内部初始化：建表（不对外暴露）"""
    os.makedirs("cache", exist_ok=True)
    conn = sqlite3.connect(数据库路径, check_same_thread=False)
    try:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS 每日信号 (
                日期 TEXT,
                代码 TEXT,
                名称 TEXT,
                板块 TEXT,
                入选价 REAL,
                入选涨幅 REAL,
                引擎评分 REAL,
                红线通过数 INTEGER,
                信号 TEXT,
                仓位系数 REAL,
                裁决分数 REAL,
                裁决决策 TEXT,
                AI解读摘要 TEXT,
                PRIMARY KEY (日期, 代码)
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS 次日验证 (
                日期 TEXT,
                代码 TEXT,
                名称 TEXT,
                入选价 REAL,
                次日开盘 REAL,
                次日最高 REAL,
                次日最低 REAL,
                次日收盘 REAL,
                隔夜收益 REAL,
                盘中最高收益 REAL,
                最大回撤 REAL,
                止盈触发 INTEGER DEFAULT 0,
                止损触发 INTEGER DEFAULT 0,
                PRIMARY KEY (日期, 代码)
            )
        """)
        conn.commit()
    finally:
        conn.close()


# 模块加载时自动初始化
_初始化数据库()


def 记录今日信号(候选股分析列表: list, 裁决结果: dict, AI解读: str = ""):
    """
    将今日筛选出的候选股信号记录到数据库。

    Args:
        候选股分析列表: 单只股票全维度分析() 返回的结果列表
        裁决结果: 最终裁决() 返回的字典
        AI解读: DeepSeek 市场解读文本（可选）
    """
    if not 候选股分析列表:
        return

    今日日期 = datetime.now().strftime('%Y-%m-%d')
    conn = sqlite3.connect(数据库路径, check_same_thread=False)
    try:
        已记录 = 0
        for 股 in 候选股分析列表:
            if 股 is None:
                continue

            代码 = 股.get('代码', '')
            名称 = 股.get('名称', '')
            板块 = 股.get('板块', '')
            入选价 = 股.get('最新价', 0)
            入选涨幅 = 股.get('涨跌幅', 0)
            引擎评分 = 股.get('决策总分', 0)
            红线通过数 = 股.get('红线通过数', 0)
            信号 = 股.get('决策信号', '')
            仓位系数 = 裁决结果.get('仓位系数', 0) if 裁决结果 else 0
            裁决分数 = 裁决结果.get('分数', 0) if 裁决结果 else 0
            裁决决策 = 裁决结果.get('决策', '') if 裁决结果 else ''
            AI解读摘要 = AI解读[:200] if AI解读 else ''

            conn.execute("""
                INSERT OR IGNORE INTO 每日信号
                (日期, 代码, 名称, 板块, 入选价, 入选涨幅, 引擎评分, 红线通过数,
                 信号, 仓位系数, 裁决分数, 裁决决策, AI解读摘要)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                今日日期, 代码, 名称, 板块, 入选价, 入选涨幅, 引擎评分, 红线通过数,
                信号, 仓位系数, 裁决分数, 裁决决策, AI解读摘要
            ))
            已记录 += 1

        conn.commit()
        print(f"  ✅ 已记录{已记录}条信号")
    except Exception as e:
        print(f"  ⚠️ 记录今日信号失败: {e}")
    finally:
        conn.close()


def 记录次日验证(代码: str, 日期: str) -> dict:
    """
    记录某只股票在指定次日的验证数据。

    Args:
        代码: 股票代码（纯数字）
        日期: 入选日期（'YYYY-MM-DD'）

    Returns:
        dict: 包含隔夜收益、是否止盈/止损等验证结果
    """
    from 工具库.数据源管理器 import get_manager

    conn = sqlite3.connect(数据库路径, check_same_thread=False)
    try:
        # 从每日信号表查出该股该日的入选信息
        cursor = conn.execute(
            "SELECT 代码, 名称, 入选价 FROM 每日信号 WHERE 日期=? AND 代码=?",
            (日期, 代码)
        )
        row = cursor.fetchone()
        if not row:
            print(f"  ⚠️ 未找到 {代码} 在 {日期} 的入选记录")
            return {"代码": 代码, "隔夜收益": 0, "是否止盈": False, "是否止损": False}

        代码_db, 名称, 入选价 = row
    except Exception as e:
        print(f"  ⚠️ 查询每日信号失败: {e}")
        conn.close()
        return {"代码": 代码, "隔夜收益": 0, "是否止盈": False, "是否止损": False}
    finally:
        conn.close()

    # 获取该股当日实时行情（使用数据源管理器的公开方法）
    try:
        mgr = get_manager()
        df = mgr.get_stock_realtime([代码])
        if df.empty:
            print(f"  ⚠️ {代码} 当日行情数据为空")
            return {"代码": 代码, "隔夜收益": 0, "是否止盈": False, "是否止损": False}

        row = df.iloc[0]
        开盘 = float(row.get('开盘', 入选价))
        最高 = float(row.get('最高', 入选价))
        最低 = float(row.get('最低', 入选价))
        最新价 = float(row.get('最新价', 入选价))
    except Exception as e:
        print(f"  ⚠️ 获取 {代码} 实时行情失败: {e}")
        return {"代码": 代码, "隔夜收益": 0, "是否止盈": False, "是否止损": False}

    # 计算收益指标
    隔夜收益 = (最新价 - 入选价) / 入选价 if 入选价 > 0 else 0
    盘中最高收益 = (最高 - 入选价) / 入选价 if 入选价 > 0 else 0
    最大回撤 = (最低 - 入选价) / 入选价 if 入选价 > 0 else 0

    # 判断触发止盈/止损
    止盈触发 = 1 if 盘中最高收益 >= 0.05 else 0
    止损触发 = 1 if 最大回撤 <= -0.02 else 0

    # 写入次日验证表
    conn2 = sqlite3.connect(数据库路径, check_same_thread=False)
    try:
        conn2.execute("""
            INSERT OR REPLACE INTO 次日验证
            (日期, 代码, 名称, 入选价, 次日开盘, 次日最高, 次日最低, 次日收盘,
             隔夜收益, 盘中最高收益, 最大回撤, 止盈触发, 止损触发)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            日期, 代码, 名称, 入选价, 开盘, 最高, 最低, 最新价,
            round(隔夜收益, 4), round(盘中最高收益, 4), round(最大回撤, 4),
            止盈触发, 止损触发
        ))
        conn2.commit()
        print(f"  ✅ 已记录 {代码} {名称} 的次日验证（隔夜收益={隔夜收益*100:+.2f}%）")
    except Exception as e:
        print(f"  ⚠️ 写入次日验证失败: {e}")
    finally:
        conn2.close()

    return {
        "代码": 代码,
        "隔夜收益": round(隔夜收益 * 100, 2),
        "是否止盈": bool(止盈触发),
        "是否止损": bool(止损触发),
    }


def _获取列名(cursor: sqlite3.Cursor) -> list:
    """从cursor descrīpion获取列名列表"""
    return [desc[0] for desc in cursor.description]


def 生成验证报告(天数: int = 5) -> str:
    """
    生成最近N天的实盘验证报告。

    Args:
        天数: 统计最近几天的数据，默认5天

    Returns:
        str: Markdown 格式的验证报告
    """
    conn = sqlite3.connect(数据库路径, check_same_thread=False)
    try:
        # 读取最近N天的验证数据（按日期降序 + LIMIT）
        cursor = conn.execute(
            "SELECT * FROM 次日验证 ORDER BY 日期 DESC, 代码 LIMIT ?",
            (天数,)
        )
        rows = cursor.fetchall()
        columns = _获取列名(cursor)

        if not rows:
            return "⚠️ 暂无验证数据"

        # 转换为列表[dict]方便处理
        data = [dict(zip(columns, row)) for row in rows]

        # 整体统计
        总信号数 = len(data)
        隔夜收益列表 = [r['隔夜收益'] for r in data]
        平均隔夜收益 = sum(隔夜收益列表) / 总信号数 * 100
        胜率 = sum(1 for r in 隔夜收益列表 if r > 0) / 总信号数 * 100
        最大盈利 = max(隔夜收益列表) * 100
        最大亏损 = min(隔夜收益列表) * 100

        # 逐日明细表
        明细行 = []
        for r in data:
            明细行.append(
                f"| {r['日期']} | {r['代码']} | {r['名称']} | "
                f"{r['入选价']:.2f} | {r['次日开盘']:.2f} | {r['次日最高']:.2f} | "
                f"{r['次日最低']:.2f} | {r['次日收盘']:.2f} | "
                f"{r['隔夜收益']*100:+.2f}% | "
                f"{'✅' if r['止盈触发'] else '❌'} | "
                f"{'✅' if r['止损触发'] else '❌'} |"
            )
        明细表 = "\n".join(明细行)

        # 回测对比（回测期望收益固定为 +0.94%）
        实盘收益 = 平均隔夜收益
        差异 = 实盘收益 - 0.94

        报告 = f"""## 📊 实盘验证报告（最近{天数}天）

### 整体统计
- 总信号数：{总信号数}
- 平均隔夜收益：{平均隔夜收益:+.2f}%
- 胜率：{胜率:.1f}%
- 最大单日盈利：{最大盈利:+.2f}%
- 最大单日亏损：{最大亏损:+.2f}%

### 逐日明细表
| 日期 | 代码 | 名称 | 入选价 | 开盘 | 最高 | 最低 | 收盘 | 隔夜收益 | 止盈 | 止损 |
|------|------|------|--------|------|------|------|------|----------|------|------|
{明细表}

### 与回测对比
- 回测期望收益：+0.94%
- 实盘期望收益：{实盘收益:+.2f}%
- 差异：{差异:+.2f}%
"""
        return 报告

    except Exception as e:
        return f"⚠️ 生成验证报告失败: {e}"
    finally:
        conn.close()


def 批量补录验证(日期范围: tuple = None):
    """
    批量补录历史验证数据。
    遍历每日信号表中还没有对应次日验证记录的条目，逐一补录。

    Args:
        日期范围: (开始日期, 结束日期) 元组，格式 'YYYY-MM-DD'，为 None 则补录所有
    """
    conn = sqlite3.connect(数据库路径, check_same_thread=False)
    try:
        if 日期范围:
            开始日期, 结束日期 = 日期范围
            cursor = conn.execute("""
                SELECT s.日期, s.代码, s.名称
                FROM 每日信号 s
                LEFT JOIN 次日验证 v ON s.日期=v.日期 AND s.代码=v.代码
                WHERE v.日期 IS NULL
                  AND s.日期 >= ? AND s.日期 <= ?
                ORDER BY s.日期, s.代码
            """, (开始日期, 结束日期))
        else:
            cursor = conn.execute("""
                SELECT s.日期, s.代码, s.名称
                FROM 每日信号 s
                LEFT JOIN 次日验证 v ON s.日期=v.日期 AND s.代码=v.代码
                WHERE v.日期 IS NULL
                ORDER BY s.日期, s.代码
            """)

        rows = cursor.fetchall()
        if not rows:
            print("  ✅ 无需补录，所有信号已有验证记录")
            return

        total = len(rows)
        print(f"  📋 需要补录 {total} 条验证记录...")
    except Exception as e:
        print(f"  ⚠️ 查询待补录数据失败: {e}")
        conn.close()
        return
    finally:
        conn.close()

    成功 = 0
    for idx, (日期, 代码, 名称) in enumerate(rows, 1):
        try:
            结果 = 记录次日验证(代码, 日期)
            if 结果.get("隔夜收益", 0) != 0 or 代码:
                成功 += 1
            print(f"    进度: {idx}/{total}")
        except Exception as e:
            print(f"  ⚠️ 补录 {代码} {日期} 失败: {e}")

    print(f"  ✅ 已补录{成功}/{total}条")
