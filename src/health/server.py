# src/health/server.py
import asyncio
import logging
from aiohttp import web
from datetime import datetime
from api.runtipi import RuntipiAPI

logger = logging.getLogger(__name__)

class HealthServer:
    def __init__(self, api: RuntipiAPI, port: int = 7777):
        self.api = api
        self.port = port
        self.start_time = datetime.now()
        self.last_health_check = None
        self.health_status = "unknown"
        
    async def health_handler(self, request):
        """Endpoint de health check"""
        try:
            # Testa conexão com Runtipi periodicamente (cache de 60s)
            now = datetime.now()
            if (not self.last_health_check or 
                (now - self.last_health_check).seconds > 60):
                
                self.health_status = "healthy" if await asyncio.to_thread(
                    self.api.test_connection
                ) else "unhealthy"
                self.last_health_check = now
            
            uptime = (now - self.start_time).total_seconds()
            
            status = {
                "status": self.health_status,
                "uptime_seconds": uptime,
                "timestamp": now.isoformat(),
                "service": "runtipi-telegram-bot"
            }
            
            status_code = 200 if self.health_status == "healthy" else 503
            return web.json_response(status, status=status_code)
            
        except Exception as e:
            logger.error(f"Health check error: {e}")
            return web.json_response({
                "status": "error",
                "error": str(e)
            }, status=500)
    
    async def metrics_handler(self, request):
        """Endpoint básico de métricas"""
        uptime = (datetime.now() - self.start_time).total_seconds()
        
        metrics = {
            "uptime_seconds": uptime,
            "last_health_check": self.last_health_check.isoformat() if self.last_health_check else None,
            "runtipi_status": self.health_status
        }
        
        return web.json_response(metrics)
    
    async def start_server(self):
        """Inicia o servidor de health check"""
        app = web.Application()
        app.router.add_get('/health', self.health_handler)
        app.router.add_get('/metrics', self.metrics_handler)
        
        runner = web.AppRunner(app)
        await runner.setup()
        
        site = web.TCPSite(runner, '0.0.0.0', self.port)
        await site.start()
        
        logger.info(f"Health server started on port {self.port}")
        return runner