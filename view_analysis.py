#!/usr/bin/env python3
"""
Script para visualizar análise multi-timeframe
"""
import requests
import json
import sys

def print_analysis(symbol, timeframes=None, limit=500):
    """Imprime análise formatada"""
    
    # Monta URL
    url = f"http://localhost:8000/api/multi-timeframe/analyze?symbol={symbol}&limit={limit}"
    if timeframes:
        url += f"&timeframes={timeframes}"
    
    print(f"Buscando dados de {symbol}...")
    
    try:
        response = requests.get(url, timeout=300)  # 5 minutos timeout
        response.raise_for_status()
        data = response.json()
    except Exception as e:
        print(f"❌ Erro: {e}")
        return
    
    # Cabeçalho
    print("=" * 70)
    print(f"ANÁLISE MULTI-TIMEFRAME: {symbol}")
    print("=" * 70)
    print()
    
    # Melhor timeframe
    if data.get('best_timeframe'):
        bt = data['best_timeframe']
        print(f"🏆 MELHOR TIMEFRAME: {bt['timeframe']} ({bt['respect_rate']:.1f}% respect rate)")
        print()
    
    # Melhor indicador
    if data.get('best_overall_indicator'):
        bi = data['best_overall_indicator']
        print(f"🎯 MELHOR INDICADOR: {bi['indicator_name']} no {bi['timeframe']}")
        print(f"   Win Rate: {bi['win_rate']:.1f}%")
        print(f"   Profit Factor: {bi['profit_factor']:.2f}")
        print(f"   Score: {bi['score']:.1f}")
        print(f"   Confiança: {bi['confidence_level']}")
        print()
    
    # Ranking de timeframes
    print("📊 RANKING DE TIMEFRAMES:")
    for tf in data['timeframes_analyzed']:
        # Emoji baseado no respect rate
        if tf['respect_rate'] >= 70:
            emoji = "🟢"
        elif tf['respect_rate'] >= 50:
            emoji = "🟡"
        elif tf['respect_rate'] >= 30:
            emoji = "🟠"
        else:
            emoji = "🔴"
        
        print(f"  {emoji} {tf['timeframe']:>4s}: {tf['respect_rate']:5.1f}% respect | score: {tf['total_score']:5.1f}")
        
        # Mostra melhor indicador do timeframe
        if tf.get('best_indicator'):
            ind = tf['best_indicator']
            print(f"       └─ Melhor: {ind['indicator_name']} (WR: {ind['win_rate']:.1f}%, Trades: {ind['total_trades']})")
    
    print()
    
    # Recomendações
    print("💡 RECOMENDAÇÕES:")
    for rec in data.get('recommendations', []):
        print(f"  {rec}")
    
    print()
    
    # Summary
    summary = data.get('summary', {})
    print("📈 RESUMO:")
    print(f"  Timeframes analisados: {summary.get('total_timeframes_analyzed', 0)}")
    print(f"  Indicadores testados: {summary.get('total_indicators_tested', 0)}")
    print(f"  Taxa de respeito média: {summary.get('avg_respect_rate', 0):.1f}%")
    
    tf_quality = summary.get('timeframes_by_quality', {})
    if tf_quality.get('excellent'):
        print(f"  Excelentes: {', '.join(tf_quality['excellent'])}")
    if tf_quality.get('good'):
        print(f"  Bons: {', '.join(tf_quality['good'])}")
    if tf_quality.get('fair'):
        print(f"  Regulares: {', '.join(tf_quality['fair'])}")
    if tf_quality.get('poor'):
        print(f"  Ruins: {', '.join(tf_quality['poor'])}")
    
    print()
    print("=" * 70)


def print_indicator_ranking(indicator, symbol, timeframes=None):
    """Imprime ranking de indicador específico"""
    
    url = f"http://localhost:8000/api/indicator-ranking/{indicator}?symbol={symbol}"
    if timeframes:
        url += f"&timeframes={timeframes}"
    
    print(f"Analisando {indicator} em {symbol}...")
    
    try:
        response = requests.get(url, timeout=300)
        response.raise_for_status()
        data = response.json()
    except Exception as e:
        print(f"❌ Erro: {e}")
        return
    
    print("=" * 70)
    print(f"RANKING: {data['indicator']} - {symbol}")
    print("=" * 70)
    print()
    
    if data.get('best_timeframe'):
        bt = data['best_timeframe']
        print(f"🏆 MELHOR TIMEFRAME: {bt['timeframe']}")
        print(f"   Win Rate: {bt['win_rate']:.1f}%")
        print(f"   Score: {bt['score']:.1f}")
        print(f"   Profit Factor: {bt['profit_factor']:.2f}")
        print()
    
    print("📊 RANKING COMPLETO:")
    for i, ind in enumerate(data.get('ranking', []), 1):
        # Emoji baseado no score
        if ind['score'] >= 60:
            emoji = "🟢"
        elif ind['score'] >= 40:
            emoji = "🟡"
        elif ind['score'] >= 20:
            emoji = "🟠"
        else:
            emoji = "🔴"
        
        print(f"  {i}. {emoji} {ind['timeframe']:>4s}: Score {ind['score']:5.1f} | WR {ind['win_rate']:5.1f}% | PF {ind['profit_factor']:4.2f} | {ind['confidence_level']}")
    
    print()
    summary = data.get('summary', {})
    print("📈 RESUMO:")
    print(f"  Timeframes analisados: {data.get('timeframes_analyzed', 0)}")
    print(f"  Win Rate médio: {summary.get('avg_win_rate', 0):.1f}%")
    print(f"  Score médio: {summary.get('avg_score', 0):.1f}")
    print(f"  Total de trades: {summary.get('total_trades', 0)}")
    print()
    print("=" * 70)


def quick_scan(symbol):
    """Quick scan simplificado"""
    
    url = f"http://localhost:8000/api/multi-timeframe/quick-scan?symbol={symbol}"
    
    print(f"Quick scan de {symbol} (pode demorar alguns minutos)...")
    
    try:
        response = requests.get(url, timeout=600)  # 10 minutos
        response.raise_for_status()
        data = response.json()
    except Exception as e:
        print(f"❌ Erro: {e}")
        return
    
    print()
    print("=" * 70)
    print(f"⚡ QUICK SCAN: {symbol}")
    print("=" * 70)
    print()
    
    if data.get('best_timeframe'):
        bt = data['best_timeframe']
        print(f"🏆 MELHOR TIMEFRAME: {bt['timeframe']}")
        print(f"   Respect Rate: {bt['respect_rate']:.1f}%")
        print(f"   Score: {bt['total_score']:.1f}")
        print()
    
    if data.get('best_overall_indicator'):
        bi = data['best_overall_indicator']
        print(f"🎯 MELHOR INDICADOR: {bi['indicator_name']}")
        print(f"   Timeframe: {bi['timeframe']}")
        print(f"   Win Rate: {bi['win_rate']:.1f}%")
        print(f"   Profit Factor: {bi['profit_factor']:.2f}")
        print()
    
    print("💡 RECOMENDAÇÕES:")
    for rec in data.get('recommendations', []):
        print(f"  {rec}")
    
    print()
    print("=" * 70)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso:")
        print("  python3 view_analysis.py <symbol>                    # Quick scan")
        print("  python3 view_analysis.py <symbol> <timeframes>       # Análise customizada")
        print("  python3 view_analysis.py <symbol> indicator:<name>   # Ranking de indicador")
        print()
        print("Exemplos:")
        print("  python3 view_analysis.py BTC-USDT")
        print("  python3 view_analysis.py ETH-USDT 15m,1h,4h")
        print("  python3 view_analysis.py BTC-USDT indicator:Order-Block")
        sys.exit(1)
    
    symbol = sys.argv[1]
    
    if len(sys.argv) >= 3 and sys.argv[2].startswith("indicator:"):
        # Ranking de indicador
        indicator = sys.argv[2].split(":", 1)[1]
        timeframes = sys.argv[3] if len(sys.argv) >= 4 else None
        print_indicator_ranking(indicator, symbol, timeframes)
    elif len(sys.argv) >= 3:
        # Análise customizada
        timeframes = sys.argv[2]
        print_analysis(symbol, timeframes)
    else:
        # Quick scan
        quick_scan(symbol)
