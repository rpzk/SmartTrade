#!/usr/bin/env python3
"""
Script para visualizar predições de preço
"""
import requests
import json
import sys
from datetime import datetime

def print_prediction(symbol, timeframe="1h", periods=10, model="simple_ma"):
    """Imprime predição formatada"""
    
    url = f"http://localhost:8000/api/predict/{symbol}?timeframe={timeframe}&periods={periods}&model={model}&limit=500"
    
    print(f"Buscando predição de {symbol} {timeframe}...")
    
    try:
        response = requests.get(url, timeout=60)
        response.raise_for_status()
        data = response.json()
    except Exception as e:
        print(f"❌ Erro: {e}")
        return
    
    # Cabeçalho
    print("=" * 80)
    print(f"📈 PREDIÇÃO DE PREÇO: {data['symbol']} ({data['timeframe']})")
    print("=" * 80)
    print()
    
    # Preço atual
    print(f"💰 PREÇO ATUAL: ${data['current_price']:,.2f}")
    print()
    
    # Tendência
    trend_emoji = {"bullish": "🟢", "bearish": "🔴", "neutral": "🟡"}
    print(f"📊 TENDÊNCIA: {trend_emoji.get(data['trend'], '⚪')} {data['trend'].upper()}")
    print(f"   Força: {data['trend_strength']:.1f}%")
    print()
    
    # Resumo
    print(f"📝 RESUMO: {data['summary']}")
    print()
    
    # Modelo
    print(f"🤖 MODELO: {data['model_used']}")
    if data.get('metrics'):
        print(f"   Métricas: {json.dumps(data['metrics'], indent=2)}")
    print()
    
    # Predições
    print("🔮 PREDIÇÕES FUTURAS:")
    print(f"{'#':>3} {'Data/Hora':<20} {'Preço':>12} {'Variação':>10} {'Confiança':>10} {'Intervalo':<25}")
    print("-" * 80)
    
    for i, pred in enumerate(data['predictions'], 1):
        # Timestamp para datetime
        dt = datetime.fromtimestamp(pred['timestamp'] / 1000)
        dt_str = dt.strftime("%d/%m %H:%M")
        
        # Variação percentual
        change = ((pred['predicted_price'] - data['current_price']) / data['current_price']) * 100
        change_str = f"{change:+.2f}%"
        
        # Emoji baseado na variação
        if change > 1:
            emoji = "🟢"
        elif change < -1:
            emoji = "🔴"
        else:
            emoji = "🟡"
        
        # Confiança
        conf = pred['confidence']
        if conf >= 70:
            conf_emoji = "🟢"
        elif conf >= 50:
            conf_emoji = "🟡"
        else:
            conf_emoji = "🔴"
        
        # Intervalo
        interval = f"${pred['lower_bound']:,.0f} - ${pred['upper_bound']:,.0f}"
        
        print(f"{emoji} {i:>2} {dt_str:<20} ${pred['predicted_price']:>10,.2f} {change_str:>10} {conf_emoji} {conf:>3.0f}% {interval:<25}")
    
    print()
    
    # Análise final
    last_pred = data['predictions'][-1]
    final_change = ((last_pred['predicted_price'] - data['current_price']) / data['current_price']) * 100
    
    print("📌 ANÁLISE:")
    if final_change > 2:
        print(f"   ✅ Perspectiva POSITIVA: Previsão de alta de {final_change:.2f}%")
        print(f"   💡 Sugestão: Considere posições LONG")
    elif final_change < -2:
        print(f"   ⚠️  Perspectiva NEGATIVA: Previsão de queda de {abs(final_change):.2f}%")
        print(f"   💡 Sugestão: Considere posições SHORT ou aguarde")
    else:
        print(f"   🔸 Perspectiva NEUTRA: Movimento lateral previsto ({abs(final_change):.2f}%)")
        print(f"   💡 Sugestão: Aguarde sinais mais claros")
    
    print()
    print(f"   ⚠️  Confiança média: {sum(p['confidence'] for p in data['predictions'])/len(data['predictions']):.1f}%")
    print(f"   ⚠️  Predições são baseadas em dados históricos e não garantem resultados futuros")
    print()
    print("=" * 80)


def compare_models(symbol, timeframe="1h", periods=10):
    """Compara diferentes modelos"""
    
    url = f"http://localhost:8000/api/predict/compare-models?symbol={symbol}&timeframe={timeframe}&periods={periods}&limit=500"
    
    print(f"Comparando modelos para {symbol} {timeframe}...")
    
    try:
        response = requests.post(url, timeout=120)
        response.raise_for_status()
        data = response.json()
    except Exception as e:
        print(f"❌ Erro: {e}")
        return
    
    print("=" * 80)
    print(f"🔬 COMPARAÇÃO DE MODELOS: {data['symbol']} ({data['timeframe']})")
    print("=" * 80)
    print()
    
    print(f"Modelos testados: {data['models_tested']}")
    print(f"Recomendação: {data['recommendation']}")
    print()
    
    for model_name, result in data['results'].items():
        if 'error' in result:
            print(f"❌ {model_name}: {result['error']}")
            continue
        
        print(f"📊 {model_name.upper()}")
        print(f"   Tendência: {result['trend']}")
        print(f"   Força: {result['trend_strength']:.1f}%")
        print(f"   Predições: {len(result['predictions'])}")
        
        last_pred = result['predictions'][-1]
        change = ((last_pred['predicted_price'] - result['current_price']) / result['current_price']) * 100
        print(f"   Variação prevista: {change:+.2f}%")
        print(f"   Confiança: {last_pred['confidence']:.1f}%")
        print()
    
    print("=" * 80)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso:")
        print("  python3 view_prediction.py <symbol>                    # Predição padrão (1h, 10 períodos)")
        print("  python3 view_prediction.py <symbol> <timeframe>        # Timeframe customizado")
        print("  python3 view_prediction.py <symbol> <timeframe> <periods> # Períodos customizados")
        print("  python3 view_prediction.py <symbol> compare            # Comparar modelos")
        print()
        print("Exemplos:")
        print("  python3 view_prediction.py BTC-USDT")
        print("  python3 view_prediction.py ETH-USDT 4h")
        print("  python3 view_prediction.py BTC-USDT 1h 20")
        print("  python3 view_prediction.py ETH-USDT compare")
        sys.exit(1)
    
    symbol = sys.argv[1]
    
    if len(sys.argv) >= 3 and sys.argv[2] == "compare":
        compare_models(symbol)
    elif len(sys.argv) >= 4:
        timeframe = sys.argv[2]
        periods = int(sys.argv[3])
        print_prediction(symbol, timeframe, periods)
    elif len(sys.argv) >= 3:
        timeframe = sys.argv[2]
        print_prediction(symbol, timeframe)
    else:
        print_prediction(symbol)
