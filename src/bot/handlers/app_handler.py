import logging
from telegram import Update
from telegram.ext import ContextTypes
from typing import final

from api.runtipi import RuntipiAPI, AppStatus
from bot.utils.messages import BotMessages

logger = logging.getLogger(__name__)

@final
class AppCommandHandler:
    """Handlers para comandos relacionados a aplicativos Runtipi."""
    
    def __init__(self, runtipi_api: RuntipiAPI):
        self._api = runtipi_api

    async def list_apps(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handler para o comando /apps."""
        try:
            loading_msg = await update.effective_chat.send_message(
                BotMessages.format_loading_message("Buscando aplicativos")
            )
            
            apps = self._api.get_installed_apps()
            message = BotMessages.format_apps_list(apps)
            await context.bot.edit_message_text(
                chat_id=update.effective_chat.id,
                message_id=loading_msg.message_id,
                text=message,
                parse_mode='Markdown'
            )
            
        except Exception as e:
            logger.error(f"Erro ao listar apps: {e}", exc_info=True)
            error_msg = BotMessages.format_error_message(
                "Falha ao buscar lista de aplicativos",
                "list_apps"
            )
            await update.effective_chat.send_message(error_msg)

    async def summary(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handler para o comando /status."""
        try:
            loading_msg = await update.effective_chat.send_message(
                BotMessages.format_loading_message("Verificando status do sistema")
            )
            
            apps = self._api.get_installed_apps()
            message = BotMessages.format_status_summary(apps)
            
            await context.bot.edit_message_text(
                chat_id=update.effective_chat.id,
                message_id=loading_msg.message_id,
                text=message,
                parse_mode='Markdown'
            )
            
        except Exception as e:
            logger.error(f"Erro ao gerar resumo: {e}", exc_info=True)
            error_msg = BotMessages.format_error_message(
                "Falha ao gerar resumo do sistema",
                "summary"
            )
            await update.effective_chat.send_message(error_msg)

    async def toggle_app(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handler para mensagens de texto para ligar/desligar apps."""
        app_id = update.message.text.strip().lower()
        
        try:
            target_app = self._api.find_app_by_id(app_id)

            if not target_app:
                await update.effective_chat.send_message(
                    BotMessages.format_error_message(
                        f"Aplicativo `{app_id}` não encontrado"
                    ),
                    parse_mode='Markdown'
                )
                return
            action = "stop" if target_app.status == AppStatus.RUNNING else "start"
            action_verb = "Desligando" if action == "stop" else "Ligando"
            loading_msg = await update.effective_chat.send_message(
                BotMessages.format_loading_message(f"{action_verb} `{app_id}`"),
                parse_mode='Markdown'
            )
            response = self._api.toggle_app_action(app_id, target_app.status)
            if response.success:
                result_message = BotMessages.format_app_action_result(
                    app_id, action, True
                )
            else:
                result_message = BotMessages.format_app_action_result(
                    app_id, action, False, response.error
                )
            
            await context.bot.edit_message_text(
                chat_id=update.effective_chat.id,
                message_id=loading_msg.message_id,
                text=result_message,
                parse_mode='Markdown'
            )
            
        except Exception as e:
            logger.error(f"Erro ao alternar app {app_id}: {e}", exc_info=True)
            error_msg = BotMessages.format_error_message(
                f"Erro interno ao interagir com o app `{app_id}`",
                "toggle_app"
            )
            await update.effective_chat.send_message(error_msg, parse_mode='Markdown')

    async def restart_app(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handler para reiniciar um app (parar e iniciar)."""
        if not context.args:
            await update.effective_chat.send_message(
                BotMessages.format_error_message("Uso: `/restart [nome_do_app]`"),
                parse_mode='Markdown'
            )
            return
        
        app_id = context.args[0].strip().lower()
        
        try:
            target_app = self._api.find_app_by_id(app_id)
            
            if not target_app:
                await update.effective_chat.send_message(
                    BotMessages.format_error_message(f"App `{app_id}` não encontrado"),
                    parse_mode='Markdown'
                )
                return
            
            loading_msg = await update.effective_chat.send_message(
                BotMessages.format_loading_message(f"Reiniciando `{app_id}`"),
                parse_mode='Markdown'
            )
            if target_app.status == AppStatus.RUNNING:
                stop_response = self._api.stop_app(app_id)
                if not stop_response.success:
                    await context.bot.edit_message_text(
                        chat_id=update.effective_chat.id,
                        message_id=loading_msg.message_id,
                        text=BotMessages.format_error_message(
                            f"Falha ao parar o app `{app_id}`: {stop_response.error}"
                        ),
                        parse_mode='Markdown'
                    )
                    return
            start_response = self._api.start_app(app_id)
            
            if start_response.success:
                result_message = BotMessages.format_success_message(
                    f"App `{app_id}` reiniciado com sucesso!"
                )
            else:
                result_message = BotMessages.format_error_message(
                    f"Falha ao iniciar o app `{app_id}`: {start_response.error}"
                )
            
            await context.bot.edit_message_text(
                chat_id=update.effective_chat.id,
                message_id=loading_msg.message_id,
                text=result_message,
                parse_mode='Markdown'
            )
            
        except Exception as e:
            logger.error(f"Erro ao reiniciar app {app_id}: {e}", exc_info=True)
            error_msg = BotMessages.format_error_message(
                f"Erro interno ao reiniciar o app `{app_id}`"
            )
            await update.effective_chat.send_message(error_msg, parse_mode='Markdown')