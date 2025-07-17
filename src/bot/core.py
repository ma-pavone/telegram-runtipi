import logging
import asyncio
import signal
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from config.settings import BotConfig
from api.runtipi import RuntipiAPI
from bot.handlers import BasicHandlers, AppsHandlers, ScriptsHandlers
from health.server import HealthServer

logger = logging.getLogger(__name__)

class RuntipiBot:
    def __init__(self, config: BotConfig):
        self.config = config
        self.api = RuntipiAPI(
            host=config.runtipi_host,
            username=config.runtipi_username,
            password=config.runtipi_password
        )
        self.health_server = HealthServer(self.api, port=7777)
        self.application = Application.builder().token(config.telegram_token).build()

    def _setup_handlers(self):
        """Inicializa e configura todos os handlers do bot."""
        basic_handlers = BasicHandlers(self.config.allowed_chat_id)
        apps_handlers = AppsHandlers(self.config.allowed_chat_id, self.api)
        scripts_handlers = ScriptsHandlers(self.config.allowed_chat_id, self.config.scripts_dir)
        
        self.application.add_handler(CommandHandler("start", basic_handlers.start_command))
        self.application.add_handler(CommandHandler("help", basic_handlers.help_command))
        self.application.add_handler(CommandHandler("apps", apps_handlers.apps_command))
        self.application.add_handler(CommandHandler("status", apps_handlers.status_command))
        self.application.add_handler(CommandHandler("scripts", scripts_handlers.list_scripts_command))
        self.application.add_handler(CommandHandler("run", scripts_handlers.run_script_command))
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, apps_handlers.toggle_handler))
        self.application.add_error_handler(self.error_handler)

    async def error_handler(self, update, context):
        """Loga erros e notifica o usuário."""
        logger.error(f"Update {update} causou erro: {context.error}", exc_info=context.error)
        if update and update.effective_message:
            try:
                await update.effective_message.reply_text("❌ Ocorreu um erro inesperado. Verifique os logs.")
            except Exception as e:
                logger.error(f"Não foi possível enviar a mensagem de erro: {e}")

    async def _test_api_connection(self):
        """Testa a conexão com a API do Runtipi."""
        logger.info("Testing Runtipi API connection...")
        if await asyncio.to_thread(self.api.test_connection):
            logger.info("✅ Runtipi API connection successful.")
            return True
        logger.error("❌ Failed to connect to Runtipi API.")
        return False

    async def run_async(self):
        """Executa o bot e os serviços auxiliares."""
        if not await self._test_api_connection():
            return False

        try:
            await self.health_server.start()
            logger.info("🚀 Bot is polling for updates...")
            await self.application.run_polling(drop_pending_updates=True)
            return True
        except (KeyboardInterrupt, SystemExit):
            logger.info("🛑 Shutdown signal received.")
            return True
        except Exception as e:
            logger.critical(f"❌ Critical error in bot execution: {e}", exc_info=True)
            return False
        finally:
            await self.health_server.stop()
            logger.info("👋 Bot has been shut down.")

    def run(self) -> bool:
        """Ponto de entrada síncrono para executar o bot."""
        self._setup_handlers()
        
        loop = asyncio.get_event_loop()
        
        # Configura graceful shutdown para SIGINT e SIGTERM
        for sig in (signal.SIGINT, signal.SIGTERM):
            loop.add_signal_handler(sig, lambda s=sig: asyncio.create_task(self.shutdown(s)))

        try:
            return loop.run_until_complete(self.run_async())
        except Exception as e:
            logger.critical(f"Fatal error in event loop: {e}")
            return False

    async def shutdown(self, signal_type):
        """Realiza o shutdown gradual do bot."""
        logger.info(f"Received signal {signal_type}, initiating shutdown...")
        if self.application.running:
            await self.application.stop()
        # Outras tarefas de limpeza podem ser adicionadas aqui