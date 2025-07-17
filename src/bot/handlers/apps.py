import asyncio
import logging
from telegram import Update, constants
from telegram.ext import ContextTypes
from bot.middleware.auth import require_auth
from bot.utils.messages import BotMessages
from api.runtipi import RuntipiAPI

logger = logging.getLogger(__name__)

class AppsHandlers:
    def __init__(self, allowed_chat_id: int, api: RuntipiAPI):
        self.allowed_chat_id = allowed_chat_id
        self.api = api

    @require_auth
    async def apps_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Lista todos os apps instalados e seus status."""
        await update.message.reply_text("🔄 Obtendo lista de apps...")
        try:
            apps = await asyncio.to_thread(self.api.get_installed_apps)
            message = BotMessages.format_apps_list(apps)
            await update.message.reply_text(message, parse_mode=constants.ParseMode.MARKDOWN_V2)
        except Exception as e:
            logger.error(f"Erro no comando /apps: {e}", exc_info=True)
            await update.message.reply_text("❌ Erro ao obter a lista de apps.")

    @require_auth
    async def status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Fornece um resumo do status dos apps (rodando/parados)."""
        await update.message.reply_text("🔄 Verificando status dos apps...")
        try:
            apps = await asyncio.to_thread(self.api.get_installed_apps)
            message = BotMessages.format_status_summary(apps)
            await update.message.reply_text(message, parse_mode=constants.ParseMode.MARKDOWN_V2)
        except Exception as e:
            logger.error(f"Erro no comando /status: {e}", exc_info=True)
            await update.message.reply_text("❌ Erro ao obter o status dos apps.")

    @require_auth
    async def toggle_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Alterna o estado de um app (liga/desliga) com base no nome."""
        app_id = update.message.text.strip().lower()
        if not self._is_valid_app_id(app_id):
            await update.message.reply_text("⚠️ Nome de app inválido. Use apenas o ID, ex: `jellyfin`.", parse_mode=constants.ParseMode.MARKDOWN_V2)
            return

        await update.message.reply_text(f"🔄 Processando `{app_id}`...", parse_mode=constants.ParseMode.MARKDOWN_V2)
        
        try:
            app_data = await asyncio.to_thread(self.api.get_app_data, app_id)
            if not app_data:
                await update.message.reply_text(f"❌ App `{app_id}` não encontrado.", parse_mode=constants.ParseMode.MARKDOWN_V2)
                return

            is_running = app_data.get('app', {}).get('status') == 'running'
            action_text = "parando" if is_running else "iniciando"
            final_state = "parado" if is_running else "iniciado"
            
            await update.message.reply_text(f"⏳ {action_text.capitalize()} `{app_id}`...", parse_mode=constants.ParseMode.MARKDOWN_V2)

            success = await asyncio.to_thread(self.api.toggle_app_action, app_id)
            
            if success:
                status_emoji = "🔴" if is_running else "🟢"
                await update.message.reply_text(f"{status_emoji} App `{app_id}` foi {final_state} com sucesso!", parse_mode=constants.ParseMode.MARKDOWN_V2)
            else:
                await update.message.reply_text(f"❌ Falha ao processar `{app_id}`.", parse_mode=constants.ParseMode.MARKDOWN_V2)

        except Exception as e:
            logger.error(f"Erro ao dar toggle no app {app_id}: {e}", exc_info=True)
            await update.message.reply_text(f"❌ Erro ao processar `{app_id}`.", parse_mode=constants.ParseMode.MARKDOWN_V2)

    def _is_valid_app_id(self, app_id: str) -> bool:
        """Valida o ID de um app para segurança e consistência."""
        return app_id and ' ' not in app_id and 2 < len(app_id) < 50