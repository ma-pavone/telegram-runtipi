# src/bot/handlers.py
import os
import re
import asyncio
import logging
from typing import Dict, Callable, Any
from telegram import Update, constants
from telegram.ext import ContextTypes
from api.runtipi import RuntipiAPI
from .middleware.auth import require_auth
from .utils.messages import MessageFormatter
from .utils.scripts import ScriptRunner

logger = logging.getLogger(__name__)

class BotHandlers:
    """Handlers consolidados para melhor organização"""
    
    def __init__(self, allowed_chat_id: int, api: RuntipiAPI, scripts_dir: str):
        self.allowed_chat_id = allowed_chat_id
        self.api = api
        self.scripts_dir = scripts_dir
        self.auth = require_auth(allowed_chat_id)
        self.formatter = MessageFormatter()
        self.script_runner = ScriptRunner(scripts_dir)
        
        # Mapeamento de comandos para handlers
        self.command_map = {
            'start': self.help_command,
            'help': self.help_command,
            'apps': self.apps_command,
            'status': self.status_command,
            'scripts': self.scripts_command,
            'run': self.run_command
        }

    async def handle_command(self, command: str, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Dispatcher central de comandos"""
        handler = self.command_map.get(command)
        if handler:
            await handler(update, context)
        else:
            await update.message.reply_text("❌ Comando não encontrado. Use /help")

    @require_auth
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Comando de ajuda"""
        await update.message.reply_text(
            self.formatter.help_text(), 
            parse_mode=constants.ParseMode.MARKDOWN
        )

    @require_auth
    async def apps_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Lista apps instalados"""
        await self._execute_api_command(
            update,
            self.api.get_installed_apps,
            self.formatter.apps_list,
            "🔄 Obtendo apps...",
            "❌ Erro ao obter apps"
        )

    @require_auth
    async def status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Status resumido dos apps"""
        await self._execute_api_command(
            update,
            self.api.get_installed_apps,
            self.formatter.status_summary,
            "🔄 Verificando status...",
            "❌ Erro ao verificar status"
        )

    @require_auth
    async def scripts_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Lista scripts disponíveis"""
        try:
            scripts_info = await asyncio.to_thread(self.script_runner.list_scripts)
            message = self.formatter.scripts_list(scripts_info, self.scripts_dir)
            await update.message.reply_text(message, parse_mode=constants.ParseMode.MARKDOWN)
        except Exception as e:
            logger.error(f"Error listing scripts: {e}")
            await update.message.reply_text("❌ Erro ao listar scripts")

    @require_auth
    async def run_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Executa script"""
        if not context.args:
            await update.message.reply_text(
                "⚠️ Uso: `/run <script.sh>`\nVer scripts: `/scripts`",
                parse_mode=constants.ParseMode.MARKDOWN
            )
            return

        script_name = context.args[0]
        if not self.script_runner.is_safe_name(script_name):
            await update.message.reply_text(
                f"❌ Nome inválido: `{script_name}`",
                parse_mode=constants.ParseMode.MARKDOWN
            )
            return

        exec_msg = await update.message.reply_text(
            f"🚀 Executando `{script_name}`...",
            parse_mode=constants.ParseMode.MARKDOWN
        )
        
        try:
            result = await self.script_runner.execute(script_name)
            message = self.formatter.script_result(script_name, result)
            await exec_msg.edit_text(message, parse_mode=constants.ParseMode.MARKDOWN)
        except Exception as e:
            logger.error(f"Script execution error: {e}")
            await exec_msg.edit_text(
                f"❌ Erro ao executar: `{str(e)}`",
                parse_mode=constants.ParseMode.MARKDOWN
            )

    @require_auth
    async def toggle_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handler para toggle de apps"""
        app_id = update.message.text.strip().lower()
        
        if not self._is_valid_app_id(app_id):
            await update.message.reply_text(
                "⚠️ ID inválido. Use apenas letras, números e hífen.",
                parse_mode=constants.ParseMode.MARKDOWN
            )
            return

        msg = await update.message.reply_text(
            f"🔄 Processando `{app_id}`...",
            parse_mode=constants.ParseMode.MARKDOWN
        )
        
        try:
            # Verifica se app existe
            app_data = await asyncio.to_thread(self.api.get_app_data, app_id)
            if not app_data:
                await msg.edit_text(
                    f"❌ App `{app_id}` não encontrado",
                    parse_mode=constants.ParseMode.MARKDOWN
                )
                return

            # Determina ação
            is_running = app_data.get('app', {}).get('status') == 'running'
            action = "parando" if is_running else "iniciando"
            
            await msg.edit_text(
                f"⏳ {action.capitalize()} `{app_id}`...",
                parse_mode=constants.ParseMode.MARKDOWN
            )

            # Executa toggle
            success = await asyncio.to_thread(self.api.toggle_app, app_id)
            
            if success:
                emoji = "🔴" if is_running else "🟢"
                state = "parado" if is_running else "iniciado"
                await msg.edit_text(
                    f"{emoji} `{app_id}` {state} com sucesso!",
                    parse_mode=constants.ParseMode.MARKDOWN
                )
            else:
                await msg.edit_text(
                    f"❌ Falha ao processar `{app_id}`",
                    parse_mode=constants.ParseMode.MARKDOWN
                )
                
        except Exception as e:
            logger.error(f"Toggle error for {app_id}: {e}")
            await msg.edit_text(
                f"❌ Erro inesperado com `{app_id}`",
                parse_mode=constants.ParseMode.MARKDOWN
            )

    async def _execute_api_command(self, update: Update, api_call: Callable, 
                                 formatter: Callable, loading_msg: str, error_msg: str):
        """Executa comando de API com tratamento padrão"""
        await update.message.reply_text(loading_msg)
        try:
            data = await asyncio.to_thread(api_call)
            message = formatter(data)
            await update.message.reply_text(
                message, 
                parse_mode=constants.ParseMode.MARKDOWN_V2
            )
        except Exception as e:
            logger.error(f"API command error: {e}")
            await update.message.reply_text(error_msg)

    def _is_valid_app_id(self, app_id: str) -> bool:
        """Valida ID do app"""
        return bool(re.match(r"^[a-zA-Z0-9\-_]{2,50}$", app_id))