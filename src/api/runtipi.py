import requests
import logging
from typing import Any, final

from .cache import APICache

logger = logging.getLogger(__name__)
API_BASE_URL = "http://localhost:8080"
AUTH_ENDPOINT = "/api/auth/login"
INSTALLED_APPS_ENDPOINT = "/api/apps/installed"
APP_LIFECYCLE_ENDPOINT = "/api/apps/{app_id}/{action}"

@final
class RuntipiAPI:
    """
    Cliente HTTP para a API do Runtipi, gerenciando autenticação e chamadas.
    """
    def __init__(self, username: str, password: str):
        self._username = username
        self._password = password
        self._session = requests.Session()
        self._cache = APICache()
        self._is_authenticated = False

    def _authenticate(self) -> bool:
        """Realiza a autenticação na API do Runtipi e armazena a sessão."""
        url = f"{API_BASE_URL}{AUTH_ENDPOINT}"
        credentials = {"username": self._username, "password": self._password}
        try:
            response = self._session.post(url, json=credentials, timeout=10)
            response.raise_for_status()
            self._is_authenticated = True
            logger.info("Autenticação na API do Runtipi bem-sucedida.")
            return True
        except requests.RequestException as e:
            logger.error(f"Falha ao autenticar na API do Runtipi: {e}")
            self._is_authenticated = False
            return False

    def _make_request(self, method: str, endpoint: str, **kwargs: Any) -> Any:
        """Método central para requisições, com lógica de reautenticação."""
        if not self._is_authenticated and not self._authenticate():
            raise ConnectionError("Não foi possível autenticar na API do Runtipi.")

        url = f"{API_BASE_URL}{endpoint}"
        try:
            response = self._session.request(method, url, timeout=15, **kwargs)
            if response.status_code == 401:  # Não autorizado / Sessão expirada
                logger.warning("Sessão expirada. Tentando reautenticar...")
                if self._authenticate():
                    response = self._session.request(method, url, timeout=15, **kwargs)
            
            response.raise_for_status()
            return response.json() if response.content else {}
        except requests.RequestException as e:
            logger.error(f"Erro na requisição para {method.upper()} {url}: {e}")
            raise

    @APICache().cached(ttl=15)
    def get_installed_apps(self) -> list[dict[str, Any]]:
        """Busca a lista de apps instalados (com cache de 15s)."""
        logger.debug("Buscando lista de apps instalados na API.")
        return self._make_request("GET", INSTALLED_APPS_ENDPOINT)

    def _lifecycle(self, app_id: str, action: str) -> dict[str, Any]:
        """Executa uma ação de ciclo de vida (start, stop) em um app."""
        logger.info(f"Executando ação '{action}' para o app '{app_id}'.")
        endpoint = APP_LIFECYCLE_ENDPOINT.format(app_id=app_id, action=action)
        return self._make_request("POST", endpoint)

    def start_app(self, app_id: str) -> dict[str, Any]:
        """Inicia um app."""
        return self._lifecycle(app_id, "start")

    def stop_app(self, app_id: str) -> dict[str, Any]:
        """Para um app."""
        return self._lifecycle(app_id, "stop")

    def toggle_app_action(self, app_id: str, current_status: str) -> dict[str, Any]:
        """Inicia ou para um app com base em seu status atual."""
        action = "stop" if current_status == "running" else "start"
        return self._lifecycle(app_id, action)