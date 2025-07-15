import logging
import asyncio
import signal
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from config.settings import BotConfig
from api.runtipi import RuntipiAPI
from bot.handlers.basic import BasicHandlers
from bot.handlers.apps import AppsHandlers
from bot.handlers.scripts import ScriptsHandlers
from health.server import HealthServer

logger = logging.getLogger(__name__)


class RuntipiBot:
    def __init__(self, config: BotConfig):
        self.config = config
        self.health_server = HealthServer(None, port=7777)
        self.api = RuntipiAPI(
            host=config.runtipi_host,
            username=config.runtipi_username,
            password=config.runtipi_password
        )
        
        self.application = (Application.builder()
                          .token(config.telegram_token)
                          .get_updates_request_kwargs({'timeout': 30, 'limit': 10})
                          .build())
        
        self._init_handlers()
        self._setup_handlers()
        self._setup_error_handlers()

    def _init_handlers(self):
        """Inicializa todos os handlers"""
        self.basic_handlers = BasicHandlers(self.config.allowed_chat_id)
        self.apps_handlers = AppsHandlers(self.config.allowed_chat_id, self.api)
        self.scripts_handlers = ScriptsHandlers(self.config.allowed_chat_id, self.config.scripts_dir)
        self.health_server.api = self.api

    def _setup_handlers(self):
        """Configura todos os handlers do bot"""
        handlers = [
            CommandHandler("help", self.basic_handlers.help_command),
            CommandHandler("start", self.basic_handlers.start_command),
            CommandHandler("apps", self.apps_handlers.apps_command),
            CommandHandler("status", self.apps_handlers.status_command),
            CommandHandler("scripts", self.scripts_handlers.list_scripts_command),
            CommandHandler("run", self.scripts_handlers.run_script_command),
            MessageHandler(filters.TEXT & ~filters.COMMAND, self.apps_handlers.toggle_handler)
        ]
        
        for handler in handlers:
            self.application.add_handler(handler)

    def _setup_error_handlers(self):
        """Configura handlers de erro"""
        async def error_handler(update, context):
            logger.error(f"Update {update} causou erro {context.error}")
            if update and update.effective_message:
                try:
                    await update.effective_message.reply_text(
                        "❌ Ocorreu um erro interno. Tente novamente."
                    )
                except Exception as e:
                    logger.error(f"Erro ao enviar mensagem de erro: {e}")
        
        self.application.add_error_handler(error_handler)

    def _setup_signal_handlers(self):
        """Configura handlers para sinais do sistema"""
        def signal_handler(signum, frame):
            logger.info(f"Recebido sinal {signum}, iniciando shutdown...")
            raise KeyboardInterrupt()
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

    async def _test_runtipi_connection(self):
        """Testa conexão inicial com Runtipi"""
        try:
            if await asyncio.to_thread(self.api.test_connection):
                logger.info("✅ Conexão com Runtipi estabelecida")
                return True
            else:
                logger.warning("⚠️ Falha na conexão com Runtipi")
                return False
        except Exception as e:
            logger.error(f"❌ Erro ao testar conexão: {e}")
            return False

    async def _start_health_server(self):
        """Inicia servidor de health check"""
        try:
            await self.health_server.start_server()
            logger.info("✅ Health server iniciado")
        except Exception as e:
            logger.error(f"❌ Erro ao iniciar health server: {e}")

    async def _stop_health_server(self):
        """Para servidor de health check"""
        if self.health_server:
            try:
                await self.health_server.stop_server()
                logger.info("✅ Health server parado")
            except Exception as e:
                logger.error(f"❌ Erro ao parar health server: {e}")

    def run(self):
        """Inicia o bot"""
        if not self.config.is_valid():
            logger.error("❌ Configuração inválida!")
            return False

        self._setup_signal_handlers()
        logger.info("🤖 Iniciando Bot Runtipi...")
        
        async def run_bot():
            try:
                await self._start_health_server()
                await self._test_runtipi_connection()
                
                logger.info("🚀 Iniciando polling...")
                await self.application.run_polling(
                    drop_pending_updates=True,
                    poll_interval=5.0,
                    timeout=30,
                    bootstrap_retries=3,
                    read_timeout=30,
                    write_timeout=30,
                    connect_timeout=30
                )
                
            except KeyboardInterrupt:
                logger.info("🛑 Shutdown solicitado")
            except Exception as e:
                logger.error(f"❌ Erro crítico: {e}")
                raise
            finally:
                await self._stop_health_server()
                logger.info("👋 Bot finalizado")

        try:
            asyncio.run(run_bot())
            return True
        except KeyboardInterrupt:
            logger.info("🛑 Bot interrompido")
            return True
        except Exception as e:
            logger.error(f"💥 Erro fatal: {e}")
            return False