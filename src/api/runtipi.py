import requests
import logging
from typing import Dict, Optional, Any, List
from .cache import cached

logger = logging.getLogger(__name__)

# Desativa avisos de SSL para ambientes locais (não ideal para produção externa)
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
            response = self.session.post(auth_url, json=payload, verify=False, timeout=10)
            response.raise_for_status()
            self._authenticated = True
            logger.info("Authentication successful.")
            return True
        except requests.RequestException as e:
            logger.error(f"Authentication failed: {e}")
            self._authenticated = False
            return False

    def _make_request(self, method: str, endpoint: str, **kwargs) -> Optional[Any]:
        """Realiza uma requisição à API, cuidando da autenticação."""
        if not self._authenticate():
            return None
            
        url = f"{self.host}/api{endpoint}"
        kwargs.setdefault('verify', False)
        kwargs.setdefault('timeout', 15)

        try:
            response = self.session.request(method, url, **kwargs)
            if response.status_code == 401: # Token expirado
                logger.warning("Token expired, re-authenticating...")
                self._authenticated = False
                if self._authenticate():
                    response = self.session.request(method, url, **kwargs)

            response.raise_for_status()
            
            # Retorna JSON se possível, senão o texto da resposta.
            try:
                return response.json()
            except ValueError:
                return response.text or None

        except requests.RequestException as e:
            logger.error(f"Request failed to {method} {endpoint}: {e}")
            return None

    @cached(ttl=30, rate_limit=5) # Cache por 30s, com limite de chamada de 5s
    def get_installed_apps(self) -> List[Dict[str, Any]]:
        """Busca e cacheia a lista de apps instalados."""
        data = self._make_request("GET", "/apps/installed")
        return data.get('installed', []) if isinstance(data, dict) else []

    def get_all_apps_status(self) -> Dict[str, str]:
        """Retorna um dicionário com o status de todos os apps."""
        apps = self.get_installed_apps()
        return {
            app['info']['id']: app['app']['status']
            for app in apps
            if 'info' in app and 'id' in app['info'] and 'app' in app and 'status' in app['app']
        }

    def get_app_data(self, app_id: str) -> Optional[Dict[str, Any]]:
        """Busca os dados de um app específico pelo ID."""
        for app in self.get_installed_apps():
            if app.get('info', {}).get('id') == app_id:
                return app
        return None

    def toggle_app_action(self, app_id: str) -> bool:
        """Inicia ou para um app com base no seu estado atual."""
        app_data = self.get_app_data(app_id)
        if not app_data:
            logger.error(f"App not found: {app_id}")
            return False
            
        current_status = app_data.get('app', {}).get('status')
        action = "stop" if current_status == "running" else "start"
        
        app_id_encoded = f"{app_id}%3Amigrated"
        endpoint = f"/app-lifecycle/{app_id_encoded}/{action}"
        
        result = self._make_request("POST", endpoint)
        return result is not None

    def test_connection(self) -> bool:
        """Testa a conexão e autenticação com a API."""
        return self._authenticate()