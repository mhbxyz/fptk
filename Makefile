# Makefile for funktools
# Usage: make <target>

PY ?= python3
PKG := funktools
SRC := src/$(PKG) tests

.DEFAULT_GOAL := help

## Show available targets
help:
	@echo "Available targets:" && \
	awk 'BEGIN {FS=":.*##"} /^[a-zA-Z0-9_.-]+:.*##/ { printf "  [36m%-22s[0m %s", $$1, $$2 }' $(MAKEFILE_LIST)

## Create/refresh dev environment and tools
install-dev:
	$(PY) -m pip install --upgrade pip
	pip install -e .
	pip install ruff black mypy pytest hypothesis pytest-benchmark pre-commit build twine pytest-cov

## Run formatters (black) in-place
format:
	black .

## Lint (ruff) + check formatting (black --check)
lint:
	ruff check .
	black --check .

## Static type checking
Type:
	mypy src

## Run unit tests (quiet)
test:
	pytest -q

## Run tests verbosely
Test-verbose:
	pytest -vv

## Test coverage report
coverage:
	pytest --cov=$(PKG) --cov-report=term-missing

## Quick property/benchmark tests (if present)
bench:
	pytest -q --benchmark-only

## Run all quality gates: lint, type, tests (CI-like)
check: lint Type test

## Build sdist and wheel (dist/)
build:
	$(PY) -m build

## Validate built artifacts with twine
build-check: build
	twine check dist/*

## Set up pre-commit hooks locally
precommit-install:
	pre-commit install

## Run all pre-commit hooks on the repo
precommit-run:
	pre-commit run --all-files

## Clean caches and build artifacts
clean:
	rm -rf build/ dist/ .pytest_cache/ .mypy_cache/ .ruff_cache/ *.egg-info
	find . -name "__pycache__" -type d -exec rm -rf {} +

.PHONY: help install-dev format lint Type test Test-verbose coverage bench check build build-check precommit-install precommit-run clean