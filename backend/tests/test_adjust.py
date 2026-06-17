from datetime import date
from decimal import Decimal

from app.core.adjust import apply_adjust, hfq_to_qfq
from app.providers.base import Bar


def _bar(d: str, ohlc: float, raw_close: float, status: int = 1) -> Bar:
    v = Decimal(str(ohlc))
    return Bar(
        date=date.fromisoformat(d),
        open=v,
        high=v,
        low=v,
        close=v,
        volume=Decimal("100"),
        amount=Decimal("100"),
        raw_close=Decimal(str(raw_close)),
        trade_status=status,
    )


def test_hfq_to_qfq_latest_equals_raw_latest() -> None:
    # k = raw_latest / hfq_latest = 11/110 = 0.1
    out = hfq_to_qfq([Decimal("100"), Decimal("110")], Decimal("11"), Decimal("110"))
    assert out == [Decimal("10"), Decimal("11")]
    assert out[-1] == Decimal("11")  # 前复权最新 == 不复权最新价


def test_apply_adjust_qfq_latest_close_equals_raw_close() -> None:
    # 模拟除权: hfq 是放大序列, raw_close 为真实价
    bars = [_bar("2024-06-18", 10603.8, 1521.5), _bar("2024-06-19", 10677.6, 1501.0)]
    out = apply_adjust(bars, "qfq")
    # 验收 §6.4: qfq 最新日 == 不复权最新价
    assert out[-1].close == bars[-1].raw_close
    # 全局等比缩放, 形状不变(收益率一致)
    ratio_in = bars[1].close / bars[0].close
    ratio_out = out[1].close / out[0].close
    assert ratio_in == ratio_out


def test_apply_adjust_none_each_bar_close_equals_raw_close() -> None:
    bars = [_bar("2024-06-18", 10603.8, 1521.5), _bar("2024-06-19", 10677.6, 1501.0)]
    out = apply_adjust(bars, "none")
    for b in out:
        assert b.close == b.raw_close


def test_apply_adjust_hfq_unchanged() -> None:
    bars = [_bar("2024-06-18", 10603.8, 1521.5)]
    assert apply_adjust(bars, "hfq") == bars


def test_apply_adjust_empty() -> None:
    assert apply_adjust([], "qfq") == []
