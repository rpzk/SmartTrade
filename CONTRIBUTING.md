# Guia de Contribuição / Contributing Guide

## 🚨 Regra #1: Sem Dados Simulados

**A regra mais importante deste projeto:**

> **NUNCA** adicione, commit ou use dados simulados, mockados ou fictícios no código de produção.

Antes de fazer qualquer contribuição, leia atentamente [DATA_POLICY.md](DATA_POLICY.md).

---

## Como Contribuir

### 1. Validação Obrigatória

Antes de fazer commit, execute:

```bash
python3 validate_no_mock_data.py
```

Este script verifica se seu código viola a política de dados reais.

### 2. Diretrizes de Código

#### ✅ BOM - Usando Dados Reais

```python
# Correto: buscar dados da API BingX
def get_market_price(symbol):
    response = bingx_api.get_price(symbol)
    return response['data']['price']
```

#### ❌ MAU - Usando Dados Simulados

```python
# ERRADO: NÃO faça isso!
def get_market_price(symbol):
    # Dados mockados - PROIBIDO
    mock_prices = {
        'BTC-USDT': 45000.00,
        'ETH-USDT': 3000.00
    }
    return mock_prices.get(symbol, 0)
```

### 3. Tratamento de Erros

Quando a API falhar, **NÃO** use fallback para dados fictícios:

#### ✅ BOM

```python
def get_price(symbol):
    try:
        return bingx_api.get_price(symbol)
    except APIError as e:
        # Retornar erro claro
        return {'error': 'API indisponível', 'message': str(e)}
```

#### ❌ MAU

```python
def get_price(symbol):
    try:
        return bingx_api.get_price(symbol)
    except APIError:
        # ERRADO: não use dados fictícios como fallback
        return {'price': 50000.00}  # PROIBIDO!
```

### 4. Testes

Para testes unitários, use fixtures claramente identificadas:

```python
# test_trading.py
import pytest

@pytest.fixture
def mock_api_response():
    """Fixture para teste - CLARAMENTE identificado como teste"""
    return {
        'price': 45000.00,
        'timestamp': 1234567890,
        '_test_fixture': True  # Marca clara
    }

def test_price_parsing(mock_api_response):
    # Use fixtures apenas em testes
    result = parse_price(mock_api_response)
    assert result > 0
```

### 5. Documentação

Ao documentar exemplos, deixe claro que são exemplos:

```python
def get_ticker(symbol):
    """
    Obtém dados do ticker.
    
    Exemplo de resposta da API:
    {
        'symbol': 'BTC-USDT',
        'price': 45000.00  # Exemplo ilustrativo apenas
    }
    """
    return bingx_api.get_ticker(symbol)
```

### 6. Checklist de PR

Antes de abrir um Pull Request:

- [ ] Li e entendi [DATA_POLICY.md](DATA_POLICY.md)
- [ ] Executei `python3 validate_no_mock_data.py` sem erros
- [ ] Não há dados hardcoded de preços/volumes
- [ ] Não há geradores de dados aleatórios para mercado
- [ ] Tratamento de erros não usa fallback para dados fictícios
- [ ] Testes usam fixtures claramente marcadas
- [ ] Documentação indica claramente o que são exemplos

---

## 🌍 English Version

### Rule #1: No Simulated Data

**The most important rule of this project:**

> **NEVER** add, commit, or use simulated, mocked, or fictitious data in production code.

Before contributing, carefully read [DATA_POLICY.md](DATA_POLICY.md).

### Validation

Before committing, run:

```bash
python3 validate_no_mock_data.py
```

### PR Checklist

Before opening a Pull Request:

- [ ] Read and understood [DATA_POLICY.md](DATA_POLICY.md)
- [ ] Ran `python3 validate_no_mock_data.py` without errors
- [ ] No hardcoded price/volume data
- [ ] No random data generators for market simulation
- [ ] Error handling doesn't use fallback to fictitious data
- [ ] Tests use clearly marked fixtures
- [ ] Documentation clearly indicates what are examples

---

## 📞 Dúvidas / Questions

Se tiver dúvidas sobre se algo viola a política de dados:

1. Consulte [DATA_POLICY.md](DATA_POLICY.md)
2. Execute o validador: `python3 validate_no_mock_data.py`
3. Em caso de dúvida, pergunte antes de fazer commit

**Em caso de dúvida, sempre prefira dados reais da API!**
