import os
import dataclasses
from dotenv import load_dotenv
from typing import final
load_dotenv()

@final
@dataclasses.dataclass(frozen=True)
class BotConfig:
    """
    Estrutura de dados imutável para armazenar as configurações da aplicação.
    """
    telegram_token: str
    telegram_chat_id: int
    runtipi_username: str
    runtipi_password: str
    scripts_path: str

    @classmethod
    def from_env(cls) -> 'BotConfig':
        """
        Cria uma instância de BotConfig a partir de variáveis de ambiente.
        Levanta um ValueError se uma variável essencial estiver ausente ou inválida.
        """
        try:
            return cls(
                telegram_token=os.environ["TELEGRAM_TOKEN"],
                telegram_chat_id=int(os.environ["TELEGRAM_CHAT_ID"]),
                runtipi_username=os.environ["RUNTIPI_USERNAME"],
                runtipi_password=os.environ["RUNTIPI_PASSWORD"],
                scripts_path=os.getenv("SCRIPTS_PATH", "/scripts"),
            )
        except (KeyError, ValueError) as e:
            raise ValueError(f"Variável de ambiente ausente ou com tipo inválido: {e}") from e