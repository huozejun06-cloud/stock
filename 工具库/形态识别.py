# ==============================================================================
# 工具库/形态识别.py — 🔍 K线形态识别
# 功能：检测5分钟K线中的W底双底形态
# ==============================================================================


def detect_w_bottom(kline_5min: list) -> dict:
    """
    在5分钟K线中检测W底（双底）形态。

    W底定义（在30分钟内完成）：
    1. 第一低点 A（时间t1，价格p1）
    2. 反弹至中间高点 B（时间t2，价格p2），反弹幅度 ≥ 1%
    3. 再次回落至第二低点 C（时间t3，价格p3），双底对称
    4. 当前最新价格从C反弹，已突破颈线（颈线 = B×0.8 + A×0.2）

    Args:
        kline_5min: 5分钟K线列表，按时间顺序排列，每根格式：
            {"time": "09:35", "open": 10.0, "high": 10.2, "low": 9.9, "close": 10.1, "volume": 12345}

    Returns:
        dict: W底检测结果
    """
    if not kline_5min or len(kline_5min) < 6:
        return {
            "is_w_bottom": False,
            "score": 0,
            "grade": "不是W底",
            "left_low": {},
            "middle_high": {},
            "right_low": {},
            "neckline": 0,
            "current_breakthrough": False,
            "current_price": 0,
            "description": "K线数据不足（至少需要6根5分钟K线）"
        }

    最新价 = kline_5min[-1]["close"]
    窗口大小 = 6  # 6根5分钟K线 = 30分钟
    最佳结果 = None
    最佳评分 = 0

    # 滑动窗口检测
    for start in range(len(kline_5min) - 窗口大小 + 1):
        window = kline_5min[start:start + 窗口大小]

        # 在窗口中找最低点 A
        a_idx = min(range(len(window)), key=lambda i: window[i]["low"])
        p1 = window[a_idx]["low"]
        t1 = window[a_idx]["time"]
        v1 = window[a_idx]["volume"]

        # 在A之后找最高点 B
        after_a = window[a_idx + 1:] if a_idx + 1 < len(window) else []
        if len(after_a) < 2:
            continue

        b_idx_local = max(range(len(after_a)), key=lambda i: after_a[i]["high"])
        b_idx = a_idx + 1 + b_idx_local
        p2 = window[b_idx]["high"]
        t2 = window[b_idx]["time"]
        v2 = window[b_idx]["volume"]

        # 在B之后找第二低点 C
        after_b = window[b_idx + 1:] if b_idx + 1 < len(window) else []
        if len(after_b) < 1:
            continue

        c_idx_local = min(range(len(after_b)), key=lambda i: after_b[i]["low"])
        c_idx = b_idx + 1 + c_idx_local
        p3 = window[c_idx]["low"]
        t3 = window[c_idx]["time"]
        v3 = window[c_idx]["volume"]

        # === 条件验证 ===
        # 条件1：反弹幅度 ≥ 1%
        反弹幅度 = (p2 - p1) / p1 if p1 > 0 else 0
        if 反弹幅度 < 0.01:
            continue

        # 条件2：双底对称性 |p3-p1|/p1 ≤ 0.5%
        双底对称性 = abs(p3 - p1) / p1 if p1 > 0 else 1
        if 双底对称性 > 0.005:
            continue

        # 条件3：当前价格已突破颈线（颈线 = B×0.8 + A×0.2）
        颈线 = p2 * 0.8 + p1 * 0.2
        已突破 = window[-1]["close"] > 颈线

        # === 评分 ===
        得分 = 70  # 基础分（通过上述3个条件即可获得70分）

        # 双底对称性加分（越对称分越高）
        if 双底对称性 <= 0.002:
            得分 += 10

        # 反弹幅度大（≥2%）加15分
        if 反弹幅度 >= 0.02:
            得分 += 15

        # 放量突破颈线
        if 已突破:
            # 突破时成交量 > 前3根平均量
            突破索引 = min(len(kline_5min) - 1, c_idx + 1)
            if 突破索引 > 0 and 突破索引 < len(kline_5min):
                突破量 = kline_5min[突破索引]["volume"]
                前三均量 = sum(
                    kline_5min[j]["volume"] for j in range(max(0, 突破索引 - 3), 突破索引)
                ) / min(3, 突破索引) if 突破索引 > 0 else 0
                if 前三均量 > 0 and 突破量 > 前三均量 * 1.5:
                    得分 += 20  # 放量突破（需超过前3根平均量的1.5倍）

        # 突破幅度 > 颈线的0.5%
        if 已突破 and 颈线 > 0:
            突破幅度 = (window[-1]["close"] - 颈线) / 颈线
            if 突破幅度 > 0.005:
                得分 += 15

        # 底到顶时间在25-35分钟（5-7根K线）
        底到顶K线数 = c_idx - a_idx
        if 5 <= 底到顶K线数 <= 7:
            得分 += 15

        # 第二低点成交量 < 第一低点成交量（缩量回调）
        if v3 < v1:
            得分 += 15

        # 记录评分最高的结果
        if 得分 > 最佳评分:
            最佳评分 = 得分
            最佳结果 = {
                "left_low": {"time": t1, "price": round(p1, 2), "volume": v1},
                "middle_high": {"time": t2, "price": round(p2, 2), "volume": v2},
                "right_low": {"time": t3, "price": round(p3, 2), "volume": v3},
                "neckline": round(颈线, 2),
                "current_breakthrough": 已突破,
                "current_price": round(最新价, 2),
            }

    # 没有检测到W底
    if 最佳结果 is None:
        return {
            "is_w_bottom": False,
            "score": 0,
            "grade": "不是W底",
            "left_low": {},
            "middle_high": {},
            "right_low": {},
            "neckline": 0,
            "current_breakthrough": False,
            "current_price": round(最新价, 2),
            "description": "未检测到W底形态"
        }

    # 确定等级
    if 最佳评分 >= 90:
        grade = "完美W底"
    elif 最佳评分 >= 70:
        grade = "有效W底"
    elif 最佳评分 >= 50:
        grade = "疑似W底"
    else:
        grade = "不是W底"

    # 生成描述
    l = 最佳结果["left_low"]
    m = 最佳结果["middle_high"]
    r = 最佳结果["right_low"]
    desc_parts = [f"{l['time']}→{m['time']}→{r['time']}完成W底"]
    if 最佳结果["current_breakthrough"]:
        desc_parts.append(f"已突破颈线{最佳结果['neckline']}")
    else:
        desc_parts.append(f"未突破颈线{最佳结果['neckline']}")
    description = "，".join(desc_parts)

    return {
        "is_w_bottom": 最佳评分 >= 70,
        "score": 最佳评分,
        "grade": grade,
        **最佳结果,
        "description": description
    }
