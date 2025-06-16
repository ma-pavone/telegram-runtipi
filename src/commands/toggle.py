# src/commands/toggle.py

from telegram import Update
from telegram.ext import ContextTypes
import logging

logger = logging.getLogger(__name__)

async def toggle_command(update: Update, context: ContextTypes.DEFAULT_TYPE, api):
    if not context.args:
        await update.message.reply_text("⚠️ Você precisa informar o nome técnico do app para togglar")
        return

    app_id = context.args[0]
    logger.info(f"[API Runtipi] Requisição de toggle recebida para o app: {app_id}")

    app_data = api.get_app_status(app_id)
    if not app_data or 'app' not in app_data:
        await update.message.reply_text(f"❌ Não foi possível encontrar o app `{app_id}`")
        logger.error(f"[API Runtipi] Falha ao obter status do app {app_id}: {app_data}")
        return

    current_status = app_data['app']['status']
    logger.info(f"[API Runtipi] Status atual do app {app_id}: {current_status}")

    if current_status == "running":
        logger.info(f"[API Runtipi] Parando app {app_id}...")
        success = api.stop_app(app_id)
        action = "parar"
    else:
        logger.info(f"[API Runtipi] Iniciando app {app_id}...")
        success = api.start_app(app_id)
        action = "iniciar"

    if success:
        await update.message.reply_text(f"✅ App `{app_id}` foi solicitado para {action}")
        logger.info(f"[API Runtipi] App {app_id} foi solicitado para {action} com sucesso")
    else:
        await update.message.reply_text(f"❌ Falha ao tentar {action} o app `{app_id}`")
        logger.error(f"[API Runtipi] Falha ao tentar {action} o app {app_id}")
