# src/bot/middleware/auth.py
from functools import wraps
from telegram import Update
from telegram.ext import ContextTypes
import logging

logger = logging.getLogger(__name__)

def require_auth(allowed_chat_id: int):
    """Decorator para verificar autorização do usuário"""
    def decorator(func):
        @wraps(func)
        async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
            if update.effective_chat.id != allowed_chat_id:
                await update.message.reply_text("❌ Acesso negado!")
                logger.warning(f"Tentativa de acesso negada para chat_id: {update.effective_chat.id}")
                return
            return await func(update, context, *args, **kwargs)
        return wrapper
    return decorator