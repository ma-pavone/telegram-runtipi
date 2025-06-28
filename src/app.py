# src/app.py
import logging
import sys
import os
from pathlib import Path
from config.settings import BotConfig
from bot.core import RuntipiBot

# Configuração de logging melhorada
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.StreamHandler(sys.stdout),
        # Opcional: adicionar FileHandler se necessário
        # logging.FileHandler('/app/logs/bot.log')
    ]
)

# Reduz verbosidade de algumas bibliotecas
logging.getLogger('httpx').setLevel(logging.WARNING)
logging.getLogger('urllib3').setLevel(logging.WARNING)
logging.getLogger('aiohttp').setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

def validate_environment():
    """Valida ambiente antes de iniciar o bot"""
    required_vars = [
        'TELEGRAM_TOKEN',
        'TELEGRAM_CHAT_ID',
        'RUNTIPI_USERNAME',
        'RUNTIPI_PASSWORD'
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        logger.error("❌ Variáveis de ambiente obrigatórias não definidas:")
        for var in missing_vars:
            logger.error(f"   • {var}")
        return False
    
    # Valida diretório de scripts se especificado
    scripts_dir = os.getenv('SCRIPTS_PATH', '/scripts')
    if not os.path.exists(scripts_dir):
        logger.warning(f"⚠️ Diretório de scripts não existe: {scripts_dir}")
        try:
            os.makedirs(scripts_dir, exist_ok=True)
            logger.info(f"✅ Diretório de scripts criado: {scripts_dir}")
        except Exception as e:
            logger.error(f"❌ Erro ao criar diretório de scripts: {e}")
    
    return True

def main():
    """Função principal"""
    logger.info("=" * 50)
    logger.info("🤖 RUNTIPI TELEGRAM BOT")
    logger.info("=" * 50)
    
    # Valida ambiente
    if not validate_environment():
        logger.error("💥 Falha na validação do ambiente")
        sys.exit(1)
    
    try:
        # Carrega configuração
        config = BotConfig.from_env()
        logger.info("✅ Configuração carregada")
        
        # Inicializa e executa o bot
        bot = RuntipiBot(config)
        success = bot.run()
        
        if success:
            logger.info("✅ Bot finalizado com sucesso")
            sys.exit(0)
        else:
            logger.error("❌ Bot finalizado com erro")
            sys.exit(1)
            
    except KeyboardInterrupt:
        logger.info("🛑 Interrompido pelo usuário")
        sys.exit(0)
    except Exception as e:
        logger.error(f"💥 Erro fatal na aplicação: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()