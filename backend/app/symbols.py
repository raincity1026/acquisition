"""标的代码统一规范与各数据源转换。

内部统一格式：``{code}.{market}``，code 为 6 位数字，market ∈ {SH, SZ, BJ}。
指数同形，如 ``000300.SH``。未来多市场（``AAPL.US`` / ``00700.HK``）由后缀路由。
"""

import re

_MARKETS = ("SH", "SZ", "BJ")
_SYMBOL_RE = re.compile(r"^(\d{6})\.(SH|SZ|BJ)$")
_BAOSTOCK_RE = re.compile(r"^(sh|sz|bj)\.(\d{6})$")


def market_of(symbol: str) -> str:
    """返回内部 symbol 的市场后缀（SH/SZ/BJ）。非法格式抛 ValueError。"""
    m = _SYMBOL_RE.match(symbol)
    if m is None:
        raise ValueError(f"非法标的代码: {symbol!r}（应形如 600519.SH）")
    return m.group(2)


def to_baostock(symbol: str) -> str:
    """``600519.SH`` -> ``sh.600519``。"""
    m = _SYMBOL_RE.match(symbol)
    if m is None:
        raise ValueError(f"非法标的代码: {symbol!r}（应形如 600519.SH）")
    code, market = m.group(1), m.group(2)
    return f"{market.lower()}.{code}"


def from_baostock(bs_code: str) -> str:
    """``sh.600519`` -> ``600519.SH``。"""
    m = _BAOSTOCK_RE.match(bs_code)
    if m is None:
        raise ValueError(f"非法 Baostock 代码: {bs_code!r}（应形如 sh.600519）")
    market, code = m.group(1), m.group(2)
    return f"{code}.{market.upper()}"


def to_akshare(symbol: str) -> str:
    """``600519.SH`` -> ``600519``（AKShare 多数接口用纯 code）。"""
    m = _SYMBOL_RE.match(symbol)
    if m is None:
        raise ValueError(f"非法标的代码: {symbol!r}（应形如 600519.SH）")
    return m.group(1)


def to_akshare_daily(symbol: str) -> str:
    """``600519.SH`` -> ``sh600519``（AKShare ``stock_zh_a_daily`` 用带前缀的格式）。"""
    m = _SYMBOL_RE.match(symbol)
    if m is None:
        raise ValueError(f"非法标的代码: {symbol!r}（应形如 600519.SH）")
    code, market = m.group(1), m.group(2)
    return f"{market.lower()}{code}"
