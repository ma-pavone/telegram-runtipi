# src/app.py
import logging
import sys
import os
from config.settings import BotConfig
from bot.core import RuntipiBot

# Configuração centralizada de logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    stream=sys.stdout
)

# Reduz a verbosidade de bibliotecas HTTP
for logger_name in ['httpx', 'urllib3', 'aiohttp', 'telegram']:
    logging.getLogger(logger_name).setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

def main():
    """Função principal para iniciar o bot."""
    logger.info("=" * 50)
    logger.info("🤖 INICIANDO RUNTIPI TELEGRAM BOT")
    logger.info("=" * 50)

    try:
        # Carrega configuração a partir do ambiente
        config = BotConfig.from_env()
        logger.info("✅ Configuração carregada com sucesso.")

        # Cria e executa o bot
        bot = RuntipiBot(config)
        if not bot.run():
            logger.error("❌ Bot finalizado com erro.")
            sys.exit(1)

        logger.info("✅ Bot finalizado com sucesso.")
        sys.exit(0)

    except ValueError as e:
        logger.error(f"💥 Erro de configuração: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        logger.info("🛑 Bot interrompido pelo usuário.")
        sys.exit(0)
    except Exception as e:
        logger.critical(f"💥 Erro fatal na aplicação: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()