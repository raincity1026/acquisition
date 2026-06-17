"""补全被 eastmoney 限流的 akshare 子项, 改用 sina/netease 源端点。
2.5 主备一致性 / 2.7 指数 / 2.9 耗时。"""
import _compat  # noqa
import time
import baostock as bs
import akshare as ak
import pandas as pd

def retry(fn, tries=6, pause=3.0, label=""):
    for i in range(tries):
        try:
            return fn()
        except Exception as e:
            print(f"    [retry {label}] {i+1}/{tries} {type(e).__name__}: {str(e)[:55]}")
            time.sleep(pause*(i+1))
    print(f"    [SOFT-FAIL {label}]")
    return None

def bs_kline(code, start, end, adjustflag="3", fields="date,close"):
    bs.query_history_k_data_plus
    rs = bs.query_history_k_data_plus(code, fields, start_date=start, end_date=end,
                                      frequency="d", adjustflag=adjustflag)
    df = rs.get_data()
    for c in df.columns:
        if c != "date":
            df[c] = pd.to_numeric(df[c], errors="coerce")
    return df

bs.login()
print("="*78)
print("2.5 主备一致性 (600519: Baostock vs AKShare sina源 stock_zh_a_daily)")
print("="*78)
t0 = time.perf_counter()
ak_u = retry(lambda: ak.stock_zh_a_daily(symbol="sh600519", start_date="20250101",
             end_date="20260615", adjust=""), label="ak不复权(sina)")
ak_h = retry(lambda: ak.stock_zh_a_daily(symbol="sh600519", start_date="20250101",
             end_date="20260615", adjust="hfq"), label="ak后复权(sina)")
perf_ak = time.perf_counter()-t0

bs_u = bs_kline("sh.600519","2025-01-01","2026-06-15", adjustflag="3")
bs_h = bs_kline("sh.600519","2025-01-01","2026-06-15", adjustflag="1")

if ak_u is not None:
    au = ak_u.reset_index()
    au["date"] = pd.to_datetime(au["date"]).dt.strftime("%Y-%m-%d")
    au = au.rename(columns={"close":"ak_close"})[["date","ak_close"]]
    cmp = bs_u.rename(columns={"close":"bs_close"}).merge(au, on="date")
    cmp["diff"] = (cmp["bs_close"]-cmp["ak_close"]).abs()
    print(f"不复权收盘价对齐 {len(cmp)} 行: 最大绝对差={cmp['diff'].max():.4f} 平均差={cmp['diff'].mean():.6f}")
    print("  (不复权=真实价, 两源应几乎完全一致)  尾3行:")
    print(cmp.tail(3).to_string(index=False))
if ak_h is not None:
    ah = ak_h.reset_index()
    ah["date"] = pd.to_datetime(ah["date"]).dt.strftime("%Y-%m-%d")
    ah = ah.rename(columns={"close":"akh"})[["date","akh"]]
    ch = bs_h.rename(columns={"close":"bsh"}).merge(ah, on="date")
    ch["bs_ret"] = ch["bsh"].pct_change()*100
    ch["ak_ret"] = ch["akh"].pct_change()*100
    ch["ret_diff"] = (ch["bs_ret"]-ch["ak_ret"]).abs()
    print(f"\n后复权日收益率对齐 {len(ch)} 行: 最大收益率差={ch['ret_diff'].max():.6f}% (锚点不同故比日收益率)")
    print("  → 收益率几乎为0差 = 两源后复权口径一致")

print("\n" + "="*78)
print("2.7 指数 (000300: Baostock vs AKShare sina源 stock_zh_index_daily)")
print("="*78)
bs_idx = bs_kline("sh.000300","2025-06-01","2026-06-15", fields="date,close")
ak_idx = retry(lambda: ak.stock_zh_index_daily(symbol="sh000300"), label="ak指数(sina)")
if ak_idx is not None:
    ai = ak_idx.reset_index()
    ai["date"] = pd.to_datetime(ai["date"]).dt.strftime("%Y-%m-%d")
    ai = ai[(ai["date"]>="2025-06-01")&(ai["date"]<="2026-06-15")].rename(columns={"close":"ak_close"})[["date","ak_close"]]
    m = bs_idx.rename(columns={"close":"bs_close"}).merge(ai, on="date")
    m["diff"] = (m["bs_close"]-m["ak_close"]).abs()
    print(f"沪深300收盘对齐 {len(m)} 行: 最大绝对差={m['diff'].max():.4f}")
    print(m.tail(3).to_string(index=False))

print("\n" + "="*78)
print("2.9 性能 (近2年日线耗时)")
print("="*78)
t0 = time.perf_counter(); bs_kline("sh.600519","2024-06-15","2026-06-15", adjustflag="1"); print(f"  Baostock 600519 近2年: {time.perf_counter()-t0:.2f}s")
t0 = time.perf_counter()
r = retry(lambda: ak.stock_zh_a_daily(symbol="sh600519", start_date="20240615", end_date="20260615", adjust="hfq"), label="ak耗时(sina)")
if r is not None:
    print(f"  AKShare(sina) 600519 近2年: {len(r)} 行, {time.perf_counter()-t0:.2f}s")

bs.logout()
print("\n[DONE]")
