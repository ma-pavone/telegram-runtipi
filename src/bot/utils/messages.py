# src/bot/utils/messages.py
from typing import List, Dict, Any

class MessageFormatter:
    """Formatador de mensagens centralizado"""
    
    @staticmethod
    def help_text() -> str:
        return """🤖 *Runtipi Controller Bot*

*Comandos:*
• `/help` - Esta ajuda
• `/apps` - Lista apps e status
• `/status` - Resumo de status
• `/scripts` - Scripts disponíveis
• `/run <script>` - Executa script

*Toggle Apps:*
Digite apenas o ID do app para ligar/desligar
Ex: `jellyfin`, `sonarr`, `radarr`

*Exemplos:*
```
/apps
jellyfin
/run backup.sh
```"""

    def apps_list(self, apps: List[Dict[str, Any]]) -> str:
        """Formata lista de apps"""
        if not apps:
            return "❌ Nenhum app encontrado"

        running = []
        stopped = []

        for app in apps:
            app_info = app.get('info', {})
            app_id = app_info.get('id', 'unknown')
            app_name = app_info.get('name', app_id)
            status = app.get('app', {}).get('status', 'unknown')
            
            display = f"`{app_id}`"
            if app_name != app_id:
                display += f" ({app_name})"
            
            if status == "running":
                running.append(f"🟢 {display}")
            else:
                stopped.append(f"🔴 {display}")

        parts = ["📱 *Apps Instalados:*\n"]
        
        if running:
            parts.append("*🟢 Executando:*")
            parts.extend(running)
            parts.append("")
        
        if stopped:
            parts.append("*🔴 Parados:*")
            parts.extend(stopped)

        return "\n".join(parts)

    def status_summary(self, apps: List[Dict[str, Any]]) -> str:
        """Resumo de status"""
        if not apps:
            return "❌ Nenhum app encontrado"

        total = len(apps)
        running = sum(1 for app in apps 
                     if app.get('app', {}).get('status') == 'running')
        stopped = total - running

        return f"""📊 *Status Resumido:*

🟢 Executando: {running}
🔴 Parados: {stopped}
📱 Total: {total}"""

    def scripts_list(self, scripts_info: Dict[str, Any], scripts_dir: str) -> str:
        """Lista de scripts"""
        if scripts_info['error']:
            return f"❌ {scripts_info['error']}"
        
        executable = scripts_info['executable']
        non_executable = scripts_info['non_executable']
        
        if not executable and not non_executable:
            return f"⚠️ Nenhum script encontrado em `{scripts_dir}`"

        parts = [f"📂 *Scripts em `{scripts_dir}`:*\n"]
        
        if executable:
            parts.append("*🟢 Executáveis:*")
            parts.extend(f"• `{script}`" for script in sorted(executable))
            parts.append("")
        
        if non_executable:
            parts.append("*🔴 Sem permissão:*")
            parts.extend(f"• `{script}`" for script in sorted(non_executable))
            parts.append("")
        
        parts.append("*Uso:* `/run <script.sh>`")
        
        return "\n".join(parts)

    def script_result(self, script_name: str, result: Dict[str, Any]) -> str:
        """Resultado de execução de script"""
        status = "✅ Sucesso" if result['success'] else "❌ Falha"
        
        parts = [
            f"**{script_name}**\n",
            f"{status}",
            f"*Tempo:* `{result['duration']:.2f}s`",
            f"*Código:* `{result['exit_code']}`"
        ]
        
        if result['stdout']:
            stdout = result['stdout'][:2000]  # Trunca para evitar limite
            parts.append(f"\n📋 **Saída:**\n```\n{stdout}\n```")
        
        if result['stderr']:
            stderr = result['stderr'][:1000]
            parts.append(f"\n🔥 **Erro:**\n```\n{stderr}\n```")
        
        return "\n".join(parts)


# src/bot/utils/scripts.py
import os
import re
import time
import asyncio
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class ScriptRunner:
    """Executor de scripts com validação e timeout"""
    
    def __init__(self, scripts_dir: str):
        self.scripts_dir = scripts_dir
        self.timeout = 300  # 5 minutos

    def is_safe_name(self, script_name: str) -> bool:
        """Valida nome do script"""
        if not script_name or '..' in script_name or '/' in script_name:
            return False
        return bool(re.match(r"^[a-zA-Z0-9_.-]+\.sh$", script_name))

    def list_scripts(self) -> Dict[str, Any]:
        """Lista scripts disponíveis"""
        try:
            if not os.path.isdir(self.scripts_dir):
                return {'error': f"Diretório não encontrado: {self.scripts_dir}"}
            
            all_files = [f for f in os.listdir(self.scripts_dir) 
                        if os.path.isfile(os.path.join(self.scripts_dir, f))]
            
            valid_scripts = [f for f in all_files if self.is_safe_name(f)]
            
            executable = []
            non_executable = []
            
            for script in valid_scripts:
                path = os.path.join(self.scripts_dir, script)
                if os.access(path, os.X_OK):
                    executable.append(script)
                else:
                    non_executable.append(script)
            
            return {
                'error': None,
                'executable': executable,
                'non_executable': non_executable
            }
            
        except Exception as e:
            logger.error(f"Error listing scripts: {e}")
            return {'error': f"Erro ao listar scripts: {str(e)}"}

    async def execute(self, script_name: str) -> Dict[str, Any]:
        """Executa script com timeout"""
        script_path = os.path.join(self.scripts_dir, script_name)
        
        # Validações
        if not os.path.isfile(script_path):
            raise FileNotFoundError(f"Script não encontrado: {script_name}")
        
        if not os.access(script_path, os.X_OK):
            raise PermissionError(f"Script sem permissão: {script_name}")
        
        start_time = time.time()
        
        try:
            process = await asyncio.create_subprocess_exec(
                script_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=self.scripts_dir
            )
            
            stdout, stderr = await asyncio.wait_for(
                process.communicate(), 
                timeout=self.timeout
            )
            
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
            return {
                'success': False,
                'exit_code': -1,
                'stdout': '',
                'stderr': 'Timeout excedido (5 minutos)',
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