"""
工具库/热点生命周期.py — 板块生命周期识别
判断每个板块当前处于：启动期/发酵期/高潮期/退潮期
"""
import sys, os, pandas as pd, numpy as np
from config import BASE_DIR, CACHE_DIR
sys.path.insert(0, BASE_DIR)

def 判断板块生命周期(板块名: str, 板块股票: list, 全量数据: dict = None) -> dict:
    """判断一个板块所处的生命周期阶段"""
    if not 板块股票: return {"板块": 板块名, "阶段": "未知", "评分": 0}
    
    # 从缓存加载板块内各股票的数据，计算平均涨跌幅
    short_ret = []; mid_ret = []
    for code in 板块股票:
        path = os.path.join(CACHE_DIR, f"{code}_日K.csv")
        if not os.path.exists(path): continue
        try:
            df = pd.read_csv(path, parse_dates=["date"])
            if len(df) >= 20:
                c = df["close"].values
                short_ret.append(c[-1] / c[-4] - 1)   # 3日
                mid_ret.append(c[-1] / c[-11] - 1)    # 10日
        except Exception as e:
            print(f"  ⚠️ 热点生命周期.py: {e}")
            continue
    
    if not short_ret: return {"板块": 板块名, "阶段": "未知", "评分": 0}
    
    sr = np.mean(short_ret) * 100  # 短期涨幅%
    mr = np.mean(mid_ret) * 100    # 中期涨幅%
    
    if sr > 6: 阶段, 评分 = "高潮期", 80
    elif sr > 3 and mr > 4: 阶段, 评分 = "发酵期", 65
    elif sr > 1 and mr > 0: 阶段, 评分 = "启动期", 45
    else: 阶段, 评分 = "退潮期", 20
    
    return {"板块": 板块名, "阶段": 阶段, "评分": 评分, "短期": round(sr,1), "中期": round(mr,1)}


def 批量生命周期(板块映射: dict, 全量数据: dict = None) -> list:
    """分析所有板块的生命周期"""
    results = []
    for 板块名, 股票列表 in 板块映射.items():
        r = 判断板块生命周期(板块名, 股票列表, 全量数据)
        results.append(r)
    results.sort(key=lambda x: -x["评分"])
    return results


if __name__ == "__main__":
    from 工具库.数据源管理器 import get_manager
    results = 批量生命周期(get_manager().BOARD_STOCK_MAP)
    for r in results:
        print("%s: %s(评分%d) 短%.1f%% 中%.1f%%" % (r["板块"], r["阶段"], r["评分"], r["短期"], r["中期"]))
