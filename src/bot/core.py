# src/bot/core.py
import asyncio
import signal
import logging
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from config.settings import BotConfig
from api.runtipi import RuntipiAPI
from .handlers import BotHandlers

logger = logging.getLogger(__name__)

class RuntipiBot:
    """Bot principal com arquitetura simplificada"""
    
    def __init__(self, config: BotConfig):
        self.config = config
        self.api = RuntipiAPI(
            host=config.runtipi_host,
            username=config.runtipi_username,
            password=config.runtipi_password
        )
        self.handlers = BotHandlers(
            allowed_chat_id=config.allowed_chat_id,
            api=self.api,
            scripts_dir=config.scripts_dir
        )
        self.app = Application.builder().token(config.telegram_token).build()
        self._setup_handlers()

    def _setup_handlers(self):
        """Configura handlers do bot"""
        # Comandos específicos
        commands = ['start', 'help', 'apps', 'status', 'scripts', 'run']
        for cmd in commands:
            self.app.add_handler(
                CommandHandler(cmd, self._command_dispatcher)
            )
        
        # Handler para toggle de apps (mensagens não-comando)
        self.app.add_handler(
            MessageHandler(
                filters.TEXT & ~filters.COMMAND,
                self.handlers.toggle_handler
            )
        )
        
        # Handler de erro global
        self.app.add_error_handler(self._error_handler)

    async def _command_dispatcher(self, update, context):
        """Dispatcher central de comandos"""
        command = update.message.text.split()[0][1:]  # Remove '/'
        await self.handlers.handle_command(command, update, context)

    async def _error_handler(self, update, context):
        """Handler de erros global"""
        logger.error(f"Bot error: {context.error}", exc_info=context.error)
        if update and update.effective_message:
            try:
                await update.effective_message.reply_text(
                    "❌ Erro interno. Verifique os logs."
                )
            except Exception as e:
                logger.error(f"Failed to send error message: {e}")

    async def _test_connection(self) -> bool:
        """Testa conexão com Runtipi"""
        logger.info("Testing Runtipi connection...")
        try:
            success = await asyncio.to_thread(self.api.test_connection)
            if success:
                logger.info("✅ Runtipi connection successful")
            else:
                logger.error("❌ Runtipi connection failed")
            return success
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False

    def run(self) -> bool:
        """Executa o bot"""
        try:
            loop = asyncio.get_event_loop()
            
            # Configura shutdown graceful
            for sig in (signal.SIGINT, signal.SIGTERM):
                loop.add_signal_handler(
                    sig, 
                    lambda: asyncio.create_task(self._shutdown())
                )
            
            return loop.run_until_complete(self._run_async())
            
        except Exception as e:
            logger.critical(f"Fatal error: {e}")
            return False

    async def _run_async(self) -> bool:
        """Execução assíncrona