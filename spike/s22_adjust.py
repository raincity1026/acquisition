"""2.2 复权正确性 —— 茅台 不复权/前复权/后复权 三连对比。"""
import sys
import _compat  # noqa: F401  (pandas.append 垫片，必须在 baostock 之前)
import baostock as bs
import pandas as pd

CODE = "sh.600519"
START = "2023-01-01"
END   = "2026-12-31"
FIELDS = "date,open,high,low,close,volume,amount,pctChg"

def pull(adjustflag):
    rs = bs.query_history_k_data_plus(
        CODE, FIELDS, start_date=START, end_date=END,
        frequency="d", adjustflag=adjustflag)
    if rs.error_code != "0":
        raise RuntimeError(f"baostock error {rs.error_code}: {rs.error_msg}")
    df = rs.get_data()
    for c in ["open", "high", "low", "close", "volume", "amount", "pctChg"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    return df

lg = bs.login()
print(f"[login] code={lg.error_code} msg={lg.error_msg}")

# adjustflag: 1=后复权, 2=前复权, 3=不复权
raw = pull("3")   # 不复权
qfq = pull("2")   # 前复权
hfq = pull("1")   # 后复权
bs.logout()

print(f"\n行数: raw={len(raw)} qfq={len(qfq)} hfq={len(hfq)}  日期范围 {raw['date'].iloc[0]} ~ {raw['date'].iloc[-1]}")

# 合并三连，按日期对齐
m = raw[["date", "close", "pctChg"]].rename(columns={"close": "raw_close"})
m = m.merge(qfq[["date", "close"]].rename(columns={"close": "qfq_close"}), on="date")
m = m.merge(hfq[["date", "close"]].rename(columns={"close": "hfq_close"}), on="date")
m = m.reset_index(drop=True)

# 稳健地定位除权日：不复权日收益率 与 后复权(真实)日收益率 出现背离即为除权除息日
m["raw_ret"] = (m["raw_close"] / m["raw_close"].shift(1) - 1) * 100
m["hfq_ret"] = (m["hfq_close"] / m["hfq_close"].shift(1) - 1) * 100
m["ret_gap"] = m["raw_ret"] - m["hfq_ret"]   # ≈ 除权造成的"假"跌幅
cand = m[m["ret_gap"].abs() > 0.5].copy()
print("\n=== 自动识别的除权/除息日（不复权日收益率 与 后复权真实日收益率 背离 > 0.5%）===")
print(cand[["date", "raw_close", "raw_ret", "hfq_ret", "ret_gap"]].to_string(index=False))
print("  解读：raw_ret 为不复权看到的'账面'涨跌，hfq_ret 为真实涨跌；除权日二者背离即'假摔'。")

# 针对每个除权日，打印前后各 3 行
for d in cand["date"].tolist():
    idx = m.index[m["date"] == d]
    if len(idx) == 0:
        continue
    i = idx[0]
    lo, hi = max(0, i - 3), min(len(m), i + 4)
    print(f"\n=== 除权日 {d} 前后 close 三连对比（★=除权当日）===")
    win = m.iloc[lo:hi].copy()
    win["mark"] = ["★" if dd == d else " " for dd in win["date"]]
    print(win[["mark", "date", "raw_close", "qfq_close", "hfq_close", "raw_ret", "hfq_ret"]].to_string(index=False))

# 验证最后一段三者数值关系：最新一天前复权应=真实价(=不复权最新)
last = m.iloc[-1]
print(f"\n=== 最新交易日 {last['date']} ===")
print(f"  不复权 close = {last['raw_close']}")
print(f"  前复权 close = {last['qfq_close']}  (应≈不复权最新真实价)")
print(f"  后复权 close = {last['hfq_close']}")
print(f"  前复权 vs 不复权 最新日差异 = {last['qfq_close'] - last['raw_close']:.4f}")

# 后复权"重复拉取历史值不变"验证：再拉一次 hfq，比对历史 close
bs.login()
hfq2 = pull("1")
bs.logout()
chk = hfq[["date", "close"]].merge(hfq2[["date", "close"]], on="date", suffixes=("_1", "_2"))
maxdiff = (chk["close_1"] - chk["close_2"]).abs().max()
print(f"\n=== 后复权重复拉取稳定性：两次拉取 {len(chk)} 行历史 close 最大差异 = {maxdiff:.8f} ===")
print("  （=0 表示后复权历史值不随时间漂移，可安全入库）")
