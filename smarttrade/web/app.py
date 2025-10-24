from __future__ import annotations

import os
import asyncio
from typing import Any, Dict

from fastapi import FastAPI, HTTPException, Query, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from ..bingx_client import BingXClient


app = FastAPI(title="SmartTrade Web", version="0.2.0")

static_dir = os.path.join(os.path.dirname(__file__), "static")
app.mount("/static", StaticFiles(directory=static_dir), name="static")


@app.get("/")
def index() -> FileResponse:
    index_path = os.path.join(static_dir, "index.html")
    return FileResponse(index_path)


@app.get("/api/ping")
def ping() -> Dict[str, str]:
    return {"status": "ok"}


@app.get("/api/spot/ticker")
def api_spot_ticker(symbol: str = Query(..., description="Ex: BTC-USDT")) -> Any:
    try:
        with BingXClient() as bx:
            data = bx.spot_ticker_24h(symbol)
            return JSONResponse(content=data)
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))


@app.get("/api/swap/ticker")
def api_swap_ticker(symbol: str = Query(..., description="Ex: BTC-USDT")) -> Any:
    try:
        with BingXClient() as bx:
            data = bx.swap_ticker(symbol)
            return JSONResponse(content=data)
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))


@app.get("/api/swap/klines")
def api_swap_klines(
    symbol: str = Query(..., description="Ex: BTC-USDT"),
    interval: str = Query("1m", description="Ex: 1m,5m,15m,1h,4h,1d"),
    limit: int = Query(20, ge=1, le=500, description="Quantidade de candles"),
) -> Any:
    try:
        with BingXClient() as bx:
            data = bx.swap_klines(symbol, interval, limit)
            return JSONResponse(content=data)
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))


@app.websocket("/ws/swap/klines")
async def ws_swap_klines(websocket: WebSocket, symbol: str, interval: str = "1m") -> None:
    """
    WebSocket de streaming de klines (perp).
    Fallback: faz polling nos endpoints reais da BingX e envia diffs/snapshot.
    """
    await websocket.accept()
    last_time: int | None = None

    # Enviar snapshot inicial
    try:
        def fetch_snapshot():
            with BingXClient() as bx:
                return bx.swap_klines(symbol, interval, 100)

        kl = await asyncio.to_thread(fetch_snapshot)
        await websocket.send_json({"type": "snapshot", "data": kl})
        if kl:
            last_time = kl[-1].get("time")
    except Exception as e:
        await websocket.send_json({"type": "error", "message": str(e)})

    # Loop de atualização incremental
    try:
        while True:
            await asyncio.sleep(2.0)

            def fetch_last_two():
                with BingXClient() as bx:
                    return bx.swap_klines(symbol, interval, 2)

            try:
                latest = await asyncio.to_thread(fetch_last_two)
            except Exception as e:
                await websocket.send_json({"type": "error", "message": str(e)})
                continue

            if not latest:
                continue

            cur = latest[-1]
            cur_time = cur.get("time")
            if last_time is None or cur_time > last_time:
                await websocket.send_json({"type": "kline", "data": cur})
                last_time = cur_time
            elif cur_time == last_time:
                # Atualização do candle em formação
                await websocket.send_json({"type": "kline", "data": cur})
    except WebSocketDisconnect:
        return


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("smarttrade.web.app:app", host="0.0.0.0", port=8000, reload=False)
