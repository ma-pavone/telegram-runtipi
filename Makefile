.PHONY: help build up down restart logs clean test lint format check-env health

# Variáveis
COMPOSE_FILE = docker-compose.yml
CONTAINER_NAME = runtipi-telegram-runtipi
IMAGE_NAME = runtipi-telegram-runtipi

# Comando padrão
help: ## Mostra esta mensagem de ajuda
	@echo "🤖 Runtipi Telegram Bot - Comandos disponíveis:"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'
	@echo ""
	@echo "Exemplos:"
	@echo "  make build    # Constrói a imagem"
	@echo "  make up       # Inicia o bot"
	@echo "  make logs     # Visualiza logs"
	@echo "  make health   # Verifica saúde do bot"

check-env: ## Verifica se as variáveis de ambiente estão definidas
	@echo "🔍 Verificando variáveis de ambiente..."
	@if [ -z "$$TELEGRAM_TOKEN" ]; then echo "❌ TELEGRAM_TOKEN não definido"; exit 1; fi
	@if [ -z "$$TELEGRAM_CHAT_ID" ]; then echo "❌ TELEGRAM_CHAT_ID não definido"; exit 1; fi
	@if [ -z "$$RUNTIPI_USERNAME" ]; then echo "❌ RUNTIPI_USERNAME não definido"; exit 1; fi
	@if [ -z "$$RUNTIPI_PASSWORD" ]; then echo "❌ RUNTIPI_PASSWORD não definido"; exit 1; fi
	@echo "✅ Variáveis de ambiente OK"

build: ## Constrói a imagem Docker
	@echo "🔨 Construindo imagem Docker..."
	docker-compose build --no-cache

up: check-env ## Inicia o bot em background
	@echo "🚀 Iniciando bot..."
	docker-compose up -d

down: ## Para o bot
	@echo "🛑 Parando bot..."
	docker-compose down

restart: ## Reinicia o bot
	@echo "🔄 Reiniciando bot..."
	docker-compose restart

logs: ## Mostra logs do bot
	@echo "📋 Logs do bot:"
	docker-compose logs -f --tail=100

logs-live: ## Mostra logs em tempo real
	@echo "📋 Logs em tempo real:"
	docker-compose logs -f

status: ## Mostra status do container
	@echo "📊 Status do container:"
	@docker ps -f name=$(CONTAINER_NAME) --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

health: ## Verifica saúde do bot
	@echo "🏥 Verificando saúde do bot..."
	@if docker ps -f name=$(CONTAINER_NAME) --format '{{.Names}}' | grep -q $(CONTAINER_NAME); then \
		echo "✅ Container está rodando"; \
		docker exec $(CONTAINER_NAME) python -c "print('✅ Python OK')" 2>/dev/null || echo "❌ Python com problemas"; \
	else \
		echo "❌ Container não está rodando"; \
	fi

clean: down ## Remove containers, volumes e imagens
	@echo "🧹 Limpando recursos Docker..."
	docker-compose down -v --rmi all --remove-orphans
	docker system prune -f

shell: ## Acessa shell do container
	@echo "🐚 Acessando shell do container..."
	docker exec -it $(CONTAINER_NAME) /bin/bash

test-api: ## Testa conexão com API do Runtipi
	@echo "🧪 Testando conexão com API..."
	docker exec $(CONTAINER_NAME) python -c "from src.runtipi_api import RuntipiAPI; import os; api = RuntipiAPI(os.getenv('RUNTIPI_HOST'), os.getenv('RUNTIPI_USERNAME'), os.getenv('RUNTIPI_PASSWORD')); print('✅ API OK' if api.health_check() else '❌ API com problemas')"

update: ## Atualiza e reconstrói o bot
	@echo "🔄 Atualizando bot..."
	git pull
	$(MAKE) down
	$(MAKE) build
	$(MAKE) up

backup-logs: ## Faz backup dos logs
	@echo "💾 Fazendo backup dos logs..."
	@mkdir -p ./backups
	@docker cp $(CONTAINER_NAME):/app/logs ./backups/logs-$(shell date +%Y%m%d_%H%M%S) 2>/dev/null || echo "ℹ️ Sem logs para backup"

dev: ## Modo desenvolvimento com rebuild automático
	@echo "🔧 Modo desenvolvimento..."
	docker-compose up --build

# Debug e troubleshooting
debug: ## Mostra informações de debug
	@echo "🐛 Informações de debug:"