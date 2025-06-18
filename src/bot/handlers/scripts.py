# src/bot/handlers/scripts.py
import os
import asyncio
import subprocess
import logging
from pathlib import Path
from telegram import Update
from telegram.ext import ContextTypes
from bot.middleware.auth import require_auth

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
                    await update.message.reply_text(
                        f"❌ Diretório de scripts não encontrado: `{self.scripts_dir}`",
                        parse_mode='Markdown'
                    )
                    return

                # Lista todos os arquivos no diretório
                all_files = []
                executable_scripts = []
                
                for item in os.listdir(self.scripts_dir):
                    item_path = os.path.join(self.scripts_dir, item)
                    if os.path.isfile(item_path):
                        all_files.append(item)
                        # Verifica se é executável
                        if os.access(item_path, os.X_OK):
                            executable_scripts.append(item)

                if not all_files:
                    await update.message.reply_text("⚠️ Nenhum arquivo encontrado no diretório de scripts")
                    return

                message = f"📂 *Scripts em `{self.scripts_dir}`:*\n\n"
                
                if executable_scripts:
                    script_list = "\n".join(f"🟢 `{s}`" for s in sorted(executable_scripts))
                    message += f"*Executáveis:*\n{script_list}\n\n"
                
                # Lista arquivos não executáveis
                non_executable = [f for f in all_files if f not in executable_scripts]
                if non_executable:
                    file_list = "\n".join(f"🔴 `{s}`" for s in sorted(non_executable))
                    message += f"*Sem permissão de execução:*\n{file_list}\n\n"
                
                message += "*Uso:* `/run <nome_do_script>`\n"
                message += "*Legenda:* 🟢 Executável | 🔴 Sem permissão"
                
                await update.message.reply_text(message, parse_mode='Markdown')
                
            except Exception as e:
                logger.error(f"Erro ao listar scripts: {e}")
                await update.message.reply_text(f"❌ Erro ao listar scripts: {str(e)}")

        await _list_handler(update, context)

    async def run_script_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Executa script com melhor tratamento de erros"""
        @self.auth_required
        async def _run_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
            if not context.args:
                await update.message.reply_text(
                    "⚠️ *Uso:* `/run <nome_do_script>`\n\n"
                    "*Exemplo:* `/run backup.sh`\n"
                    "*Ver scripts:* `/scripts`",
                    parse_mode='Markdown'
                )
                return

            script_name = context.args[0]
            script_path = os.path.join(self.scripts_dir, script_name)

            # Validações de segurança
            if not self._is_safe_script_name(script_name):
                await update.message.reply_text(
                    f"❌ Nome de script inválido: `{script_name}`\n"
                    "Use apenas nomes de arquivos sem caracteres especiais",
                    parse_mode='Markdown'
                )
                return

            if not os.path.exists(script_path):
                await update.message.reply_text(
                    f"❌ Script `{script_name}` não encontrado em `{self.scripts_dir}`",
                    parse_mode='Markdown'
                )
                return

            if not os.path.isfile(script_path):
                await update.message.reply_text(
                    f"❌ `{script_name}` não é um arquivo válido",
                    parse_mode='Markdown'
                )
                return

            if not os.access(script_path, os.X_OK):
                await update.message.reply_text(
                    f"❌ Script `{script_name}` sem permissão de execução\n"
                    f"Execute: `chmod +x {script_path}`",
                    parse_mode='Markdown'
                )
                return

            # Inicia execução
            await update.message.reply_text(
                f"🚀 Executando `{script_name}`...\n"
                f"📁 Diretório: `{self.scripts_dir}`", 
                parse_mode='Markdown'
            )
            
            try:
                # Executa o script com subprocess para melhor controle
                result = await self._execute_script_async(script_path)
                
                # Formata resultado
                if result['success']:
                    message = f"✅ *Script executado com sucesso*\n\n"
                    message += f"🕐 Tempo: {result['duration']:.2f}s\n"
                    message += f"📤 Código de saída: {result['exit_code']}"
                    
                    if result['stdout']:
                        # Limita output para evitar mensagens muito longas
                        stdout = result['stdout'][:1000]
                        if len(result['stdout']) > 1000:
                            stdout += "\n... (saída truncada)"
                        message += f"\n\n📋 *Saída:*\n```\n{stdout}\n```"
                        
                else:
                    message = f"❌ *Script falhou*\n\n"
                    message += f"🕐 Tempo: {result['duration']:.2f}s\n"
                    message += f"📤 Código de saída: {result['exit_code']}"
                    
                    if result['stderr']:
                        stderr = result['stderr'][:1000]
                        if len(result['stderr']) > 1000:
                            stderr += "\n... (erro truncado)"
                        message += f"\n\n🔥 *Erro:*\n```\n{stderr}\n```"
                
                await update.message.reply_text(message, parse_mode='Markdown')
                    
            except Exception as e:
                logger.error(f"Erro ao executar script {script_name}: {e}")
                await update.message.reply_text(
                    f"❌ *Erro interno ao executar script*\n\n"
                    f"Script: `{script_name}`\n"
                    f"Erro: `{str(e)}`",
                    parse_mode='Markdown'
                )

        await _run_handler(update, context)

    async def _execute_script_async(self, script_path: str) -> dict:
        """Executa script de forma assíncrona com timeout"""
        import time
        start_time = time.time()
        
        try:
            # Executa o processo com timeout de 5 minutos
            process = await asyncio.create_subprocess_exec(
                script_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=self.scripts_dir
            )
            
            # Aguarda com timeout
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(), 
                    timeout=300  # 5 minutos
                )
                exit_code = process.returncode
                
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
                return {
                    'success': False,
                    'exit_code': -1,
                    'stdout': '',
                    'stderr': 'Script executou por mais de 5 minutos e foi interrompido',
                    'duration': time.time() - start_time
                }
            
            # Decodifica saídas
            stdout_text = stdout.decode('utf-8', errors='replace') if stdout else ''
            stderr_text = stderr.decode('utf-8', errors='replace') if stderr else ''
            
            return {
                'success': exit_code == 0,
                'exit_code': exit_code,
                'stdout': stdout_text.strip(),
                'stderr': stderr_text.strip(),
                'duration': time.time() - start_time
            }
            
        except Exception as e:
            return {
                'success': False,
                'exit_code': -1,
                'stdout': '',
                'stderr': f'Erro na execução: {str(e)}',
                'duration': time.time() - start_time
            }

    def _is_safe_script_name(self, script_name: str) -> bool:
        """Valida se o nome do script é seguro"""
        # Evita path traversal e caracteres perigosos
        if not script_name or len(script_name) > 100:
            return False
            
        dangerous_chars = ['..', '/', '\\', '|', ';', '&', '$', '`', '(', ')', '{', '}']
        return not any(char in script_name for char in dangerous_chars)