import requests
import logging

logger = logging.getLogger(__name__)

class RuntipiAPI:
    def __init__(self, host, username, password):
        self.host = host.rstrip('/')
        self.username = username
        self.password = password
        self.session = requests.Session()
        self.authenticated = False

    def login(self):
        try:
            login_data = {"username": self.username, "password": self.password}
            headers = {
                'Content-Type': 'application/json',
                'Accept': '*/*',
                'Origin': self.host,
                'Referer': f'{self.host}/login',
                'User-Agent': 'Mozilla/5.0'
            }
            response = self.session.post(
                f"{self.host}/api/auth/login",
                json=login_data,
                headers=headers,
                timeout=10
            )
            if response.status_code == 201:
                self.authenticated = True
                logger.info("[API Runtipi] Login realizado com sucesso")
                return True
            else:
                logger.error(f"[API Runtipi] Erro no login: {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"[API Runtipi] Erro na autenticação: {e}")
            return False

    def get_installed_apps(self):
        if not self.authenticated and not self.login():
            return None
        try:
            headers = {
                'Accept': '*/*',
                'Accept-Language': 'en,pt-BR;q=0.9,pt;q=0.8',
                'Connection': 'keep-alive',
                'Referer': f'{self.host}/apps',
                'User-Agent': 'Mozilla/5.0'
            }
            response = self.session.get(
                f"{self.host}/api/apps/installed",
                headers=headers,
                timeout=10
            )
            if response.status_code == 200:
                logger.info("[API Runtipi] Apps instalados obtidos com sucesso")
                return response.json()
            else:
                logger.error(f"[API Runtipi] Erro ao obter apps: {response.status_code}")
                return None
        except Exception as e:
            logger.error(f"[API Runtipi] Erro ao obter apps instalados: {e}")
            return None

    def toggle_app(self, app_urn, action):
        if not self.authenticated and not self.login():
            return False
        try:
            encoded_urn = app_urn.replace(':', '%3A')
            headers = {
                'Accept': '*/*',
                'Origin': self.host,
                'Referer': f'{self.host}/apps/migrated/{app_urn.split(":")[0]}',
                'User-Agent': 'Mozilla/5.0'
            }
            response = self.session.post(
                f"{self.host}/api/app-lifecycle/{encoded_urn}/{action}",
                headers=headers,
                timeout=30
            )
            if response.status_code in [200, 201]:
                logger.info(f"[API Runtipi] App {app_urn} {action} executado com sucesso")
                return True
            else:
                logger.error(f"[API Runtipi] Erro ao {action} app {app_urn}: {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"[API Runtipi] Erro ao {action} app {app_urn}: {e}")
            return False
