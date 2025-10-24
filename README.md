# SmartTrade

Coletor inicial de dados reais da BingX (Spot e Perp) — sem dados simulados ou mockups.

## Requisitos

- Python 3.10+

## Instalação

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
```

## Uso rápido

Com o ambiente ativado, execute:

```bash
# Ticker 24h do par Spot
python -m smarttrade.main spot-ticker BTC-USDT

# Ticker do contrato perpétuo (swap)
python -m smarttrade.main swap-ticker BTC-USDT

# Klines (candles) do perpétuo
python -m smarttrade.main swap-klines BTC-USDT 1m 5
```

Saídas são retornadas em JSON diretamente da API pública da BingX.

## Interface Web (FastAPI)

Para iniciar o servidor web com uma página simples que consome os endpoints reais:

```bash
python -m smarttrade.web.app
```

Acesse em http://localhost:8000 e escolha o símbolo/intervalo. A página faz polling a cada 5s nos endpoints:

- GET /api/spot/ticker?symbol=BTC-USDT
- GET /api/swap/ticker?symbol=BTC-USDT
- GET /api/swap/klines?symbol=BTC-USDT&interval=1m&limit=10

Além disso, há streaming via WebSocket do servidor para klines (sem mock):

- WS /ws/swap/klines?symbol=BTC-USDT&interval=1m

A UI renderiza candles com Chart.js (plugin financial) e atualiza em tempo real.

## Notas

- Alguns endpoints públicos da BingX exigem o parâmetro `timestamp` (ms), mas não requerem assinatura para leitura de market data.
- Endpoints usados:
	- Spot 24h ticker: `/openApi/spot/v1/ticker/24hr`
	- Swap ticker: `/openApi/swap/v2/quote/ticker`
	- Swap klines: `/openApi/swap/v2/quote/klines`

## Próximos passos

- Adicionar WebSocket público para stream de trades/klines em tempo real.
- Unificar formatos de resposta em modelos dataclass/TypedDict.
- Opções de persistência (ex.: CSV/Parquet/SQLite) para backtesting.