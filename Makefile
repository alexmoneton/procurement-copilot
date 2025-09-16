# Procurement Copilot Makefile
# Provides common development commands

.PHONY: help install dev-install up down logs migrate seed ingest test lint format clean

# Default target
help: ## Show this help message
	@echo "Procurement Copilot - Available Commands:"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# Installation
install: ## Install production dependencies
	pip install -e .

dev-install: ## Install development dependencies
	pip install -e ".[dev]"
	pre-commit install

# Docker commands
up: ## Start all services with docker-compose
	cd infra && docker-compose up -d

down: ## Stop all services
	cd infra && docker-compose down

logs: ## Show logs from all services
	cd infra && docker-compose logs -f

logs-api: ## Show API logs
	cd infra && docker-compose logs -f api

logs-scheduler: ## Show scheduler logs
	cd infra && docker-compose logs -f scheduler

logs-db: ## Show database logs
	cd infra && docker-compose logs -f postgres

# Database commands
migrate: ## Run database migrations
	cd backend/app && alembic upgrade head

migrate-create: ## Create a new migration (usage: make migrate-create MESSAGE="description")
	cd backend/app && alembic revision --autogenerate -m "$(MESSAGE)"

migrate-downgrade: ## Downgrade database by one migration
	cd backend/app && alembic downgrade -1

migrate-history: ## Show migration history
	cd backend/app && alembic history

# Data commands
seed: ## Seed database with sample data
	python -c "import asyncio; from backend.app.db.session import init_db; asyncio.run(init_db())"

ingest: ## Run tender ingestion manually
	python -m backend.app.tasks.jobs run_ingest

ingest-ted: ## Run TED ingestion only
	python -m backend.app.tasks.jobs run_ted_ingest

ingest-boamp: ## Run BOAMP ingestion only
	python -m backend.app.tasks.jobs run_boamp_ingest

alerts: ## Send alerts for all daily filters
	python -m backend.app.tasks.jobs send_alerts

alerts-filter: ## Send alerts for a specific filter (usage: make alerts-filter FILTER_ID=uuid)
	python -m backend.app.tasks.jobs send_alerts_filter $(FILTER_ID)

# Outreach commands
leads-build: ## Build lead list (usage: make leads-build STRATEGY=lost_bidders CPV=72000000 COUNTRY=FR LIMIT=200)
	python -m backend.app.cli leads build --strategy $(STRATEGY) --cpv $(CPV) --country $(COUNTRY) --limit $(LIMIT)

leads-send: ## Send outreach campaign (usage: make leads-send CAMPAIGN=missed_opportunities STRATEGY=lost_bidders LIMIT=50)
	python -m backend.app.cli leads send --campaign $(CAMPAIGN) --strategy $(STRATEGY) --limit $(LIMIT)

companies-import: ## Import companies from CSV (usage: make companies-import FILE=companies.csv)
	python -m backend.app.cli companies import --file $(FILE)

companies-list: ## List companies in database (usage: make companies-list COUNTRY=FR LIMIT=50)
	python -m backend.app.cli companies list --country $(COUNTRY) --limit $(LIMIT)

# Docker commands
up: ## Start all services with docker-compose
	docker-compose up -d

down: ## Stop all services
	docker-compose down

logs: ## View logs from all services
	docker-compose logs -f

logs-api: ## View API logs
	docker-compose logs -f api

logs-scheduler: ## View scheduler logs
	docker-compose logs -f scheduler

logs-frontend: ## View frontend logs
	docker-compose logs -f frontend

# Database commands
db-migrate: ## Run database migrations
	docker-compose exec api python -m alembic upgrade head

db-seed: ## Seed database with demo data
	docker-compose exec api python scripts/seed.py

db-backup: ## Create database backup
	docker-compose exec postgres ./scripts/backup.sh

# Monitoring commands
monitoring-up: ## Start monitoring stack (Grafana + Loki)
	docker-compose -f docker-compose.yml -f docker-compose.monitoring.yml up -d

monitoring-down: ## Stop monitoring stack
	docker-compose -f docker-compose.yml -f docker-compose.monitoring.yml down

# Demo commands
demo-data: ## Generate demo data for marketing
	./scripts/demo_screenshots.sh

# Production commands
build: ## Build Docker images
	docker-compose build

deploy: ## Deploy to production (requires production config)
	docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# Development commands
dev: ## Start development server
	uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000

dev-frontend: ## Start frontend development server
	cd frontend && npm run dev

dev-full: ## Start both backend and frontend in development mode
	@echo "Starting full development environment..."
	@echo "Backend: http://localhost:8000"
	@echo "Frontend: http://localhost:3000"
	@echo "API Docs: http://localhost:8000/api/v1/docs"
	@echo ""
	@echo "Press Ctrl+C to stop both servers"
	@trap 'kill %1; kill %2' INT; \
	cd frontend && npm run dev & \
	uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000 & \
	wait

scheduler: ## Start scheduler in standalone mode
	python -m backend.app.tasks.scheduler

# Testing
test: ## Run all tests
	pytest backend/app/tests/ -v

test-cov: ## Run tests with coverage
	pytest backend/app/tests/ --cov=backend/app --cov-report=html --cov-report=term

test-watch: ## Run tests in watch mode
	pytest backend/app/tests/ -v --looponfail

# Code quality
lint: ## Run linting
	ruff check backend/app/
	mypy backend/app/
	cd frontend && npm run lint

format: ## Format code
	ruff format backend/app/
	isort backend/app/
	cd frontend && npm run format

# Frontend commands
frontend-install: ## Install frontend dependencies
	cd frontend && npm install

frontend-build: ## Build frontend for production
	cd frontend && npm run build

frontend-start: ## Start frontend production server
	cd frontend && npm start

frontend-type-check: ## Run TypeScript type checking
	cd frontend && npm run type-check

format-check: ## Check code formatting
	ruff format --check backend/app/
	isort --check-only backend/app/

# Cleanup
clean: ## Clean up temporary files
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf .pytest_cache/
	rm -rf .coverage
	rm -rf htmlcov/
	rm -rf dist/
	rm -rf build/

clean-docker: ## Clean up Docker resources
	cd infra && docker-compose down -v
	docker system prune -f

# Database management
db-shell: ## Connect to database shell
	cd infra && docker-compose exec postgres psql -U postgres -d procurement_copilot

db-reset: ## Reset database (WARNING: destroys all data)
	cd infra && docker-compose down -v
	cd infra && docker-compose up -d postgres
	sleep 10
	make migrate

# Monitoring
status: ## Show service status
	cd infra && docker-compose ps

health: ## Check API health
	curl -f http://localhost:8000/api/v1/health || echo "API not responding"

# Production commands
build: ## Build Docker images
	cd infra && docker-compose build

deploy: ## Deploy to production (placeholder)
	@echo "Production deployment not implemented yet"

# Documentation
docs: ## Generate API documentation
	@echo "API documentation available at: http://localhost:8000/api/v1/docs"

# Environment setup
env-setup: ## Copy environment file
	cp infra/env.example .env
	@echo "Environment file created. Please edit .env with your settings."

# Quick start
quick-start: env-setup up migrate ingest ## Quick start: setup environment, start services, migrate DB, and run initial ingest
	@echo "Quick start completed!"
	@echo "API available at: http://localhost:8000"
	@echo "API docs at: http://localhost:8000/api/v1/docs"
