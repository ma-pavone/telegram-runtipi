# src/commands/scripts.py

import os
from telegram import Update
from telegram.ext import ContextTypes
import logging

logger = logging.getLogger(__name__)

SCRIPTS_DIR = os.environ.get("SCRIPTS_DIR")

async def list_scripts_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info("[BOT] Listando scripts em %s", SCRIPTS_DIR)

    if not SCRIPTS_DIR or not os.path.isdir(SCRIPTS_DIR):
        await update.message.reply_text("❌ Diretório de scripts não encontrado ou inválido.")
        logger.error("[BOT] Diretório de scripts inválido: %s", SCRIPTS_DIR)
        return

    scripts = [f for f in os.listdir(SCRIPTS_DIR) if os.path.isfile(os.path.join(SCRIPTS_DIR, f)) and os.access(os.path.join(SCRIPTS_DIR, f), os.X_OK)]

    if not scripts:
        await update.message.reply_text("⚠️ Nenhum script executável encontrado no diretório.")
        return

    script_list = "\n".join(f"• `{s}`" for s in sorted(scripts))
    await update.message.reply_text(f"📂 *Scripts disponíveis:*\n\n{script_list}", parse_mode='Markdown')


async def run_script_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info("[BOT] Comando de execução de script recebido")

    if not SCRIPTS_DIR or not os.path.isdir(SCRIPTS_DIR):
        await update.message.reply_text("❌ Diretório de scripts não encontrado ou inválido.")
        logger.error("[BOT] Diretório de scripts inválido: %s", SCRIPTS_DIR)
        return

    if len(context.args) != 1:
        await update.message.reply_text("⚠️ Uso correto: /run <script.sh>")
        return

    script_name = context.args[0]
    script_path = os.path.join(SCRIPTS_DIR, script_name)

    if not os.path.isfile(script_path) or not os.access(script_path, os.X_OK):
        await update.message.reply_text(f"❌ Script `{script_name}` não encontrado ou sem permissão de execução.", parse_mode='Markdown')
        logger.warning("[BOT] Script inválido: %s", script_path)
        return

    await update.message.reply_text(f"🚀 Executando `{script_name}`...", parse_mode='Markdown')
    logger.info("[BOT] Executando script: %s", script_path)

    exit_code = os.system(script_path)

    if exit_code == 0:
        await update.message.reply_text("✅ Script executado com sucesso.")
    else:
        await update.message.reply_text(f"❌ Erro ao executar script. Código de saída: {exit_code}")
        logger.error("[BOT] Script falhou: %s (exit %s)", script_name, exit_code)
