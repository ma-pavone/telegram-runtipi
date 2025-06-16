# src/bot/handlers/apps.py
import asyncio
from telegram import Update
from telegram.ext import ContextTypes
from bot.middleware.auth import require_auth
from bot.utils.messages import BotMessages
from api.runtipi import RuntipiAPI
import logging

logger = logging.getLogger(__name__)

class AppsHandlers:
    def __init__(self, allowed_chat_id: int, api: RuntipiAPI):
        self.allowed_chat_id = allowed_chat_id
        self.api = api

    @property
    def auth_required(self):
        return require_auth(self.allowed_chat_id)

    async def apps_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Lista apps instalados com status"""
        @self.auth_required
        async def _apps_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
            await update.message.reply_text("🔄 Obtendo lista de apps...")
            
            try:
                apps_data = await asyncio.to_thread(self.api.get_installed_apps)
                message = BotMessages.format_apps_list(apps_data)
                await update.message.reply_text(message, parse_mode='Markdown')
                
            except Exception as e:
                logger.error(f"Erro no comando apps: {e}")
                await update.message.reply_text("❌ Erro interno ao obter apps")

        await _apps_handler(update, context)

    async def status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Status resumido dos apps"""
        @self.auth_required
        async def _status_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
            await update.message.reply_text("🔄 Verificando status...")
            
            try:
                apps_data = await asyncio.to_thread(self.api.get_installed_apps)
                message = BotMessages.format_status_summary(apps_data)
                await update.message.reply_text(message, parse_mode='Markdown')
                
            except Exception as e:
                logger.error(f"Erro no comando status: {e}")
                await update.message.reply_text("❌ Erro interno ao obter status")

        await _status_handler(update, context)

    async def toggle_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handler para toggle de apps via mensagem de texto"""
        @self.auth_required
        async def _toggle_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
            app_id = update.message.text.strip().lower()
            
            # Validação básica do nome do app
            if not app_id or len(app_id) > 50 or ' ' in app_id:
                await update.message.reply_text(
                    "⚠️ Digite apenas o nome técnico do app\n"
                    "Exemplo: `jellyfin`, `sonarr`, `radarr`",
                    parse_mode='Markdown'
                )
                return

            await update.message.reply_text(
                f"🔄 Processando toggle para `{app_id}`...", 
                parse_mode='Markdown'
            )
            
            try:
                # Verifica se o app existe e obtém status atual
                app_data = await asyncio.to_thread(self.api.get_app_status, app_id)
                
                if not app_data:
                    await update.message.reply_text(
                        f"❌ App `{app_id}` não encontrado", 
                        parse_mode='Markdown'
                    )
                    return

                current_status = app_data['app']['status']
                action = "stop" if current_status == "running" else "start"
                action_text = "parado" if action == "stop" else "iniciado"
                
                await update.message.reply_text(
                    f"⚡ {action_text.capitalize()} `{app_id}`...", 
                    parse_mode='Markdown'
                )
                
                # Executa a ação
                success = await asyncio.to_thread(self.api.toggle_app_action, app_id, action)
                
                if success:
                    status_emoji = "🔴" if action == "stop" else "🟢"
                    await update.message.reply_text(
                        f"{status_emoji} App `{app_id}` {action_text}",
                        parse_mode='Markdown'
                    )
                else:
                    await update.message.reply_text(
                        f"❌ Falha ao {action_text.replace('o', 'ar')} o app `{app_id}`",
                        parse_mode='Markdown'
                    )
                    
            except Exception as e:
                logger.error(f"Erro no toggle do app {app_id}: {e}")
                await update.message.reply_text(
                    f"❌ Erro interno ao processar `{app_id}`", 
                    parse_mode='Markdown'
                )

        await _toggle_handler(update, context)
