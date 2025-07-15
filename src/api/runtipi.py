# src/api/runtipi.py

import requests
import logging
from typing import Dict, Optional, Any, List
from .cache import cached

logger = logging.getLogger(__name__)

# Desativa avisos de SSL para ambientes locais
requests.packages.urllib3.disable_warnings(requests.packages.urllib3.exceptions.InsecureRequestWarning)

class RuntipiAPI:
    def __init__(self, host: str, username: str, password: str):
        self.host = host.rstrip('/')
        self.username = username
        self.password = password
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'TelegramRuntipiBot/1.0',
            'Accept': 'application/json, */*',
        })
        self._authenticated = False

    def _authenticate(self) -> bool:
        """Realiza a autenticação na API do Runtipi."""
        if self._authenticated:
            return True
        
        auth_url = f"{self.host}/api/auth/login"
        payload = {"username": self.username, "password": self.password}
        
        try:
            logger.debug("Attempting to authenticate with Runtipi API.")
            response = self.session.post(auth_url, json=payload, verify=False, timeout=10)
            response.raise_for_status()
            self._authenticated = True
            logger.info("Authentication to Runtipi API successful.")
            return True
        except requests.RequestException as e:
            logger.error(f"Authentication failed: {e}")
            self._authenticated = False
            return False

    def _make_request(self, method: str, endpoint: str, **kwargs) -> Optional[Any]:
        """Realiza uma requisição à API, cuidando da autenticação."""
        if not self._authenticated and not self._authenticate():
            return None
            
        url = f"{self.host}/api{endpoint}"
        kwargs.setdefault('verify', False)
        kwargs.setdefault('timeout', 15)

        try:
            response = self.session.request(method, url, **kwargs)
            if response.status_code == 401: # Token pode ter expirado
                logger.warning("Token expired, re-authenticating...")
                self._authenticated = False
                if self._authenticate():
                    response = self.session.request(method, url, **kwargs)
                else:
                    return None

            response.raise_for_status()
            
            return response.json() if response.content else None

        except ValueError: # JSONDecodeError
            logger.warning(f"Non-JSON response received from {method} {endpoint}. Response: {response.text[:100]}")
            return response.text or None
        except requests.RequestException as e:
            logger.error(f"Request failed to {method} {endpoint}: {e}")
            return None

    # O cache aqui é muito eficiente. Mantido como está.
    @cached(ttl=30, rate_limit=5)
    def get_installed_apps(self) -> List[Dict[str, Any]]:
        """Busca e cacheia a lista de apps instalados."""
        data = self._make_request("GET", "/apps/installed")
        return data.get('installed', []) if isinstance(data, dict) else []

    def get_app_data(self, app_id: str) -> Optional[Dict[str, Any]]:
        """Busca os dados de um app específico pelo ID."""
        apps = self.get_installed_apps()
        for app in apps:
            if app.get('info', {}).get('id') == app_id:
                return app
        logger.warning(f"App with id '{app_id}' not found in installed list.")
        return None

    def toggle_app_action(self, app_id: str) -> bool:
        """Inicia ou para um app com base no seu estado atual."""
        app_data = self.get_app_data(app_id)
        if not app_data:
            logger.error(f"Cannot toggle app: App '{app_id}' not found.")
            return False
            
        current_status = app_data.get('app', {}).get('status', 'unknown')
        action = "stop" if current_status == "running" else "start"
        
        # O sufixo '%3Amigrated' parece ser um requisito da API para apps da store principal.
        # Esta é a parte mais "frágil". Se a Runtipi mudar isso, precisará de ajuste.
        # Uma alternativa seria extrair o 'app_id_encoded' de outra propriedade, se existir.
        app_id_encoded = f"{app_id}%3Amigrated"
        endpoint = f"/app-lifecycle/{app_id_encoded}/{action}"
        
        logger.info(f"Attempting to '{action}' app '{app_id}'.")
        result = self._make_request("POST", endpoint)
        
        if result is not None:
             logger.info(f"Successfully sent '{action}' command for app '{app_id}'.")
             return True
        else:
             logger.error(f"Failed to send '{action}' command for app '{app_id}'.")
             return False

    def test_connection(self) -> bool:
        """Testa a conexão e autenticação com a API."""
        return self._authenticate()