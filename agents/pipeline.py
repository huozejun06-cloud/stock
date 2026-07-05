# ==============================================================================
# agents/pipeline.py — 新 Agent 全市场选股流水线
# ==============================================================================

import sys, os, time, json, asyncio, gzip
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import numpy as np

from config import KLINE_CSV_PATH as KLINE_PATH
_MASTER_CACHE = None
_KLINE_MAX_DATE = None


def _load_kline(code: str, use_cache: bool = True) -> pd.DataFrame:
    """加载K线: 本地缓存(过期则自动下载) → 同花顺API → 全量数据集"""
    global _MASTER_CACHE, _KLINE_MAX_DATE
    
    # 检查本地文件缓存（含日期校验）
    if use_cache:
        from config import CACHE_DIR
        cache_path = os.path.join(CACHE_DIR, f"{code}_日K.csv")
        if os.path.exists(cache_path):
            df = pd.read_csv(cache_path, parse_dates=["date"])
            if len(df) >= 60:
                _days = (pd.Timestamp.now() - df['date'].max()).days
                if _days < 5:  # 5天内 → 直接用
                    return df.tail(200).reset_index(drop=True)
    
    # 缓存过期或不存在 → 从同花顺API下载
    if use_cache:
        try:
            from 工具库.数据工具 import 获取日K线数据
            df_new = 获取日K线数据(code, 起始日期="20260101")
            if df_new is not None and len(df_new) >= 60:
                df_new.to_csv(cache_path, index=False)
                _cd = str(df_new['date'].max())[:10]
                if _KLINE_MAX_DATE is None or _cd > _KLINE_MAX_DATE:
                    _KLINE_MAX_DATE = _cd
                return df_new.tail(200).reset_index(drop=True)
        except Exception as e:
            print(f"  ⚠️ pipeline.py: {e}")
            pass
    
    # 从全量数据集加载
    if _MASTER_CACHE is None:
        print("  📦 加载全量K线数据集...")
        _MASTER_CACHE = pd.read_csv(KLINE_PATH, on_bad_lines='skip')
        _MASTER_CACHE['_code'] = _MASTER_CACHE['代码'].astype(str).str.zfill(6)
        _MASTER_CACHE = _MASTER_CACHE.sort_values(['_code', 'date']).reset_index(drop=True)
        print(f"  ✅ {len(_MASTER_CACHE):,} 行, {_MASTER_CACHE['_code'].nunique()} 只")
        _KLINE_MAX_DATE = str(_MASTER_CACHE['date'].max())[:10]
    
    sub = _MASTER_CACHE[_MASTER_CACHE['_code'] == code]
    if len(sub) < 60:
        return None
    
    # gzip 返回数据（不覆盖已有缓存，因为 gzip 数据更旧）
    sub = sub.tail(200).copy()
    sub['pct_chg'] = sub['close'].pct_change() * 100
    sub['pct_chg'] = sub['pct_chg'].fillna(0)
    
    if use_cache:
        from config import CACHE_DIR as _cdir
        _cp = os.path.join(_cdir, f"{code}_日K.csv")
        _has_newer = False
        if os.path.exists(_cp):
            try:
                _edf = pd.read_csv(_cp, nrows=3)
                if 'date' in _edf.columns and _edf['date'].max() >= sub['date'].max():
                    _has_newer = True
            except Exception as e:
                print(f"  ⚠️ pipeline.py: {e}")
                pass
        if not _has_newer:
            sub.to_csv(_cp, index=False)
    
    return sub


def run() -> str:
    t0 = time.time()
    lines = []
    def log(msg=""): lines.append(msg)
    
    log(f"\n{'='*55}")
    log(f"  🔄 新 Agent 全市场选股")
    log(f"{'='*55}")
    
    # ─── 1. 实时全市场扫描 ───
    log(f"\n[1/4] 实时全市场扫描...")
    from 工具库.数据源管理器 import DataSourceManager
    mgr = DataSourceManager()
    df_stocks = mgr.get_all_market_stocks()
    
    if df_stocks is None or len(df_stocks) == 0:
        return "❌ 扫描失败"
    
    # 条件1: 涨跌幅 2%~7%
    df_hot = df_stocks[(df_stocks['涨跌幅'] >= 2) & (df_stocks['涨跌幅'] <= 7)].copy()
    
    # 条件2: 排除 ST / 退市 / 科创板 / 创业板 / 北交所
    before = len(df_hot)
    df_hot = df_hot[~df_hot['名称'].str.contains('ST|退', na=False)]
    # 代码前缀过滤: 科创板688/689, 创业板300/301, 北交所8
    hot_codes = df_hot['代码'].astype(str).str.zfill(6)
    df_hot = df_hot[~hot_codes.str.match(r'^(688|689|300|301|8)')]
    log(f"  全市场: {len(df_stocks)} 只 | 涨跌幅2~7%: {before} 只 | 剔除ST+板块: {len(df_hot)} 只")
    # 多维度排序: 涨跌幅 × 量比 (量价配合优先)
    df_hot['_量比clip'] = df_hot['换手率'].clip(lower=0.5, upper=2.0)
    df_hot['_初评分'] = df_hot['涨跌幅'] * df_hot['_量比clip']
    df_hot = df_hot.sort_values("_初评分", ascending=False)
    
    if len(df_hot) == 0:
        return "❌ 无候选股"
    
    # ─── 2/5: 并行预下载 K 线缓存 ───
    log(f"\n[2/5] 并行预下载 K 线缓存 (数据源: {mgr.current_source})...")
    if mgr.current_source != 'eastmoney':
        log(f"  ⚠️ 东财不可用, 使用备用源 {mgr.current_source}")
    from concurrent.futures import ThreadPoolExecutor, as_completed

    def _prefetch(code):
        from config import CACHE_DIR as _cd
        _p = os.path.join(_cd, f"{code}_日K.csv")
        if os.path.exists(_p):
            try:
                _df = pd.read_csv(_p, nrows=3, parse_dates=['date'])
                if len(_df) > 0 and 'date' in _df.columns:
                    _age = (pd.Timestamp.now() - _df['date'].max()).days
                    if _age < 5:
                        return
            except Exception as e:
                print(f"  ⚠️ pipeline.py: {e}")
                pass
        try:
            from 工具库.数据工具 import 获取日K线数据
            _df = 获取日K线数据(code, 起始日期="20260101")
            if _df is not None and len(_df) >= 60:
                from config import CACHE_DIR as _cd2
                _df.to_csv(os.path.join(_cd2, f"{code}_日K.csv"), index=False)
        except Exception as e:
            print(f"  ⚠️ pipeline.py: {e}")
            pass

    _hot_codes = [str(c).zfill(6) for c in df_hot['代码']]
    _done = 0
    with ThreadPoolExecutor(max_workers=10) as _pool:
        _futs = {_pool.submit(_prefetch, c): c for c in _hot_codes[:200]}
        for f in as_completed(_futs):
            _done += 1
            if _done % 50 == 0:
                log(f"  预下载: {_done}/{min(200, len(_hot_codes))}")
    # ─── 获取板块强度数据（用于评分 + LLM辩论）───
    _top_sectors = []
    try:
        from 工具库.数据工具 import 动态板块扫描
        _board_data = 动态板块扫描()
        _board_list = _board_data.get("板块列表", [])
        _top_sectors = [b.get("名称", "") for b in _board_list[:5]]
        sector_data = {
            "板块强度": "TOP3: " + ", ".join(_top_sectors[:3]),
            "领涨板块": _top_sectors[0] if _top_sectors else "未知",
        }
        log(f"  强势板块: {', '.join(_top_sectors)}")
    except Exception as _e:
        sector_data = {"板块强度": "获取失败", "领涨板块": "未知"}
        log(f"  ⚠️ 板块数据获取失败: {_e}")
    

    # ─── 3/5: 规则 Agent 评分 ───
    log(f"\n[3/5] 规则 Agent + 趋势筛选 (0 LLM)...")
    from 工具库.数据工具 import 计算全部技术指标
    from agents.technical import analyze as tech
    from agents.chip import analyze as chip
    from agents.pattern import analyze as pattern
    from agents.risk import analyze as risk_agent
    
    scored = []
    codes_seen = set()
    skipped = {"趋势不满足": 0, "风控拦截": 0, "ST": before - len(df_hot)}
    
    for _, row in df_hot.iterrows():
        code = str(row['代码']).zfill(6)
        if code in codes_seen:
            continue
        codes_seen.add(code)
        
        sub = _load_kline(code, use_cache=True)
        if sub is None:
            continue
        
        # 条件3: MA5多头 (MA5 > MA10)
        ma5 = sub['close'].rolling(5).mean().iloc[-1]
        ma10 = sub['close'].rolling(10).mean().iloc[-1]
        if not (ma5 > ma10):
            skipped["趋势不满足"] += 1
            continue
        
        # 条件4: 股价站上MA5
        close = sub['close'].iloc[-1]
        if not (close > ma5):
            skipped["趋势不满足"] += 1
            continue
        
        # 条件5: 量比 > 0.8
        vol_ma5 = sub['volume'].rolling(5).mean().iloc[-1]
        current_vol = sub['volume'].iloc[-1]
        vol_ratio = current_vol / vol_ma5 if vol_ma5 > 0 else 0
        if vol_ratio < 0.8:
            skipped["趋势不满足"] += 1
            continue
        
        # 条件6: 3日累计涨幅 > 0 (避免今天突然涨但前面在跌)
        return_3d = (sub['close'].iloc[-1] / sub['close'].iloc[-4] - 1) * 100 if len(sub) >= 4 else 0
        if return_3d <= 0:
            skipped["趋势不满足"] += 1
            continue
        
        # 条件7: MA5斜率 > 0 (MA5还在上升)
        ma5_prev = sub['close'].rolling(5).mean().iloc[-2] if len(sub) >= 2 else ma5
        ma5_slope = ma5 - ma5_prev
        if ma5_slope <= 0:
            skipped["趋势不满足"] += 1
            continue
        
        # 连涨天数 (仅显示,不过滤)
        consecutive = 0
        for i in range(-1, -min(6, len(sub)), -1):
            if sub['close'].iloc[i] > sub['close'].iloc[i-1]:
                consecutive += 1
            else:
                break
        
        ind_df = 计算全部技术指标(sub)
        latest = ind_df.iloc[-1].to_dict()
        prev = ind_df.iloc[-2].to_dict() if len(ind_df) > 1 else ind_df.iloc[-1]
        
        t = tech(sub)
        c = chip(sub)
        p = pattern(df_daily=sub)
        # 获取资金流向用于风控检查
        try:
            from 工具库.数据工具 import 获取资金流向 as _gf
            _flow = _gf(code)
        except Exception as e:
            print(f"  ⚠️ pipeline.py: {e}")
            _flow = {"主力净流入": 0}
        # 资金流向评分（用于评分权重）
        try:
            _net = float(_flow.get("主力净流入", 0))
            if _net > 100000000:
                _fund_score = 85
            elif _net > 0:
                _fund_score = 65
            elif _net > -100000000:
                _fund_score = 35
            else:
                _fund_score = 15
        except Exception as _fe:
            print(f"  ⚠️ pipeline fund: {_fe}")
            _fund_score = 50
        
        # 板块评分（名称匹配强势板块）
        _sector_score = 50
        try:
            _sname = str(row.get("名称", ""))
            for _sec in _top_sectors:
                if _sec and _sec in _sname:
                    _sector_score = 75
                    break
        except:
            _sector_score = 50
        
        r = risk_agent(ind_df, latest, prev, fund_flow=_flow)
        
        if not r.get("trading_allowed", True):
            skipped["风控拦截"] += 1
            continue
        
        score = (
            max(0, (t.get("direction_strength", 0) + 100) / 2) * 0.35 +
            min(100, c.get("cost_concentration", 0)) * 0.25 +
            (75 if p.get("overall_signal") == "看涨" else 50) * 0.15 +
            _fund_score * 0.15 +
            _sector_score * 0.10
        )
        
        # 放量突破加分：量比>2 且涨幅>5% → +15%
        _breakout = vol_ratio > 2.0 and float(row.get('涨跌幅', 0)) > 5
        if _breakout:
            score = min(100, score * 1.15)
        
        scored.append({
            "code": code, "name": row['名称'],
            "change": row['涨跌幅'],
            "price": float(latest.get("close", sub['close'].iloc[-1])),
            "score": round(score, 1),
            "vol_ratio": round(vol_ratio, 2),
            "ma5": round(ma5, 2), "ma10": round(ma10, 2),
            "consecutive_up": consecutive,
            "return_3d": round(return_3d, 1),
            "ma5_slope": round(ma5_slope, 2),
            "breakout": _breakout,
            "technical": t, "chip": c, "pattern": p, "risk": r,
        })
        
        if len(scored) >= 30:
            break
    
    scored.sort(key=lambda x: -x["score"])
    log(f"  通过趋势筛选: {len(scored)} 只")
    log(f"  跳过: {skipped}")
    top_n = scored[:10]
    log(f"  TOP {len(top_n)} 进入 LLM 辩论")
    
    if len(top_n) == 0:
        return "❌ 无可用数据"
    
    # ─── 6/5: 获取数据新鲜度 + 市场情绪 ───
    # 扫描实际缓存目录获取最新日期
    import datetime as _dt
    _kd_all = []
    try:
        from config import CACHE_DIR as _cdir
        for _f in os.listdir(_cdir):
            if _f.endswith('_日K.csv'):
                try:
                    _kdf = pd.read_csv(os.path.join(_cdir, _f), nrows=5, usecols=['date'])
                    _kd_all.append(str(_kdf['date'].max())[:10])
                except Exception as e:
                    print(f"  ⚠️ pipeline.py: {e}")
                    pass
        if _kd_all:
            _kd = max(_kd_all)
            _days = (_dt.date.today() - _dt.datetime.strptime(_kd, "%Y-%m-%d").date()).days
            log(f"  K线数据截止: {_kd} (距今{_days}天)")
    except Exception as _e:
        log(f"  ⚠️ 缓存日期扫描失败: {_e}")
    
    # ─── 6/5: 获取真实市场情绪数据 ───
    try:
        from 工具库.数据工具 import 获取市场情绪数据
        from 工具库.情绪周期 import 判断情绪周期
        _emotion = 获取市场情绪数据()
        _cycle = 判断情绪周期(_emotion)
        sentiment_data = {
            "周期": _cycle.get("周期", "中性"),
            "评分": _cycle.get("评分", 50),
            "涨停家数": int(_emotion.get("涨停家数", 0) or 0),
            "跌停家数": int(_emotion.get("跌停家数", 0) or 0),
            "建议": _cycle.get("建议", ""),
        }
        log(f"  真实情绪: {sentiment_data['周期']} "
             f"(涨停{sentiment_data['涨停家数']} 跌停{sentiment_data['跌停家数']})")
    except Exception as _e:
        sentiment_data = {"周期": "中性", "评分": 50, "涨停家数": 0, "跌停家数": 0, "建议": "数据获取失败"}
        log(f"  ⚠️ 情绪数据获取失败: {_e}")
    
    
    # ─── 4. LLM 辩论 + 分阶段委员会 ───
    log(f"\n[6/5] LLM 角色辩论...")
    from agents.trend_follower import debate as td
    from agents.value_investor import debate as vd
    from agents.sentiment_trader import debate as sd
    from agents.committee import finalize
    
    async def _run_llm():
        loop = asyncio.get_event_loop()
        tasks = []
        for s in top_n:
            tasks.append(loop.run_in_executor(None, _debate_stock, s))
        return await asyncio.gather(*tasks)
    
    def _debate_stock(s):
        # 获取真实资金流向 + 龙虎榜
        try:
            from 工具库.数据工具 import 获取资金流向, 获取龙虎榜数据
            _flow = 获取资金流向(s["code"])
            _longhu = 获取龙虎榜数据(s["code"])
        except Exception as e:
            print(f"  ⚠️ pipeline.py: {e}")
            _flow = {"主力净流入": 0}
            _longhu = {}
        
        # 获取新闻/题材/公告
        try:
            from 工具库.新闻搜索 import 搜索新闻 as _sn
            from 工具库.热点归因 import 获取股票题材 as _gt
            from 工具库.公告检查 import 检查巨潮公告 as _gn
            _news_cnt = len(_sn(s["name"], 3) or [])
            _topics = _gt(s["code"]) or []
            _notice = _gn(s["code"]) or {}
        except Exception as e:
            print(f"  ⚠️ pipeline.py: {e}")
            _news_cnt = 0
            _topics = []
            _notice = {}
        # 获取龙虎榜数据
        try:
            from 工具库.数据工具 import 获取龙虎榜数据
            _lh = 获取龙虎榜数据(s["code"], 5)
        except Exception as e:
            print(f"  ⚠️ pipeline.py: {e}")
            _lh = {"有龙虎榜": False, "知名游资": [], "净买入额": "N/A"}
        # 3 角色辩论（并行）
        t1 = td(technical=s["technical"], chip=s["chip"], pattern=s["pattern"], risk=s["risk"],
                fund_flow=_flow, longhu=_longhu,
                news_count=_news_cnt, topics=_topics, notice=_notice)
        t2 = vd(chip=s["chip"], technical=s["technical"], risk=s["risk"])
        t3 = sd(pattern=s["pattern"], risk=s["risk"],
                sentiment=sentiment_data,
                sector=sector_data,
                longhu=_lh)
        return s, t1, t2, t3
    
    results_raw = asyncio.run(_run_llm())
    
    # 角色辩论后按平均分排序 → 前 8 只进入委员会
    scored_with_llm = []
    for s, t1, t2, t3 in results_raw:
        avg = (t1.get("score", 50) + t2.get("score", 50) + t3.get("score", 50)) / 3
        scored_with_llm.append((avg, s, t1, t2, t3))
    
    scored_with_llm.sort(key=lambda x: -x[0])
    top_for_committee = scored_with_llm[:10]
    
    log(f"\n[6/5] 委员会裁决 (前 8 只)...")
    committee_results = []
    for avg, s, t1, t2, t3 in top_for_committee:
        f = finalize(trend_follower=t1, value_investor=t2, sentiment_trader=t3,
                     technical=s["technical"], chip=s["chip"], pattern=s["pattern"], risk=s["risk"])
        committee_results.append((f["total_score"], s, t1, t2, t3, f))
    
    committee_results.sort(key=lambda x: -x[0])
    top10 = committee_results[:10]
    
    # ─── 5. 报告 ───
    elapsed = round(time.time() - t0, 1)
    llm_calls = len(top_n) * 3 + len(top_for_committee) * 1
    
    log(f"\n{'='*55}")
    log(f"  🏆 新 Agent 选股 TOP {len(top10)} (实时)")
    log(f"{'='*55}")
    
    for i, (_, s, t1, t2, t3, f) in enumerate(top10, 1):
        icon = {"BUY": "🟢", "WATCH": "🟡", "SELL": "🔴"}.get(f["final_signal"], "⚪")
        ex = f["execution"]
        log(f"\n{i:2d}. {icon} {s['code']} {s['name']}")
        log(f"     连涨{s.get('consecutive_up','?')}天 · 3日涨幅{s.get('return_3d','?')}% · MA5斜率{s.get('ma5_slope','?')}")
        log(f"     价格: {s['price']:.2f} ({s['change']:+.2f}%) 量比:{s['vol_ratio']}")
        log(f"     信号: {f['final_signal']} | 评分: {f['total_score']} | {f['consensus']}")
        log(f"     趋势:{t1['stance']}({t1['score']}) "
             f"价值:{t2['stance']}({t2['score']}) "
             f"情绪:{t3['stance']}({t3['score']})")
        log(f"     策略: 止损{ex.get('stop_loss','-')} → 目标{ex.get('target_price','-')} 仓位{ex.get('position','-')}")
    
    log(f"\n{'='*55}")
    log(f"  总计: {len(top10)} 只 · LLM: {llm_calls}次 · 耗时: {elapsed}s")
    log(f"{'='*55}")
    
    return "\n".join(lines)


if __name__ == "__main__":
    print(run())
