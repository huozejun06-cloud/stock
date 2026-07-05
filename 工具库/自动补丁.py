"""
自动补丁 - 当东方财富不可用时，自动切换到备用数据源
将所有 akshare 函数透明替换为 DataSourceManager 实现
"""
from 工具库.数据源管理器 import get_manager


def auto_patch():
    """自动打补丁"""
    mgr = get_manager()

    # 如果东财可用，不打补丁（直接用原生akshare）
    if mgr.current_source == 'eastmoney':
        print("✅ 东方财富可用，使用原生akshare")
        return

    print(f"⚠️ 东方财富不可用，切换到 {mgr.current_source} 数据源")

    # 对 akshare 打补丁
    try:
        import akshare as ak

        # 保存原始函数引用
        _original_spot = ak.stock_zh_a_spot_em
        _original_board_cons = ak.stock_board_industry_cons_em
        _original_board_spot = ak.stock_board_industry_spot_em

        # 替换实时行情 -> 使用腾讯并发全市场扫描引擎
        def patched_spot_em():
            import pandas as pd
            print("    📡 [补丁模式] 使用腾讯并发引擎扫描全市场...")
            # 使用全市场扫描，3秒扫完5000+只
            df = mgr.get_all_market_stocks()
            if not df.empty and len(df) > 1000:
                # 转换为akshare兼容格式（东财格式）
                rows = []
                for _, row in df.iterrows():
                    rows.append({
                        '代码': row.get('代码', ''),
                        '名称': row.get('名称', ''),
                        '最新价': row.get('最新价', 0),
                        '涨跌幅': row.get('涨跌幅', 0),
                        '涨跌额': 0,
                        '成交量': 0,
                        '成交额': 0,
                        '换手率': 0,
                        '量比': 0,
                    })
                return pd.DataFrame(rows)
            return pd.DataFrame()

        # 替换板块成分股查询
        def patched_board_cons(symbol):
            import pandas as pd
            print(f"    📡 [补丁模式] 查询板块 {symbol} 成分股...")
            return mgr.get_board_stocks(symbol)

        # 替换板块热点查询
        def patched_board_spot_em():
            import pandas as pd
            print(f"    📡 [补丁模式] 使用本地板块映射计算热点...")
            hot_boards = mgr.get_hot_boards()
            if not hot_boards:
                return pd.DataFrame()
            # 转换为akshare兼容格式
            rows = []
            for b in hot_boards:
                rows.append({
                    '板块名称': b['名称'],
                    '涨跌幅': b['涨跌幅'],
                    '涨跌额': 0,
                    '成交量': 0,
                    '成交额': 0,
                    '公司数': b['公司家数'],
                })
            return pd.DataFrame(rows)

        # 应用补丁
        ak.stock_zh_a_spot_em = patched_spot_em
        ak.stock_board_industry_cons_em = patched_board_cons
        ak.stock_board_industry_spot_em = patched_board_spot_em

        print(f"✅ 补丁生效，当前数据源: {mgr.current_source}")
        print(f"   已替换函数: stock_zh_a_spot_em, stock_board_industry_cons_em, stock_board_industry_spot_em")
    except ImportError:
        print("⚠️ akshare 未安装，补丁跳过")
    except Exception as e:
        print(f"⚠️ 补丁应用失败: {e}")
