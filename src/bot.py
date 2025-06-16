import os
import logging
from telegram.ext import Application, CommandHandler, MessageHandler, filters

from runtipi_api import RuntipiAPI
from commands.help import help_command
from commands.apps import apps_command
from commands.status import status_command
from commands.toggle import toggle_command

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def is_authorized(chat_id, allowed_chat_id):
    return chat_id == allowed_chat_id

def main():
    TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
    TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
    RUNTIPI_HOST = os.getenv('RUNTIPI_HOST', 'http://localhost')
    RUNTIPI_USERNAME = os.getenv('RUNTIPI_USERNAME')
    RUNTIPI_PASSWORD = os.getenv('RUNTIPI_PASSWORD')

    if not all([TELEGRAM_TOKEN, TELEGRAM_CHAT_ID, RUNTIPI_USERNAME, RUNTIPI_PASSWORD]):
        logger.error("Variáveis de ambiente obrigatórias não definidas!")
        return

    runtipi_api = RuntipiAPI(RUNTIPI_HOST, RUNTIPI_USERNAME, RUNTIPI_PASSWORD)

    application = Application.builder().token(TELEGRAM_TOKEN).build()

    allowed_chat_id = int(TELEGRAM_CHAT_ID)

    # Handlers comandos fixos
    application.add_handler(CommandHandler("help", lambda update, context: help_command(update, context)))
    application.add_handler(CommandHandler("apps", lambda update, context: 
        apps_command(update, context, runtipi_api)))
    application.add_handler(CommandHandler("status", lambda update, context: 
        status_command(update, context, runtipi_api)))

    # Handler texto para toggle, só se autorizado
    async def text_handler(update, context):
        chat_id = update.effective_chat.id
        if not is_authorized(chat_id, allowed_chat_id):
            await update.message.reply_text("❌ Acesso negado!")
            logger.warning(f"Acesso negado para chat_id={chat_id}")
            return
        await toggle_command(update, context, runtipi_api)

    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))

    logger.info("Bot iniciado")
    application.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
