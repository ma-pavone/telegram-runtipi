from telegram import Update
from telegram.ext import ContextTypes
from typing import final

from bot.utils.messages import BotMessages

@final
class BasicCommandHandler:
    """Handlers para comandos básicos como /start e /help."""

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Envia uma mensagem de boas-vindas."""
        await self.help(update, context)

    async def help(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Envia a mensagem de ajuda."""
        message = BotMessages.get_help_message()
        await update.effective_chat.send_message(message, parse_mode='Markdown')