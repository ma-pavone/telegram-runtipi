import requests
import logging
from typing import Dict, Optional, Any
import urllib.parse

logger = logging.getLogger(__name__)

class RuntipiAPI:
    def __init__(self, host: str, username: str, password: str):
        self.host = host.rstrip('/')
        self.username = username
        self.password = password
        self.session = requests.Session()
        self.authenticated = False
        
        # Headers padrão para requisições
        self.default_headers = {
            'Accept': '*/*',
            'User-Agent': 'Mozilla/5.0 (compatible; RuntipiBot/1.0)',
            'Content-Type': 'application/json'
        }

    def _make_request(self, method: str, endpoint: str, **kwargs) -> Optional[requests.Response]:
        """Método genérico para fazer requisições com tratamento de erro"""
        if not self.authenticated and not self.login():
            logger.error("[API] Falha na autenticação")
            return None
            
        url = f"{self.host}{endpoint}"
        headers = {**self.default_headers, **kwargs.pop('headers', {})}
        
        try:
            response = self.session.request(
                method=method,
                url=url,
                headers=headers,
                timeout=30,
                **kwargs
            )
            
            if response.status_code == 401:
                logger.warning("[API] Token expirado, tentando reautenticar...")
                self.authenticated = False
                if self.login():
                    return self._make_request(method, endpoint, **kwargs)
                return None
                
            return response
            
        except requests.exceptions.RequestException as e:
            logger.error(f"[API] Erro na requisição {method} {endpoint}: {e}")
            return None

    def login(self) -> bool:
        """Autentica na API do Runtipi"""
        try:
            login_data = {
                "username": self.username,
                "password": self.password
            }
            
            headers = {
                **self.default_headers,
                'Origin': self.host,
                'Referer': f'{self.host}/login'
            }
            
            response = self.session.post(
                f"{self.host}/api/auth/login",
                json=login_data,
                headers=headers,
                timeout=15
            )
            
            if response.status_code == 201:
                self.authenticated = True
                logger.info("[API] Login realizado com sucesso")
                return True
            else:
                logger.error(f"[API] Erro no login: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"[API] Erro na autenticação: {e}")
            return False

    def get_installed_apps(self) -> Optional[Dict[str, Any]]:
        """Obtém lista de apps instalados"""
        response = self._make_request(
            'GET', 
            '/api/apps/installed',
            headers={'Referer': f'{self.host}/apps'}
        )
        
        if response and response.status_code == 200:
            logger.info("[API] Apps instalados obtidos com sucesso")
            return response.json()
        else:
            status = response.status_code if response else "Sem resposta"
            logger.error(f"[API] Erro ao obter apps: {status}")
            return None

    def get_app_status(self, app_id: str) -> Optional[Dict[str, Any]]:
        """Obtém status específico de um app"""
        # Primeiro tenta obter da lista de apps instalados
        apps_data = self.get_installed_apps()
        
        if not apps_data or 'installed' not in apps_data:
            return None
            
        # Procura o app na lista
        for app in apps_data['installed']:
            if app['info']['id'].lower() == app_id.lower():
                return app
                
        logger.warning(f"[API] App {app_id} não encontrado na lista de instalados")
        return None

    def _build_app_urn(self, app_id: str) -> str:
        """Constrói o URN do app no formato esperado pela API"""
        return f"{app_id}:migrated"

    def _encode_urn(self, urn: str) -> str:
        """Codifica o URN para uso na URL"""
        return urllib.parse.quote(urn, safe='')

    def toggle_app_action(self, app_id: str, action: str) -> bool:
        """Executa ação de start/stop no app"""
        if action not in ['start', 'stop']:
            logger.error(f"[API] Ação inválida: {action}")
            return False
            
        # Constrói URN e codifica
        app_urn = self._build_app_urn(app_id)
        encoded_urn = self._encode_urn(app_urn)
        
        logger.info(f"[API] Executando {action} para {app_id} (URN: {app_urn})")
        
        response = self._make_request(
            'POST',
            f'/api/app-lifecycle/{encoded_urn}/{action}',
            headers={
                'Origin': self.host,
                'Referer': f'{self.host}/apps/migrated/{app_id}'
            }
        )
        
        if response and response.status_code in [200, 201]:
            logger.info(f"[API] {action.capitalize()} executado com sucesso para {app_id}")
            return True
        else:
            status = response.status_code if response else "Sem resposta"
            logger.error(f"[API] Erro ao executar {action} em {app_id}: {status}")
            return False

    def start_app(self, app_id: str) -> bool:
        """Inicia um app"""
        return self.toggle_app_action(app_id, 'start')

    def stop_app(self, app_id: str) -> bool:
        """Para um app"""
        return self.toggle_app_action(app_id, 'stop')

    def get_system_info(self) -> Optional[Dict[str, Any]]:
        """Obtém informações do sistema (se disponível)"""
        response = self._make_request('GET', '/api/system/info')
        
        if response and response.status_code == 200:
            logger.info("[API] Informações do sistema obtidas")
            return response.json()
        else:
            logger.warning("[API] Não foi possível obter informações do sistema")
            return None

    def health_check(self) -> bool:
        """Verifica se a API está respondendo"""
        try:
            response = self.session.get(
                f"{self.host}/api/health",
                timeout=10,
                headers={'User-Agent': self.default_headers['User-Agent']}
            )
            return response.status_code == 200
        except:
            return False