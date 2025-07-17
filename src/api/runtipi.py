import requests
import logging
from typing import Any, final, Optional
from dataclasses import dataclass
from enum import Enum

from .cache import APICache

logger = logging.getLogger(__name__)
class AppStatus(Enum):
    RUNNING = "running"
    STOPPED = "stopped"
    UNKNOWN = "unknown"

class AppAction(Enum):
    START = "start"
    STOP = "stop"
@dataclass
class RuntipiApp:
    id: str
    name: str
    status: AppStatus
    version: Optional[str] = None
    
    @classmethod
    def from_dict(cls, data: dict) -> 'RuntipiApp':
        """Cria uma instância a partir de dados da API."""
        return cls(
            id=data.get('id', ''),
            name=data.get('name', data.get('id', '')),
            status=AppStatus(data.get('status', 'unknown')),
            version=data.get('version')
        )
@dataclass
class APIResponse:
    success: bool
    data: Any = None
    error: Optional[str] = None

@final
class RuntipiAPI:
    """
    Cliente HTTP para a API do Runtipi, gerenciando autenticação e chamadas.
    """
    def __init__(self, host: str, username: str, password: str, timeout: int = 15):
        self._host = host.rstrip('/')  # Remove trailing slash
        self._username = username
        self._password = password
        self._timeout = timeout
        self._session = requests.Session()
        self._cache = APICache()
        self._is_authenticated = False
        self._endpoints = {
            'auth': '/api/auth/login',
            'apps': '/api/apps/installed',
            'app_action': '/api/apps/{app_id}/{action}'
        }

    def _get_url(self, endpoint: str) -> str:
        """Constrói URL completa para um endpoint."""
        return f"{self._host}{endpoint}"

    def _authenticate(self) -> bool:
        """Realiza a autenticação na API do Runtipi e armazena a sessão."""
        url = self._get_url(self._endpoints['auth'])
        credentials = {"username": self._username, "password": self._password}
        
        try:
            response = self._session.post(url, json=credentials, timeout=self._timeout)
            response.raise_for_status()
            self._is_authenticated = True
            logger.info("Autenticação na API do Runtipi bem-sucedida.")
            return True
        except requests.RequestException as e:
            logger.error(f"Falha ao autenticar na API do Runtipi: {e}")
            self._is_authenticated = False
            return False

    def _make_request(self, method: str, endpoint: str, **kwargs: Any) -> APIResponse:
        """Método central para requisições, com lógica de reautenticação."""
        if not self._is_authenticated and not self._authenticate():
            return APIResponse(
                success=False, 
                error="Não foi possível autenticar na API do Runtipi"
            )

        url = self._get_url(endpoint)
        
        try:
            response = self._session.request(
                method, url, timeout=self._timeout, **kwargs
            )
            
            if response.status_code == 401:  # Sessão expirada
                logger.warning("Sessão expirada. Tentando reautenticar...")
                if self._authenticate():
                    response = self._session.request(
                        method, url, timeout=self._timeout, **kwargs
                    )
            
            response.raise_for_status()
            data = response.json() if response.content else {}
            
            return APIResponse(success=True, data=data)
            
        except requests.RequestException as e:
            logger.error(f"Erro na requisição para {method.upper()} {url}: {e}")
            return APIResponse(success=False, error=str(e))

    def test_connection(self) -> bool:
        """Testa se é possível conectar à API."""
        return self._authenticate()

    @APICache().cached(ttl=15)
    def get_installed_apps(self) -> list[RuntipiApp]:
        """Busca a lista de apps instalados (com cache de 15s)."""
        logger.debug("Buscando lista de apps instalados na API.")
        
        response = self._make_request("GET", self._endpoints['apps'])
        
        if not response.success:
            logger.error(f"Falha ao buscar apps: {response.error}")
            return []
        try:
            apps_data = response.data
            if isinstance(apps_data, dict):
                if 'installed' in apps_data:
                    apps_list = apps_data['installed']
                else:
                    apps_list = apps_data
            else:
                apps_list = apps_data
            
            if not isinstance(apps_list, list):
                logger.error(f"Resposta da API não é uma lista: {type(apps_list)}")
                return []
            return [RuntipiApp.from_dict(app) for app in apps_list]
            
        except (KeyError, TypeError, ValueError) as e:
            logger.error(f"Erro ao processar dados dos apps: {e}")
            return []

    def _lifecycle_action(self, app_id: str, action: AppAction) -> APIResponse:
        """Executa uma ação de ciclo de vida (start, stop) em um app."""
        logger.info(f"Executando ação '{action.value}' para o app '{app_id}'.")
        
        endpoint = self._endpoints['app_action'].format(
            app_id=app_id, action=action.value
        )
        
        return self._make_request("POST", endpoint)

    def start_app(self, app_id: str) -> APIResponse:
        """Inicia um app."""
        return self._lifecycle_action(app_id, AppAction.START)

    def stop_app(self, app_id: str) -> APIResponse:
        """Para um app."""
        return self._lifecycle_action(app_id, AppAction.STOP)

    def toggle_app_action(self, app_id: str, current_status: AppStatus) -> APIResponse:
        """Inicia ou para um app com base em seu status atual."""
        action = AppAction.STOP if current_status == AppStatus.RUNNING else AppAction.START
        return self._lifecycle_action(app_id, action)

    def find_app_by_id(self, app_id: str) -> Optional[RuntipiApp]:
        """Busca um app específico pelo ID."""
        apps = self.get_installed_apps()
        return next((app for app in apps if app.id == app_id), None)