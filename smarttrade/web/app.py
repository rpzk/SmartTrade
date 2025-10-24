from __future__ import annotations

import os
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from ..bingx_client import BingXClient


app = FastAPI(title="SmartTrade Web", version="0.1.0")

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


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("smarttrade.web.app:app", host="0.0.0.0", port=8000, reload=False)
