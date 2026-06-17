"""2.1 / 2.3 / 2.4 / 2.5 / 2.6 / 2.7 / 2.8 / 2.9 验证。
akshare 接口偶发连接重置，统一用 retry 包一层。"""
import _compat  # noqa: F401
import time, io, contextlib
import baostock as bs
import pandas as pd

pd.set_option("display.width", 200)
pd.set_option("display.max_columns", 30)

def retry(fn, tries=6, pause=3.0, label=""):
    """akshare 接口偶发限流/连接重置; 失败到顶返回 None(软失败), 不中断整段验证。"""
    last = None
    for i in range(tries):
        try:
            return fn()
        except Exception as e:
            last = e
            print(f"    [retry {label}] 第{i+1}/{tries}次失败: {type(e).__name__}: {str(e)[:60]}")
            time.sleep(pause * (i + 1))   # 递增退避
    print(f"    [SOFT-FAIL {label}] 多次重试仍失败, 跳过该 akshare 子项 (baostock 侧不受影响)")
    return None

def bs_kline(code, start, end, adjustflag="3", freq="d",
             fields="date,open,high,low,close,volume,amount,pctChg,tradestatus"):
    rs = bs.query_history_k_data_plus(code, fields, start_date=start, end_date=end,
                                      frequency=freq, adjustflag=adjustflag)
    if rs.error_code != "0":
        raise RuntimeError(f"{rs.error_code}:{rs.error_msg}")
    df = rs.get_data()
    for c in df.columns:
        if c not in ("date",):
            df[c] = pd.to_numeric(df[c], errors="coerce")
    return df

bs.login()
sep = lambda t: print("\n" + "="*78 + f"\n{t}\n" + "="*78)

# ----------------------------------------------------------------------------
sep("2.1 基础连通与字段完整性 (Baostock 600519 近2年)")
df = bs_kline("sh.600519", "2024-06-01", "2026-06-15")
need = ["date","open","high","low","close","volume","amount","pctChg"]
print("字段:", list(df.columns))
print("缺失字段:", [c for c in need if c not in df.columns] or "无")
print(f"行数={len(df)}  空值数=\n{df[need].isna().sum().to_string()}")
print("样例(头3/尾3):")
print(df[need].head(3).to_string(index=False))
print(df[need].tail(3).to_string(index=False))

# ----------------------------------------------------------------------------
sep("2.1b ChiNext/STAR 板块 + 20% 涨跌幅 (300750 宁德时代 / 688981 中芯国际)")
for code, nm in [("sz.300750","宁德时代(创业板)"), ("sh.688981","中芯国际(科创板)")]:
    d = bs_kline(code, "2024-01-01", "2026-06-15", fields="date,close,pctChg")
    mx, mn = d["pctChg"].max(), d["pctChg"].min()
    print(f"  {code} {nm}: 行数={len(d)} 最大单日涨幅={mx:.2f}% 最大跌幅={mn:.2f}% "
          f"(|涨跌|>10.5% 的天数={ (d['pctChg'].abs()>10.5).sum() }  → 证明20%机制)")

# ----------------------------------------------------------------------------
sep("2.1c 新股历史不足 (301565 中仑新材, IPO 2024-06-20; 故意请求2020起)")
d = bs_kline("sz.301565", "2020-01-01", "2026-06-15", fields="date,close")
print(f"  请求区间 2020-01-01~2026-06-15, 实际返回 {len(d)} 行, "
      f"首行={d['date'].iloc[0]} 尾行={d['date'].iloc[-1]}")
print("  → 历史不足时数据源不报错, 只从 IPO 日开始给, 无伪造数据。")

# ----------------------------------------------------------------------------
sep("2.3 停牌处理 (扫描 *ST 股找真实停牌, 对比指数交易日)")
idx = bs_kline("sh.000300", "2024-01-01", "2026-06-15", fields="date,close")
idx_days = set(idx["date"])
st_candidates = ["sh.600053","sh.600079","sh.600145","sz.000040","sz.000056","sz.000605","sh.600095"]
found = None
for code in st_candidates:
    d = bs_kline(code, "2024-01-01", "2026-06-15")
    if len(d)==0 or "tradestatus" not in d.columns:
        print(f"  {code}: 无数据(可能已退市/无该窗口数据), 跳过")
        continue
    halted = d[d["tradestatus"]==0]
    miss = sorted(idx_days - set(d["date"]))
    print(f"  {code}: 返回行数={len(d)} tradestatus=0(停牌占位)行数={len(halted)} "
          f"相对指数缺失交易日数={len(miss)}")
    # 取停牌天数最多的作为展示样本
    if (len(halted)>0 or len(miss)>0):
        if found is None or len(halted) > len(found[2]):
            found = (code, d, halted, miss)
if found:
    code, d, halted, miss = found
    print(f"\n  ★选中 {code} 展示停牌形态:")
    print(f"  Baostock tradestatus=0 占位样例:\n{halted.head(5)[['date','close','volume','tradestatus']].to_string(index=False) if len(halted) else '    (无占位行)'}")
    if miss:
        print(f"  相对指数缺失(跳过)的交易日(前10): {miss[:10]}")
    # akshare 对同一停牌票的形态
    import akshare as ak
    sym = code.split(".")[1]
    ak_df = retry(lambda: ak.stock_zh_a_hist(symbol=sym, period="daily",
                  start_date="20240101", end_date="20260615", adjust=""), label="ak停牌")
    if ak_df is not None:
        ak_days = set(pd.to_datetime(ak_df["日期"]).dt.strftime("%Y-%m-%d"))
        ak_miss = sorted(idx_days - ak_days)
        print(f"  AKShare 返回行数={len(ak_df)} 相对指数缺失交易日数={len(ak_miss)} "
              f"(akshare 对停牌日: {'跳过(不占位)' if ak_miss else '占位'})")

# ----------------------------------------------------------------------------
sep("2.4 周/月聚合 (日线自聚合 vs Baostock 原生周/月线, 600519)")
dd = bs_kline("sh.600519", "2025-01-01", "2026-06-15",
              fields="date,open,high,low,close,volume", adjustflag="1")
dd["date"] = pd.to_datetime(dd["date"])
dd = dd.set_index("date")
wk = dd.resample("W").agg({"open":"first","high":"max","low":"min","close":"last","volume":"sum"}).dropna()
mo = dd.resample("ME").agg({"open":"first","high":"max","low":"min","close":"last","volume":"sum"}).dropna()
print("自聚合周线(尾3行):")
print(wk.tail(3).to_string())
# baostock 原生周线
wk_bs = bs_kline("sh.600519","2025-01-01","2026-06-15", fields="date,open,high,low,close,volume", freq="w", adjustflag="1")
print("\nBaostock 原生周线(尾3行):")
print(wk_bs.tail(3).to_string(index=False))
print("\n自聚合月线(尾3行):")
print(mo.tail(3).to_string())

# ----------------------------------------------------------------------------
sep("2.5 主备一致性 (600519: Baostock vs AKShare)")
import akshare as ak
bs_u = bs_kline("sh.600519","2025-01-01","2026-06-15", fields="date,close")   # 不复权
bs_h = bs_kline("sh.600519","2025-01-01","2026-06-15", fields="date,close", adjustflag="1")  # 后复权
ak_u = retry(lambda: ak.stock_zh_a_hist(symbol="600519", period="daily",
             start_date="20250101", end_date="20260615", adjust=""), label="ak不复权")
ak_h = retry(lambda: ak.stock_zh_a_hist(symbol="600519", period="daily",
             start_date="20250101", end_date="20260615", adjust="hfq"), label="ak后复权")
if ak_u is not None:
    ak_u2 = ak_u.rename(columns={"日期":"date","收盘":"ak_close"})[["date","ak_close"]]
    ak_u2["date"] = pd.to_datetime(ak_u2["date"]).dt.strftime("%Y-%m-%d")
    cmp = bs_u.rename(columns={"close":"bs_close"}).merge(ak_u2, on="date")
    cmp["diff"] = (cmp["bs_close"]-cmp["ak_close"]).abs()
    print(f"不复权收盘价对齐 {len(cmp)} 行: 最大绝对差={cmp['diff'].max():.4f} 平均差={cmp['diff'].mean():.6f}")
    print("  (不复权是真实价, 两源应几乎完全一致)")
    print(cmp.tail(3).to_string(index=False))
if ak_h is not None:
    # 后复权: 两源锚点不同, 比日收益率
    ak_h2 = ak_h.rename(columns={"日期":"date","收盘":"akh"})[["date","akh"]]
    ak_h2["date"] = pd.to_datetime(ak_h2["date"]).dt.strftime("%Y-%m-%d")
    ch = bs_h.rename(columns={"close":"bsh"}).merge(ak_h2, on="date")
    ch["bs_ret"] = ch["bsh"].pct_change()*100
    ch["ak_ret"] = ch["akh"].pct_change()*100
    ch["ret_diff"] = (ch["bs_ret"]-ch["ak_ret"]).abs()
    print(f"\n后复权日收益率对齐 {len(ch)} 行: 最大收益率差={ch['ret_diff'].max():.4f}% (锚点不同故比收益率)")

# ----------------------------------------------------------------------------
sep("2.6 标的列表")
ak_list = retry(lambda: ak.stock_info_a_code_name(), label="ak代码表")
if ak_list is not None:
    print(f"AKShare stock_info_a_code_name: {len(ak_list)} 条, 字段={list(ak_list.columns)}")
    print(ak_list.head(3).to_string(index=False))
bs_all = bs.query_stock_basic().get_data()
bs_stk = bs_all[bs_all["type"]=="1"]
bs_listed = bs_stk[bs_stk["status"]=="1"]
print(f"Baostock query_stock_basic: 全部 {len(bs_all)} 条, 其中股票 {len(bs_stk)} (在市 {len(bs_listed)}), 字段={list(bs_all.columns)}")

# ----------------------------------------------------------------------------
sep("2.7 指数拉取 (000300 沪深300)")
bs_idx = bs_kline("sh.000300","2025-01-01","2026-06-15", fields="date,open,high,low,close,volume,amount")
print(f"Baostock sh.000300: 行数={len(bs_idx)} 区间 {bs_idx['date'].iloc[0]}~{bs_idx['date'].iloc[-1]}")
print(bs_idx.tail(2).to_string(index=False))
ak_idx = retry(lambda: ak.index_zh_a_hist(symbol="000300", period="daily",
               start_date="20250101", end_date="20260615"), label="ak指数")
if ak_idx is not None:
    print(f"AKShare index_zh_a_hist(000300): 行数={len(ak_idx)} 字段={list(ak_idx.columns)[:8]}")
    print(ak_idx.tail(2).to_string(index=False))

# ----------------------------------------------------------------------------
sep("2.8 交易日历")
ak_cal = retry(lambda: ak.tool_trade_date_hist_sina(), label="ak日历")
if ak_cal is not None:
    ak_cal["trade_date"] = pd.to_datetime(ak_cal["trade_date"])
    recent = ak_cal[(ak_cal["trade_date"]>="2026-01-01")&(ak_cal["trade_date"]<="2026-06-15")]
    print(f"AKShare tool_trade_date_hist_sina: 总 {len(ak_cal)} 天, 范围 {ak_cal['trade_date'].min().date()}~{ak_cal['trade_date'].max().date()}")
    # 验证排除周末
    wends = ak_cal[ak_cal["trade_date"].dt.weekday>=5]
    print(f"  含周末天数={len(wends)} (应=0)  2026年内交易日数={len(recent)}")
    print(f"  2026春节附近(2/14~2/22)交易日: {[d.strftime('%m-%d') for d in ak_cal[(ak_cal['trade_date']>='2026-02-14')&(ak_cal['trade_date']<='2026-02-22')]['trade_date']]}")
bs_cal = bs.query_trade_dates(start_date="2026-01-01", end_date="2026-06-15").get_data()
bs_open = bs_cal[bs_cal["is_trading_day"]=="1"]
print(f"Baostock query_trade_dates: 区间内 {len(bs_cal)} 自然日, 其中交易日 {len(bs_open)}")

# ----------------------------------------------------------------------------
sep("2.9 性能 (拉一只票近2年日线耗时)")
for src, fn in [
    ("Baostock 600519", lambda: bs_kline("sh.600519","2024-06-15","2026-06-15", adjustflag="1")),
    ("AKShare 600519", lambda: retry(lambda: ak.stock_zh_a_hist(symbol="600519", period="daily",
        start_date="20240615", end_date="20260615", adjust="hfq"), label="ak耗时")),
]:
    t0 = time.perf_counter()
    r = fn()
    dt = time.perf_counter()-t0
    if r is not None:
        print(f"  {src}: {len(r)} 行, 耗时 {dt:.2f}s")

bs.logout()
print("\n[DONE]")
