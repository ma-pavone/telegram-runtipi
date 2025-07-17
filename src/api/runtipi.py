# src/api/runtipi.py
import requests
import logging
from typing import Dict, Optional, Any

logger = logging.getLogger(__name__)

class RuntipiAPI:
    """Cliente para interagir com a API do Runtipi"""
    
    def __init__(self, host: str, username: str, password: str):
        self.host = host.rstrip('/')
        self.username = username
        self.password = password
        self.session = requests.Session()
        self._authenticated = False
        
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0',
            'Accept': '*/*',
            'Accept-Language': 'en,pt-BR;q=0.9,pt;q=0.8',
            'Connection': 'keep-alive'
        })
        
    def _authenticate(self) -> bool:
        if self._authenticated:
            return True
            
        try:
            auth_url = f"{self.host}/api/auth/login"
            payload = { "username": self.username, "password": self.password }
            headers = {
                'Content-Type': 'application/json',
                'Origin': self.host,
                'Referer': f'{self.host}/login'
            }

            response = self.session.post(auth_url, json=payload, headers=headers, verify=False)
            if response.status_code in [200, 201]:
                self._authenticated = True
                logger.info("Autenticado com sucesso na API do Runtipi")
                return True
            logger.error(f"Falha na autenticação: {response.status_code} - {response.text}")
            return False
                
        except Exception as e:
            logger.error(f"Erro na autenticação: {e}")
            return False
    
    def _make_request(self, method: str, endpoint: str, **kwargs) -> Optional[Dict[str, Any]]:
        if not self._authenticate():
            return None
            
        try:
            url = f"{self.host}/api{endpoint}"
            headers = kwargs.pop('headers', {})
            headers.update({ 'Referer': f'{self.host}/apps' })

            response = self.session.request(method, url, headers=headers, verify=False, **kwargs)

            if response.status_code == 401:
                self._authenticated = False
                if self._authenticate():
                    response = self.session.request(method, url, headers=headers, verify=False, **kwargs)
                else:
                    return None

            if response.status_code in [200, 201, 202]:
                try:
                    return response.json()
                except ValueError:
                    return { "success": True, "data": response.text, "status_code": response.status_code }
            else:
                logger.error(f"Erro {response.status_code} em {method} {endpoint}: {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Erro na requisição {method} {endpoint}: {e}")
            return None

    def get_installed_apps(self) -> Optional[Dict[str, Any]]:
        return self._make_request("GET", "/apps/installed")
    
    def get_app_status(self, app_name: str) -> Optional[str]:
        """Retorna apenas o status do app como string"""
        data = self.get_installed_apps()
        if not isinstance(data, dict) or 'installed' not in data:
            logger.error("Resposta inválida de get_installed_apps")
            return None
        
        for app in data['installed']:
            if not isinstance(app, dict):
                continue
            info = app.get('info')
            app_data = app.get('app')
            if isinstance(info, dict) and isinstance(app_data, dict):
                if info.get('id') == app_name:
                    return app_data.get('status')
        return None
    
    def get_app_data(self, app_name: str) -> Optional[Dict[str, Any]]:
        """Retorna o objeto completo do app"""
        data = self.get_installed_apps()
        if not isinstance(data, dict) or 'installed' not in data:
            logger.error("Resposta inválida de get_installed_apps")
            return None
        
        for app in data['installed']:
            if not isinstance(app, dict):
                continue
            info = app.get('info')
            app_data = app.get('app')
            if isinstance(info, dict) and isinstance(app_data, dict):
                if info.get('id') == app_name:
                    return app  # Retorna o objeto completo
        return None
    
    def get_all_apps_status(self) -> Optional[Dict[str, str]]:
        data = self.get_installed_apps()
        if not isinstance(data, dict) or 'installed' not in data:
            logger.error("Resposta inválida de get_installed_apps")
            return None
        
        result = {}
        for app in data['installed']:
            if not isinstance(app, dict):
                continue
            info = app.get('info')
            app_data = app.get('app')
            if isinstance(info, dict) and isinstance(app_data, dict):
                app_id = info.get('id')
                status = app_data.get('status')
                if app_id and status:
                    result[app_id] = status
        return result

    def _lifecycle(self, app_name: str, action: str) -> bool:
        if action not in ["start", "stop"]:
            logger.error(f"Ação inválida: {action}")
            return False
        app_id_encoded = f"{app_name}%3Amigrated"
        endpoint = f"/app-lifecycle/{app_id_encoded}/{action}"
        headers = {
            'Origin': self.host,
            'Referer': f'{self.host}/apps/migrated/{app_name}'
        }
        result = self._make_request("POST", endpoint, headers=headers)
        if not result:
            return False
        if isinstance(result, dict):
            if 'success' in result:
                return bool(result['success'])
            if result.get('status_code') in [200, 201, 202]:
                return True
        return True

    def start_app(self, app_name: str) -> bool:
        return self._lifecycle(app_name, "start")

    def stop_app(self, app_name: str) -> bool:
        return self._lifecycle(app_name, "stop")

    def toggle_app_action(self, app_name: str, action: str) -> bool:
        try:
            return self._lifecycle(app_name, action)
        except Exception as e:
            logger.error(f"Erro no toggle para {app_name}: {e}")
            return False

    def test_connection(self) -> bool:
        try:
            return bool(self.get_installed_apps())
        except Exception as e:
            logger.error(f"Erro no teste de conexão: {e}")
            return False