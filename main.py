# ==============================================================================
# main.py — 统一调度入口
# 用法：
#   python3 main.py morning   → 执行早盘任务
#   python3 main.py midday    → 执行午盘任务
#   python3 main.py evening   → 执行尾盘任务
#   python3 main.py night     → 夜盘复盘（预选池生成）
#   python3 main.py shanjied  → 早盘闪击判断
#   python3 main.py gui       → 启动图形界面
# ==============================================================================

import sys
from config import BASE_DIR

# 确保能找到 任务脚本/ 和 工具库/
sys.path.insert(0, BASE_DIR)


def 主函数():
    模式 = sys.argv[1] if len(sys.argv) > 1 else "evening"

    任务映射 = {
        "morning": ("任务脚本.早盘_新闻板块", "执行早盘任务", "🌅 早盘任务: 新闻聚合 & 板块轮动分析"),
        "midday":  ("任务脚本.午盘_持仓风控", "执行午盘任务", "🌤 午盘任务: 持仓风险评估 & 分时异动监控"),
        "evening": ("任务脚本.尾盘_决策报告", "执行尾盘任务", "🌆 尾盘任务: 全市场筛选Top5 + 全量数据打包 + DeepSeek决策"),
        "night":   ("任务脚本.夜盘_复盘", "执行夜盘复盘", "🌙 夜盘复盘: 全市场扫描 → 精选预选池 → 关键价位 → 保存JSON"),
        "shanjied": ("任务脚本.早盘_闪击", "执行早盘闪击", "⚡ 早盘闪击: 读取预选池 → 判断早盘闪击买入 → 回写状态"),
        "global":  ("工具库.全球市场", "获取全球市场文本摘要", "🌐 全球市场快照: 美/日/韩/港股指 + 核心美股 + 汇率"),
    "monitor": ("任务脚本.持仓监控", "监控持仓", "📡 持仓监控: 实时分析持股是否该卖 (python3 main.py monitor 代码 [入场价])"),
    }

    if 模式 not in 任务映射:
        print(f"❌ 未知模式: {模式}")
        sys.exit(1)

    模块名, 函数名, 描述 = 任务映射[模式]

    print(f"🚀 启动{描述}")
    print("=" * 60)

    # 🔥 自动数据源降级（东财不可用时自动切到同花顺/腾讯）
    print("📡 检测数据源可用性...")
    from 工具库.自动补丁 import auto_patch
    auto_patch()
    
    # 🔥 预热 V8 引擎（确保多线程前初始化完成，避免 py-mini-racer 并发撞车）
    from 工具库.V8线程锁 import preheat_v8
    preheat_v8()
    
    print("=" * 60)

    # 动态导入并执行
    import importlib
    模块 = importlib.import_module(模块名)
    函数 = getattr(模块, 函数名)
    # 传参（monitor模式需要: python3 main.py monitor 代码 [入场价]）
    if len(sys.argv) > 2 and 模式 in ("monitor",):
        函数(*sys.argv[2:])
    else:
        函数()



if __name__ == "__main__":
    主函数()
