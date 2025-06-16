.PHONY: build run list start stop toggle

build:
	docker-compose build

# Comandos rápidos
list:
	docker-compose run --rm runtipi-manager

start:
	docker-compose run --rm runtipi-manager start $(APP)

stop:
	docker-compose run --rm runtipi-manager stop $(APP)

toggle:
	docker-compose run --rm runtipi-manager toggle $(APP)

# Exemplos:
# make list
# make start APP=bazarr
# make toggle APP=gotify