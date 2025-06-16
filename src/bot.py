import os
import logging
import asyncio
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

from runtipi_api import RuntipiAPI

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class RuntipiBot:
    def __init__(self):
        self.telegram_token = os.getenv('TELEGRAM_TOKEN')
        self.allowed_chat_id = int(os.getenv('TELEGRAM_CHAT_ID'))
        self.scripts_dir = os.getenv('SCRIPTS_PATH', '/scripts')
        
        # Inicializa API do Runtipi
        self.runtipi_api = RuntipiAPI(
            host=os.getenv('RUNTIPI_HOST', 'http://localhost'),
            username=os.getenv('RUNTIPI_USERNAME'),
            password=os.getenv('RUNTIPI_PASSWORD')
        )
        
        self.application = Application.builder().token(self.telegram_token).build()
        self._setup_handlers()

    def is_authorized(self, chat_id):
        """Verifica se o chat_id está autorizado"""
        return chat_id == self.allowed_chat_id

    def _setup_handlers(self):
        """Configura todos os handlers do bot"""
        # Comandos básicos
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(CommandHandler("start", self.help_command))
        self.application.add_handler(CommandHandler("apps", self.apps_command))
        self.application.add_handler(CommandHandler("status", self.status_command))
        
        # Comandos de scripts
        self.application.add_handler(CommandHandler("scripts", self.list_scripts_command))
        self.application.add_handler(CommandHandler("run", self.run_script_command))
        
        # Handler para toggle de apps (mensagens de texto simples)
        self.application.add_handler(
            MessageHandler(filters.TEXT & ~filters.COMMAND, self.toggle_handler)
        )

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Comando de ajuda"""
        if not self.is_authorized(update.effective_chat.id):
            await update.message.reply_text("❌ Acesso negado!")
            return

        help_text = """
🤖 *Bot Runtipi Controller*

*Comandos disponíveis:*
• `/help` - Mostrar esta mensagem
• `/apps` - Listar apps instalados com status
• `/status` - Status resumido dos apps
• `/scripts` - Listar scripts disponíveis
• `/run <script>` - Executar script

*Toggle de Apps:*
• Digite apenas o nome do app para ligar/desligar
• Exemplo: `jellyfin`, `sonarr`, `radarr`

*Exemplos:*
```
/apps
jellyfin
/run backup.sh
```
        """
        await update.message.reply_text(help_text, parse_mode='Markdown')

    async def apps_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Lista apps instalados com status"""
        if not self.is_authorized(update.effective_chat.id):
            await update.message.reply_text("❌ Acesso negado!")
            return

        await update.message.reply_text("🔄 Obtendo lista de apps...")
        
        try:
            apps_data = await asyncio.to_thread(self.runtipi_api.get_installed_apps)
            
            if not apps_data or 'installed' not in apps_data:
                await update.message.reply_text("❌ Erro ao obter lista de apps")
                return

            running_apps = []
            stopped_apps = []

            for app in apps_data['installed']:
                app_id = app['info']['id']
                app_name = app['info'].get('name', app_id)
                status = app['app']['status']
                
                status_line = f"`{app_id}`"
                if app_name != app_id:
                    status_line += f" ({app_name})"
                
                if status == "running":
                    running_apps.append(f"🟢 {status_line}")
                else:
                    stopped_apps.append(f"🔴 {status_line}")

            message = "📱 *Apps Instalados:*\n\n"
            
            if running_apps:
                message += "*🟢 Rodando:*\n" + "\n".join(running_apps) + "\n\n"
            
            if stopped_apps:
                message += "*🔴 Parados:*\n" + "\n".join(stopped_apps)
            
            if not running_apps and not stopped_apps:
                message += "Nenhum app instalado encontrado"

            await update.message.reply_text(message, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Erro no comando apps: {e}")
            await update.message.reply_text("❌ Erro interno ao obter apps")

    async def status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Status resumido dos apps"""
        if not self.is_authorized(update.effective_chat.id):
            await update.message.reply_text("❌ Acesso negado!")
            return

        await update.message.reply_text("🔄 Verificando status...")
        
        try:
            apps_data = await asyncio.to_thread(self.runtipi_api.get_installed_apps)
            
            if not apps_data or 'installed' not in apps_data:
                await update.message.reply_text("❌ Erro ao obter status dos apps")
                return

            total_apps = len(apps_data['installed'])
            running_count = sum(1 for app in apps_data['installed'] 
                              if app['app']['status'] == 'running')
            stopped_count = total_apps - running_count

            message = f"📊 *Status Resumido:*\n\n"
            message += f"🟢 Rodando: {running_count}\n"
            message += f"🔴 Parados: {stopped_count}\n"
            message += f"📱 Total: {total_apps}"

            await update.message.reply_text(message, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Erro no comando status: {e}")
            await update.message.reply_text("❌ Erro interno ao obter status")

    async def list_scripts_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Lista scripts disponíveis"""
        if not self.is_authorized(update.effective_chat.id):
            await update.message.reply_text("❌ Acesso negado!")
            return

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

    async def run_script_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Executa script"""
        if not self.is_authorized(update.effective_chat.id):
            await update.message.reply_text("❌ Acesso negado!")
            return

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

        await update.message.reply_text(f"🚀 Executando `{script_name}`...", parse_mode='Markdown')
        
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

    async def toggle_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handler para toggle de apps via mensagem de texto"""
        if not self.is_authorized(update.effective_chat.id):
            await update.message.reply_text("❌ Acesso negado!")
            return

        app_id = update.message.text.strip().lower()
        
        # Validação básica do nome do app
        if not app_id or len(app_id) > 50 or ' ' in app_id:
            await update.message.reply_text(
                "⚠️ Digite apenas o nome técnico do app\n"
                "Exemplo: `jellyfin`, `sonarr`, `radarr`",
                parse_mode='Markdown'
            )
            return

        await update.message.reply_text(f"🔄 Processando toggle para `{app_id}`...", parse_mode='Markdown')
        
        try:
            # Verifica se o app existe e obtém status atual
            app_data = await asyncio.to_thread(self.runtipi_api.get_app_status, app_id)
            
            if not app_data:
                await update.message.reply_text(f"❌ App `{app_id}` não encontrado", parse_mode='Markdown')
                return

            current_status = app_data['app']['status']
            action = "stop" if current_status == "running" else "start"
            action_text = "stopped" if action == "stop" else "started"
            
            await update.message.reply_text(f"⚡ {action_text.capitalize()} `{app_id}`...", parse_mode='Markdown')
            
            # Executa a ação
            success = await asyncio.to_thread(self.runtipi_api.toggle_app_action, app_id, action)
            
            if success:
                status_emoji = "🔴" if action == "stop" else "🟢"
                await update.message.reply_text(
                    f"{status_emoji} App `{app_id}` {action_text}",
                    parse_mode='Markdown'
                )
            else:
                await update.message.reply_text(
                    f"❌ Falha ao {action_text} o app `{app_id}`",
                    parse_mode='Markdown'
                )
                
        except Exception as e:
            logger.error(f"Erro no toggle do app {app_id}: {e}")
            await update.message.reply_text(f"❌ Erro interno ao processar `{app_id}`", parse_mode='Markdown')

    def run(self):
        """Inicia o bot"""
        if not all([self.telegram_token, self.allowed_chat_id, 
                   self.runtipi_api.username, self.runtipi_api.password]):
            logger.error("Variáveis de ambiente obrigatórias não definidas!")
            return

        logger.info("🤖 Bot Runtipi iniciado")
        self.application.run_polling(drop_pending_updates=True)


def main():
    bot = RuntipiBot()
    bot.run()


if __name__ == "__main__":
    main()