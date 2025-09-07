# Makefile for fptk
# Usage: make <target>

PY ?= python3
PKG := fptk
SRC := src/$(PKG) tests

.DEFAULT_GOAL := help

## Show available targets
help:
	@echo "Available targets:" && \
	awk 'BEGIN {FS=":.*##"} /^[a-zA-Z0-9_.-]+:.*##/ { printf "  [36m%-22s[0m %s\n", $$1, $$2 }' $(MAKEFILE_LIST)

install-dev: ## Create/refresh dev env via uv (uses dependency-groups)
	@command -v uv >/dev/null 2>&1 || { \
	  echo "uv is required. Install from https://docs.astral.sh/uv/install/"; \
	  exit 1; \
	}
	uv sync --group dev

format: ## Run formatters (isort, black) in-place
	uv run isort .
	uv run black .

lint: ## Lint (ruff) + check formatting (isort --check, black --check)
	uv run ruff check .
	uv run isort --check-only .
	uv run black --check .

type: ## Static type checking
	uv run mypy src

test: ## Run unit tests (quiet)
	uv run pytest -q

test-verbose: ## Run tests verbosely
	uv run pytest -vv

coverage: ## Test coverage report
	uv run pytest --cov=$(PKG) --cov-report=term-missing

bench: ## Quick property/benchmark tests (if present)
	uv run pytest -q --benchmark-only

check: lint type test ## Run all quality gates: lint, type, tests (CI-like)

build: ## Build sdist and wheel (dist/)
	uv run -m build

build-check: build ## Validate built artifacts with twine
	uv run twine check dist/*

precommit-install: ## Set up pre-commit hooks locally
	uv run pre-commit install

precommit-run: ## Run all pre-commit hooks on the repo
	uv run pre-commit run --all-files

clean: ## Clean caches and build artifacts
	rm -rf build/ dist/ .pytest_cache/ .mypy_cache/ .ruff_cache/ *.egg-info
	find . -name "__pycache__" -type d -exec rm -rf {} +

.PHONY: help install-dev format lint type test test-verbose coverage bench check build build-check precommit-install precommit-run clean
