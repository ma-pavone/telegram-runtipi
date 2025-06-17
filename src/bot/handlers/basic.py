# src/bot/handlers/basic.py
from telegram import Update
from telegram.ext import ContextTypes
from bot.middleware.auth import require_auth
from bot.utils.messages import BotMessages
import logging

logger = logging.getLogger(__name__)

class BasicHandlers:
    def __init__(self, allowed_chat_id: int):
        self.allowed_chat_id = allowed_chat_id

    @property
    def auth_required(self):
        return require_auth(self.allowed_chat_id)

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Comando de ajuda"""
        @self.auth_required
        async def _help_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
            await update.message.reply_text(
                BotMessages.help_text(), 
                parse_mode='Markdown'
            )
        
        await _help_handler(update, context)

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Comando start (alias para help)"""
        await self.help_command(update, context)