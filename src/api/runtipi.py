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
        
    def _authenticate(self) -> bool:
        """Autentica com a API do Runtipi"""
        if self._authenticated:
            return True
            
        try:
            auth_url = f"{self.host}/api/auth/login"
            payload = {
                "username": self.username,
                "password": self.password
            }
            
            response = self.session.post(auth_url, json=payload)
            
            if response.status_code == 200:
                self._authenticated = True
                logger.info("Autenticado com sucesso na API do Runtipi")
                return True
            else:
                logger.error(f"Falha na autenticação: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Erro na autenticação: {e}")
            return False
    
    def _make_request(self, method: str, endpoint: str, **kwargs) -> Optional[Dict[str, Any]]:
        """Faz requisição autenticada para a API"""
        if not self._authenticate():
            return None
            
        try:
            url = f"{self.host}/api{endpoint}"
            response = self.session.request(method, url, **kwargs)
            
            if response.status_code == 401:
                # Token expirou, tenta reautenticar
                self._authenticated = False
                if self._authenticate():
                    response = self.session.request(method, url, **kwargs)
                else:
                    return None
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Erro na requisição {method} {endpoint}: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Erro na requisição {method} {endpoint}: {e}")
            return None
    
    def get_installed_apps(self) -> Optional[Dict[str, Any]]:
        """Obtém lista de apps instalados"""
        return self._make_request("GET", "/apps/installed")
    
    def get_app_status(self, app_id: str) -> Optional[Dict[str, Any]]:
        """Obtém status de um app específico"""
        return self._make_request("GET", f"/apps/{app_id}")
    
    def start_app(self, app_id: str) -> bool:
        """Inicia um app"""
        result = self._make_request("POST", f"/apps/{app_id}/start")
        return result is not None
    
    def stop_app(self, app_id: str) -> bool:
        """Para um app"""
        result = self._make_request("POST", f"/apps/{app_id}/stop")
        return result is not None
    
    def toggle_app_action(self, app_id: str, action: str) -> bool:
        """Executa ação de toggle (start/stop) em um app"""
        if action == "start":
            return self.start_app(app_id)
        elif action == "stop":
            return self.stop_app(app_id)
        else:
            logger.error(f"Ação inválida: {action}")
            return False