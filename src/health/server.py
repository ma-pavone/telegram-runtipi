# src/health/server.py
import asyncio
import logging
from aiohttp import web
from datetime import datetime
from api.runtipi import RuntipiAPI
from typing import Optional

logger = logging.getLogger(__name__)

class HealthServer:
    def __init__(self, api: RuntipiAPI, port: int = 7777):
        self.api = api
        self.port = port
        self.start_time = datetime.now()
        self.last_health_check = None
        self.health_status = "unknown"
        self.app = None
        self.runner = None
        self.site = None
        
    async def health_handler(self, request):
        """Endpoint de health check"""
        try:
            # Testa conexão com Runtipi periodicamente (cache de 60s)
            now = datetime.now()
            if (not self.last_health_check or 
                (now - self.last_health_check).seconds > 60):
                
                logger.debug("Executando health check do Runtipi...")
                self.health_status = "healthy" if await asyncio.to_thread(
                    self.api.test_connection
                ) else "unhealthy"
                self.last_health_check = now
                logger.debug(f"Health check resultado: {self.health_status}")
            
            uptime = (now - self.start_time).total_seconds()
            
            status = {
                "status": self.health_status,
                "uptime_seconds": uptime,
                "uptime_human": self._format_uptime(uptime),
                "timestamp": now.isoformat(),
                "service": "telegram-runtipi",
                "last_health_check": self.last_health_check.isoformat() if self.last_health_check else None
            }
            
            status_code = 200 if self.health_status == "healthy" else 503
            return web.json_response(status, status=status_code)
            
        except Exception as e:
            logger.error(f"Health check error: {e}")
            return web.json_response({
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }, status=500)
    
    async def metrics_handler(self, request):
        """Endpoint básico de métricas"""
        uptime = (datetime.now() - self.start_time).total_seconds()
        
        metrics = {
            "uptime_seconds": uptime,
            "uptime_human": self._format_uptime(uptime),
            "last_health_check": self.last_health_check.isoformat() if self.last_health_check else None,
            "runtipi_status": self.health_status,
            "service": "telegram-runtipi",
            "start_time": self.start_time.isoformat()
        }
        
        return web.json_response(metrics)
    
    async def ready_handler(self, request):
        """Endpoint de readiness (sempre retorna 200 se o servidor está rodando)"""
        return web.json_response({
            "status": "ready",
            "timestamp": datetime.now().isoformat()
        })
    
    def _format_uptime(self, seconds: float) -> str:
        """Formata uptime em formato legível"""
        days = int(seconds // 86400)
        hours = int((seconds % 86400) // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        
        if days > 0:
            return f"{days}d {hours}h {minutes}m {secs}s"
        elif hours > 0:
            return f"{hours}h {minutes}m {secs}s"
        elif minutes > 0:
            return f"{minutes}m {secs}s"
        else:
            return f"{secs}s"
    
    async def start_server(self):
        """Inicia o servidor de health check"""
        self.app = web.Application()
        
        # Rotas de health check
        self.app.router.add_get('/health', self.health_handler)
        self.app.router.add_get('/healthz', self.health_handler)  # Alias Kubernetes
        self.app.router.add_get('/metrics', self.metrics_handler)
        self.app.router.add_get('/ready', self.ready_handler)
        self.app.router.add_get('/readiness', self.ready_handler)  # Alias
        
        # Rota raiz simples
        self.app.router.add_get('/', self._root_handler)
        
        self.runner = web.AppRunner(self.app)
        await self.runner.setup()
        
        self.site = web.TCPSite(self.runner, '0.0.0.0', self.port)
        await self.site.start()
        
        logger.info(f"🏥 Health server iniciado na porta {self.port}")
        logger.info(f"   Endpoints disponíveis:")
        logger.info(f"   • http://0.0.0.0:{self.port}/health")
        logger.info(f"   • http://0.0.0.0:{self.port}/metrics")
        logger.info(f"   • http://0.0.0.0:{self.port}/ready")
        
        return self.runner
    
    async def stop_server(self):
        """Para o servidor de health check"""
        if self.runner:
            await self.runner.cleanup()
            logger.info("Health server parado")
    
    async def _root_handler(self, request):
        """Handler para rota raiz"""
        return web.json_response({
            "service": "telegram-runtipi",
            "status": "running",
            "endpoints": {
                "health": "/health",
                "metrics": "/metrics", 
                "ready": "/ready"
            },
            "timestamp": datetime.now().isoformat()
        })