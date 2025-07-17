from typing import final
from enum import Enum
class Icons(Enum):
    STATUS_OK = "✅"
    STATUS_OFF = "❌"
    BOT = "🤖"
    SUMMARY = "📊"
    SCRIPTS = "📜"
    TIP = "💡"
    ERROR = "🔴"
    WARNING = "⚠️"
    SUCCESS = "🎉"
    LOADING = "⏳"

class MessageType(Enum):
    INFO = "info"
    ERROR = "error"
    SUCCESS = "success"
    WARNING = "warning"

@final
class BotMessages:
    """Namespace para todas as funções geradoras de mensagens do bot."""

    @staticmethod
    def get_help_message() -> str:
        """Retorna a mensagem de ajuda formatada em Markdown."""
        return (
            f"{Icons.BOT.value} *Bot de Controle do Runtipi* {Icons.BOT.value}\n\n"
            "Comandos disponíveis:\n\n"
            "*/apps* - Lista todos os aplicativos e seus status.\n"
            "*/status* - Mostra um resumo rápido de quantos apps estão ativos.\n"
            f"*/scripts* - {Icons.SCRIPTS.value} Lista os scripts disponíveis para execução.\n"
            "*/run `[nome_do_script]`* - Executa um script específico.\n"
            "*/help* - Mostra esta mensagem de ajuda.\n\n"
            f"{Icons.TIP.value} *Dica*: Envie o nome de um app (ex: `jellyfin`) para iniciá-lo ou pará-lo."
        )

    @staticmethod
    def format_apps_list(apps: list) -> str:
        """Formata a lista de aplicativos com status."""
        if not apps:
            return f"{Icons.WARNING.value} Nenhum aplicativo encontrado."

        lines = ["*Aplicativos Instalados:*\n"]
        running_apps = [app for app in apps if getattr(app, 'status', None) and app.status.value == "running"]
        stopped_apps = [app for app in apps if getattr(app, 'status', None) and app.status.value != "running"]
        
        if running_apps:
            lines.append(f"{Icons.STATUS_OK.value} *Ativos ({len(running_apps)}):*")
            for app in sorted(running_apps, key=lambda x: x.id):
                lines.append(f"  • `{app.id}`")
            lines.append("")
        
        if stopped_apps:
            lines.append(f"{Icons.STATUS_OFF.value} *Inativos ({len(stopped_apps)}):*")
            for app in sorted(stopped_apps, key=lambda x: x.id):
                lines.append(f"  • `{app.id}`")
        
        return "\n".join(lines)

    @staticmethod
    def format_status_summary(apps: list) -> str:
        """Cria um resumo do status dos apps."""
        if not apps:
            return f"{Icons.WARNING.value} Nenhum aplicativo para resumir."
        
        total = len(apps)
        running = sum(1 for app in apps if getattr(app, 'status', None) and app.status.value == "running")
        stopped = total - running
        
        return (
            f"{Icons.SUMMARY.value} *Resumo do Sistema:*\n"
            f"{Icons.STATUS_OK.value} Ativos: {running}\n"
            f"{Icons.STATUS_OFF.value} Inativos: {stopped}\n"
            f"📱 Total: {total}"
        )

    @staticmethod
    def format_scripts_list(scripts: list[str]) -> str:
        """Formata a lista de scripts executáveis."""
        if not scripts:
            return f"{Icons.WARNING.value} Nenhum script executável encontrado no diretório configurado."
        
        lines = [f"{Icons.SCRIPTS.value} *Scripts Executáveis ({len(scripts)}):*\n"]
        lines.extend(f"• `{script}`" for script in sorted(scripts))
        lines.append(f"\n{Icons.TIP.value} Use `/run [nome_do_script]` para executar um deles.")
        return "\n".join(lines)

    @staticmethod
    def format_script_output(script_name: str, stdout: str, stderr: str, exit_code: int) -> str:
        """Formata a saída de um script executado."""
        success_icon = Icons.SUCCESS.value if exit_code == 0 else Icons.ERROR.value
        status = "sucesso" if exit_code == 0 else "falha"
        
        header = f"{success_icon} Execução de `{script_name}` - {status} (código: {exit_code})"
        max_length = 3000
        
        if stdout:
            if len(stdout) > max_length:
                stdout = stdout[:max_length] + "\n... (saída truncada)"
            output_str = f"\n*📤 Saída Padrão:*\n```\n{stdout}\n```"
        else:
            output_str = f"\n*📤 Saída Padrão:* (vazia)"
        
        error_str = ""
        if stderr:
            if len(stderr) > max_length:
                stderr = stderr[:max_length] + "\n... (saída truncada)"
            error_str = f"\n*{Icons.ERROR.value} Saída de Erro:*\n```\n{stderr}\n```"
            
        return f"{header}{output_str}{error_str}"

    @staticmethod
    def format_app_action_result(app_id: str, action: str, success: bool, error: str = None) -> str:
        """Formata o resultado de uma ação em um app."""
        if success:
            icon = Icons.SUCCESS.value
            verb = "ligado" if action == "start" else "desligado"
            return f"{icon} App `{app_id}` foi {verb} com sucesso!"
        else:
            icon = Icons.ERROR.value
            return f"{icon} Falha ao {action} o app `{app_id}`: {error or 'Erro desconhecido'}"

    @staticmethod
    def format_error_message(error: str, context: str = None) -> str:
        """Formata uma mensagem de erro."""
        if context:
            return f"{Icons.ERROR.value} Erro em {context}: {error}"
        return f"{Icons.ERROR.value} {error}"

    @staticmethod
    def format_loading_message(action: str) -> str:
        """Formata uma mensagem de carregamento."""
        return f"{Icons.LOADING.value} {action}..."

    @staticmethod
    def format_success_message(message: str) -> str:
        """Formata uma mensagem de sucesso."""
        return f"{Icons.SUCCESS.value} {message}"

    @staticmethod
    def format_warning_message(message: str) -> str:
        """Formata uma mensagem de aviso."""
        return f"{Icons.WARNING.value} {message}"