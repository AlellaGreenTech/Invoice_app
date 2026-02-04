.PHONY: help build up down restart logs shell test clean migrate seed

help:
	@echo "Invoice Processor - Makefile Commands"
	@echo "======================================"
	@echo ""
	@echo "Setup & Start:"
	@echo "  make build      - Build Docker containers"
	@echo "  make up         - Start all services"
	@echo "  make down       - Stop all services"
	@echo "  make restart    - Restart all services"
	@echo ""
	@echo "Development:"
	@echo "  make logs       - View logs (all services)"
	@echo "  make shell      - Access Flask shell"
	@echo "  make bash       - Access container bash"
	@echo "  make test       - Run tests"
	@echo "  make test-cov   - Run tests with coverage"
	@echo ""
	@echo "Database:"
	@echo "  make migrate    - Run database migrations"
	@echo "  make seed       - Seed default categories"
	@echo "  make db-shell   - Access PostgreSQL shell"
	@echo "  make db-reset   - Reset database (WARNING: deletes data)"
	@echo ""
	@echo "Maintenance:"
	@echo "  make clean      - Remove containers and volumes"
	@echo "  make ps         - Show running services"
	@echo "  make stats      - Show container stats"
	@echo ""

build:
	docker-compose build

up:
	docker-compose up -d
	@echo "Services started. Access at http://localhost:5000"

down:
	docker-compose down

restart:
	docker-compose restart

logs:
	docker-compose logs -f

logs-web:
	docker-compose logs -f web

logs-celery:
	docker-compose logs -f celery

shell:
	docker-compose exec web flask shell

bash:
	docker-compose exec web bash

test:
	docker-compose exec web pytest

test-cov:
	docker-compose exec web pytest --cov=app tests/

test-verbose:
	docker-compose exec web pytest -v

migrate:
	docker-compose exec web flask db upgrade

migrate-create:
	@read -p "Enter migration message: " msg; \
	docker-compose exec web flask db migrate -m "$$msg"

seed:
	docker-compose exec web flask seed-categories

db-shell:
	docker-compose exec db psql -U invoice_user -d invoice_app

db-reset:
	@echo "WARNING: This will delete all data!"
	@read -p "Are you sure? (yes/no): " confirm; \
	if [ "$$confirm" = "yes" ]; then \
		docker-compose exec web flask reset-db; \
	fi

clean:
	docker-compose down -v
	@echo "Containers and volumes removed"

ps:
	docker-compose ps

stats:
	docker stats

setup: build up migrate seed
	@echo "Setup complete! Access at http://localhost:5000"

install:
	pip install -r requirements.txt

lint:
	docker-compose exec web flake8 app/

format:
	docker-compose exec web black app/

check:
	@echo "Running checks..."
	@docker-compose exec web pytest --tb=short
	@echo "All checks passed!"
