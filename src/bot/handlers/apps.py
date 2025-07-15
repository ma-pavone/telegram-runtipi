import asyncio
import logging
from telegram import Update
from telegram.ext import ContextTypes
from bot.middleware.auth import require_auth
from bot.utils.messages import BotMessages
from api.runtipi import RuntipiAPI

logger = logging.getLogger(__name__)


class AppsHandlers:
    def __init__(self, allowed_chat_id: int, api: RuntipiAPI):
        self.allowed_chat_id = allowed_chat_id
        self.api = api
        self.auth_required = require_auth(allowed_chat_id)

    async def apps_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Lista apps instalados com status"""
        @self.auth_required
        async def handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
            await update.message.reply_text("🔄 Obtendo lista de apps...")
            
            try:
                apps_data = await asyncio.to_thread(self.api.get_installed_apps)
                message = BotMessages.format_apps_list(apps_data)
                await update.message.reply_text(message, parse_mode='Markdown')
            except Exception as e:
                logger.error(f"Erro no comando apps: {e}")
                await update.message.reply_text("❌ Erro ao obter apps")
        
        await handler(update, context)

    async def status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Status resumido dos apps"""
        @self.auth_required
        async def handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
            await update.message.reply_text("🔄 Verificando status...")
            
            try:
                apps_data = await asyncio.to_thread(self.api.get_installed_apps)
                message = BotMessages.format_status_summary(apps_data)
                await update.message.reply_text(message, parse_mode='Markdown')
            except Exception as e:
                logger.error(f"Erro no comando status: {e}")
                await update.message.reply_text("❌ Erro ao obter status")
        
        await handler(update, context)

    async def toggle_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Toggle de apps via mensagem de texto"""
        @self.auth_required
        async def handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
            app_id = update.message.text.strip().lower()
            
            if not self._is_valid_app_id(app_id):
                await update.message.reply_text(
                    "⚠️ Digite apenas o nome técnico do app\n"
                    "Exemplo: `jellyfin`, `sonarr`, `radarr`",
                    parse_mode='Markdown'
                )
                return

            await update.message.reply_text(f"🔄 Processando `{app_id}`...", parse_mode='Markdown')
            
            try:
                current_status = await asyncio.to_thread(self.api.get_app_status, app_id)
                
                if not current_status:
                    await update.message.reply_text(f"❌ App `{app_id}` não encontrado", parse_mode='Markdown')
                    return

                action = "stop" if current_status == "running" else "start"
                action_text = "parado" if action == "stop" else "iniciado"
                
                await update.message.reply_text(f"⚡ {action_text.capitalize()} `{app_id}`...", parse_mode='Markdown')
                
                success = await asyncio.to_thread(self.api.toggle_app_action, app_id, action)
                
                if success:
                    status_emoji = "🔴" if action == "stop" else "🟢"
                    await update.message.reply_text(f"{status_emoji} App `{app_id}` {action_text}", parse_mode='Markdown')
                else:
                    await update.message.reply_text(f"❌ Falha ao {action_text.replace('o', 'ar')} `{app_id}`", parse_mode='Markdown')
                    
            except Exception as e:
                logger.error(f"Erro no toggle {app_id}: {e}")
                await update.message.reply_text(f"❌ Erro ao processar `{app_id}`", parse_mode='Markdown')

        await handler(update, context)

    def _is_valid_app_id(self, app_id: str) -> bool:
        """Valida ID do app"""
        return app_id and len(app_id) <= 50 and ' ' not in app_id