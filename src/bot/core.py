# src/bot/core.py
import logging
import asyncio
import signal
import sys
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
        self.health_server = None
        
        # Inicializa API do Runtipi
        self.api = RuntipiAPI(
            host=config.runtipi_host,
            username=config.runtipi_username,
            password=config.runtipi_password
        )
        
        # Inicializa aplicação do Telegram com configurações otimizadas
        self.application = (Application.builder()
                          .token(config.telegram_token)
                          .get_updates_request_kwargs({
                              'timeout': 30,  # Timeout para long polling
                              'limit': 10     # Limite de updates por request
                          })
                          .build())
        
        # Inicializa handlers
        self.basic_handlers = BasicHandlers(config.allowed_chat_id)
        self.apps_handlers = AppsHandlers(config.allowed_chat_id, self.api)
        self.scripts_handlers = ScriptsHandlers(config.allowed_chat_id, config.scripts_dir)
        
        # Inicializa health server
        self.health_server = HealthServer(self.api, port=7777)
        
        # Configura handlers
        self._setup_handlers()
        self._setup_error_handlers()

    def _setup_handlers(self):
        """Configura todos os handlers do bot"""
        # Comandos básicos
        self.application.add_handler(
            CommandHandler("help", self.basic_handlers.help_command)
        )
        self.application.add_handler(
            CommandHandler("start", self.basic_handlers.start_command)
        )
        
        # Comandos de apps
        self.application.add_handler(
            CommandHandler("apps", self.apps_handlers.apps_command)
        )
        self.application.add_handler(
            CommandHandler("status", self.apps_handlers.status_command)
        )
        
        # Comandos de scripts
        self.application.add_handler(
            CommandHandler("scripts", self.scripts_handlers.list_scripts_command)
        )
        self.application.add_handler(
            CommandHandler("run", self.scripts_handlers.run_script_command)
        )
        
        # Handler para toggle de apps (mensagens de texto simples)
        self.application.add_handler(
            MessageHandler(
                filters.TEXT & ~filters.COMMAND, 
                self.apps_handlers.toggle_handler
            )
        )

    def _setup_error_handlers(self):
        """Configura handlers de erro"""
        async def error_handler(update, context):
            """Log todos os erros causados por Updates."""
            logger.error(f"Update {update} causou erro {context.error}")
            
            # Tenta enviar mensagem de erro para o usuário se possível
            if update and update.effective_message:
                try:
                    await update.effective_message.reply_text(
                        "❌ Ocorreu um erro interno. Tente novamente em alguns momentos."
                    )
                except Exception as e:
                    logger.error(f"Erro ao enviar mensagem de erro: {e}")
        
        self.application.add_error_handler(error_handler)

    async def _start_health_server(self):
        """Inicia o servidor de health check"""
        try:
            await self.health_server.start_server()
            logger.info("✅ Health server iniciado com sucesso")
        except Exception as e:
            logger.error(f"❌ Erro ao iniciar health server: {e}")

    async def _stop_health_server(self):
        """Para o servidor de health check"""
        if self.health_server:
            try:
                await self.health_server.stop_server()
                logger.info("✅ Health server parado com sucesso")
            except Exception as e:
                logger.error(f"❌ Erro ao parar health server: {e}")

    def _setup_signal_handlers(self):
        """Configura handlers para sinais do sistema"""
        def signal_handler(signum, frame):
            logger.info(f"Recebido sinal {signum}, iniciando shutdown graceful...")
            # O asyncio irá tratar o KeyboardInterrupt
            raise KeyboardInterrupt()
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

    async def _test_runtipi_connection(self):
        """Testa conexão inicial com Runtipi"""
        logger.info("🔧 Testando conexão com Runtipi...")
        
        try:
            if await asyncio.to_thread(self.api.test_connection):
                logger.info("✅ Conexão com Runtipi estabelecida")
                return True
            else:
                logger.warning("⚠️ Falha na conexão com Runtipi - continuando mesmo assim")
                return False
        except Exception as e:
            logger.error(f"❌ Erro ao testar conexão com Runtipi: {e}")
            return False

    def run(self):
        """Inicia o bot com todas as configurações"""
        if not self.config.validate():
            logger.error("❌ Variáveis de ambiente obrigatórias não definidas!")
            return False

        # Configura signal handlers
        self._setup_signal_handlers()

        logger.info("🤖 Iniciando Bot Runtipi...")
        logger.info(f"📡 Runtipi Host: {self.config.runtipi_host}")
        logger.info(f"👤 Runtipi User: {self.config.runtipi_username}")
        logger.info(f"📁 Scripts Path: {self.config.scripts_dir}")
        logger.info(f"💬 Allowed Chat ID: {self.config.allowed_chat_id}")

        async def run_bot():
            try:
                # Inicia health server
                await self._start_health_server()
                
                # Testa conexão com Runtipi
                await self._test_runtipi_connection()
                
                # Inicia o bot com polling otimizado
                logger.info("🚀 Iniciando polling do Telegram...")
                await self.application.run_polling(
                    drop_pending_updates=True,
                    poll_interval=5.0,  # Polling a cada 5 segundos (menos agressivo)
                    timeout=30,         # Timeout de 30s para long polling
                    bootstrap_retries=3,
                    read_timeout=30,
                    write_timeout=30,
                    connect_timeout=30
                )
                
            except KeyboardInterrupt:
                logger.info("🛑 Shutdown solicitado pelo usuário")
            except Exception as e:
                logger.error(f"❌ Erro crítico no bot: {e}")
                raise
            finally:
                # Cleanup
                logger.info("🧹 Executando cleanup...")
                await self._stop_health_server()
                logger.info("👋 Bot finalizado")

        try:
            asyncio.run(run_bot())
            return True
        except KeyboardInterrupt:
            logger.info("🛑 Bot interrompido pelo usuário")
            return True
        except Exception as e:
            logger.error(f"💥 Erro fatal: {e}")
            return False