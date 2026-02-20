.PHONY: help up down build logs migrate test lint format clean dev-backend dev-frontend

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# ── Docker ────────────────────────────────────────────────────────────────────
up: ## Start all services
	docker-compose up -d

down: ## Stop all services
	docker-compose down

build: ## Build all Docker images
	docker-compose build

logs: ## Tail logs
	docker-compose logs -f

restart: ## Restart all services
	docker-compose restart

# ── Database ──────────────────────────────────────────────────────────────────
migrate: ## Run Alembic migrations
	docker-compose exec api alembic upgrade head

migrate-create: ## Create a new migration (usage: make migrate-create MSG="your message")
	docker-compose exec api alembic revision --autogenerate -m "$(MSG)"

migrate-down: ## Rollback last migration
	docker-compose exec api alembic downgrade -1

# ── Development ───────────────────────────────────────────────────────────────
dev-backend: ## Run backend locally (requires local venv)
	cd backend && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

dev-frontend: ## Run frontend dev server
	cd frontend && npm run dev

install-backend: ## Install backend dependencies
	cd backend && pip install -r requirements.txt

install-frontend: ## Install frontend dependencies
	cd frontend && npm install

# ── Quality ───────────────────────────────────────────────────────────────────
test: ## Run backend tests
	cd backend && pytest tests/ -v --tb=short

test-cov: ## Run tests with coverage
	cd backend && pytest tests/ -v --cov=app --cov-report=term-missing

lint: ## Run linters
	cd backend && ruff check app/ tests/
	cd backend && mypy app/ --ignore-missing-imports

format: ## Format code
	cd backend && black app/ tests/
	cd backend && ruff check --fix app/ tests/

# ── Cleanup ───────────────────────────────────────────────────────────────────
clean: ## Remove containers, volumes, and build artifacts
	docker-compose down -v
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -delete 2>/dev/null || true

# ── Model Download ────────────────────────────────────────────────────────────
download-models: ## Pre-download ML models inside the api container
	docker-compose exec api python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')"
	docker-compose exec api python -m spacy download en_core_web_sm
