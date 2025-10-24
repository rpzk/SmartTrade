import os
import time
import pytest

from smarttrade.bingx_client import BingXClient

pytestmark = pytest.mark.integration


@pytest.mark.timeout(20)
def test_spot_ticker_live_btc_usdt():
    if os.getenv("RUN_LIVE", "1") != "1":
        pytest.skip("RUN_LIVE != 1")
    with BingXClient() as bx:
        data = bx.spot_ticker_24h("BTC-USDT")
        assert isinstance(data, dict)
        for key in ("symbol", "lastPrice", "highPrice", "lowPrice"):
            assert key in data


@pytest.mark.timeout(20)
def test_swap_klines_live_small():
    if os.getenv("RUN_LIVE", "1") != "1":
        pytest.skip("RUN_LIVE != 1")
    with BingXClient() as bx:
        kl = bx.swap_klines("BTC-USDT", "1m", 3)
        assert isinstance(kl, list)
        assert len(kl) >= 1
        k = kl[-1]
        for key in ("open", "close", "high", "low", "time"):
            assert key in k
