# 🔮 Guia Rápido — Predições de Preço

## ✅ Status: TUDO FUNCIONANDO!

- ✅ Prophet instalado
- ✅ Dashboard web pronto
- ✅ Servidor rodando
- ✅ API funcionando

---

## 🚀 3 Formas de Usar Predições

### 1️⃣ Dashboard Web (MAIS FÁCIL)

**Acesse agora:**
```
http://localhost:8000/static/prediction_overlay.html
```

**OU** clique no botão **🔮 Predições** em:
```
http://localhost:8000
```

**Como usar:**
1. Digite o símbolo (ex: BTC-USDT, ETH-USDT)
2. Escolha o timeframe (1m, 5m, 15m, 1h, 4h, 1d)
3. Defina quantos períodos prever (1-50)
4. Selecione o modelo (prophet recomendado!)
5. Clique em **Atualizar**

**Você verá:**
- 📊 Candles históricos
- 📈 Linha de predição (laranja)
- 📉 Bandas de confiança (superior/inferior)
- ℹ️ Resumo com tendência e métricas

---

### 2️⃣ Via CLI (Linha de Comando)

**Predição padrão:**
```bash
python3 view_prediction.py BTC-USDT
```

**Customizado:**
```bash
python3 view_prediction.py ETH-USDT 4h 20
#                          ↑        ↑  ↑
#                       símbolo  tf  períodos
```

**Comparar modelos:**
```bash
python3 view_prediction.py BTC-USDT compare
```

---

### 3️⃣ Via API REST

**Predição com Prophet:**
```bash
curl "http://localhost:8000/api/predict/BTC-USDT?timeframe=1h&periods=10&model=prophet" | python3 -m json.tool
```

**Comparar todos os modelos:**
```bash
curl -X POST "http://localhost:8000/api/predict/compare-models?symbol=ETH-USDT&timeframe=4h&periods=10" | python3 -m json.tool
```

---

## 📊 Exemplo de Resultado

```json
{
  "symbol": "BTC-USDT",
  "timeframe": "1h",
  "model_used": "prophet",
  "current_price": 110382.8,
  "predictions": [
    {
      "timestamp": 1762030800000,
      "predicted_price": 110420.52,
      "confidence": 90,
      "lower_bound": 109339.05,
      "upper_bound": 111481.81
    }
  ],
  "trend": "neutral",
  "trend_strength": 50.0,
  "metrics": {
    "mae": 184.24,
    "rmse": 209.58,
    "mape": 0.17
  },
  "summary": "Tendência NEUTRAL com 50.0% de força. Previsão de alta de 0.14% (confiança: 90.0%)"
}
```

---

## 🧠 Modelos Disponíveis

| Modelo | Status | Quando Usar |
|--------|--------|-------------|
| **prophet** | ✅ Instalado | Melhor para tendências e sazonalidade |
| **simple_ma** | ✅ Sempre disponível | Rápido, baseline confiável |
| **lstm** | ⏳ Não instalado | Padrões complexos (requer tensorflow) |
| **arima** | ⏳ Não instalado | Análise estatística (requer statsmodels) |

---

## 🎯 Dicas Rápidas

### ✅ Melhores Práticas

1. **Use timeframes maiores** (1h, 4h, 1d) para predições mais confiáveis
2. **Prophet é melhor** para 10+ períodos
3. **Simple MA é mais rápido** para 1-5 períodos
4. **Confiança > 60%** = predição razoável
5. **Tendência forte (> 70%)** = sinal mais claro

### ⚠️ Limitações

- Predições não são garantias
- Eventos inesperados podem invalidar tudo
- Use sempre stop loss e gestão de risco
- Confiança diminui com o tempo (mais distante = menos confiável)

---

## 🔧 Troubleshooting

### Problema: Prophet não funciona
```bash
# Reinstalar Prophet
/bin/python3 -m pip install prophet --break-system-packages --force-reinstall
```

### Problema: Servidor não inicia
```bash
# Parar processos antigos
pkill -f 'smarttrade.web.app'

# Instalar dependências
/bin/python3 -m pip install -r requirements.txt --break-system-packages

# Reiniciar
cd /workspaces/SmartTrade
nohup /bin/python3 -m smarttrade.web.app > server.log 2>&1 &
```

### Problema: Página não carrega
```bash
# Verificar se servidor está rodando
ps aux | grep smarttrade

# Ver logs
tail -f server.log
```

---

## 📚 Documentação Completa

Para detalhes técnicos completos, veja:
- **PREDICTION_GUIDE.md** — Guia completo de predições
- **README.md** — Documentação geral do SmartTrade

---

## 🎉 Pronto!

**Acesse agora e faça sua primeira predição:**

👉 **http://localhost:8000/static/prediction_overlay.html**

Ou teste via CLI:
```bash
python3 view_prediction.py BTC-USDT 1h 10
```

**Divirta-se prevendo o futuro! 🔮📈**
