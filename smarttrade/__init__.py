"""
SmartTrade - Cliente para API da BingX com suporte a trading e análise de dados.
"""

__version__ = "0.3.0"

__all__ = [
    "BingXClient",
    "BingXError",
    "BingXAPIError",
    "BingXConfig",
]

from .bingx_client import BingXClient, BingXError, BingXAPIError
from .config import BingXConfig
