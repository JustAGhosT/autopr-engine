# AutoPR Engine - Development Makefile
# =====================================
# Usage: make [target]
# Run 'make help' for available commands

.PHONY: help install install-dev install-full clean clean-all test test-cov test-fast \
        lint lint-fix format check run server worker \
        docker-build docker-up docker-down docker-logs docker-shell docker-restart docker-clean \
        setup-action setup-venv setup-poetry env deps-update docs quickstart

# Default target
.DEFAULT_GOAL := help

# Variables
PYTHON := python3
PIP := pip3
DOCKER_COMPOSE := docker compose

# Colors
BLUE := \033[0;34m
GREEN := \033[0;32m
YELLOW := \033[1;33m
NC := \033[0m

#------------------------------------------------------------------------------
# HELP
#------------------------------------------------------------------------------

help: ## Show this help message
	@echo ""
	@echo "AutoPR Engine - Development Commands"
	@echo "====================================="
	@echo ""
	@echo "$(BLUE)Installation:$(NC)"
	@grep -E '^(install|setup)[a-zA-Z_-]*:.*?## ' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(GREEN)%-20s$(NC) %s\n", $$1, $$2}'
	@echo ""
	@echo "$(BLUE)Development:$(NC)"
	@grep -E '^(test|lint|format|check|run|server|worker)[a-zA-Z_-]*:.*?## ' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(GREEN)%-20s$(NC) %s\n", $$1, $$2}'
	@echo ""
	@echo "$(BLUE)Docker:$(NC)"
	@grep -E '^docker[a-zA-Z_-]*:.*?## ' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(GREEN)%-20s$(NC) %s\n", $$1, $$2}'
	@echo ""
	@echo "$(BLUE)Utilities:$(NC)"
	@grep -E '^(clean|env)[a-zA-Z_-]*:.*?## ' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(GREEN)%-20s$(NC) %s\n", $$1, $$2}'
	@echo ""

#------------------------------------------------------------------------------
# INSTALLATION
#------------------------------------------------------------------------------

install: ## Install AutoPR Engine (standard)
	@echo "$(BLUE)Installing AutoPR Engine...$(NC)"
	$(PIP) install -e .
	@echo "$(GREEN)Installation complete!$(NC)"

install-dev: ## Install with development dependencies
	@echo "$(BLUE)Installing AutoPR Engine (development mode)...$(NC)"
	$(PIP) install -e ".[dev]"
	pre-commit install
	@echo "$(GREEN)Development installation complete!$(NC)"

install-full: ## Install with all features
	@echo "$(BLUE)Installing AutoPR Engine (full)...$(NC)"
	$(PIP) install -e ".[full]"
	@echo "$(GREEN)Full installation complete!$(NC)"

setup-venv: ## Create and activate virtual environment
	@echo "$(BLUE)Creating virtual environment...$(NC)"
	$(PYTHON) -m venv venv
	@echo "$(GREEN)Virtual environment created!$(NC)"
	@echo "$(YELLOW)Activate with: source venv/bin/activate$(NC)"

setup-poetry: ## Install using Poetry
	@echo "$(BLUE)Installing with Poetry...$(NC)"
	poetry install
	@echo "$(GREEN)Poetry installation complete!$(NC)"

setup-action: ## Create GitHub Action workflow in current repo
	@echo "$(BLUE)Setting up GitHub Action...$(NC)"
	@mkdir -p .github/workflows
	@if [ -f templates/quick-start/autopr-workflow.yml ]; then \
		cp templates/quick-start/autopr-workflow.yml .github/workflows/autopr.yml; \
		echo "$(GREEN)Copied from local templates$(NC)"; \
	elif curl -sSL --fail https://raw.githubusercontent.com/JustAGhosT/autopr-engine/main/templates/quick-start/autopr-workflow.yml -o .github/workflows/autopr.yml; then \
		echo "$(GREEN)Downloaded from GitHub$(NC)"; \
	else \
		echo "$(RED)Failed to set up GitHub Action$(NC)"; \
		exit 1; \
	fi
	@echo "$(GREEN)Created .github/workflows/autopr.yml$(NC)"
	@echo "$(YELLOW)Remember to add OPENAI_API_KEY to your repository secrets!$(NC)"

#------------------------------------------------------------------------------
# DEVELOPMENT
#------------------------------------------------------------------------------

test: ## Run tests
	@echo "$(BLUE)Running tests...$(NC)"
	pytest tests/ -v

test-cov: ## Run tests with coverage
	@echo "$(BLUE)Running tests with coverage...$(NC)"
	pytest tests/ --cov=autopr --cov-report=html --cov-report=term

test-fast: ## Run tests (fast mode, stop on first failure)
	@echo "$(BLUE)Running tests (fast mode)...$(NC)"
	pytest tests/ -x -v

lint: ## Run linting checks
	@echo "$(BLUE)Running linters...$(NC)"
	ruff check autopr/
	mypy autopr/ --ignore-missing-imports

lint-fix: ## Fix linting issues automatically
	@echo "$(BLUE)Fixing linting issues...$(NC)"
	ruff check autopr/ --fix
	black autopr/

format: ## Format code with black and isort
	@echo "$(BLUE)Formatting code...$(NC)"
	black autopr/ tests/
	isort autopr/ tests/

check: lint test ## Run all checks (lint + test)

run: ## Run the CLI
	@echo "$(BLUE)Running AutoPR CLI...$(NC)"
	$(PYTHON) -m autopr.cli

server: ## Run the API server
	@echo "$(BLUE)Starting API server...$(NC)"
	$(PYTHON) -m autopr.server --reload

worker: ## Run the background worker
	@echo "$(BLUE)Starting background worker...$(NC)"
	$(PYTHON) -m autopr.worker

#------------------------------------------------------------------------------
# DOCKER
#------------------------------------------------------------------------------

docker-build: ## Build Docker image
	@echo "$(BLUE)Building Docker image...$(NC)"
	docker build -t autopr-engine:latest .

docker-up: ## Start all services with Docker Compose
	@echo "$(BLUE)Starting Docker services...$(NC)"
	$(DOCKER_COMPOSE) up -d

docker-down: ## Stop all Docker services
	@echo "$(BLUE)Stopping Docker services...$(NC)"
	$(DOCKER_COMPOSE) down

docker-logs: ## View Docker logs
	$(DOCKER_COMPOSE) logs -f

docker-shell: ## Open shell in running container
	$(DOCKER_COMPOSE) exec autopr-engine bash

docker-restart: docker-down docker-up ## Restart Docker services

docker-clean: ## Remove Docker containers and volumes
	@echo "$(YELLOW)Removing Docker containers and volumes...$(NC)"
	$(DOCKER_COMPOSE) down -v --remove-orphans

#------------------------------------------------------------------------------
# UTILITIES
#------------------------------------------------------------------------------

env: ## Create .env file from template
	@if [ ! -f .env ]; then \
		cp .env.example .env; \
		echo "$(GREEN)Created .env file$(NC)"; \
		echo "$(YELLOW)Please edit .env with your API keys$(NC)"; \
	else \
		echo "$(YELLOW).env file already exists$(NC)"; \
	fi

clean: ## Clean build artifacts
	@echo "$(BLUE)Cleaning build artifacts...$(NC)"
	rm -rf build/ dist/ *.egg-info/ .pytest_cache/ .mypy_cache/ .ruff_cache/
	rm -rf htmlcov/ .coverage
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@echo "$(GREEN)Clean complete!$(NC)"

clean-all: clean ## Clean everything including venv
	rm -rf venv/
	rm -rf .venv/

deps-update: ## Update dependencies
	@echo "$(BLUE)Updating dependencies...$(NC)"
	poetry update

docs: ## Build documentation
	@echo "$(BLUE)Building documentation...$(NC)"
	cd docs && make html

#------------------------------------------------------------------------------
# QUICK START
#------------------------------------------------------------------------------

quickstart: env install ## Quick start: create env and install
	@echo ""
	@echo "$(GREEN)============================================$(NC)"
	@echo "$(GREEN)AutoPR Engine is ready!$(NC)"
	@echo "$(GREEN)============================================$(NC)"
	@echo ""
	@echo "Next steps:"
	@echo "  1. Edit .env with your API keys"
	@echo "  2. Run: make server"
	@echo "  3. Or add to your repo: make setup-action"
	@echo ""
