# src/bot/core.py
import logging
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from config.settings import BotConfig
from api.runtipi import RuntipiAPI
from bot.handlers.basic import BasicHandlers
from bot.handlers.apps import AppsHandlers
from bot.handlers.scripts import ScriptsHandlers

logger = logging.getLogger(__name__)

class RuntipiBot:
    def __init__(self, config: BotConfig):
        self.config = config
        
        # Inicializa API do Runtipi
        self.api = RuntipiAPI(
            host=config.runtipi_host,
            username=config.runtipi_username,
            password=config.runtipi_password
        )
        
        # Inicializa aplicação do Telegram
        self.application = Application.builder().token(config.telegram_token).build()
        
        # Inicializa handlers
        self.basic_handlers = BasicHandlers(config.allowed_chat_id)
        self.apps_handlers = AppsHandlers(config.allowed_chat_id, self.api)
        self.scripts_handlers = ScriptsHandlers(config.allowed_chat_id, config.scripts_dir)
        
        # Configura handlers
        self._setup_handlers()

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

    def run(self):
        """Inicia o bot"""
        if not self.config.validate():
            logger.error("Variáveis de ambiente obrigatórias não definidas!")
            return

        logger.info("🤖 Bot Runtipi iniciado")
        self.application.run_polling(drop_pending_updates=True)