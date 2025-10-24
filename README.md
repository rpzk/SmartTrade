# SmartTrade

SmartTrade é uma aplicação de trading que **prioriza dados da BingX**.

## Prioridade de Dados

Este sistema foi projetado com a seguinte prioridade de fontes de dados:

1. **BingX** (Prioridade: 100) - FONTE PRIMÁRIA
2. **Binance** (Prioridade: 50) - Fonte secundária/fallback

### Por que BingX é Prioritária?

Os dados provenientes da BingX são sempre preferidos quando disponíveis. O sistema automaticamente:

- ✅ Usa dados da BingX quando disponíveis
- ✅ Faz fallback para Binance se BingX estiver indisponível
- ✅ Mantém a ordem de prioridade independente da ordem de inicialização

## Instalação

```bash
# Clone o repositório
git clone https://github.com/rpzk/SmartTrade.git
cd SmartTrade

# Instale as dependências
pip install -r requirements.txt

# Instale o pacote em modo desenvolvimento
pip install -e .
```

## Uso

### Exemplo Básico

```python
from smarttrade import DataAggregator, BingXExchange, BinanceExchange

# Inicializar exchanges
bingx = BingXExchange()
binance = BinanceExchange()

# Criar agregador (ordem não importa, BingX sempre será prioritária)
aggregator = DataAggregator([binance, bingx])

# Obter ticker - sempre retorna BingX quando disponível
ticker = aggregator.get_ticker("BTC-USDT")
print(f"Fonte: {ticker['source']}")  # Output: "Fonte: BingX"
print(f"Preço: {ticker['price']}")
```

### Executar Exemplo

```bash
python example.py
```

## Testes

Execute os testes para verificar o comportamento de priorização:

```bash
# Executar todos os testes
pytest

# Executar com cobertura
pytest --cov=smarttrade --cov-report=html

# Executar testes específicos de prioridade
pytest tests/test_data_aggregator.py::TestDataAggregatorPriority -v
```

## Arquitetura

```
src/smarttrade/
├── __init__.py
├── data_aggregator.py      # Lógica de priorização
└── exchanges/
    ├── __init__.py
    ├── base.py              # Interface base
    ├── bingx.py             # BingX (Prioridade 100)
    └── binance.py           # Binance (Prioridade 50)
```

### Como a Priorização Funciona

1. Cada exchange tem um valor de `priority` (maior = mais prioritária)
2. O `DataAggregator` ordena exchanges por prioridade automaticamente
3. Ao buscar dados, o agregador tenta cada exchange em ordem de prioridade
4. O primeiro resultado disponível é retornado (BingX primeiro)

## Características

- ✅ **Priorização Automática**: BingX sempre primeiro
- ✅ **Fallback Automático**: Usa Binance se BingX indisponível
- ✅ **Extensível**: Fácil adicionar novas exchanges
- ✅ **Testado**: Testes completos verificam comportamento de prioridade
- ✅ **Tipado**: Type hints para melhor IDE support

## Licença

MIT