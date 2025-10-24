"""
Módulo de persistência para histórico de klines (candles).
Usa SQLAlchemy com SQLite para armazenamento local.
"""
from __future__ import annotations

import logging
from datetime import datetime
from typing import List, Optional, Dict, Any
from contextlib import asynccontextmanager

from sqlalchemy import create_engine, Column, Integer, String, Float, BigInteger, Index
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base, Session
from sqlalchemy.sql import select

logger = logging.getLogger(__name__)

Base = declarative_base()


class Kline(Base):
    """
    Modelo de candle/kline para persistência.
    
    Armazena dados OHLCV (Open, High, Low, Close, Volume) com timestamp.
    """
    __tablename__ = "klines"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String(20), nullable=False, index=True)
    interval = Column(String(10), nullable=False, index=True)
    time = Column(BigInteger, nullable=False)  # Timestamp em ms
    open = Column(String(50), nullable=False)
    high = Column(String(50), nullable=False)
    low = Column(String(50), nullable=False)
    close = Column(String(50), nullable=False)
    volume = Column(String(50), nullable=False)
    created_at = Column(BigInteger, nullable=False)  # Timestamp de inserção
    
    # Índice composto para queries eficientes
    __table_args__ = (
        Index('idx_symbol_interval_time', 'symbol', 'interval', 'time', unique=True),
    )
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário compatível com API BingX"""
        return {
            "time": self.time,
            "open": self.open,
            "high": self.high,
            "low": self.low,
            "close": self.close,
            "volume": self.volume,
        }


class KlineStorage:
    """
    Gerenciador de persistência de klines.
    
    Suporta operações síncronas e assíncronas.
    """
    
    def __init__(self, db_url: str = "sqlite:///smarttrade.db"):
        """
        Inicializa o storage.
        
        Args:
            db_url: URL de conexão do banco (padrão: SQLite local)
        """
        self.db_url = db_url
        self.engine = create_engine(db_url, echo=False)
        self.Session = Session
        
        # Cria tabelas se não existirem
        Base.metadata.create_all(self.engine)
        logger.info(f"KlineStorage initialized with {db_url}")
    
    def save_klines(
        self,
        symbol: str,
        interval: str,
        klines_data: List[Dict[str, Any]]
    ) -> int:
        """
        Salva múltiplos klines no banco.
        
        Args:
            symbol: Par de negociação (ex: BTC-USDT)
            interval: Intervalo temporal (ex: 1m, 5m, 1h)
            klines_data: Lista de dicts com dados dos klines
            
        Returns:
            Quantidade de klines inseridos/atualizados
        """
        if not klines_data:
            return 0
        
        session = Session(self.engine)
        now_ms = int(datetime.now().timestamp() * 1000)
        inserted = 0
        
        try:
            for kline_dict in klines_data:
                # Verifica se já existe
                existing = session.query(Kline).filter_by(
                    symbol=symbol,
                    interval=interval,
                    time=kline_dict["time"]
                ).first()
                
                if existing:
                    # Atualiza valores (candle pode ter sido atualizado)
                    existing.open = str(kline_dict["open"])
                    existing.high = str(kline_dict["high"])
                    existing.low = str(kline_dict["low"])
                    existing.close = str(kline_dict["close"])
                    existing.volume = str(kline_dict["volume"])
                else:
                    # Insere novo
                    kline = Kline(
                        symbol=symbol,
                        interval=interval,
                        time=kline_dict["time"],
                        open=str(kline_dict["open"]),
                        high=str(kline_dict["high"]),
                        low=str(kline_dict["low"]),
                        close=str(kline_dict["close"]),
                        volume=str(kline_dict["volume"]),
                        created_at=now_ms
                    )
                    session.add(kline)
                    inserted += 1
            
            session.commit()
            logger.info(
                f"Saved {inserted} klines for {symbol} {interval}",
                extra={"total": len(klines_data), "new": inserted}
            )
            return inserted
            
        except Exception as e:
            session.rollback()
            logger.error(f"Error saving klines: {e}")
            raise
        finally:
            session.close()
    
    def get_klines(
        self,
        symbol: str,
        interval: str,
        limit: Optional[int] = 100,
        start_time: Optional[int] = None,
        end_time: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Busca klines do banco.
        
        Args:
            symbol: Par de negociação
            interval: Intervalo temporal
            limit: Quantidade máxima de resultados
            start_time: Timestamp inicial (ms)
            end_time: Timestamp final (ms)
            
        Returns:
            Lista de klines como dicts
        """
        session = Session(self.engine)
        
        try:
            query = session.query(Kline).filter_by(
                symbol=symbol,
                interval=interval
            )
            
            if start_time:
                query = query.filter(Kline.time >= start_time)
            if end_time:
                query = query.filter(Kline.time <= end_time)
            
            query = query.order_by(Kline.time.desc())
            
            if limit:
                query = query.limit(limit)
            
            klines = query.all()
            result = [k.to_dict() for k in reversed(klines)]  # Ordem crescente
            
            logger.debug(
                f"Retrieved {len(result)} klines for {symbol} {interval}",
                extra={"limit": limit, "start": start_time, "end": end_time}
            )
            
            return result
            
        finally:
            session.close()
    
    def get_latest_kline(
        self,
        symbol: str,
        interval: str
    ) -> Optional[Dict[str, Any]]:
        """
        Busca o kline mais recente.
        
        Args:
            symbol: Par de negociação
            interval: Intervalo temporal
            
        Returns:
            Kline mais recente ou None
        """
        session = Session(self.engine)
        
        try:
            kline = session.query(Kline).filter_by(
                symbol=symbol,
                interval=interval
            ).order_by(Kline.time.desc()).first()
            
            return kline.to_dict() if kline else None
            
        finally:
            session.close()
    
    def count_klines(self, symbol: str, interval: str) -> int:
        """
        Conta quantos klines existem para um símbolo/intervalo.
        
        Args:
            symbol: Par de negociação
            interval: Intervalo temporal
            
        Returns:
            Quantidade de klines armazenados
        """
        session = Session(self.engine)
        
        try:
            count = session.query(Kline).filter_by(
                symbol=symbol,
                interval=interval
            ).count()
            
            return count
            
        finally:
            session.close()
    
    def delete_old_klines(
        self,
        symbol: str,
        interval: str,
        before_time: int
    ) -> int:
        """
        Remove klines antigos.
        
        Args:
            symbol: Par de negociação
            interval: Intervalo temporal
            before_time: Remove klines anteriores a este timestamp (ms)
            
        Returns:
            Quantidade de registros removidos
        """
        session = Session(self.engine)
        
        try:
            deleted = session.query(Kline).filter(
                Kline.symbol == symbol,
                Kline.interval == interval,
                Kline.time < before_time
            ).delete()
            
            session.commit()
            
            logger.info(
                f"Deleted {deleted} old klines for {symbol} {interval}",
                extra={"before_time": before_time}
            )
            
            return deleted
            
        except Exception as e:
            session.rollback()
            logger.error(f"Error deleting klines: {e}")
            raise
        finally:
            session.close()
    
    def close(self):
        """Fecha conexões do banco"""
        self.engine.dispose()
        logger.info("KlineStorage closed")


# Instância global de storage
_storage: Optional[KlineStorage] = None


def get_storage() -> KlineStorage:
    """
    Retorna instância singleton do storage.
    
    Returns:
        Instância de KlineStorage
    """
    global _storage
    if _storage is None:
        _storage = KlineStorage()
    return _storage
