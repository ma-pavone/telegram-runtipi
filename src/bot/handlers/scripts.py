# src/bot/handlers/scripts.py
import os
import asyncio
from telegram import Update
from telegram.ext import ContextTypes
from bot.middleware.auth import require_auth
import logging

logger = logging.getLogger(__name__)

class ScriptsHandlers:
    def __init__(self, allowed_chat_id: int, scripts_dir: str):
        self.allowed_chat_id = allowed_chat_id
        self.scripts_dir = scripts_dir

    @property
    def auth_required(self):
        return require_auth(self.allowed_chat_id)

    async def list_scripts_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Lista scripts disponíveis"""
        @self.auth_required
        async def _list_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
            try:
                if not os.path.isdir(self.scripts_dir):
                    await update.message.reply_text("❌ Diretório de scripts não encontrado")
                    return

                scripts = [f for f in os.listdir(self.scripts_dir) 
                          if os.path.isfile(os.path.join(self.scripts_dir, f)) 
                          and os.access(os.path.join(self.scripts_dir, f), os.X_OK)]

                if not scripts:
                    await update.message.reply_text("⚠️ Nenhum script executável encontrado")
                    return

                script_list = "\n".join(f"• `{s}`" for s in sorted(scripts))
                message = f"📂 *Scripts disponíveis:*\n\n{script_list}\n\n"
                message += "*Uso:* `/run <nome_do_script>`"
                
                await update.message.reply_text(message, parse_mode='Markdown')
                
            except Exception as e:
                logger.error(f"Erro ao listar scripts: {e}")
                await update.message.reply_text("❌ Erro ao listar scripts")

        await _list_handler(update, context)

    async def run_script_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Executa script"""
        @self.auth_required
        async def _run_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
            if not context.args:
                await update.message.reply_text("⚠️ Uso: `/run <nome_do_script>`")
                return

            script_name = context.args[0]
            script_path = os.path.join(self.scripts_dir, script_name)

            if not os.path.isfile(script_path) or not os.access(script_path, os.X_OK):
                await update.message.reply_text(
                    f"❌ Script `{script_name}` não encontrado ou sem permissão",
                    parse_mode='Markdown'
                )
                return

            await update.message.reply_text(
                f"🚀 Executando `{script_name}`...", 
                parse_mode='Markdown'
            )
            
            try:
                # Executa script em thread separada para não bloquear
                exit_code = await asyncio.to_thread(os.system, script_path)
                
                if exit_code == 0:
                    await update.message.reply_text("✅ Script executado com sucesso")
                else:
                    await update.message.reply_text(f"❌ Script falhou (código: {exit_code})")
                    
            except Exception as e:
                logger.error(f"Erro ao executar script {script_name}: {e}")
                await update.message.reply_text("❌ Erro interno ao executar script")

        await _run_handler(update, context)
