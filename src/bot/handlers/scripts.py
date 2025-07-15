import os
import asyncio
import logging
import time
from telegram import Update
from telegram.ext import ContextTypes
from bot.middleware.auth import require_auth

logger = logging.getLogger(__name__)


class ScriptsHandlers:
    def __init__(self, allowed_chat_id: int, scripts_dir: str):
        self.allowed_chat_id = allowed_chat_id
        self.scripts_dir = scripts_dir
        self.auth_required = require_auth(allowed_chat_id)

    async def list_scripts_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Lista scripts disponíveis"""
        @self.auth_required
        async def handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
            try:
                if not os.path.isdir(self.scripts_dir):
                    await update.message.reply_text(f"❌ Diretório não encontrado: `{self.scripts_dir}`", parse_mode='Markdown')
                    return

                all_files = [f for f in os.listdir(self.scripts_dir) 
                           if os.path.isfile(os.path.join(self.scripts_dir, f))]
                
                if not all_files:
                    await update.message.reply_text("⚠️ Nenhum arquivo encontrado")
                    return

                executable_scripts = [f for f in all_files 
                                    if os.access(os.path.join(self.scripts_dir, f), os.X_OK)]
                non_executable = [f for f in all_files if f not in executable_scripts]

                message = f"📂 *Scripts em `{self.scripts_dir}`:*\n\n"
                
                if executable_scripts:
                    script_list = "\n".join(f"🟢 `{s}`" for s in sorted(executable_scripts))
                    message += f"*Executáveis:*\n{script_list}\n\n"
                
                if non_executable:
                    file_list = "\n".join(f"🔴 `{s}`" for s in sorted(non_executable))
                    message += f"*Sem permissão:*\n{file_list}\n\n"
                
                message += "*Uso:* `/run <script>`"
                
                await update.message.reply_text(message, parse_mode='Markdown')
                
            except Exception as e:
                logger.error(f"Erro ao listar scripts: {e}")
                await update.message.reply_text(f"❌ Erro: {str(e)}")

        await handler(update, context)

    async def run_script_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Executa script"""
        @self.auth_required
        async def handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
            if not context.args:
                await update.message.reply_text(
                    "⚠️ *Uso:* `/run <script>`\n*Ver scripts:* `/scripts`",
                    parse_mode='Markdown'
                )
                return

            script_name = context.args[0]
            script_path = os.path.join(self.scripts_dir, script_name)

            if not self._is_safe_script_name(script_name):
                await update.message.reply_text(f"❌ Nome inválido: `{script_name}`", parse_mode='Markdown')
                return

            if not os.path.exists(script_path):
                await update.message.reply_text(f"❌ Script `{script_name}` não encontrado", parse_mode='Markdown')
                return

            if not os.path.isfile(script_path):
                await update.message.reply_text(f"❌ `{script_name}` não é um arquivo", parse_mode='Markdown')
                return

            if not os.access(script_path, os.X_OK):
                await update.message.reply_text(f"❌ Script sem permissão de execução", parse_mode='Markdown')
                return

            await update.message.reply_text(f"🚀 Executando `{script_name}`...", parse_mode='Markdown')
            
            try:
                result = await self._execute_script_async(script_path)
                message = self._format_script_result(script_name, result)
                await update.message.reply_text(message, parse_mode='Markdown')
                    
            except Exception as e:
                logger.error(f"Erro ao executar {script_name}: {e}")
                await update.message.reply_text(f"❌ Erro interno: `{str(e)}`", parse_mode='Markdown')

        await handler(update, context)

    async def _execute_script_async(self, script_path: str) -> dict:
        """Executa script de forma assíncrona"""
        start_time = time.time()
        
        try:
            process = await asyncio.create_subprocess_exec(
                script_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=self.scripts_dir
            )
            
            try:
                stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=300)
                exit_code = process.returncode
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
                return {
                    'success': False,
                    'exit_code': -1,
                    'stdout': '',
                    'stderr': 'Timeout (5 minutos)',
                    'duration': time.time() - start_time
                }
            
            return {
                'success': exit_code == 0,
                'exit_code': exit_code,
                'stdout': stdout.decode('utf-8', errors='replace').strip() if stdout else '',
                'stderr': stderr.decode('utf-8', errors='replace').strip() if stderr else '',
                'duration': time.time() - start_time
            }
            
        except Exception as e:
            return {
                'success': False,
                'exit_code': -1,
                'stdout': '',
                'stderr': f'Erro: {str(e)}',
                'duration': time.time() - start_time
            }

    def _format_script_result(self, script_name: str, result: dict) -> str:
        """Formata resultado da execução"""
        status = "✅ Sucesso" if result['success'] else "❌ Falha"
        message = f"{status}\n\n🕐 Tempo: {result['duration']:.2f}s\n📤 Código: {result['exit_code']}"
        
        if result['stdout']:
            stdout = result['stdout'][:1000]
            if len(result['stdout']) > 1000:
                stdout += "\n... (truncado)"
            message += f"\n\n📋 *Saída:*\n```\n{stdout}\n```"
        
        if result['stderr']:
            stderr = result['stderr'][:1000]
            if len(result['stderr']) > 1000:
                stderr += "\n... (truncado)"
            message += f"\n\n🔥 *Erro:*\n```\n{stderr}\n```"
        
        return message

    def _is_safe_script_name(self, script_name: str) -> bool:
        """Valida nome do script"""
        if not script_name or len(script_name) > 100:
            return False
        
        dangerous_chars = ['..', '/', '\\', '|', ';', '&', '$', '`', '(', ')', '{', '}']
        return not any(char in script_name for char in dangerous_chars)