from datetime import date
from decimal import Decimal

import pytest

from app.core.resample import resample
from app.providers.base import Bar


def _bar(
    d: str,
    o: float,
    h: float,
    low: float,
    c: float,
    vol: float | None = 100,
    status: int = 1,
) -> Bar:
    return Bar(
        date=date.fromisoformat(d),
        open=Decimal(str(o)),
        high=Decimal(str(h)),
        low=Decimal(str(low)),
        close=Decimal(str(c)),
        volume=None if vol is None else Decimal(str(vol)),
        amount=None if vol is None else Decimal(str(vol)),
        raw_close=Decimal(str(c)),
        trade_status=status,
    )


# 两个 ISO 周: 06-17~06-19 一周, 06-24 下一周
DAILY = [
    _bar("2024-06-17", 10, 12, 9, 11, 100),
    _bar("2024-06-18", 11, 15, 10, 14, 200),
    _bar("2024-06-19", 14, 16, 8, 9, 150),
    _bar("2024-06-24", 9, 10, 7, 8, 50),
]


def test_resample_weekly_ohlcv() -> None:
    wk = resample(DAILY, "W")
    assert len(wk) == 2
    w1 = wk[0]
    assert w1.open == Decimal("10")  # 周一开
    assert w1.high == Decimal("16")  # 周内最高
    assert w1.low == Decimal("8")  # 周内最低
    assert w1.close == Decimal("9")  # 周末收
    assert w1.volume == Decimal("450")  # 求和
    assert w1.date == date(2024, 6, 19)
    assert wk[1].volume == Decimal("50")


def test_resample_monthly_ohlcv() -> None:
    mo = resample(DAILY, "M")
    assert len(mo) == 1
    m = mo[0]
    assert m.open == Decimal("10")
    assert m.high == Decimal("16")
    assert m.low == Decimal("7")
    assert m.close == Decimal("8")
    assert m.volume == Decimal("500")


def test_resample_excludes_suspended_from_high_low() -> None:
    # 停牌日带极端值, 不应污染周高/低
    bars = [
        _bar("2024-06-17", 10, 12, 9, 11, 100),
        _bar("2024-06-18", 11, 999, 1, 11, None, status=0),  # 停牌占位, 极端 OHLC
        _bar("2024-06-19", 14, 16, 8, 9, 150),
    ]
    wk = resample(bars, "W")
    assert wk[0].high == Decimal("16")
    assert wk[0].low == Decimal("8")
    assert wk[0].volume == Decimal("250")  # 仅正常日


def test_resample_raw_close_is_last_normal() -> None:
    wk = resample(DAILY, "W")
    assert wk[0].raw_close == Decimal("9")


def test_resample_invalid_period() -> None:
    with pytest.raises(ValueError):
        resample(DAILY, "d")


def test_resample_empty() -> None:
    assert resample([], "W") == []
