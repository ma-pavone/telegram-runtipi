# src/config/settings.py
import os
from dataclasses import dataclass
import logging

@dataclass
class BotConfig:
    telegram_token: str
    allowed_chat_id: int
    scripts_dir: str
    runtipi_host: str
    runtipi_username: str
    runtipi_password: str

    @classmethod
    def from_env(cls):
        return cls(
            telegram_token=os.getenv('TELEGRAM_TOKEN'),
            allowed_chat_id=int(os.getenv('TELEGRAM_CHAT_ID')),
            scripts_dir=os.getenv('SCRIPTS_PATH', '/scripts'),
            runtipi_host=os.getenv('RUNTIPI_HOST', 'http://localhost'),
            runtipi_username=os.getenv('RUNTIPI_USERNAME'),
            runtipi_password=os.getenv('RUNTIPI_PASSWORD')
        )

    def validate(self) -> bool:
        """Valida se todas as configurações obrigatórias estão definidas"""
        required_fields = [
            self.telegram_token,
            self.allowed_chat_id,
            self.runtipi_username,
            self.runtipi_password
        ]
        return all(required_fields)