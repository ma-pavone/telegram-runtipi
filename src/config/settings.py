import os
import dataclasses
from dotenv import load_dotenv
from typing import final
from pathlib import Path

load_dotenv()

@final
@dataclasses.dataclass(frozen=True)
class BotConfig:
    """
    Estrutura de dados imutável para armazenar as configurações da aplicação.
    """
    telegram_token: str
    telegram_chat_id: int
    runtipi_host: str  # ✅ Novo campo para URL configurável
    runtipi_username: str
    runtipi_password: str
    scripts_path: str
    api_timeout: int = 15  # ✅ Timeout configurável
    cache_ttl: int = 15    # ✅ TTL do cache configurável

    @classmethod
    def from_env(cls) -> 'BotConfig':
        """
        Cria uma instância de BotConfig a partir de variáveis de ambiente.
        Levanta um ValueError se uma variável essencial estiver ausente ou inválida.
        """
        try:
            chat_id_str = os.environ["TELEGRAM_CHAT_ID"]
            try:
                chat_id = int(chat_id_str)
            except ValueError:
                raise ValueError(f"TELEGRAM_CHAT_ID deve ser um número inteiro, recebido: {chat_id_str}")
            scripts_path = os.getenv("SCRIPTS_PATH", "/scripts")
            if not Path(scripts_path).exists():
                raise FileNotFoundError(f"Diretório de scripts não encontrado: {scripts_path}")
            runtipi_host = os.getenv("RUNTIPI_HOST", "http://localhost:8080")
            if not runtipi_host.startswith(('http://', 'https://')):
                raise ValueError(f"RUNTIPI_HOST deve começar com http:// ou https://, recebido: {runtipi_host}")
            
            return cls(
                telegram_token=os.environ["TELEGRAM_TOKEN"],
                telegram_chat_id=chat_id,
                runtipi_host=runtipi_host,
                runtipi_username=os.environ["RUNTIPI_USERNAME"],
                runtipi_password=os.environ["RUNTIPI_PASSWORD"],
                scripts_path=scripts_path,
                api_timeout=int(os.getenv("API_TIMEOUT", "15")),
                cache_ttl=int(os.getenv("CACHE_TTL", "15")),
            )
        except KeyError as e:
            raise ValueError(f"Variável de ambiente obrigatória ausente: {e}") from e
        except (ValueError, FileNotFoundError) as e:
            raise ValueError(f"Configuração inválida: {e}") from e

    def __post_init__(self):
        """Validações adicionais após inicialização."""
        if self.api_timeout <= 0:
            raise ValueError("API_TIMEOUT deve ser maior que zero")
        if self.cache_ttl <= 0:
            raise ValueError("CACHE_TTL deve ser maior que zero")