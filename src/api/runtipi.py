# src/api/runtipi.py
import requests
import logging
from typing import Dict, Optional, Any, List
from .cache import cached
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)

# Suprime warnings SSL para ambiente local
requests.packages.urllib3.disable_warnings()

class RuntipiAPI:
    """Cliente otimizado para API Runtipi com retry e pooling"""
    
    def __init__(self, host: str, username: str, password: str):
        self.host = host.rstrip('/')
        self.username = username
        self.password = password
        self._setup_session()
        self._authenticated = False

    def _setup_session(self):
        """Configura sessão com retry e pooling"""
        self.session = requests.Session()
        
        # Configuração de retry
        retry_strategy = Retry(
            total=3,
            backoff_factor=0.5,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        
        adapter = HTTPAdapter(
            max_retries=retry_strategy,
            pool_connections=10,
            pool_maxsize=10
        )
        
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
        self.session.headers.update({
            'User-Agent': 'TelegramRuntipiBot/2.0',
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        })

    def _authenticate(self) -> bool:
        """Autentica com retry automático"""
        if self._authenticated:
            return True
        
        try:
            response = self.session.post(
                f"{self.host}/api/auth/login",
                json={"username": self.username, "password": self.password},
                verify=False,
                timeout=10
            )
            response.raise_for_status()
            self._authenticated = True
            logger.info("Runtipi API authentication successful")
            return True
            
        except requests.RequestException as e:
            logger.error(f"Authentication failed: {e}")
            self._authenticated = False
            return False

    def _request(self, method: str, endpoint: str, **kwargs) -> Optional[Any]:
        """Requisição com auto-retry de auth"""
        if not self._authenticated and not self._authenticate():
            return None
            
        kwargs.setdefault('verify', False)
        kwargs.setdefault('timeout', 15)
        
        url = f"{self.host}/api{endpoint}"
        
        try:
            response = self.session.request(method, url, **kwargs)
            
            # Re-autentica se token expirou
            if response.status_code == 401:
                logger.info("Token expired, re-authenticating...")
                self._authenticated = False
                if self._authenticate():
                    response = self.session.request(method, url, **kwargs)
                else:
                    return None

            response.raise_for_status()
            return response.json() if response.content else None
            
        except requests.JSONDecodeError:
            logger.warning(f"Non-JSON response from {method} {endpoint}")
            return response.text if response.content else None
        except requests.RequestException as e:
            logger.error(f"Request failed {method} {endpoint}: {e}")
            return None

    @cached(ttl=30, rate_limit=5)
    def get_installed_apps(self) -> List[Dict[str, Any]]:
        """Retorna lista de apps instalados"""
        data = self._request("GET", "/apps/installed")
        if isinstance(data, dict) and 'installed' in data:
            return data['installed']
        return []

    def get_app_data(self, app_id: str) -> Optional[Dict[str, Any]]:
        """Busca dados específicos de um app"""
        apps = self.get_installed_apps()
        return next(
            (app for app in apps if app.get('info', {}).get('id') == app_id),
            None
        )

    def toggle_app(self, app_id: str) -> bool:
        """Alterna estado do app (start/stop)"""
        app_data = self.get_app_data(app_id)
        if not app_data:
            logger.error(f"App '{app_id}' not found")
            return False
            
        current_status = app_data.get('app', {}).get('status', 'unknown')
        action = "stop" if current_status == "running" else "start"
        
        # Encoding necessário para apps migrados
        app_id_encoded = f"{app_id}%3Amigrated"
        endpoint = f"/app-lifecycle/{app_id_encoded}/{action}"
        
        result = self._request("POST", endpoint)
        success = result is not None
        
        if success:
            logger.info(f"Successfully {action}ed app '{app_id}'")
        else:
            logger.error(f"Failed to {action} app '{app_id}'")
            
        return success

    def test_connection(self) -> bool:
        """Testa conectividade"""
        return self._authenticate()