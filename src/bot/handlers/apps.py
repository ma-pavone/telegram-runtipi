from telegram import Update
from telegram.ext import ContextTypes
from typing import final

from api.runtipi import RuntipiAPI
from bot.utils.messages import BotMessages

@final
class AppCommandHandler:
    """Handlers para comandos relacionados a aplicativos Runtipi."""
    
    def __init__(self, runtipi_api: RuntipiAPI):
        self._api = runtipi_api

    async def list_apps(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handler para o comando /apps."""
        apps = self._api.get_installed_apps()
        message = BotMessages.format_apps_list(apps)
        await update.effective_chat.send_message(message, parse_mode='Markdown')

    async def summary(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handler para o comando /status."""
        apps = self._api.get_installed_apps()
        message = BotMessages.format_status_summary(apps)
        await update.effective_chat.send_message(message, parse_mode='Markdown')

    async def toggle_app(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handler para mensagens de texto para ligar/desligar apps."""
        app_id = update.message.text.strip().lower()
        apps = self._api.get_installed_apps()
        
        target_app = next((app for app in apps if app.get('id') == app_id), None)

        if not target_app:
            await update.effective_chat.send_message(f"Aplicativo `{app_id}` não encontrado.", parse_mode='Markdown')
            return

        current_status = target_app.get('status', 'unknown')
        action_verb = "desligando" if current_status == "running" else "ligando"
        
        try:
            await update.effective_chat.send_message(f"Ok, {action_verb} `{app_id}`...")
            self._api.toggle_app_action(app_id, current_status)
            new_status_icon = BotMessages.STATUS_ICON_OFF if current_status == "running" else BotMessages.STATUS_ICON_OK
            await context.bot.edit_message_text(
                chat_id=update.effective_chat.id,
                message_id=update.message.message_id + 1,
                text=f"{new_status_icon} Aplicativo `{app_id}` foi {action_verb.replace('ando', 'ado')} com sucesso!",
                parse_mode='Markdown'
            )
        except Exception as e:
            await context.bot.edit_message_text(
                chat_id=update.effective_chat.id,
                message_id=update.message.message_id + 1,
                text=f"Falha ao interagir com o app `{app_id}`: {e}",
                parse_mode='Markdown'
            )