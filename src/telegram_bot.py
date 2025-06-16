# src/telegram_bot.py

import logging
from telegram import Update
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    ContextTypes, filters
)

from commands.start import start_command
from commands.apps import apps_command, status_command
from commands.toggle import toggle_command

logger = logging.getLogger(__name__)

class TelegramBot:
    def __init__(self, token, allowed_chat_id, runtipi_api):
        self.token = token
        self.allowed_chat_id = int(allowed_chat_id)
        self.runtipi_api = runtipi_api
        self.app = Application.builder().token(token).build()

        self._setup_handlers()

    def _setup_handlers(self):
        self.app.add_handler(CommandHandler("start", self._wrap(start_command)))
        self.app.add_handler(CommandHandler("apps", self._wrap(apps_command)))
        self.app.add_handler(CommandHandler("status", self._wrap(status_command)))
        self.app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self._wrap(toggle_command)))

    def _wrap(self, func):
        async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
            if update.effective_chat.id != self.allowed_chat_id:
                await update.message.reply_text("\u274C Acesso negado!")
                return
            await func(update, context, self.runtipi_api)
        return wrapper

    def run(self):
        logger.info("Iniciando bot...")
        self.app.run_polling(drop_pending_updates=True)
