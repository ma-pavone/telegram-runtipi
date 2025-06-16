# src/api/runtipi.py
import requests
import logging
from typing import Dict, Optional, Any
from urllib.parse import urljoin

logger = logging.getLogger(__name__)

class RuntipiAPI:
    """Cliente para interagir com a API do Runtipi"""
    
    def __init__(self, host: str, username: str, password: str):
        self.host = host.rstrip('/')
        self.username = username
        self.password = password
        self.session = requests.Session()
        self._authenticated = False
        
        # Headers padrão que imitam um browser real
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36',
            'Accept': '*/*',
            'Accept-Language': 'en,pt-BR;q=0.9,pt;q=0.8',
            'Connection': 'keep-alive'
        })
        
    def _authenticate(self) -> bool:
        """Autentica com a API do Runtipi seguindo o padrão exato do curl"""
        if self._authenticated:
            return True
            
        try:
            auth_url = f"{self.host}/api/auth/login"
            payload = {
                "username": self.username,
                "password": self.password
            }
            
            # Headers específicos para autenticação
            auth_headers = {
                'Content-Type': 'application/json',
                'Origin': self.host,
                'Referer': f'{self.host}/login'
            }
            
            logger.info(f"Tentando autenticar em: {auth_url}")
            
            response = self.session.post(
                auth_url, 
                json=payload, 
                headers=auth_headers,
                verify=False  # Equivale ao -k do curl
            )
            
            logger.debug(f"Status da autenticação: {response.status_code}")
            logger.debug(f"Headers da resposta: {dict(response.headers)}")
            logger.debug(f"Cookies recebidos: {dict(response.cookies)}")
            
            if response.status_code == 200:
                self._authenticated = True
                logger.info("Autenticado com sucesso na API do Runtipi")
                return True
            else:
                logger.error(f"Falha na autenticação: {response.status_code}")
                logger.error(f"Resposta: {response.text}")
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
            
            # Headers específicos para requisições normais
            request_headers = kwargs.pop('headers', {})
            request_headers.update({
                'Referer': f'{self.host}/apps'
            })
            
            logger.debug(f"Fazendo requisição {method} para: {url}")
            
            response = self.session.request(
                method, 
                url, 
                headers=request_headers,
                verify=False,  # Equivale ao -k do curl
                **kwargs
            )
            
            logger.debug(f"Status da requisição: {response.status_code}")
            
            if response.status_code == 401:
                # Token/cookie expirou, tenta reautenticar
                logger.info("Token expirado, tentando reautenticar...")
                self._authenticated = False
                if self._authenticate():
                    response = self.session.request(
                        method, 
                        url, 
                        headers=request_headers,
                        verify=False,
                        **kwargs
                    )
                else:
                    return None
            
            if response.status_code == 200:
                try:
                    return response.json()
                except ValueError:
                    # Resposta não é JSON válido
                    logger.warning("Resposta não é JSON válido")
                    return {"success": True, "data": response.text}
            else:
                logger.error(f"Erro na requisição {method} {endpoint}: {response.status_code}")
                logger.error(f"Resposta: {response.text}")
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
        """Inicia um app usando o endpoint correto"""
        # Usando o endpoint correto baseado no curl
        endpoint = f"/app-lifecycle/{app_id}%3Amigrated/start"
        
        headers = {
            'Origin': self.host,
            'Referer': f'{self.host}/apps/migrated/{app_id}'
        }
        
        result = self._make_request("POST", endpoint, headers=headers)
        return result is not None
    
    def stop_app(self, app_id: str) -> bool:
        """Para um app usando o endpoint correto"""
        # Assumindo que existe um endpoint similar para stop
        endpoint = f"/app-lifecycle/{app_id}%3Amigrated/stop"
        
        headers = {
            'Origin': self.host,
            'Referer': f'{self.host}/apps/migrated/{app_id}'
        }
        
        result = self._make_request("POST", endpoint, headers=headers)
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
    
    def test_connection(self) -> bool:
        """Testa a conexão e autenticação"""
        try:
            result = self.get_installed_apps()
            return result is not None
        except Exception as e:
            logger.error(f"Erro no teste de conexão: {e}")
            return False