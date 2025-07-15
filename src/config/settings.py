import os
from dataclasses import dataclass
from typing import Optional


@dataclass
class BotConfig:
    """Configuração do bot Telegram com validação integrada"""
    telegram_token: str
    allowed_chat_id: int
    scripts_dir: str
    runtipi_host: str
    runtipi_username: str
    runtipi_password: str

    @classmethod
    def from_env(cls) -> 'BotConfig':
        """Cria configuração a partir de variáveis de ambiente"""
        config = cls(
            telegram_token=os.getenv('TELEGRAM_TOKEN', ''),
            allowed_chat_id=int(os.getenv('TELEGRAM_CHAT_ID', '0')),
            scripts_dir=os.getenv('SCRIPTS_PATH', '/scripts'),
            runtipi_host=os.getenv('RUNTIPI_HOST', 'http://localhost'),
            runtipi_username=os.getenv('RUNTIPI_USERNAME', ''),
            runtipi_password=os.getenv('RUNTIPI_PASSWORD', '')
        )
        
        if not config.is_valid():
            raise ValueError("Configuração inválida: verifique as variáveis de ambiente")
        
        return config

    def is_valid(self) -> bool:
        """Valida configurações obrigatórias"""
        return all([
            self.telegram_token,
            self.allowed_chat_id > 0,
            self.runtipi_username,
            self.runtipi_password
        ])

    @property
    def is_production(self) -> bool:
        """Verifica se está em ambiente de produção"""
        return os.getenv('ENV', 'development').lower() == 'production'