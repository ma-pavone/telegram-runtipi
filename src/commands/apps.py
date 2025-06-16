from telegram import Update
from telegram.ext import ContextTypes
import logging

logger = logging.getLogger(__name__)

async def apps_command(update: Update, context: ContextTypes.DEFAULT_TYPE, api):
    await update.message.reply_text("🔄 Obtendo lista de apps...")
    logger.info("[API Runtipi] Requisição para lista de apps iniciada")

    apps_data = api.get_installed_apps()
    if not apps_data or 'installed' not in apps_data:
        await update.message.reply_text("❌ Erro ao obter lista de apps")
        logger.error("[API Runtipi] Erro ao obter lista de apps: resposta malformada ou vazia")
        return

    apps_list = []
    for app in apps_data['installed']:
        app_id = app['info']['id']  # nome técnico
        status = app['app']['status']
        status_emoji = "🟢" if status == "running" else "🔴"
        apps_list.append(f"{status_emoji} `{app_id}`")

    if apps_list:
        message = "📱 *Apps Instalados (nomes técnicos):*\n\n" + "\n".join(apps_list)
    else:
        message = "📱 Nenhum app instalado encontrado"

    await update.message.reply_text(message, parse_mode='Markdown')
    logger.info("[API Runtipi] Lista de apps enviada com sucesso")
