import asyncio
import json
import gzip
import io
import logging
import time
from typing import Dict, Set, Callable, Any, Optional
import websockets
from websockets.exceptions import ConnectionClosed

logger = logging.getLogger(__name__)

class BingXWebSocketManager:
    """
    Gerenciador de conexão WebSocket com a BingX.
    Mantém uma única conexão robusta e distribui mensagens para múltiplos assinantes.
    """
    
    BASE_URL = "wss://open-api-swap.bingx.com/swap-market"
    
    def __init__(self):
        self._ws: Optional[websockets.WebSocketClientProtocol] = None
        self._subscribers: Dict[str, Set[Callable[[dict], Any]]] = {}
        self._running = False
        self._lock = asyncio.Lock()
        self._connect_task: Optional[asyncio.Task] = None
        self._active_subscriptions: Set[str] = set()
        
    async def start(self):
        """Inicia o gerenciador em background"""
        if self._running:
            return
        self._running = True
        self._connect_task = asyncio.create_task(self._connection_loop())
        logger.info("BingX WebSocket Manager started")

    async def stop(self):
        """Para o gerenciador e fecha conexões"""
        self._running = False
        if self._ws:
            await self._ws.close()
        if self._connect_task:
            self._connect_task.cancel()
            try:
                await self._connect_task
            except asyncio.CancelledError:
                pass
        logger.info("BingX WebSocket Manager stopped")

    async def subscribe(self, symbol: str, interval: str, callback: Callable[[dict], Any]):
        """
        Assina atualizações de klines para um símbolo/intervalo.
        
        Args:
            symbol: Par (ex: BTC-USDT)
            interval: Timeframe (ex: 1m)
            callback: Função async para receber dados
        """
        channel = f"{symbol}@kline_{interval}"
        
        async with self._lock:
            if channel not in self._subscribers:
                self._subscribers[channel] = set()
            self._subscribers[channel].add(callback)
            
            # Se já estiver conectado e ainda não assinado na exchange, envia comando
            if self._ws and channel not in self._active_subscriptions:
                await self._send_subscribe(channel)

    async def unsubscribe(self, symbol: str, interval: str, callback: Callable[[dict], Any]):
        """Remove assinatura"""
        channel = f"{symbol}@kline_{interval}"
        
        async with self._lock:
            if channel in self._subscribers:
                self._subscribers[channel].discard(callback)
                if not self._subscribers[channel]:
                    del self._subscribers[channel]
                    # Opcional: enviar unsubscribe para exchange se ninguém mais ouve
                    # await self._send_unsubscribe(channel)

    async def _connection_loop(self):
        """Loop principal de conexão e reconexão"""
        while self._running:
            try:
                logger.info(f"Connecting to BingX WS: {self.BASE_URL}")
                async with websockets.connect(self.BASE_URL, ping_interval=None) as ws:
                    self._ws = ws
                    self._active_subscriptions.clear()
                    logger.info("Connected to BingX WS")
                    
                    # Re-assinar canais pendentes
                    async with self._lock:
                        for channel in self._subscribers.keys():
                            await self._send_subscribe(channel)
                    
                    await self._listen_loop(ws)
                    
            except (ConnectionClosed, OSError) as e:
                logger.warning(f"BingX WS connection lost: {e}. Reconnecting in 5s...")
                self._ws = None
                await asyncio.sleep(5)
            except Exception as e:
                logger.error(f"Unexpected error in BingX WS loop: {e}", exc_info=True)
                await asyncio.sleep(5)

    async def _listen_loop(self, ws):
        """Loop de leitura de mensagens"""
        while self._running:
            try:
                message = await ws.recv()
                await self._handle_message(message)
            except ConnectionClosed:
                raise
            except Exception as e:
                logger.error(f"Error processing message: {e}")

    async def _handle_message(self, message: bytes | str):
        """Processa mensagem crua (descomprime e roteia)"""
        # Descompressão Gzip se necessário
        if isinstance(message, bytes):
            try:
                message = gzip.GzipFile(fileobj=io.BytesIO(message)).read().decode('utf-8')
            except Exception:
                pass # Pode ser texto puro
                
        if message == "Ping":
            if self._ws:
                await self._ws.send("Pong")
            return

        try:
            data = json.loads(message)
        except json.JSONDecodeError:
            return

        # Roteamento
        channel = data.get("dataType")
        if channel and channel in self._subscribers:
            # Formata dados para o padrão esperado pelo frontend
            # BingX envia: {"data": [{"c":..., "o":...}]}
            # Frontend espera: {"time":..., "open":..., "close":...}
            
            raw_data = data.get("data", [])
            if not raw_data:
                return
                
            candle = raw_data[0]
            formatted = {
                "time": candle.get("T"), # Timestamp ms
                "open": candle.get("o"),
                "high": candle.get("h"),
                "low": candle.get("l"),
                "close": candle.get("c"),
                "volume": candle.get("v")
            }
            
            # Notifica subscribers
            callbacks = list(self._subscribers[channel])
            for cb in callbacks:
                try:
                    await cb(formatted)
                except Exception as e:
                    logger.error(f"Error in subscriber callback: {e}")

    async def _send_subscribe(self, channel: str):
        """Envia comando de subscribe para a exchange"""
        if not self._ws:
            return
            
        msg = {
            "id": f"sub-{int(time.time())}",
            "reqType": "sub",
            "dataType": channel
        }
        try:
            await self._ws.send(json.dumps(msg))
            self._active_subscriptions.add(channel)
            logger.debug(f"Subscribed to {channel}")
        except Exception as e:
            logger.error(f"Failed to subscribe to {channel}: {e}")

# Instância global
_ws_manager = BingXWebSocketManager()

def get_ws_manager() -> BingXWebSocketManager:
    return _ws_manager
