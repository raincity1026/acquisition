import pytest

from app.symbols import (
    from_baostock,
    market_of,
    to_akshare,
    to_akshare_daily,
    to_baostock,
)


@pytest.mark.parametrize(
    ("symbol", "bs"),
    [
        ("600519.SH", "sh.600519"),
        ("000001.SZ", "sz.000001"),
        ("000300.SH", "sh.000300"),
        ("301565.SZ", "sz.301565"),
        ("920819.BJ", "bj.920819"),
    ],
)
def test_to_and_from_baostock_roundtrip(symbol: str, bs: str) -> None:
    assert to_baostock(symbol) == bs
    assert from_baostock(bs) == symbol


def test_to_akshare_strips_suffix() -> None:
    assert to_akshare("600519.SH") == "600519"
    assert to_akshare("000001.SZ") == "000001"


def test_to_akshare_daily_prefixes_market() -> None:
    assert to_akshare_daily("600519.SH") == "sh600519"
    assert to_akshare_daily("000001.SZ") == "sz000001"


def test_market_of() -> None:
    assert market_of("600519.SH") == "SH"
    assert market_of("000001.SZ") == "SZ"
    assert market_of("920819.BJ") == "BJ"


@pytest.mark.parametrize("bad", ["600519", "600519.US", "600519.sh", ".SH", "", "abc.SH"])
def test_invalid_symbol_raises(bad: str) -> None:
    with pytest.raises(ValueError):
        to_baostock(bad)


@pytest.mark.parametrize("bad", ["sh600519", "us.600519", "SH.600519", ""])
def test_invalid_baostock_code_raises(bad: str) -> None:
    with pytest.raises(ValueError):
        from_baostock(bad)
