from typing import final
STATUS_ICON_OK = "✅"
STATUS_ICON_OFF = "❌"
ICON_BOT = "🤖"
ICON_SUMMARY = "📊"
ICON_SCRIPTS = "📜"
ICON_TIP = "💡"

@final
class BotMessages:
    """Namespace para todas as funções geradoras de mensagens do bot."""

    @staticmethod
    def get_help_message() -> str:
        """Retorna a mensagem de ajuda formatada em Markdown."""
        return (
            f"{ICON_BOT} *Bot de Controle do Runtipi* {ICON_BOT}\n\n"
            "Comandos disponíveis:\n\n"
            "*/apps* - Lista todos os aplicativos e seus status.\n"
            "*/status* - Mostra um resumo rápido de quantos apps estão ativos.\n"
            f"*/scripts* - {ICON_SCRIPTS} Lista os scripts disponíveis para execução.\n"
            "*/run `[nome_do_script]`* - Executa um script específico.\n"
            "*/help* - Mostra esta mensagem de ajuda.\n\n"
            f"{ICON_TIP} *Dica*: Envie o nome de um app (ex: `jellyfin`) para iniciá-lo ou pará-lo."
        )

    @staticmethod
    def format_apps_list(apps: list[dict]) -> str:
        """Formata a lista de aplicativos com status."""
        if not apps:
            return "Nenhum aplicativo encontrado."

        lines = ["*Aplicativos Instalados:*\n"]
        for app in sorted(apps, key=lambda x: x.get('id', '')):
            status_icon = STATUS_ICON_OK if app.get('status') == "running" else STATUS_ICON_OFF
            lines.append(f"{status_icon} `{app.get('id', 'N/A')}`")
        
        return "\n".join(lines)

    @staticmethod
    def format_status_summary(apps: list[dict]) -> str:
        """Cria um resumo do status dos apps."""
        if not apps:
            return "Nenhum aplicativo para resumir."
        
        total = len(apps)
        running = sum(1 for app in apps if app.get('status') == "running")
        return f"{ICON_SUMMARY} *Resumo*: {running} de {total} aplicativos estão ativos."

    @staticmethod
    def format_scripts_list(scripts: list[str]) -> str:
        """Formata a lista de scripts executáveis."""
        if not scripts:
            return f"{ICON_SCRIPTS} Nenhum script executável encontrado no diretório configurado."
        
        lines = [f"{ICON_SCRIPTS} *Scripts Executáveis:*\n"]
        lines.extend(f"• `{script}`" for script in sorted(scripts))
        lines.append("\nUse `/run [nome_do_script]` para executar um deles.")
        return "\n".join(lines)

    @staticmethod
    def format_script_output(script_name: str, stdout: str, stderr: str, exit_code: int) -> str:
        """Formata a saída de um script executado."""
        status = "sucesso" if exit_code == 0 else "falha"
        header = f"Resultado da execução de `{script_name}` (status: {status}, código: {exit_code}):"
        
        output_str = f"*Saída Padrão (stdout):*\n```\n{stdout or '(vazio)'}\n```"
        
        error_str = ""
        if stderr:
            error_str = f"\n*Saída de Erro (stderr):*\n```\n{stderr}\n```"
            
        return f"{header}\n\n{output_str}{error_str}"