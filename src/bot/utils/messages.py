# src/bot/utils/messages.py
class BotMessages:
    @staticmethod
    def help_text():
        return """
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

    @staticmethod
    def format_apps_list(apps_data):
        """Formata lista de apps com status"""
        if not apps_data or 'installed' not in apps_data:
            return "❌ Erro ao obter lista de apps"

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

        return message

    @staticmethod
    def format_status_summary(apps_data):
        """Formata resumo de status dos apps"""
        if not apps_data or 'installed' not in apps_data:
            return "❌ Erro ao obter status dos apps"

        total_apps = len(apps_data['installed'])
        running_count = sum(1 for app in apps_data['installed'] 
                          if app['app']['status'] == 'running')
        stopped_count = total_apps - running_count

        message = f"📊 *Status Resumido:*\n\n"
        message += f"🟢 Rodando: {running_count}\n"
        message += f"🔴 Parados: {stopped_count}\n"
        message += f"📱 Total: {total_apps}"

        return message