import pytest

from app.providers.akshare_provider import AkshareProvider


@pytest.mark.integration
def test_akshare_detail_maotai_market_cap():
    d = AkshareProvider().get_instrument_detail("600519.SH")
    assert d.total_mv is not None and d.total_mv > 0
    assert d.circ_mv is not None and d.circ_mv > 0
