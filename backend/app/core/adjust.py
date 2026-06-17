"""复权换算。

入库存的是**后复权** OHLC + **不复权** ``raw_close``（两者历史值都不随新除权变动，
spike 实测重复拉取差 0）。展示时按需换算：

- ``hfq``：原样（已是后复权）。
- ``qfq``：前复权"钉住今天"——全局乘常数 ``k = raw_close_latest / hfq_close_latest``，
  故最新日换算后 == ``raw_close_latest``（真实价）。同一天内 OHLC 同比例缩放，曲线形状
  （日收益率）不变。
- ``none``：不复权——逐 bar 用 ``k_t = raw_close_t / hfq_close_t`` 还原当日真实 OHLC。
"""

from dataclasses import replace
from decimal import Decimal

from app.providers.base import Bar


def hfq_to_qfq(
    hfq_closes: list[Decimal], raw_close_latest: Decimal, hfq_close_latest: Decimal
) -> list[Decimal]:
    """后复权 close 序列 → 前复权 close 序列。

    k 用最新交易日的值（数据须已更新到最新）。
    """
    k = raw_close_latest / hfq_close_latest
    return [c * k for c in hfq_closes]


def _scale_ohlc(bar: Bar, k: Decimal) -> Bar:
    return replace(bar, open=bar.open * k, high=bar.high * k, low=bar.low * k, close=bar.close * k)


def apply_adjust(bars: list[Bar], adjust: str) -> list[Bar]:
    """把后复权 bars 换算为指定复权口径。``adjust`` ∈ {'hfq','qfq','none'}。"""
    if adjust == "hfq" or not bars:
        return bars
    if adjust == "qfq":
        k = bars[-1].raw_close / bars[-1].close
        return [_scale_ohlc(b, k) for b in bars]
    if adjust == "none":
        return [_scale_ohlc(b, b.raw_close / b.close) for b in bars]
    raise ValueError(f"未知复权口径: {adjust!r}（应为 hfq/qfq/none）")
