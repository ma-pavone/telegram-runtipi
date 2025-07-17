import os
import asyncio
import logging
from telegram import Update
from telegram.ext import ContextTypes
from typing import final

from bot.utils.messages import BotMessages

logger = logging.getLogger(__name__)

@final
class ScriptCommandHandler:
    """Handlers para listar e executar scripts seguros."""

    def __init__(self, scripts_path: str):
        if not os.path.isdir(scripts_path):
            raise FileNotFoundError(f"O diretório de scripts '{scripts_path}' não existe.")
        self._scripts_path = scripts_path

    def _get_executable_scripts(self) -> list[str]:
        """Retorna uma lista de nomes de arquivos executáveis no diretório de scripts."""
        try:
            return [
                f for f in os.listdir(self._scripts_path)
                if os.path.isfile(os.path.join(self._scripts_path, f))
                and os.access(os.path.join(self._scripts_path, f), os.X_OK)
            ]
        except OSError as e:
            logger.error(f"Não foi possível ler o diretório de scripts '{self._scripts_path}': {e}")
            return []

    async def list_scripts(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handler para o comando /scripts."""
        scripts = self._get_executable_scripts()
        message = BotMessages.format_scripts_list(scripts)
        await update.effective_chat.send_message(message, parse_mode='Markdown')

    async def run_script(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handler para o comando /run."""
        if not context.args:
            await update.effective_chat.send_message("Uso: `/run [nome_do_script]`", parse_mode='Markdown')
            return

        script_name = context.args[0]
        if '..' in script_name or '/' in script_name:
            await update.effective_chat.send_message("Nome de script inválido. Apenas nomes de arquivos são permitidos.")
            return

        executable_scripts = self._get_executable_scripts()
        if script_name not in executable_scripts:
            await update.effective_chat.send_message(f"Script `{script_name}` não encontrado ou não é executável.", parse_mode='Markdown')
            return

        full_path = os.path.join(self._scripts_path, script_name)
        
        await update.effective_chat.send_message(f"Executando `{script_name}`...", parse_mode='Markdown')

        try:
            proc = await asyncio.wait_for(
                asyncio.create_subprocess_exec(
                    full_path,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                ),
                timeout=300.0  # Timeout de 5 minutos
            )

            stdout, stderr = await proc.communicate()
            
            message = BotMessages.format_script_output(
                script_name,
                stdout.decode('utf-8', errors='replace'),
                stderr.decode('utf-8', errors='replace'),
                proc.returncode
            )
            await update.effective_chat.send_message(message, parse_mode='Markdown')

        except asyncio.TimeoutError:
            await update.effective_chat.send_message(f"Timeout! O script `{script_name}` demorou mais de 5 minutos para executar.", parse_mode='Markdown')
        except Exception as e:
            logger.error(f"Falha ao executar o script '{script_name}': {e}", exc_info=True)
            await update.effective_chat.send_message(f"Ocorreu um erro crítico ao executar o script `{script_name}`.", parse_mode='Markdown')