import argparse
import json
from typing import Any

from .bingx_client import BingXClient


def pretty(obj: Any) -> str:
    return json.dumps(obj, ensure_ascii=False, indent=2)


def run() -> None:
    parser = argparse.ArgumentParser(description="SmartTrade - Coleta de dados reais da BingX (sem mockups)")
    sub = parser.add_subparsers(dest="cmd", required=True)

    # Spot 24h ticker
    p_spot_ticker = sub.add_parser("spot-ticker", help="Ticker 24h Spot")
    p_spot_ticker.add_argument("symbol", help="Par, ex: BTC-USDT")

    # Swap ticker
    p_swap_ticker = sub.add_parser("swap-ticker", help="Ticker Swap (perp)")
    p_swap_ticker.add_argument("symbol", help="Par, ex: BTC-USDT")

    # Swap klines
    p_swap_kl = sub.add_parser("swap-klines", help="Klines Swap (perp)")
    p_swap_kl.add_argument("symbol", help="Par, ex: BTC-USDT")
    p_swap_kl.add_argument("interval", default="1m", nargs="?", help="Intervalo: 1m,5m,15m,1h,4h,1d...")
    p_swap_kl.add_argument("limit", type=int, default=10, nargs="?", help="Quantidade de candles (max típico 100)")

    args = parser.parse_args()

    with BingXClient() as bx:
        if args.cmd == "spot-ticker":
            data = bx.spot_ticker_24h(args.symbol)
            print(pretty(data))
        elif args.cmd == "swap-ticker":
            data = bx.swap_ticker(args.symbol)
            print(pretty(data))
        elif args.cmd == "swap-klines":
            data = bx.swap_klines(args.symbol, args.interval, args.limit)
            print(pretty(data))
        else:
            parser.error("Comando desconhecido")


if __name__ == "__main__":
    run()
