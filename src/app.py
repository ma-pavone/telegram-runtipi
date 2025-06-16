# src/app.py

import logging
import os
from telegram_bot import TelegramBot
from runtipi_api import RuntipiAPI

def main():
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.INFO
    )
    logger = logging.getLogger(__name__)

    TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
    TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
    RUNTIPI_HOST = os.getenv('RUNTIPI_HOST', 'http://localhost')
    RUNTIPI_USERNAME = os.getenv('RUNTIPI_USERNAME')
    RUNTIPI_PASSWORD = os.getenv('RUNTIPI_PASSWORD')

    if not all([TELEGRAM_TOKEN, TELEGRAM_CHAT_ID, RUNTIPI_USERNAME, RUNTIPI_PASSWORD]):
        logger.error("Variáveis de ambiente obrigatórias não definidas!")
        return

    runtipi_api = RuntipiAPI(RUNTIPI_HOST, RUNTIPI_USERNAME, RUNTIPI_PASSWORD)
    bot = TelegramBot(TELEGRAM_TOKEN, TELEGRAM_CHAT_ID, runtipi_api)

    try:
        bot.run()
    except KeyboardInterrupt:
        logger.info("Bot interrompido pelo usuário")
    except Exception as e:
        logger.error(f"Erro no bot: {e}")

if __name__ == '__main__':
    main()
