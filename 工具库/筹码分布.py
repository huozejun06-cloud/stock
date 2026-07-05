"""
工具库/筹码分布.py — 筹码分布分析（A股特有）
追踪每只股票的持仓成本分布，识别真实支撑位和压力位
数据源：历史日K线（成交量和价格）
"""
import sys, os, numpy as np, pandas as pd
from scipy.ndimage import gaussian_filter1d
from config import BASE_DIR, CACHE_DIR
sys.path.insert(0, BASE_DIR)


def 计算筹码分布(df: pd.DataFrame, 回看天数: int = 200, 价格区间数: int = 200) -> dict:
    """
    计算股票的筹码分布
    输入: df - 日K线DataFrame (必须有 close, volume, high, low 列)
         回看天数 - 分析最近多少天的数据
         价格区间数 - 将价格区间分成多少份
    返回: {
        '价格区间': [...],        # 每个价格区间的中间价
        '筹码密度': [...],        # 每个区间的筹码密度(归一化0-100)
        '平均成本': float,         # 加权平均持仓成本
        '成本集中度': float,       # 0-100, 越高说明筹码越集中
        '获利盘比例': float,       # 0-100, 当前价格以下的筹码占比
        '支撑位': [...],          # 主要支撑价位
        '压力位': [...],          # 主要压力价位
        '峰谷分析': str,           # 文字描述
    }
    """
    if df is None or len(df) < 20:
        return {"错误": "数据不足"}
    
    recent = df.tail(回看天数).copy()
    current_price = recent['close'].iloc[-1]
    
    # 价格区间
    price_min = recent['low'].min() * 0.95
    price_max = recent['high'].max() * 1.05
    price_bins = np.linspace(price_min, price_max, 价格区间数)
    bin_width = (price_max - price_min) / 价格区间数
    
    # 高斯核密度估计：将每天成交量分配到附近价格区间
    distribution = np.zeros(价格区间数)
    total_vol = recent['volume'].sum()
    
    bandwidth = bin_width * 3  # 带宽控制平滑程度
    if bandwidth <= 0:
        bandwidth = bin_width
    
    for _, row in recent.iterrows():
        close = row['close']
        vol = row['volume'] if row['volume'] > 0 else 1
        # 高斯权重分配
        weights = np.exp(-((price_bins - close) ** 2) / (2 * bandwidth ** 2))
        weights /= weights.sum()  # 归一化
        distribution += vol * weights
    
    # 归一化到0-100
    if distribution.max() > 0:
        distribution = distribution / distribution.max() * 100
    
    # 平滑
    try:
        distribution = gaussian_filter1d(distribution, sigma=2)
    except Exception as e:
        print(f"  ⚠️ 筹码分布.py: {e}")
        pass
    
    # 找峰值（筹码密集区）
    peaks = []
    for i in range(2, len(distribution) - 2):
        if (distribution[i] > distribution[i-1] and 
            distribution[i] > distribution[i+1] and
            distribution[i] > distribution[i-2] and
            distribution[i] > distribution[i+2] and
            distribution[i] > 15):  # 排除小峰值
            peaks.append({
                '价格': round(price_bins[i], 2),
                '强度': round(distribution[i], 1),
                '类型': '支撑' if price_bins[i] < current_price else '压力',
            })
    peaks.sort(key=lambda x: x['价格'])
    
    # 支撑位和压力位
    支撑位 = [p['价格'] for p in peaks if p['类型'] == '支撑'][:3]
    压力位 = [p['价格'] for p in peaks if p['类型'] == '压力'][:3]
    
    # 平均成本（成交量加权平均价）
    平均成本 = np.average(price_bins, weights=distribution)
    
    # 获利盘比例（当前价格以下筹码占比）
    idx_current = np.abs(price_bins - current_price).argmin()
    获利比例 = distribution[:idx_current].sum() / distribution.sum() * 100 if distribution.sum() > 0 else 50
    
    # 成本集中度（筹码峰的高度/宽度比）
    if len(peaks) > 0:
        集中度 = min(100, sum(p['强度'] for p in peaks) / len(peaks))
    else:
        集中度 = 0
    
    # 峰谷分析文字
    if 集中度 > 70:
        描述 = f"筹码高度集中(集中度{集中度:.0f})，即将选择方向"
    elif 集中度 > 50:
        描述 = f"筹码较集中(集中度{集中度:.0f})，有主力运作痕迹"
    elif 集中度 > 30:
        描述 = f"筹码分散(集中度{集中度:.0f})，需长时间整理"
    else:
        描述 = f"筹码极度分散(集中度{集中度:.0f})，无主力"
    
    if 获利比例 > 80:
        描述 += "，获利盘多，抛压大"
    elif 获利比例 < 20:
        描述 += "，套牢盘多，抛压小"
    
    return {
        '价格区间': [round(p, 2) for p in price_bins],
        '筹码密度': [round(d, 2) for d in distribution],
        '平均成本': round(平均成本, 2),
        '成本集中度': round(集中度, 1),
        '获利盘比例': round(获利比例, 1),
        '支撑位': 支撑位,
        '压力位': 压力位,
        '峰谷分析': 描述,
        '当前价': round(current_price, 2),
    }


def 筹码评分(筹码结果: dict) -> int:
    """根据筹码分布给出评分(0-100)"""
    if not 筹码结果 or '错误' in 筹码结果:
        return 50
    
    集中度 = 筹码结果.get('成本集中度', 0)
    获利比例 = 筹码结果.get('获利盘比例', 50)
    当前价 = 筹码结果.get('当前价', 0)
    平均成本 = 筹码结果.get('平均成本', 0)
    
    得分 = 50
    
    # 筹码集中加分
    if 集中度 > 70: 得分 += 20
    elif 集中度 > 50: 得分 += 10
    elif 集中度 < 20: 得分 -= 10
    
    # 获利比例适中
    if 30 < 获利比例 < 70: 得分 += 10
    elif 获利比例 > 90: 得分 -= 15  # 获利太多，抛压大
    
    # 价格在平均成本附近（主力未大幅获利）
    if 平均成本 > 0 and 当前价 > 0:
        偏离 = (当前价 - 平均成本) / 平均成本 * 100
        if -5 < 偏离 < 5: 得分 += 15  # 主力成本区
        elif 偏离 > 20: 得分 -= 10    # 大幅脱离成本区
    
    return max(0, min(100, 得分))


if __name__ == "__main__":
    # 测试
    path = os.path.join(CACHE_DIR, "002138_日K.csv")
    df = pd.read_csv(path, parse_dates=['date'])
    result = 计算筹码分布(df)
    print(f"平均成本: {result['平均成本']} | 当前价: {result['当前价']}")
    print(f"集中度: {result['成本集中度']}")
    print(f"获利盘: {result['获利盘比例']:.1f}%")
    print(f"支撑位: {result['支撑位']}")
    print(f"压力位: {result['压力位']}")
    print(f"分析: {result['峰谷分析']}")
