# src/commands/status.py

from telegram import Update
from telegram.ext import ContextTypes
import logging

logger = logging.getLogger(__name__)

async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE, api):
    await update.message.reply_text("🔄 Verificando status dos apps...")
    logger.info("[API Runtipi] Requisição para status dos apps iniciada")

    apps_data = api.get_installed_apps()
    if not apps_data or 'installed' not in apps_data:
        await update.message.reply_text("❌ Erro ao obter status dos apps")
        logger.error("[API Runtipi] Erro ao obter status dos apps: resposta malformada ou vazia")
        return

    running = []
    stopped = []

    for app in apps_data['installed']:
        app_id = app['info']['id']
        status = app['app']['status']

        if status == "running":
            running.append(f"🟢 `{app_id}`")
        else:
            stopped.append(f"🔴 `{app_id}`")

    message = "📊 *Status dos Apps (IDs técnicos):*\n\n"

    if running:
        message += "*🟢 Rodando:*\n" + "\n".join(running) + "\n\n"

    if stopped:
        message += "*🔴 Parados:*\n" + "\n".join(stopped)

    if not running and not stopped:
        message += "Nenhum app encontrado"

    await update.message.reply_text(message, parse_mode='Markdown')
    logger.info("[API Runtipi] Status dos apps listado com sucesso")