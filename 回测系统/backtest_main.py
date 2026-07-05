"""
回测主入口
带进度条、预估剩余时间、自动检测可用数据
"""
import os
import sys
import time
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from backtest_engine import 运行回测, 打印回测结果, 获取候选股列表


def main():
    """回测主函数"""
    开始时间 = time.time()
    print("=" * 60)
    print("📊 【回测系统 v2.0】修复未来函数 + 手续费滑点")
    print(f"   启动时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    # 检测可用数据
    股票列表 = 获取候选股列表()
    print(f"\n📂 检测可用缓存数据...")

    # 检查哪些股票有缓存数据
    有数据的股票 = []
    CACHE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "缓存")
    for 代码 in 股票列表:
        csv_path = os.path.join(CACHE_DIR, f"{代码}_日K.csv")
        if os.path.exists(csv_path):
            有数据的股票.append(代码)

    print(f"   共 {len(股票列表)} 只候选股，{len(有数据的股票)} 只有缓存数据")
    if len(有数据的股票) == 0:
        print("   ❌ 无可用缓存数据，请先运行 evening 任务采集数据")
        return

    # 进度回调（带时间预估）
    总股票数 = len(有数据的股票)
    已完成数 = [0]

    def 进度回调(已完成, 总数):
        已完成数[0] = 已完成
        已用时间 = time.time() - 开始时间
        每日平均耗时 = 已用时间 / 已完成 if 已完成 > 0 else 0
        剩余天数 = 总数 - 已完成
        预估剩余 = 每日平均耗时 * 剩余天数
        # 进度条（每10%打印一次）
        if 已完成 % max(1, 总数 // 10) == 0 or 已完成 == 总数:
            进度比 = 已完成 / 总数 * 100
            print(f"   📊 进度: {已完成}/{总数} ({进度比:.0f}%) | 已用: {已用时间:.0f}s | 预估剩余: {预估剩余:.0f}s")

    print(f"\n🚀 开始全市场回测...")
    stats = 运行回测(股票列表=有数据的股票, 进度回调=进度回调)

    总耗时 = time.time() - 开始时间
    print(f"\n📊 总耗时: {总耗时:.0f} 秒 ({总耗时/60:.1f} 分钟)")

    打印回测结果(stats)

    # 总结
    print("\n" + "=" * 60)
    print("📋 回测总结")
    print("=" * 60)

    胜率1日 = stats.get('1日_胜率(%)', None)
    if 胜率1日 is not None:
        if 胜率1日 > 55:
            print(f"  🟢 Top1_1日 胜率 {胜率1日}% > 55% → 策略有Alpha")
        elif 胜率1日 > 48:
            print(f"  🟡 Top1_1日 胜率 {胜率1日}% (48%-52%) → 接近随机水平")
        else:
            print(f"  🔴 Top1_1日 胜率 {胜率1日}% < 48% → 策略在亏钱")

    平均1日 = stats.get('1日_平均收益(%)', None)
    总成本 = 0.0003 * 2 + 0.0002 + 0.001 * 2  # 佣金+印花税+滑点
    if 平均1日 is not None:
        if 平均1日 < 总成本 * 100:
            print(f"  🔴 扣费后平均收益 {平均1日}% → 手续费吃掉利润")
        elif 平均1日 < 0.5:
            print(f"  🟡 扣费后平均收益 {平均1日}% → 勉强覆盖成本")
        else:
            print(f"  🟢 扣费后平均收益 {平均1日}% → 有利可图")

    print(f"\n   详细结果已保存至: 回测结果.csv")


if __name__ == "__main__":
    main()
