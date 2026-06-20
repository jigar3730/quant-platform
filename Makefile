.PHONY: help build up down run-scan run-lynch run-swing view test test-int logs

help:
	@echo "Available automation tasks:"
	@echo "  make build       - Build local Docker containers"
	@echo "  make up          - Start background containers (scheduler/cron/dashboard)"
	@echo "  make down        - Stop all containers"
	@echo "  make run-scan    - Execute a breakout scan immediately inside Docker"
	@echo "  make run-swing   - Execute a swing pullback scan immediately inside Docker"
	@echo "  make logs        - Tail the docker scanner logs"

build:
	docker compose build

up:
	docker compose up -d

down:
	docker compose down

run-scan:
	docker compose run --rm scanner scan

run-lynch:
	docker compose run --rm scanner python -m quant_platform.lynch --report both --archive

run-swing:
	docker compose run --rm scanner python -m quant_platform.swing --dry-run --tickers AAPL,MSFT,NVDA

logs:
	docker compose logs -f scanner