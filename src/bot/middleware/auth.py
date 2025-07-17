import logging
from functools import wraps
from typing import Callable, final

from telegram import Update
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)

@final
class AuthMiddleware:
    """
    Middleware que funciona como um decorador para restringir o acesso a um chat_id específico.
    """
    def __init__(self, allowed_chat_id: int):
        self._allowed_chat_id = allowed_chat_id
        if not isinstance(self._allowed_chat_id, int):
            raise TypeError("allowed_chat_id deve ser um inteiro.")

    def __call__(self, func: Callable) -> Callable:
        """Permite que a instância da classe seja usada como um decorador."""
        @wraps(func)
        async def wrapped(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs) -> None:
            if not update or not update.effective_chat:
                return

            if update.effective_chat.id != self._allowed_chat_id:
                logger.warning(f"Acesso negado para o chat_id: {update.effective_chat.id}")
                await update.effective_chat.send_message("⛔ Acesso negado. Este bot é privado.")
                return
            
            await func(update, context, *args, **kwargs)
        return wrapped