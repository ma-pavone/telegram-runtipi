import logging
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from telegram import Update

from config.settings import BotConfig
from api.runtipi import RuntipiAPI
from bot.middleware.auth import AuthMiddleware
from bot.handlers.basic_handler import BasicCommandHandler
from bot.handlers.app_handler import AppCommandHandler
from bot.handlers.script_handler import ScriptCommandHandler

logger = logging.getLogger(__name__)

class RuntipiBot:
    """A classe central que monta, configura e executa o bot."""
    
    def __init__(self, config: BotConfig, runtipi_api: RuntipiAPI):
        self.config = config
        self.api = runtipi_api
        
        auth = AuthMiddleware(allowed_chat_id=self.config.telegram_chat_id)

        basic_handlers = BasicCommandHandler()
        app_handlers = AppCommandHandler(self.api)
        script_handlers = ScriptCommandHandler(self.config.scripts_path)
        
        self.application = Application.builder().token(self.config.telegram_token).build()

        self.application.add_handlers([
            CommandHandler("start", auth(basic_handlers.start)),
            CommandHandler("help", auth(basic_handlers.help)),
            CommandHandler("apps", auth(app_handlers.list_apps)),
            CommandHandler("status", auth(app_handlers.summary)),
            CommandHandler("scripts", auth(script_handlers.list_scripts)),
            CommandHandler("run", auth(script_handlers.run_script)),
            MessageHandler(filters.TEXT & ~filters.COMMAND, auth(app_handlers.toggle_app))
        ])
        
        self.application.add_error_handler(self._error_handler)

    async def _error_handler(self, update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Loga erros e notifica o usuário."""
        logger.error("Exceção ao processar um update:", exc_info=context.error)
        if isinstance(update, Update) and update.effective_chat:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="🔴 Ocorreu um erro interno ao processar sua solicitação."
            )

    async def run(self) -> None:
        """Inicia o polling do Telegram e aguarda o encerramento."""
        logger.info("Iniciando o bot...")
        
        async with self.application:
            await self.application.start()
            logger.info("Bot iniciado e recebendo updates.")
            await self.application.run_polling()
        logger.info("Bot encerrado gracefully.")