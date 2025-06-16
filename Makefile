.PHONY: help dev-setup up down logs ps test lint migrate migrate-up migrate-down clean

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

dev-setup: ## Setup development environment
	docker-compose up -d postgres redis nats
	sleep 5
	docker-compose up migration

up: ## Start all services
	docker-compose up -d

down: ## Stop all services
	docker-compose down

logs: ## Show logs
	docker-compose logs -f

ps: ## Show running services
	docker-compose ps

test: ## Run tests
	pytest

lint: ## Run linters
	flake8 src tests
	mypy src tests

migrate: ## Create a new migration
	alembic revision --autogenerate -m "$(message)"

migrate-up: ## Apply migrations
	alembic upgrade head

migrate-down: ## Rollback last migration
	alembic downgrade -1

clean: ## Remove all containers and volumes
	docker-compose down -v
	rm -rf __pycache__
	rm -rf .pytest_cache
	rm -rf .mypy_cache