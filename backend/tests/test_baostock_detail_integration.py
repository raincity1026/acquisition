import pytest

from app.providers.baostock_provider import BaostockProvider


@pytest.mark.integration
def test_baostock_detail_maotai():
    d = BaostockProvider().get_instrument_detail("600519.SH")
    assert d.industry is not None
    assert d.pe_ttm is not None and d.pe_ttm > 0
    assert d.pb_mrq is not None and d.pb_mrq > 0
