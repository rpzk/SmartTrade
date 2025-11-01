# Guia de Análise Multi-Timeframe

## Como Descobrir os Timeframes e Indicadores Mais Respeitados

Este guia explica como usar a análise multi-timeframe para descobrir **quais timeframes o ativo respeita mais** e **qual indicador SMC é mais confiável**.

---

## 🎯 Endpoints Disponíveis

### 1. Quick Scan (Scan Rápido)
**Analisa TODOS os timeframes padrão automaticamente**

```bash
GET /api/multi-timeframe/quick-scan?symbol=BTC-USDT&risk_reward=2.0
```

**O que faz:**
- Testa automaticamente: 1m, 5m, 15m, 30m, 1h, 4h, 1d
- Analisa Order Blocks, Fair Value Gaps e Fibonacci em cada timeframe
- Retorna o melhor timeframe e indicador

**Exemplo de uso:**
```bash
curl "http://localhost:8000/api/multi-timeframe/quick-scan?symbol=BTC-USDT"
```

**Use quando:** Você quer uma resposta rápida sobre qual timeframe operar

---

### 2. Análise Customizada
**Analisa timeframes específicos com mais controle**

```bash
GET /api/multi-timeframe/analyze?symbol=BTC-USDT&timeframes=15m,1h,4h&limit=500&risk_reward=2.0
```

**Parâmetros:**
- `symbol`: Par de negociação (ex: BTC-USDT)
- `timeframes`: Timeframes separados por vírgula (ex: 1m,5m,15m)
- `limit`: Quantidade de candles para analisar (100-1440, padrão: 500)
- `risk_reward`: Razão risco/recompensa (1.0-5.0, padrão: 2.0)

**Exemplo:**
```bash
curl "http://localhost:8000/api/multi-timeframe/analyze?symbol=BTC-USDT&timeframes=15m,1h,4h&limit=300"
```

**Use quando:** Você quer testar timeframes específicos ou usar mais dados

---

### 3. Ranking de Indicador Específico
**Descobre em quais timeframes um indicador funciona melhor**

```bash
GET /api/indicator-ranking/Fair-Value-Gap?symbol=BTC-USDT&timeframes=15m,1h,4h
```

**Indicadores disponíveis:**
- `Order-Block` (ou `orderblock`)
- `Fair-Value-Gap` (ou `fvg`)
- `Fibonacci` (ou `fibonacci`)

**Exemplo:**
```bash
curl "http://localhost:8000/api/indicator-ranking/Order-Block?symbol=BTC-USDT"
```

**Use quando:** Você já tem um indicador favorito e quer saber qual timeframe usar

---

## 📊 Como Interpretar os Resultados

### Estrutura do Relatório

```json
{
  "symbol": "BTC-USDT",
  "best_timeframe": {
    "timeframe": "1h",
    "respect_rate": 67.5,  // Taxa de respeito (win rate médio)
    "total_score": 65.3,   // Score ponderado (0-100)
    "best_indicator": {
      "indicator_name": "Fair Value Gap",
      "win_rate": 70.5,
      "total_trades": 45,
      "profit_factor": 2.3,
      "score": 75.2
    }
  },
  "best_overall_indicator": {
    "indicator_name": "Order Block",
    "timeframe": "4h",
    "win_rate": 72.0,
    "score": 78.5
  },
  "recommendations": [
    "✅ Opere prioritariamente no timeframe 1h (taxa de respeito: 67.5%)",
    "✅ Use Fair Value Gap como indicador principal no 1h (win rate: 70.5%)",
    "⚠️ Evite operar nos timeframes: 1m, 5m - Baixa taxa de respeito"
  ]
}
```

---

## 🔍 Métricas Explicadas

### 1. **Respect Rate (Taxa de Respeito)**
- **O que é:** Porcentagem média de win rate ponderada pelos scores dos indicadores
- **Interpretação:**
  - ≥ 70%: **EXCELENTE** - Timeframe muito confiável
  - 50-70%: **BOM** - Timeframe adequado para trading
  - 30-50%: **REGULAR** - Use com cautela
  - < 30%: **RUIM** - Evite operar neste timeframe

### 2. **Score de Confiabilidade (0-100)**
Calculado com base em:
- **Win Rate (40%)**: Taxa de acerto das operações
- **Profit Factor (30%)**: Razão lucro/prejuízo
- **Número de Trades (15%)**: Mais trades = mais dados = mais confiável
- **Max Drawdown (15%)**: Quanto menor, melhor

**Interpretação:**
- ≥ 80: Confiança **Muito Alta**
- 60-80: Confiança **Alta**
- 40-60: Confiança **Média**
- 20-40: Confiança **Baixa**
- < 20: Confiança **Muito Baixa**

### 3. **Win Rate**
- Porcentagem de trades vencedores
- Não é o único fator! Um indicador com 60% WR mas PF=3.0 é melhor que 70% WR com PF=1.2

### 4. **Profit Factor**
- Razão entre lucros e perdas totais
- > 2.0: Excelente
- 1.5-2.0: Bom
- 1.0-1.5: Moderado
- < 1.0: Não lucrativo

---

## 💡 Casos de Uso Práticos

### Caso 1: "Quero começar a operar BTC, qual timeframe usar?"

```bash
curl "http://localhost:8000/api/multi-timeframe/quick-scan?symbol=BTC-USDT"
```

**Veja:**
- `best_timeframe.timeframe` → Timeframe recomendado
- `best_timeframe.respect_rate` → Confiabilidade
- `recommendations` → Dicas práticas

---

### Caso 2: "Eu gosto de operar com Order Blocks, qual timeframe funciona melhor?"

```bash
curl "http://localhost:8000/api/indicator-ranking/Order-Block?symbol=BTC-USDT"
```

**Veja:**
- `best_timeframe` → Onde Order Blocks funcionam melhor
- `ranking` → Lista ordenada por score

---

### Caso 3: "Quero comparar 1h vs 4h vs 1d"

```bash
curl "http://localhost:8000/api/multi-timeframe/analyze?symbol=BTC-USDT&timeframes=1h,4h,1d&limit=500"
```

**Veja:**
- `timeframes_analyzed` → Análise detalhada de cada um
- `summary.timeframes_by_quality` → Classificação por qualidade

---

### Caso 4: "Qual indicador é mais confiável para ETH?"

```bash
curl "http://localhost:8000/api/multi-timeframe/quick-scan?symbol=ETH-USDT"
```

**Veja:**
- `best_overall_indicator` → Melhor indicador geral
- `summary.most_reliable_indicators` → Top 3 indicadores

---

## 🎓 Como Tomar Decisões

### 1. **Escolha de Timeframe**
```
1. Execute quick-scan para o ativo
2. Veja best_timeframe.respect_rate
3. Se ≥ 50%, use esse timeframe
4. Se < 50%, veja timeframes_by_quality.good ou excellent
5. Evite timeframes em poor
```

### 2. **Escolha de Indicador**
```
1. Veja best_overall_indicator
2. Confira o score (deve ser ≥ 40)
3. Veja total_trades (≥ 10 é ideal)
4. Confira profit_factor (≥ 1.5 é bom)
```

### 3. **Confluência Multi-Timeframe**
```
Se você encontrar:
- Timeframe A: OB funciona bem (score 70)
- Timeframe B: FVG funciona bem (score 65)

ESTRATÉGIA:
- Use timeframe maior para direção (trend)
- Use timeframe menor para entrada precisa
- Combine indicadores para confluência
```

---

## 📈 Exemplo de Análise Completa

```bash
# 1. Scan rápido
curl "http://localhost:8000/api/multi-timeframe/quick-scan?symbol=BTC-USDT"

# Resultado:
# - Melhor timeframe: 4h (respect_rate: 68%)
# - Melhor indicador: Fair Value Gap (WR: 72%, Score: 75)

# 2. Detalhar o indicador vencedor
curl "http://localhost:8000/api/indicator-ranking/Fair-Value-Gap?symbol=BTC-USDT"

# Resultado:
# - 4h: Score 75 (melhor)
# - 1h: Score 62
# - 15m: Score 45

# DECISÃO FINAL:
# ✅ Operar BTC-USDT no 4h
# ✅ Usar Fair Value Gap como setup principal
# ✅ Risk/Reward: 2.0 (default testado)
```

---

## ⚠️ Notas Importantes

1. **Dados Históricos**: Resultados baseiam-se nos últimos 500-1440 candles
2. **Não é Garantia**: Passado não garante futuro, use gestão de risco
3. **Reanalyse Periodicamente**: Mercado muda, refaça a análise mensalmente
4. **Combine com Análise Manual**: Use como guia, não como regra absoluta
5. **Timeframes Menores**: Mais voláteis, precisam de mais capital para margem
6. **Timeframes Maiores**: Mais confiáveis, mas operações mais demoradas

---

## 🔧 Troubleshooting

### "Out of range float values are not JSON compliant: inf"
- **Causa**: Algum indicador não gerou trades suficientes
- **Solução**: Já corrigido automaticamente, valores infinitos são tratados

### "Could not fetch data for any timeframe"
- **Causa**: Problema de conexão com BingX API
- **Solução**: Verifique sua conexão e tente novamente

### Win Rate muito baixo em todos os timeframes
- **Causa**: Ativo muito volátil ou lateral
- **Solução**: 
  - Teste outro ativo
  - Ajuste o risk_reward (tente 1.5 ou 3.0)
  - Use mais dados (limit=1000)

---

## 📚 Próximos Passos

1. **Execute quick-scan** no seu ativo favorito
2. **Anote** o melhor timeframe e indicador
3. **Teste na prática** com paper trading
4. **Compare** com sua experiência manual
5. **Ajuste** os parâmetros conforme necessário

---

## 💻 Integração com Frontend

```javascript
// Exemplo de chamada no JavaScript
async function analyzeBTC() {
  const response = await fetch('/api/multi-timeframe/quick-scan?symbol=BTC-USDT');
  const data = await response.json();
  
  console.log('Melhor timeframe:', data.best_timeframe.timeframe);
  console.log('Taxa de respeito:', data.best_timeframe.respect_rate + '%');
  console.log('Indicador recomendado:', data.best_overall_indicator.indicator_name);
  
  // Mostrar recomendações
  data.recommendations.forEach(rec => {
    console.log(rec);
  });
}
```

---

**Dúvidas?** Execute os exemplos acima e veja os resultados reais!
