"""
Módulo de configuração centralizada para SmartTrade.
Suporta configuração via environment variables com valores padrão sensatos.
"""
from __future__ import annotations

import os
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class BingXConfig(BaseSettings):
    """Configuração para o cliente BingX"""
    
    base_url: str = "https://open-api.bingx.com"
    timeout: float = 10.0
    max_retries: int = 3
    rate_limit_calls: int = 100
    rate_limit_period: int = 60  # segundos
    
    model_config = SettingsConfigDict(
        env_prefix="BINGX_",
        case_sensitive=False,
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


class AppConfig(BaseSettings):
    """Configuração geral da aplicação"""
    
    log_level: str = "INFO"
    cache_ttl_seconds: int = 5
    
    model_config = SettingsConfigDict(
        case_sensitive=False,
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


class WebConfig(BaseSettings):
    """Configuração do servidor web"""
    
    host: str = "0.0.0.0"
    port: int = 8000
    
    model_config = SettingsConfigDict(
        env_prefix="WEB_",
        case_sensitive=False,
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


# Instâncias globais de configuração
bingx_config = BingXConfig()
app_config = AppConfig()
web_config = WebConfig()
