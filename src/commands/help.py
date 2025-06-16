from telegram import Update
from telegram.ext import ContextTypes
import logging

logger = logging.getLogger(__name__)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"[Telegram] /help chamado por chat_id={update.effective_chat.id}")
    help_text = """
*Bot Runtipi Controller*

Comandos disponíveis:
/help - Mostrar esta mensagem
/apps - Listar apps instalados
/status - Mostrar status dos apps
<nome_app> - Ligar/desligar app pelo nome técnico

Exemplo:
/jellyfin (liga/desliga o app jellyfin)
    """
    await update.message.reply_text(help_text)