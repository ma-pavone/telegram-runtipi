import logging
from functools import wraps
from telegram import Update
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)


def require_auth(allowed_chat_id: int):
    """Decorator para verificar autorização"""
    def decorator(func):
        @wraps(func)
        async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
            if update.effective_chat.id != allowed_chat_id:
                await update.message.reply_text("❌ Acesso negado!")
                logger.warning(f"Acesso negado para chat_id: {update.effective_chat.id}")
                return
            return await func(update, context, *args, **kwargs)
        return wrapper
    return decorator