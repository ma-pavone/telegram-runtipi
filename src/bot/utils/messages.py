class BotMessages:
    @staticmethod
    def help_text():
        return """🤖 *Bot Runtipi Controller*

*Comandos:*
• `/help` - Ajuda
• `/apps` - Listar apps com status
• `/status` - Status resumido
• `/scripts` - Listar scripts
• `/run <script>` - Executar script

*Toggle:*
• Digite o nome do app para ligar/desligar
• Ex: `jellyfin`, `sonarr`, `radarr`

*Exemplos:*
```
/apps
jellyfin
/run backup.sh
```"""

    @staticmethod
    def format_apps_list(apps_data):
        """Formata lista de apps"""
        if not apps_data or 'installed' not in apps_data:
            return "❌ Erro ao obter apps"

        running_apps = []
        stopped_apps = []

        for app in apps_data['installed']:
            app_id = app['info']['id']
            app_name = app['info'].get('name', app_id)
            status = app['app']['status']
            
            display_name = f"`{app_id}`"
            if app_name != app_id:
                display_name += f" ({app_name})"
            
            if status == "running":
                running_apps.append(f"🟢 {display_name}")
            else:
                stopped_apps.append(f"🔴 {display_name}")

        message = "📱 *Apps Instalados:*\n\n"
        
        if running_apps:
            message += "*🟢 Rodando:*\n" + "\n".join(running_apps) + "\n\n"
        
        if stopped_apps:
            message += "*🔴 Parados:*\n" + "\n".join(stopped_apps)
        
        if not running_apps and not stopped_apps:
            message += "Nenhum app encontrado"

        return message

    @staticmethod
    def format_status_summary(apps_data):
        """Formata resumo de status"""
        if not apps_data or 'installed' not in apps_data:
            return "❌ Erro ao obter status"

        total_apps = len(apps_data['installed'])
        running_count = sum(1 for app in apps_data['installed'] 
                          if app['app']['status'] == 'running')
        stopped_count = total_apps - running_count

        return f"""📊 *Status Resumido:*

🟢 Rodando: {running_count}
🔴 Parados: {stopped_count}
📱 Total: {total_apps}"""