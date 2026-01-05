# DocAssist EMR - Command Reference Card

Quick reference for all CI/CD and development commands.

---

## Setup Commands

```bash
make install              # Install all dependencies
make pre-commit-install   # Install pre-commit hooks
make dev-setup           # Complete dev environment setup
python verify_cicd_setup.py  # Verify CI/CD setup
```

---

## Testing Commands

```bash
# Quick testing (during development)
make test-fast           # Run fast tests only (no integration/slow)
pytest tests/test_file.py -v  # Run specific test file

# Comprehensive testing
make test                # Run all tests
make test-cov            # Run tests with HTML coverage report
make test-integration    # Run integration tests only
make test-slow           # Run slow tests only

# Advanced testing
make test-watch          # Run tests in watch mode
pytest -k "test_name"    # Run tests matching pattern
pytest --lf              # Run last failed tests
pytest -x                # Stop on first failure
pytest -v -s             # Verbose with print statements
```

---

## Code Quality Commands

```bash
# Linting (check only)
make lint                # Run all linters
make lint-flake8         # Run flake8 only
make lint-black          # Check black formatting only
make lint-isort          # Check import sorting only

# Formatting (auto-fix)
make format              # Format all code
make format-black        # Format with black only
make format-isort        # Sort imports only

# Type checking
make type-check          # Run mypy type checker
mypy src/file.py         # Check specific file

# Security
make security            # Run all security scans
make security-bandit     # Run bandit only
make security-safety     # Check dependency vulnerabilities only

# All checks
make check-all           # Run everything (lint, type, test, security)
```

---

## Running Applications

```bash
make run                 # Run desktop app
make run-mobile          # Run mobile app
make run-cloud-api       # Run cloud API server

# Direct execution
flet run main.py         # Run desktop with Flet
python main.py           # Run desktop directly
```

---

## Building Applications

```bash
# Platform-specific builds
make build               # Build for current platform
make build-windows       # Build Windows desktop app
make build-macos         # Build macOS desktop app
make build-linux         # Build Linux desktop app
make build-android       # Build Android APK

# All platforms
make build-all           # Build for all platforms
```

---

## Database Commands

```bash
make db-init             # Initialize database
make db-backup           # Backup database to backups/
make db-restore BACKUP=backups/file.db  # Restore from backup

# Direct database operations
python -c "from src.services.database import Database; db = Database('data/clinic.db')"
```

---

## Cleanup Commands

```bash
make clean               # Clean all artifacts
make clean-build         # Clean build artifacts only
make clean-pyc           # Clean Python cache only
make clean-test          # Clean test artifacts only
make clean-db            # Clean test databases only
make reset               # Full reset (clean + reinstall)
```

---

## Pre-commit Commands

```bash
# Setup
pre-commit install       # Install hooks
pre-commit uninstall     # Remove hooks

# Running
pre-commit run           # Run on staged files
pre-commit run --all-files  # Run on all files
pre-commit run black --all-files  # Run specific hook

# Management
pre-commit autoupdate    # Update hook versions
pre-commit clean         # Clear cache

# Skip hooks (use sparingly)
git commit --no-verify   # Skip all hooks
SKIP=black git commit    # Skip specific hook
```

---

## Git Workflow Commands

```bash
# Feature development
git checkout -b feature/name  # Create feature branch
# ... make changes ...
make test-fast           # Quick test
make format              # Format code
git add .                # Stage changes
git commit -m "feat: ..."  # Commit (hooks run)
git push origin feature/name  # Push to remote

# Before pushing
make check-all           # Run all checks locally

# Creating releases
git tag -a v1.0.0 -m "Release 1.0.0"  # Create tag
git push origin v1.0.0   # Push tag (triggers release)
```

---

## Documentation Commands

```bash
make docs                # Generate documentation
open docs/index.html     # View documentation (macOS)
xdg-open docs/index.html # View documentation (Linux)
```

---

## Debugging Commands

```bash
# Interactive shell
make shell               # Python shell with imports

# Profiling
make profile             # CPU profiling
make memory-profile      # Memory profiling

# Debug tests
pytest tests/test_file.py --pdb  # Drop into debugger on failure
pytest tests/test_file.py -v --tb=long  # Verbose traceback
```

---

## Dependency Management

```bash
make freeze              # Update requirements.txt
make outdated            # Show outdated packages
make upgrade-deps        # Upgrade all dependencies
pip list --outdated      # List outdated packages
```

---

## Coverage Commands

```bash
# Generate coverage
make test-cov            # HTML + terminal report

# View coverage
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
start htmlcov/index.html # Windows

# Coverage options
pytest --cov=src --cov-report=term  # Terminal only
pytest --cov=src --cov-report=xml   # XML for CI
pytest --cov=src --cov-branch       # Include branch coverage
```

---

## Pytest Markers

```bash
# Run tests by marker
pytest -m "not slow"     # Skip slow tests
pytest -m "integration"  # Integration tests only
pytest -m "unit"         # Unit tests only
pytest -m "benchmark"    # Benchmark tests only
pytest -m "memory"       # Memory tests only

# Combine markers
pytest -m "not slow and not integration"  # Fast unit tests
```

---

## GitHub Actions Commands

```bash
# Trigger workflows manually
gh workflow run ci.yml
gh workflow run security.yml
gh workflow run release.yml --field version=v1.0.0
gh workflow run nightly.yml

# View workflow runs
gh run list
gh run view <run-id>
gh run watch <run-id>

# Download artifacts
gh run download <run-id>
```

---

## Semantic Commit Prefixes

```bash
feat: Add new feature
fix: Fix a bug
docs: Update documentation
style: Format code (no logic change)
refactor: Refactor code (no logic change)
test: Add or update tests
chore: Update dependencies, configs
perf: Performance improvement
ci: CI/CD changes
build: Build system changes
revert: Revert previous commit
```

---

## Environment Variables

```bash
# Testing
PYTEST_CURRENT_TEST      # Current test name (set by pytest)

# Skip slow hooks
SKIP=pip-audit,python-safety-dependencies-check git commit

# Python
PYTHONPATH=.             # Add current dir to path
PYTHONDONTWRITEBYTECODE=1  # Don't create .pyc files
```

---

## Useful One-Liners

```bash
# Find all TODOs
grep -r "TODO" src/

# Count lines of code
find src/ -name "*.py" | xargs wc -l

# Find large files
find . -type f -size +1M

# List all test files
find tests/ -name "test_*.py"

# Find files modified today
find . -type f -mtime 0

# Check for print statements (should use logging)
grep -r "print(" src/

# Find files without tests
comm -23 <(find src/ -name "*.py" | sort) <(find tests/ -name "test_*.py" | sed 's|tests/||' | sed 's|test_||' | sort)
```

---

## Help Commands

```bash
make help                # Show all Makefile targets
pytest --help            # Pytest help
black --help             # Black help
flake8 --help            # Flake8 help
mypy --help              # Mypy help
pre-commit --help        # Pre-commit help
```

---

## Quick Aliases (Add to ~/.bashrc or ~/.zshrc)

```bash
# DocAssist shortcuts
alias dt='make test-fast'
alias dtc='make test-cov'
alias dl='make lint'
alias df='make format'
alias dca='make check-all'
alias dr='make run'
alias dci='make install'

# Git shortcuts
alias gs='git status'
alias gp='git push'
alias gpl='git pull'
alias gc='git commit'
alias gco='git checkout'
alias gb='git branch'
```

---

## Troubleshooting

```bash
# Pre-commit too slow?
SKIP=pip-audit git commit -m "message"

# Tests failing?
pytest tests/test_file.py::test_name -v --tb=long

# Coverage too low?
make test-cov && open htmlcov/index.html

# Type errors?
mypy src/file.py --show-error-codes

# Import errors?
python -c "import src.module"

# Clear all caches
make clean && find . -type d -name "__pycache__" -exec rm -rf {} +
```

---

**Last Updated:** 2026-01-05
**For Full Documentation:** See `.github/README.md` or `.github/CICD_QUICKSTART.md`
