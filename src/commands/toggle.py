# src/commands/toggle.py

from telegram import Update
from telegram.ext import ContextTypes
import logging

logger = logging.getLogger(__name__)

async def toggle_command(update: Update, context: ContextTypes.DEFAULT_TYPE, api):
    if not context.args:
        await update.message.reply_text("❌ Você precisa especificar o ID técnico do app. Ex: `toggle jellyfin`", parse_mode='Markdown')
        return

    app_id = context.args[0].strip().lower()
    await update.message.reply_text(f"🔄 Processando toggle para: `{app_id}`", parse_mode='Markdown')
    logger.info(f"[API Runtipi] Toggle solicitado para app_id: {app_id}")

    apps_data = api.get_installed_apps()
    if not apps_data or 'installed' not in apps_data:
        await update.message.reply_text("❌ Erro ao obter lista de apps")
        logger.error("[API Runtipi] Falha ao obter lista de apps durante toggle")
        return

    # Localiza app pelo ID tecnico
    target_app = None
    for app in apps_data['installed']:
        if app['info']['id'].lower() == app_id:
            target_app = app
            break

    if not target_app:
        await update.message.reply_text(f"❌ App `{app_id}` não encontrado", parse_mode='Markdown')
        logger.warning(f"[API Runtipi] App '{app_id}' não encontrado para toggle")
        return

    current_status = target_app['app']['status']
    app_urn = target_app['info']['urn']

    action = "stop" if current_status == "running" else "start"
    action_text = "Parando" if action == "stop" else "Iniciando"

    await update.message.reply_text(f"🔄 {action_text} `{app_id}`...", parse_mode='Markdown')
    logger.info(f"[API Runtipi] Enviando POST para /api/app-lifecycle/{{urn}}/{{{action}}}")

    success = api.toggle_app(app_urn, action)

    if success:
        resultado = "parado" if action == "stop" else "iniciado"
        await update.message.reply_text(f"✅ App `{app_id}` {resultado} com sucesso!", parse_mode='Markdown')
        logger.info(f"[API Runtipi] Toggle executado com sucesso para '{app_id}' => {resultado}")
    else:
        await update.message.reply_text(f"❌ Erro ao {action_text.lower()} `{app_id}`", parse_mode='Markdown')
        logger.error(f"[API Runtipi] Erro ao executar toggle para '{app_id}'")
