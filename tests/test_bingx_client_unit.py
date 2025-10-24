"""
Testes unitários para BingXClient (sem chamadas reais à API).
"""
import time
import pytest
from unittest.mock import Mock, patch, MagicMock

from smarttrade.bingx_client import (
    BingXClient,
    BingXError,
    BingXAPIError,
    BingXConfig
)


class TestBingXClientInitialization:
    """Testes de inicialização do cliente"""
    
    def test_default_initialization(self):
        """Testa inicialização com configuração padrão"""
        client = BingXClient()
        assert client.config.base_url == "https://open-api.bingx.com"
        assert client.config.timeout == 10.0
        assert client.config.max_retries == 3
        client.close()
    
    def test_custom_config(self):
        """Testa inicialização com configuração customizada"""
        config = BingXConfig(timeout=5.0, max_retries=5)
        client = BingXClient(config)
        assert client.config.timeout == 5.0
        assert client.config.max_retries == 5
        client.close()
    
    def test_context_manager(self):
        """Testa uso como context manager"""
        with BingXClient() as client:
            assert client is not None
        # Verifica que foi fechado
        assert client._client.is_closed


class TestRateLimiting:
    """Testes de rate limiting"""
    
    def test_rate_limit_tracking(self):
        """Testa que requests são rastreadas"""
        config = BingXConfig(rate_limit_calls=5, rate_limit_period=1)
        client = BingXClient(config)
        
        # Faz algumas checagens
        for _ in range(3):
            client._check_rate_limit()
        
        assert len(client._request_times) == 3
        client.close()
    
    def test_rate_limit_enforcement(self):
        """Testa que rate limit é aplicado"""
        config = BingXConfig(rate_limit_calls=2, rate_limit_period=1)
        client = BingXClient(config)
        
        # Faz 2 requests (limite)
        client._check_rate_limit()
        client._check_rate_limit()
        
        # Terceiro deve fazer sleep
        start = time.time()
        client._check_rate_limit()
        elapsed = time.time() - start
        
        # Deve ter esperado pelo menos 0.5s
        assert elapsed >= 0.5
        client.close()
    
    def test_rate_limit_cleanup(self):
        """Testa que requests antigas são removidas"""
        config = BingXConfig(rate_limit_calls=5, rate_limit_period=1)
        client = BingXClient(config)
        
        # Adiciona request antiga manualmente
        old_time = time.time() - 2.0
        client._request_times.append(old_time)
        
        # Faz nova request
        client._check_rate_limit()
        
        # Request antiga deve ter sido removida
        assert old_time not in client._request_times
        client.close()


class TestAPIErrorHandling:
    """Testes de tratamento de erros da API"""
    
    @patch('smarttrade.bingx_client.httpx.Client.get')
    def test_api_error_response(self, mock_get):
        """Testa tratamento de erro retornado pela API"""
        mock_response = Mock()
        mock_response.json.return_value = {
            "code": "100001",
            "msg": "Invalid symbol"
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        client = BingXClient()
        
        with pytest.raises(BingXAPIError) as exc_info:
            client._get("/test")
        
        assert exc_info.value.code == "100001"
        assert exc_info.value.message == "Invalid symbol"
        client.close()
    
    @patch('smarttrade.bingx_client.httpx.Client.get')
    def test_http_error(self, mock_get):
        """Testa tratamento de erro HTTP"""
        import httpx
        
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.text = "Not found"
        
        mock_get.side_effect = httpx.HTTPStatusError(
            "404",
            request=Mock(),
            response=mock_response
        )
        
        client = BingXClient()
        
        with pytest.raises(BingXError) as exc_info:
            client._get("/test")
        
        assert "404" in str(exc_info.value)
        client.close()
    
    @patch('smarttrade.bingx_client.httpx.Client.get')
    def test_network_error(self, mock_get):
        """Testa tratamento de erro de rede"""
        import httpx
        
        mock_get.side_effect = httpx.NetworkError("Connection failed")
        
        client = BingXClient()
        
        with pytest.raises(BingXError):
            client._get("/test")
        
        client.close()


class TestInputValidation:
    """Testes de validação de entrada"""
    
    def test_invalid_symbol_empty(self):
        """Testa validação de símbolo vazio"""
        client = BingXClient()
        
        with pytest.raises(ValueError, match="Invalid symbol"):
            client.spot_ticker_24h("")
        
        client.close()
    
    def test_invalid_symbol_none(self):
        """Testa validação de símbolo None"""
        client = BingXClient()
        
        with pytest.raises(ValueError, match="Invalid symbol"):
            client.spot_ticker_24h(None)
        
        client.close()
    
    def test_invalid_limit_too_low(self):
        """Testa validação de limit muito baixo"""
        client = BingXClient()
        
        with pytest.raises(ValueError, match="Invalid limit"):
            client.swap_klines("BTC-USDT", "1m", 0)
        
        client.close()
    
    def test_invalid_limit_too_high(self):
        """Testa validação de limit muito alto"""
        client = BingXClient()
        
        with pytest.raises(ValueError, match="Invalid limit"):
            client.swap_klines("BTC-USDT", "1m", 2000)
        
        client.close()
    
    def test_invalid_interval(self):
        """Testa validação de intervalo inválido"""
        client = BingXClient()
        
        with pytest.raises(ValueError, match="Invalid interval"):
            client.swap_klines("BTC-USDT", "invalid", 10)
        
        client.close()
    
    def test_valid_intervals(self):
        """Testa que intervalos válidos são aceitos"""
        client = BingXClient()
        
        valid_intervals = ["1m", "5m", "15m", "30m", "1h", "4h", "1d", "1w"]
        
        # Mock da requisição
        with patch.object(client, '_get') as mock_get:
            mock_get.return_value = {"data": []}
            
            for interval in valid_intervals:
                # Não deve lançar exceção
                client.swap_klines("BTC-USDT", interval, 10)
        
        client.close()


class TestTimestamp:
    """Testes de geração de timestamp"""
    
    def test_timestamp_format(self):
        """Testa que timestamp está no formato correto (ms)"""
        client = BingXClient()
        ts = client._timestamp_ms()
        
        # Timestamp deve ser um inteiro grande (ms desde epoch)
        assert isinstance(ts, int)
        assert ts > 1000000000000  # Maior que 2001 em ms
        
        client.close()
    
    def test_timestamp_increases(self):
        """Testa que timestamp aumenta com o tempo"""
        client = BingXClient()
        
        ts1 = client._timestamp_ms()
        time.sleep(0.01)
        ts2 = client._timestamp_ms()
        
        assert ts2 > ts1
        
        client.close()


@patch('smarttrade.bingx_client.httpx.Client.get')
class TestSuccessfulRequests:
    """Testes de requisições bem-sucedidas"""
    
    def test_spot_ticker_success(self, mock_get):
        """Testa chamada bem-sucedida de spot ticker"""
        mock_response = Mock()
        mock_response.json.return_value = {
            "code": 0,
            "data": [{
                "symbol": "BTC-USDT",
                "lastPrice": "50000.00",
                "volume": "1000"
            }]
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        client = BingXClient()
        result = client.spot_ticker_24h("BTC-USDT")
        
        assert result["symbol"] == "BTC-USDT"
        assert result["lastPrice"] == "50000.00"
        
        client.close()
    
    def test_swap_ticker_success(self, mock_get):
        """Testa chamada bem-sucedida de swap ticker"""
        mock_response = Mock()
        mock_response.json.return_value = {
            "code": 0,
            "data": {
                "symbol": "BTC-USDT",
                "lastPrice": "50000.00"
            }
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        client = BingXClient()
        result = client.swap_ticker("BTC-USDT")
        
        assert result["symbol"] == "BTC-USDT"
        
        client.close()
    
    def test_swap_klines_success(self, mock_get):
        """Testa chamada bem-sucedida de swap klines"""
        mock_response = Mock()
        mock_response.json.return_value = {
            "code": 0,
            "data": [
                {
                    "time": 1634567890000,
                    "open": "50000",
                    "close": "50100",
                    "high": "50200",
                    "low": "49900",
                    "volume": "100"
                }
            ]
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        client = BingXClient()
        result = client.swap_klines("BTC-USDT", "1m", 1)
        
        assert len(result) == 1
        assert result[0]["open"] == "50000"
        
        client.close()
