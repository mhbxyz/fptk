.DEFAULT_GOAL := help
.PHONY: help dev install format lint type test cov bench check ci build clean

PKG := fptk

help: ## Show this help
	@awk 'BEGIN {FS=":.*##"} /^[a-zA-Z_-]+:.*##/ {printf "  \033[36m%-12s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

dev: ## First-time setup (install deps + pre-commit hooks)
	@command -v uv >/dev/null || { echo "uv required: https://docs.astral.sh/uv"; exit 1; }
	uv sync --group dev
	uv run pre-commit install

install: ## Install/sync dev dependencies
	uv sync --group dev

format: ## Auto-format code (ruff + black)
	uv run ruff check --fix .
	uv run black .

lint: ## Check code style
	uv run ruff check .
	uv run black --check .

type: ## Type check
	uv run mypy src

test: ## Run tests
	uv run pytest

cov: ## Run tests with coverage
	uv run pytest --cov=$(PKG) --cov-report=term-missing --cov-fail-under=90

bench: ## Run benchmarks
	uv run pytest --benchmark-only

check: lint type test ## Quick quality check (lint + type + test)

ci: check cov bench ## Full CI pipeline (check + coverage + bench)
	uv run python -m build
	uv run twine check dist/*

build: ## Build package
	uv run python -m build

clean: ## Remove build artifacts and caches
	rm -rf build/ dist/ .pytest_cache/ .mypy_cache/ .ruff_cache/ .coverage *.egg-info
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
