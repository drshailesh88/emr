.PHONY: help install test test-cov test-fast test-slow test-integration lint format type-check security clean run build docs pre-commit-install

# Default target
help:
	@echo "DocAssist EMR - Development Commands"
	@echo "===================================="
	@echo ""
	@echo "Setup:"
	@echo "  make install              Install all dependencies"
	@echo "  make pre-commit-install   Install pre-commit hooks"
	@echo ""
	@echo "Testing:"
	@echo "  make test                 Run all tests"
	@echo "  make test-fast            Run fast tests only"
	@echo "  make test-slow            Run slow/integration tests"
	@echo "  make test-integration     Run integration tests only"
	@echo "  make test-cov             Run tests with coverage report"
	@echo "  make test-watch           Run tests in watch mode"
	@echo ""
	@echo "Code Quality:"
	@echo "  make lint                 Run all linters (flake8, black --check, isort --check)"
	@echo "  make format               Auto-format code (black, isort)"
	@echo "  make type-check           Run mypy type checker"
	@echo "  make security             Run security scans (bandit, safety)"
	@echo "  make check-all            Run all checks (lint, type-check, test, security)"
	@echo ""
	@echo "Running:"
	@echo "  make run                  Run the desktop app"
	@echo "  make run-mobile           Run the mobile app"
	@echo "  make run-cloud-api        Run the cloud API server"
	@echo ""
	@echo "Building:"
	@echo "  make build                Build desktop app for current platform"
	@echo "  make build-windows        Build Windows desktop app"
	@echo "  make build-macos          Build macOS desktop app"
	@echo "  make build-linux          Build Linux desktop app"
	@echo "  make build-android        Build Android APK"
	@echo ""
	@echo "Documentation:"
	@echo "  make docs                 Generate documentation"
	@echo ""
	@echo "Utilities:"
	@echo "  make clean                Clean build artifacts and cache"
	@echo "  make clean-db             Clean test databases"
	@echo "  make reset                Full reset (clean + reinstall)"
	@echo ""

# Setup
install:
	python -m pip install --upgrade pip
	pip install -r requirements.txt
	pip install -r requirements-dev.txt || pip install pytest pytest-cov pytest-xdist pytest-timeout mypy black isort flake8 bandit safety

pre-commit-install:
	pip install pre-commit
	pre-commit install

# Testing
test:
	pytest tests/ -v --tb=short

test-fast:
	pytest tests/ -v -m "not slow and not integration" --tb=short

test-slow:
	pytest tests/ -v -m "slow or integration" --tb=short

test-integration:
	pytest tests/ -v -m "integration" --tb=short

test-cov:
	pytest tests/ -v --cov=src --cov-report=html --cov-report=term-missing --cov-fail-under=70
	@echo "Coverage report generated in htmlcov/index.html"

test-watch:
	pytest-watch tests/ -- -v --tb=short

# Code Quality
lint: lint-flake8 lint-black lint-isort

lint-flake8:
	@echo "Running flake8..."
	flake8 src/ tests/ --count --select=E9,F63,F7,F82 --show-source --statistics
	flake8 src/ tests/ --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics

lint-black:
	@echo "Checking code formatting with black..."
	black --check src/ tests/

lint-isort:
	@echo "Checking import sorting with isort..."
	isort --check-only src/ tests/

format: format-black format-isort

format-black:
	@echo "Formatting code with black..."
	black src/ tests/

format-isort:
	@echo "Sorting imports with isort..."
	isort src/ tests/

type-check:
	@echo "Running mypy type checker..."
	mypy src/ --ignore-missing-imports --no-strict-optional

security: security-bandit security-safety

security-bandit:
	@echo "Running bandit security scan..."
	bandit -r src/ -ll

security-safety:
	@echo "Checking dependencies for vulnerabilities..."
	safety check --json || safety check

check-all: lint type-check test security
	@echo "All checks passed!"

# Running
run:
	flet run main.py

run-mobile:
	@if [ -f "docassist_mobile/main.py" ]; then \
		cd docassist_mobile && flet run main.py; \
	else \
		echo "Mobile app not found. Please create docassist_mobile/ first."; \
	fi

run-cloud-api:
	@if [ -f "cloud-api/main.py" ]; then \
		cd cloud-api && uvicorn main:app --reload; \
	else \
		echo "Cloud API not found. Please create cloud-api/ first."; \
	fi

# Building
build:
	flet build

build-windows:
	flet build windows --product "DocAssist EMR" --org "DocAssist" --company "DocAssist Health Technologies"

build-macos:
	flet build macos --product "DocAssist EMR" --org "DocAssist" --company "DocAssist Health Technologies"

build-linux:
	flet build linux --product "DocAssist EMR" --org "DocAssist" --company "DocAssist Health Technologies"

build-android:
	flet build apk --product "DocAssist EMR Mobile" --org "com.docassist.emr" --company "DocAssist Health Technologies"

build-all: build-windows build-macos build-linux build-android

# Documentation
docs:
	@echo "Generating documentation..."
	@if command -v pdoc3 &> /dev/null; then \
		pdoc3 --html --output-dir docs src/ --force; \
		echo "Documentation generated in docs/"; \
	else \
		echo "Installing pdoc3..."; \
		pip install pdoc3; \
		pdoc3 --html --output-dir docs src/ --force; \
		echo "Documentation generated in docs/"; \
	fi

# Utilities
clean: clean-build clean-pyc clean-test clean-db

clean-build:
	@echo "Cleaning build artifacts..."
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info
	rm -rf .eggs/

clean-pyc:
	@echo "Cleaning Python cache..."
	find . -type f -name '*.pyc' -delete
	find . -type f -name '*.pyo' -delete
	find . -type d -name '__pycache__' -delete
	find . -type d -name '*.egg-info' -exec rm -rf {} + 2>/dev/null || true

clean-test:
	@echo "Cleaning test artifacts..."
	rm -rf .pytest_cache/
	rm -rf .coverage
	rm -rf htmlcov/
	rm -f coverage.xml
	rm -f .coverage.*

clean-db:
	@echo "Cleaning test databases..."
	rm -f data/test.db
	rm -f data/integration.db
	rm -f data/load_test.db
	rm -rf data/chroma_test/

reset: clean
	@echo "Performing full reset..."
	pip uninstall -y -r requirements.txt || true
	make install
	@echo "Reset complete!"

# Database management
db-init:
	python -c "from src.services.database import Database; db = Database('data/clinic.db'); db.init_db(); print('Database initialized')"

db-backup:
	@mkdir -p backups
	@cp data/clinic.db backups/clinic_backup_$$(date +%Y%m%d_%H%M%S).db
	@echo "Database backed up to backups/"

db-restore:
	@if [ -z "$(BACKUP)" ]; then \
		echo "Usage: make db-restore BACKUP=backups/clinic_backup_YYYYMMDD_HHMMSS.db"; \
	else \
		cp $(BACKUP) data/clinic.db; \
		echo "Database restored from $(BACKUP)"; \
	fi

# Development helpers
dev-setup: install pre-commit-install db-init
	@echo "Development environment setup complete!"

shell:
	python -i -c "from src.services.database import Database; from src.services.llm import LLMService; from src.services.rag import RAGService; db = Database('data/clinic.db'); print('Database loaded as: db')"

# Performance profiling
profile:
	python -m cProfile -o profile.stats main.py
	python -c "import pstats; p = pstats.Stats('profile.stats'); p.sort_stats('cumulative'); p.print_stats(20)"

memory-profile:
	python -m memory_profiler main.py

# Dependency management
freeze:
	pip freeze > requirements.txt

outdated:
	pip list --outdated

upgrade-deps:
	pip install --upgrade -r requirements.txt
