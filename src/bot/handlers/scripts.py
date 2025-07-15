# src/bot/handlers/scripts.py

import os
import asyncio
import logging
import time
import re # Importar re para validação
from telegram import Update
from telegram.ext import ContextTypes
from bot.middleware.auth import require_auth

logger = logging.getLogger(__name__)

class ScriptsHandlers:
    def __init__(self, allowed_chat_id: int, scripts_dir: str):
        self.allowed_chat_id = allowed_chat_id
        self.scripts_dir = scripts_dir
        self.auth_required = require_auth(allowed_chat_id)

    # ... (o resto da classe permanece o mesmo) ...
    # A única mudança significativa é na função _is_safe_script_name

    def _is_safe_script_name(self, script_name: str) -> bool:
        """
        Valida nome do script usando uma whitelist de caracteres.
        Permite apenas: letras, números, underscore, hífen e ponto.
        Impede '..' e barras para evitar path traversal.
        """
        if not script_name or '..' in script_name or '/' in script_name or '\\' in script_name:
            return False
        
        # Expressão regular para garantir que o nome contém apenas caracteres seguros.
        # O nome deve terminar com .sh para ser mais explícito.
        return bool(re.match(r"^[a-zA-Z0-9_.-]+\.sh$", script_name))

    # O resto dos métodos como list_scripts_command e run_script_command permanecem os mesmos.
    # O seu código original já era muito bom.

    # ... (resto do arquivo igual ao original)
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
                
                sh_scripts = [f for f in all_files if self._is_safe_script_name(f)]

                if not sh_scripts:
                    await update.message.reply_text(f"⚠️ Nenhum script `.sh` válido encontrado em `{self.scripts_dir}`", parse_mode='Markdown')
                    return

                executable_scripts = [f for f in sh_scripts
                                    if os.access(os.path.join(self.scripts_dir, f), os.X_OK)]
                non_executable = [f for f in sh_scripts if f not in executable_scripts]

                message = f"📂 *Scripts em `{os.path.basename(self.scripts_dir)}`:*\n\n"
                
                if executable_scripts:
                    script_list = "\n".join(f"🟢 `{s}`" for s in sorted(executable_scripts))
                    message += f"*Executáveis:*\n{script_list}\n\n"
                
                if non_executable:
                    file_list = "\n".join(f"🔴 `{s}`" for s in sorted(non_executable))
                    message += f"*Sem permissão de execução:*\n{file_list}\n\n"
                
                message += "*Uso:* `/run <script.sh>`"
                
                await update.message.reply_text(message, parse_mode='Markdown')
                
            except Exception as e:
                logger.error(f"Erro ao listar scripts: {e}", exc_info=True)
                await update.message.reply_text(f"❌ Erro ao listar scripts: {str(e)}")

        await handler(update, context)

    async def run_script_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Executa script"""
        @self.auth_required
        async def handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
            if not context.args:
                await update.message.reply_text(
                    "⚠️ *Uso:* `/run <script.sh>`\n*Ver scripts:* `/scripts`",
                    parse_mode='Markdown'
                )
                return

            script_name = context.args[0]
            
            if not self._is_safe_script_name(script_name):
                await update.message.reply_text(f"❌ Nome de script inválido ou inseguro: `{script_name}`", parse_mode='Markdown')
                return

            script_path = os.path.join(self.scripts_dir, script_name)

            # Verificações de existência e permissão
            if not os.path.isfile(script_path):
                await update.message.reply_text(f"❌ Script `{script_name}` não encontrado ou não é um arquivo.", parse_mode='Markdown')
                return

            if not os.access(script_path, os.X_OK):
                await update.message.reply_text(f"❌ Script sem permissão de execução. Use `chmod +x {script_name}` no servidor.", parse_mode='Markdown')
                return
            
            exec_msg = await update.message.reply_text(f"🚀 Executando `{script_name}`...", parse_mode='Markdown')
            
            try:
                result = await self._execute_script_async(script_path)
                message = self._format_script_result(script_name, result)
                await exec_msg.edit_text(message, parse_mode='Markdown')
                    
            except Exception as e:
                logger.error(f"Erro ao executar {script_name}: {e}", exc_info=True)
                await exec_msg.edit_text(f"❌ Erro interno ao executar o script: `{str(e)}`", parse_mode='Markdown')

        await handler(update, context)

    async def _execute_script_async(self, script_path: str) -> dict:
        """Executa script de forma assíncrona com timeout."""
        start_time = time.time()
        
        try:
            process = await asyncio.create_subprocess_exec(
                script_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=self.scripts_dir
            )
            
            # Timeout de 5 minutos (300 segundos)
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=300)
            
            return {
                'success': process.returncode == 0,
                'exit_code': process.returncode,
                'stdout': stdout.decode('utf-8', errors='replace').strip(),
                'stderr': stderr.decode('utf-8', errors='replace').strip(),
                'duration': time.time() - start_time
            }
        except asyncio.TimeoutError:
            process.kill()
            await process.wait()
            logger.warning(f"Script {os.path.basename(script_path)} timed out.")
            return {
                'success': False, 'exit_code': -1, 'stdout': '', 'stderr': 'Erro: Timeout de 5 minutos excedido.',
                'duration': time.time() - start_time
            }
        except Exception as e:
            logger.error(f"Falha na execução do subprocesso para {os.path.basename(script_path)}: {e}")
            return {
                'success': False, 'exit_code': -1, 'stdout': '', 'stderr': f'Erro ao iniciar o script: {e}',
                'duration': time.time() - start_time
            }

    def _format_script_result(self, script_name: str, result: dict) -> str:
        """Formata resultado da execução do script para o Telegram."""
        status = "✅ Sucesso" if result['success'] else "❌ Falha"
        message = f"**Resultado de `{script_name}`**\n\n"
        message += f"{status}\n"
        message += f"*Tempo de Execução:* `{result['duration']:.2f}s`\n"
        message += f"*Código de Saída:* `{result['exit_code']}`\n"
        
        if result['stdout']:
            # Trunca a saída para não exceder o limite de mensagem do Telegram
            stdout = result['stdout'][:3000]
            message += f"\n📋 **Saída Padrão:**\n```\n{stdout}\n```"
        
        if result['stderr']:
            stderr = result['stderr'][:1000]
            message += f"\n🔥 **Saída de Erro:**\n```\n{stderr}\n```"
        
        return message