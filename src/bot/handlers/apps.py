# src/bot/handlers/apps.py

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
        self.auth_required = require_auth(self.allowed_chat_id)

    async def _execute_command(self, update: Update, api_call, formatter, processing_message, error_message):
        """Abstrai a lógica comum de chamada de comando."""
        await update.message.reply_text(processing_message)
        try:
            # Executa a chamada de API bloqueante em uma thread separada
            data = await asyncio.to_thread(api_call)
            message = formatter(data)
            await update.message.reply_text(message, parse_mode=constants.ParseMode.MARKDOWN_V2)
        except Exception as e:
            logger.error(f"Erro ao executar comando: {e}", exc_info=True)
            await update.message.reply_text(error_message)

    @require_auth
    async def apps_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Lista todos os apps instalados e seus status."""
        await self._execute_command(
            update,
            self.api.get_installed_apps,
            BotMessages.format_apps_list,
            "🔄 Obtendo lista de apps...",
            "❌ Erro ao obter a lista de apps."
        )

    @require_auth
    async def status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Fornece um resumo do status dos apps (rodando/parados)."""
        await self._execute_command(
            update,
            self.api.get_installed_apps,
            BotMessages.format_status_summary,
            "🔄 Verificando status dos apps...",
            "❌ Erro ao obter o status dos apps."
        )

    @require_auth
    async def toggle_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Alterna o estado de um app (liga/desliga) com base no nome."""
        app_id = update.message.text.strip().lower()
        if not self._is_valid_app_id(app_id):
            await update.message.reply_text("⚠️ Nome de app inválido. Use apenas o ID, ex: `jellyfin`.", parse_mode=constants.ParseMode.MARKDOWN_V2)
            return

        processing_msg = await update.message.reply_text(f"🔄 Processando `{app_id}`...", parse_mode=constants.ParseMode.MARKDOWN_V2)
        
        try:
            app_data = await asyncio.to_thread(self.api.get_app_data, app_id)
            if not app_data:
                await processing_msg.edit_text(f"❌ App `{app_id}` não encontrado.", parse_mode=constants.ParseMode.MARKDOWN_V2)
                return

            is_running = app_data.get('app', {}).get('status') == 'running'
            action_text = "parando" if is_running else "iniciando"
            final_state_emoji = "🔴" if is_running else "🟢"
            
            await processing_msg.edit_text(f"⏳ {action_text.capitalize()} `{app_id}`...", parse_mode=constants.ParseMode.MARKDOWN_V2)

            success = await asyncio.to_thread(self.api.toggle_app_action, app_id)
            
            if success:
                final_state_text = "parado" if is_running else "iniciado"
                await processing_msg.edit_text(f"{final_state_emoji} App `{app_id}` foi {final_state_text} com sucesso!", parse_mode=constants.ParseMode.MARKDOWN_V2)
            else:
                await processing_msg.edit_text(f"❌ Falha ao {action_text} `{app_id}`. Verifique os logs.", parse_mode=constants.ParseMode.MARKDOWN_V2)

        except Exception as e:
            logger.error(f"Erro ao dar toggle no app {app_id}: {e}", exc_info=True)
            await processing_msg.edit_text(f"❌ Erro inesperado ao processar `{app_id}`.", parse_mode=constants.ParseMode.MARKDOWN_V2)

    def _is_valid_app_id(self, app_id: str) -> bool:
        """Valida o ID de um app para segurança e consistência."""
        # Permite apenas letras, números, hífen e underscore.
        import re
        return bool(re.match(r"^[a-zA-Z0-9\-_]{2,50}$", app_id))