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
	uv sync -g dev

format: ## Run formatters (isort, black) in-place
	isort .
	black .

lint: ## Lint (ruff) + check formatting (isort --check, black --check)
	ruff check .
	isort --check-only .
	black --check .

type: ## Static type checking
	mypy src

test: ## Run unit tests (quiet)
	pytest -q

test-verbose: ## Run tests verbosely
	pytest -vv

coverage: ## Test coverage report
	pytest --cov=$(PKG) --cov-report=term-missing

bench: ## Quick property/benchmark tests (if present)
	pytest -q --benchmark-only

check: lint type test ## Run all quality gates: lint, type, tests (CI-like)

build: ## Build sdist and wheel (dist/)
	$(PY) -m build

build-check: build ## Validate built artifacts with twine
	twine check dist/*

precommit-install: ## Set up pre-commit hooks locally
	pre-commit install

precommit-run: ## Run all pre-commit hooks on the repo
	pre-commit run --all-files

clean: ## Clean caches and build artifacts
	rm -rf build/ dist/ .pytest_cache/ .mypy_cache/ .ruff_cache/ *.egg-info
	find . -name "__pycache__" -type d -exec rm -rf {} +

.PHONY: help install-dev format lint type test test-verbose coverage bench check build build-check precommit-install precommit-run clean
