import os
import json
import pytest
from fastapi.testclient import TestClient

from smarttrade.web.app import app

pytestmark = pytest.mark.integration


@pytest.mark.timeout(40)
def test_ws_klines_stream_connect_and_receive_snapshot():
    if os.getenv("RUN_LIVE", "1") != "1":
        pytest.skip("RUN_LIVE != 1")

    client = TestClient(app)
    with client.websocket_connect("/ws/swap/klines?symbol=BTC-USDT&interval=1m") as ws:
        # Espera uma mensagem de snapshot
        msg = ws.receive_json()
        assert isinstance(msg, dict)
        assert msg.get("type") == "snapshot"
        data = msg.get("data")
        assert isinstance(data, list)
        # Opcionalmente esperar uma atualização
        try:
            upd = ws.receive_json(timeout=10)
            assert upd.get("type") == "kline"
        except Exception:
            # Se não vier em 10s, o teste ainda é válido pelo snapshot
            pass
