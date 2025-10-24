# SmartTrade

**Cliente moderno para API da BingX** com suporte a dados reais de Spot e Perpétuos (Swap), sem mockups.

## 🚀 Features

- ✅ **Cliente HTTP robusto** com retry automático e backoff exponencial
- ✅ **Rate limiting inteligente** para evitar bans da API
- ✅ **Logging estruturado** para debugging e monitoramento
- ✅ **Cache em memória** para reduzir chamadas redundantes
- ✅ **Validação de dados** com Pydantic
- ✅ **WebSocket streaming** com polling otimizado
- ✅ **Testes abrangentes** (unitários e de integração)
- ✅ **Interface web** com gráficos em tempo real
- ✅ **Configuração via environment variables**

## 📋 Requisitos

- Python 3.10+

## 🔧 Instalação

```bash
# Clone o repositório
git clone <repo-url>
cd SmartTrade

# Crie ambiente virtual
python3 -m venv .venv
source .venv/bin/activate  # Linux/Mac
# ou
.venv\Scripts\activate  # Windows

# Instale dependências
pip install -r requirements.txt
```

## ⚙️ Configuração

Copie o arquivo de exemplo e ajuste as variáveis conforme necessário:

```bash
cp .env.example .env
```

Variáveis disponíveis em `.env`:

```env
# API BingX
BINGX_BASE_URL=https://open-api.bingx.com
BINGX_TIMEOUT=10.0
BINGX_MAX_RETRIES=3
BINGX_RATE_LIMIT_CALLS=100
BINGX_RATE_LIMIT_PERIOD=60

# Aplicação
LOG_LEVEL=INFO
CACHE_TTL_SECONDS=5

# Servidor Web
WEB_HOST=0.0.0.0
WEB_PORT=8000
```

## 💻 Uso rápido

### CLI (Command Line Interface)

Com o ambiente ativado, execute:

```bash
# Ticker 24h do par Spot
python -m smarttrade.main spot-ticker BTC-USDT

# Ticker do contrato perpétuo (swap)
python -m smarttrade.main swap-ticker BTC-USDT

# Klines (candles) do perpétuo
python -m smarttrade.main swap-klines BTC-USDT 1m 5
```

### Uso Programático

```python
from smarttrade import BingXClient, BingXConfig

# Usar com configuração padrão
with BingXClient() as client:
    ticker = client.spot_ticker_24h("BTC-USDT")
    print(ticker)

# Ou com configuração customizada
config = BingXConfig(timeout=15.0, max_retries=5)
with BingXClient(config) as client:
    klines = client.swap_klines("ETH-USDT", "5m", 20)
    print(f"Obtidos {len(klines)} candles")
```

## 🌐 Interface Web (FastAPI)

Para iniciar o servidor web com interface gráfica:

```bash
python -m smarttrade.web.app
```

Acesse em **http://localhost:8000**

### Endpoints da API

A interface web expõe os seguintes endpoints REST:

- `GET /api/health` - Health check com métricas
- `GET /api/ping` - Ping simples
- `GET /api/spot/ticker?symbol=BTC-USDT` - Ticker spot 24h
- `GET /api/swap/ticker?symbol=BTC-USDT` - Ticker perpétuo
- `GET /api/swap/klines?symbol=BTC-USDT&interval=1m&limit=20` - Klines (salvos automaticamente)
- `GET /api/history/klines?symbol=BTC-USDT&interval=1m&limit=100` - Histórico de klines do banco local
- `GET /api/history/stats?symbol=BTC-USDT&interval=1m` - Estatísticas do histórico armazenado
- `GET /metrics` - Métricas Prometheus (para monitoramento)

### WebSocket

- `WS /ws/swap/klines?symbol=BTC-USDT&interval=1m` - Streaming de klines em tempo real

A UI renderiza candles com Chart.js (plugin financial) e atualiza automaticamente.

## 🧪 Testes

### Testes Unitários

Execute os testes unitários (sem chamadas à API real):

```bash
pytest -v -m "not integration"
```

### Testes de Integração

Para executar testes de integração (fazem chamadas reais à BingX):

```bash
RUN_LIVE=1 pytest -v -m integration
```

### Cobertura de Testes

```bash
pytest --cov=smarttrade --cov-report=html
```

## 📚 Arquitetura

### Estrutura do Projeto

```
smarttrade/
├── __init__.py           # Exports principais
├── bingx_client.py       # Cliente HTTP com retry e rate limiting
├── config.py             # Configurações via Pydantic Settings
├── models.py             # Modelos de validação de dados
├── storage.py            # Persistência SQLite para histórico
├── main.py              # CLI para uso via terminal
└── web/
    ├── app.py           # FastAPI application
    └── static/
        └── index.html   # Interface web

tests/
├── conftest.py                    # Configuração do pytest
├── test_bingx_client_unit.py     # Testes unitários
├── test_bingx_client_live.py     # Testes de integração
└── test_ping.py                  # Teste simples
```

### Componentes Principais

#### BingXClient

Cliente HTTP principal com:
- Retry automático (3 tentativas por padrão)
- Rate limiting configurável (100 calls/60s padrão)
- Connection pooling para melhor performance
- Logging estruturado para debugging
- Validação de parâmetros

#### Cache

Sistema de cache em memória com TTL configurável:
- Reduz chamadas redundantes à API
- Cleanup automático de entradas expiradas
- TTL padrão de 5 segundos

#### WebSocket Streaming

Streaming otimizado de klines:
- Polling dinâmico baseado no intervalo (1m = 5s, 1h = 60s, etc)
- Snapshot inicial + updates incrementais
- Reconexão automática em caso de erro

#### Persistência de Dados

Sistema de storage SQLite integrado:
- Salva automaticamente todos os klines consultados
- Endpoints de histórico para consultar dados locais
- Estatísticas de armazenamento
- Ideal para análises e backtesting sem chamadas adicionais à API

#### Observabilidade

Métricas Prometheus exportadas em `/metrics`:
- `smarttrade_http_requests_total` - Total de requisições HTTP
- `smarttrade_http_request_duration_seconds` - Latência das requisições
- `smarttrade_cache_hits_total` / `smarttrade_cache_misses_total` - Performance do cache
- `smarttrade_active_websockets` - Conexões WebSocket ativas

## 📖 Endpoints da BingX Utilizados

### Spot
- `/openApi/spot/v1/ticker/24hr` - Estatísticas 24h

### Swap (Perpétuos)
- `/openApi/swap/v2/quote/ticker` - Ticker atual
- `/openApi/swap/v2/quote/klines` - Candles históricos

## 🔒 Tratamento de Erros

O cliente distingue entre diferentes tipos de erro:

```python
from smarttrade import BingXClient, BingXError, BingXAPIError

try:
    with BingXClient() as client:
        data = client.spot_ticker_24h("INVALID-SYMBOL")
except BingXAPIError as e:
    # Erro retornado pela API da BingX
    print(f"API Error {e.code}: {e.message}")
except BingXError as e:
    # Erro de rede ou HTTP
    print(f"Request Error: {e}")
except ValueError as e:
    # Validação de parâmetros
    print(f"Invalid parameter: {e}")
```

## 🚧 Próximos Passos

- [ ] Suporte a endpoints privados (autenticação com API key)
- [ ] Persistência de dados (SQLite/PostgreSQL)
- [ ] Indicadores técnicos integrados
- [ ] Backtesting framework
- [ ] Estratégias de trading automatizadas
- [ ] Dashboard com métricas Prometheus
- [ ] Container Docker otimizado

## 📄 Licença

MIT

## 🤝 Contribuindo

Contribuições são bem-vindas! Por favor:

1. Fork o projeto
2. Crie uma branch para sua feature (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request