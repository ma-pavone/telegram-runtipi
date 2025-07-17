import logging
import asyncio
import sys

from config.settings import BotConfig
from api.runtipi import RuntipiAPI
from bot.core import RuntipiBot
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout,
)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("requests").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

async def main() -> None:
    """Função principal para configurar e iniciar o bot."""
    try:
        config = BotConfig.from_env()
        logger.info("Configuração carregada com sucesso.")
        runtipi_api = RuntipiAPI(
            username=config.runtipi_username,
            password=config.runtipi_password
        )
        bot = RuntipiBot(config=config, runtipi_api=runtipi_api)
        await bot.run()
        
    except (ValueError, FileNotFoundError) as e:
        logger.critical(f"Erro fatal de configuração: {e}")
        sys.exit(1)
    except Exception as e:
        logger.critical(f"Erro inesperado no nível raiz da aplicação: {e}", exc_info=True)
        sys.exit(1)

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Programa encerrado pelo usuário.")