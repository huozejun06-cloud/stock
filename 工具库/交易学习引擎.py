"""交易学习引擎 - 分析历史交易记录"""
import os, sqlite3
from datetime import datetime, timedelta
from config import DB_DIR

DB = os.path.join(DB_DIR, "实盘验证.db")

def 胜率报告(天数=90):
    if not os.path.exists(DB):
        return "暂无历史记录"
    try:
        conn = sqlite3.connect(DB)
        rows = conn.execute("SELECT * FROM signal_log ORDER BY date DESC LIMIT 20").fetchall()
        conn.close()
        if not rows:
            return "空库"
        lines = ["最近20条信号:"]
        for r in rows:
            lines.append("  %s %s" % (r[0] if len(r) > 0 else "", r[1] if len(r) > 1 else ""))
        return "\n".join(lines)
    except Exception as e:
        return "读取失败: %s" % e

if __name__ == "__main__":
    print(胜率报告())
