"""对齐 + 归一化的纯逻辑（无 DB/网络）。"""

from datetime import date
from decimal import Decimal

from app.core.align import align
from app.core.normalize import default_base_date, normalize
from app.providers.base import Bar


def _bar(d: date, close: float, status: int = 1) -> Bar:
    v = Decimal(str(close))
    return Bar(
        date=d,
        open=v,
        high=v,
        low=v,
        close=v,
        volume=Decimal("1"),
        amount=Decimal("1"),
        raw_close=v,
        trade_status=status,
    )


D = [date(2024, 1, d) for d in (2, 3, 4, 5)]  # 统一交易日轴


def test_align_fills_gap_and_suspension_and_pre_listing() -> None:
    a = [_bar(D[0], 10), _bar(D[1], 11), _bar(D[3], 12)]  # D[2] 整天缺(超长停牌)
    b = [_bar(D[1], 20), _bar(D[2], 99, status=0), _bar(D[3], 22)]  # D[0] 上市前; D[2] 停牌占位
    out = align({"A": a, "B": b}, D)

    # A: 缺口 D[2] 用前值(11)横线填充
    assert [None if x is None else float(x.close) for x in out["A"]] == [10, 11, 11, 12]
    # B: 上市前留空; 停牌日 D[2] 用前值(20)填充, 不被占位价 99 污染
    assert out["B"][0] is None
    assert [None if x is None else float(x.close) for x in out["B"]] == [None, 20, 20, 22]


def test_default_base_date_is_earliest_common_day() -> None:
    # A 从 D[0] 起, B 从 D[1] 起 → 最早共同日 = D[1]
    aligned = align({"A": [_bar(D[0], 10), _bar(D[1], 11)], "B": [_bar(D[1], 20)]}, D[:2])
    assert default_base_date(aligned, D[:2]) == D[1]


def test_normalize_cumulative_pct_from_base() -> None:
    aligned = align({"A": [_bar(D[0], 10), _bar(D[1], 11), _bar(D[2], 12)]}, D[:3])
    series = normalize(aligned, D[:3], D[0])
    assert series["A"].values == [0.0, 10.0, 20.0]  # (c/10-1)*100
    assert series["A"].latest_pct == 20.0


def test_normalize_late_listed_starts_at_own_first_day() -> None:
    # base=D[0], 但 B 在 D[1] 才上市 → B 在 D[0] 为 null, 从 D[1] 自身 0% 起
    aligned = align(
        {"A": [_bar(D[0], 10), _bar(D[1], 11)], "B": [_bar(D[1], 20), _bar(D[2], 22)]},
        D[:3],
    )
    series = normalize(aligned, D[:3], D[0])
    assert series["A"].values == [0.0, 10.0, 10.0]  # D[2] 无数据→前值填充→pct 不变
    assert series["B"].values[0] is None  # base 日尚未上市
    assert series["B"].values[1] == 0.0  # 自身起点 0%
    assert series["B"].values[2] == 10.0  # (22/20-1)*100


def test_normalize_blanks_before_base_date() -> None:
    aligned = align({"A": [_bar(D[0], 10), _bar(D[1], 11), _bar(D[2], 12)]}, D[:3])
    series = normalize(aligned, D[:3], D[1])  # base = 第二天
    assert series["A"].values[0] is None  # 基准日之前留空
    assert series["A"].values[1] == 0.0
    assert series["A"].values[2] == round((12 / 11 - 1) * 100, 4)
