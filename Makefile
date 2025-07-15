.PHONY: help build up down restart logs clean test check-env

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

clean: down ## Remove containers, volumes e imagens
	@echo "🧹 Limpando recursos Docker..."
	docker-compose down -v --rmi all --remove-orphans
	docker system prune -f

shell: ## Acessa shell do container
	@echo "🐚 Acessando shell do container..."
	docker exec -it $(CONTAINER_NAME) /bin/bash

test-api: ## Testa conexão com API do Runtipi
	@echo "🧪 Testando conexão com API..."
	docker exec $(CONTAINER_NAME) python src/test_runtipi.py

update: ## Atualiza e reconstrói o bot
	@echo "🔄 Atualizando bot..."
	git pull
	$(MAKE) down
	$(MAKE) build
	$(MAKE) up

dev: ## Modo desenvolvimento com rebuild automático
	@echo "🔧 Modo desenvolvimento..."
	docker-compose up --build

# Debug e troubleshooting
debug: ## Mostra informações de debug
	@echo "🐛 Informações de debug:"
	@docker ps -f name=$(CONTAINER_NAME)
	@echo ""
	@echo "Logs recentes:"
	@docker logs --tail=20 $(CONTAINER_NAME) 2>/dev/null || echo "Container não encontrado"