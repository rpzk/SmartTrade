#!/usr/bin/env python3
"""
Script de auditoria do banco de dados SmartTrade.
Verifica contagem de registros, intervalos de datas, duplicatas e missing values.
"""
import sqlite3
from datetime import datetime
from typing import Dict, Any, List
import json


def audit_database(db_path: str = "smarttrade.db") -> Dict[str, Any]:
    """
    Executa auditoria completa do banco de dados.
    
    Args:
        db_path: Caminho para o arquivo SQLite
        
    Returns:
        Dicionário com métricas de auditoria
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    audit_results = {
        "db_path": db_path,
        "audit_timestamp": datetime.now().isoformat(),
        "summary": {},
        "by_symbol_interval": [],
        "issues": [],
        "sample_records": []
    }
    
    try:
        # 1. Contagem total de registros
        cursor.execute("SELECT COUNT(*) FROM klines")
        total_count = cursor.fetchone()[0]
        audit_results["summary"]["total_records"] = total_count
        
        if total_count == 0:
            audit_results["issues"].append("⚠️  Banco de dados vazio - nenhum kline armazenado")
            return audit_results
        
        # 2. Contagem por símbolo e intervalo
        cursor.execute("""
            SELECT 
                symbol, 
                interval,
                COUNT(*) as count,
                MIN(time) as min_time,
                MAX(time) as max_time,
                COUNT(DISTINCT time) as unique_times
            FROM klines
            GROUP BY symbol, interval
            ORDER BY symbol, interval
        """)
        
        for row in cursor.fetchall():
            symbol, interval, count, min_time, max_time, unique_times = row
            
            # Converter timestamps para datas legíveis
            min_date = datetime.fromtimestamp(min_time / 1000).strftime("%Y-%m-%d %H:%M:%S")
            max_date = datetime.fromtimestamp(max_time / 1000).strftime("%Y-%m-%d %H:%M:%S")
            
            entry = {
                "symbol": symbol,
                "interval": interval,
                "count": count,
                "unique_times": unique_times,
                "duplicates": count - unique_times,
                "date_range": {
                    "start": min_date,
                    "end": max_date,
                    "start_ms": min_time,
                    "end_ms": max_time
                }
            }
            
            audit_results["by_symbol_interval"].append(entry)
            
            # Detectar duplicatas
            if count > unique_times:
                audit_results["issues"].append(
                    f"⚠️  {symbol} {interval}: {count - unique_times} registros duplicados por timestamp"
                )
        
        # 3. Verificar valores nulos ou vazios
        cursor.execute("""
            SELECT COUNT(*) FROM klines 
            WHERE open IS NULL OR open = '' 
               OR high IS NULL OR high = ''
               OR low IS NULL OR low = ''
               OR close IS NULL OR close = ''
               OR volume IS NULL OR volume = ''
        """)
        null_count = cursor.fetchone()[0]
        
        if null_count > 0:
            audit_results["issues"].append(
                f"⚠️  {null_count} registros com valores OHLCV nulos ou vazios"
            )
        
        # 4. Verificar valores numéricos inválidos (zero ou negativos em OHLC)
        cursor.execute("""
            SELECT COUNT(*) FROM klines 
            WHERE CAST(open AS REAL) <= 0 
               OR CAST(high AS REAL) <= 0
               OR CAST(low AS REAL) <= 0
               OR CAST(close AS REAL) <= 0
        """)
        invalid_count = cursor.fetchone()[0]
        
        if invalid_count > 0:
            audit_results["issues"].append(
                f"⚠️  {invalid_count} registros com preços <= 0"
            )
        
        # 5. Verificar consistência OHLC (high >= low, etc)
        cursor.execute("""
            SELECT COUNT(*) FROM klines 
            WHERE CAST(high AS REAL) < CAST(low AS REAL)
               OR CAST(high AS REAL) < CAST(open AS REAL)
               OR CAST(high AS REAL) < CAST(close AS REAL)
               OR CAST(low AS REAL) > CAST(open AS REAL)
               OR CAST(low AS REAL) > CAST(close AS REAL)
        """)
        inconsistent_count = cursor.fetchone()[0]
        
        if inconsistent_count > 0:
            audit_results["issues"].append(
                f"⚠️  {inconsistent_count} registros com OHLC inconsistente (high < low, etc)"
            )
        
        # 6. Amostrar 10 registros recentes
        cursor.execute("""
            SELECT symbol, interval, time, open, high, low, close, volume
            FROM klines
            ORDER BY time DESC
            LIMIT 10
        """)
        
        for row in cursor.fetchall():
            symbol, interval, time, open_p, high, low, close, volume = row
            date_str = datetime.fromtimestamp(time / 1000).strftime("%Y-%m-%d %H:%M:%S")
            
            audit_results["sample_records"].append({
                "symbol": symbol,
                "interval": interval,
                "datetime": date_str,
                "open": open_p,
                "high": high,
                "low": low,
                "close": close,
                "volume": volume
            })
        
        # 7. Estatísticas de armazenamento
        cursor.execute("SELECT COUNT(DISTINCT symbol) FROM klines")
        unique_symbols = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(DISTINCT interval) FROM klines")
        unique_intervals = cursor.fetchone()[0]
        
        audit_results["summary"]["unique_symbols"] = unique_symbols
        audit_results["summary"]["unique_intervals"] = unique_intervals
        
        if not audit_results["issues"]:
            audit_results["issues"].append("✅ Nenhum problema detectado")
        
    finally:
        conn.close()
    
    return audit_results


def print_audit_report(audit: Dict[str, Any]):
    """Imprime relatório de auditoria formatado"""
    print("\n" + "="*80)
    print("📊 RELATÓRIO DE AUDITORIA DO BANCO DE DADOS SMARTTRADE")
    print("="*80)
    
    print(f"\n🕒 Timestamp: {audit['audit_timestamp']}")
    print(f"📁 Banco: {audit['db_path']}")
    
    print(f"\n📈 RESUMO GERAL")
    print(f"  • Total de registros: {audit['summary'].get('total_records', 0):,}")
    print(f"  • Símbolos únicos: {audit['summary'].get('unique_symbols', 0)}")
    print(f"  • Intervalos únicos: {audit['summary'].get('unique_intervals', 0)}")
    
    if audit["by_symbol_interval"]:
        print(f"\n📊 DETALHAMENTO POR SÍMBOLO/INTERVALO")
        print("-" * 80)
        for entry in audit["by_symbol_interval"]:
            print(f"\n  {entry['symbol']} ({entry['interval']})")
            print(f"    • Registros: {entry['count']:,}")
            print(f"    • Timestamps únicos: {entry['unique_times']:,}")
            if entry['duplicates'] > 0:
                print(f"    • ⚠️  Duplicatas: {entry['duplicates']}")
            print(f"    • Período: {entry['date_range']['start']} até {entry['date_range']['end']}")
    
    print(f"\n🔍 PROBLEMAS DETECTADOS")
    print("-" * 80)
    for issue in audit["issues"]:
        print(f"  {issue}")
    
    if audit["sample_records"]:
        print(f"\n📄 AMOSTRA (10 registros mais recentes)")
        print("-" * 80)
        for i, rec in enumerate(audit["sample_records"][:5], 1):
            print(f"  {i}. {rec['symbol']} {rec['interval']} | {rec['datetime']}")
            print(f"     O:{rec['open']} H:{rec['high']} L:{rec['low']} C:{rec['close']} V:{rec['volume']}")
    
    print("\n" + "="*80)


def main():
    audit = audit_database()
    print_audit_report(audit)
    
    # Salvar JSON para processamento posterior
    with open("audit_report.json", "w") as f:
        json.dump(audit, f, indent=2)
    print(f"\n💾 Relatório JSON salvo em: audit_report.json")


if __name__ == "__main__":
    main()
