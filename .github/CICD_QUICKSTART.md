# CI/CD Quick Start Guide

This guide helps you get started with the DocAssist EMR CI/CD pipeline in 5 minutes.

## Prerequisites

- Python 3.11 or higher
- Git installed
- GitHub account with repository access

## 1. Initial Setup (First Time Only)

```bash
# Clone the repository
git clone https://github.com/your-org/docassist-emr.git
cd docassist-emr

# Install dependencies
make install

# Install pre-commit hooks
make pre-commit-install

# Verify setup
make check-all
```

## 2. Development Workflow

### Before You Start Coding

```bash
# Create a new branch
git checkout -b feature/your-feature-name

# Make sure you're up to date
git pull origin main
```

### While Coding

```bash
# Run tests frequently
make test-fast

# Check code quality
make lint

# Format code automatically
make format
```

### Before Committing

```bash
# Run all checks locally
make check-all

# This runs:
# - Linting (flake8, black, isort)
# - Type checking (mypy)
# - Tests with coverage
# - Security scans (bandit, safety)
```

### Committing Changes

```bash
# Stage your changes
git add .

# Commit (pre-commit hooks run automatically)
git commit -m "feat: Add your feature description"

# If pre-commit hooks fail, fix issues and commit again
```

### Pushing Changes

```bash
# Push to your branch
git push origin feature/your-feature-name

# Create pull request on GitHub
# CI pipeline runs automatically on PR
```

## 3. Common Commands

### Testing

```bash
make test           # Run all tests
make test-fast      # Run only fast tests (recommended during development)
make test-cov       # Run tests with coverage report
```

### Code Quality

```bash
make lint           # Check code quality
make format         # Auto-format code
make type-check     # Run type checker
make security       # Run security scans
```

### Running the App

```bash
make run            # Run desktop app
make run-mobile     # Run mobile app
make run-cloud-api  # Run cloud API server
```

### Cleaning Up

```bash
make clean          # Clean build artifacts
make clean-db       # Clean test databases
make reset          # Full reset (clean + reinstall)
```

## 4. Understanding CI Checks

When you create a PR, the following checks run automatically:

### ✓ Lint
- Checks code formatting with black
- Checks import sorting with isort
- Runs flake8 linter

**Fix locally:**
```bash
make format  # Auto-fix most issues
make lint    # Check if issues are resolved
```

### ✓ Type Check
- Runs mypy type checker

**Fix locally:**
```bash
make type-check
```

### ✓ Test Unit
- Runs pytest with coverage
- Requires minimum 70% coverage

**Fix locally:**
```bash
make test-cov
```

### ✓ Test Integration
- Runs integration tests with real database

**Fix locally:**
```bash
make test-integration
```

### ✓ Security Scan
- Runs bandit for security issues
- Runs safety for dependency vulnerabilities

**Fix locally:**
```bash
make security
```

### ✓ Build
- Verifies app builds on all platforms

**Fix locally:**
```bash
make build
```

## 5. Fixing Common Issues

### Pre-commit Hook Failures

**Black formatting:**
```bash
make format-black
git add .
git commit -m "your message"
```

**Import sorting:**
```bash
make format-isort
git add .
git commit -m "your message"
```

**Linting errors:**
```bash
# Fix automatically where possible
make format

# Check remaining issues
make lint

# Fix manually, then commit
```

### Test Failures

**Run specific test:**
```bash
pytest tests/test_specific.py::test_function_name -v
```

**Debug test:**
```bash
pytest tests/test_specific.py -v --tb=long
```

**Run with prints:**
```bash
pytest tests/test_specific.py -v -s
```

### Coverage Too Low

**Find uncovered lines:**
```bash
make test-cov
open htmlcov/index.html  # View coverage report
```

**Add tests:**
- Write tests for uncovered code
- Run `make test-cov` again
- Coverage should increase

### Type Check Errors

**Common fixes:**
```python
# Add type hints
def my_function(param: str) -> int:
    return len(param)

# Use Optional for nullable values
from typing import Optional
def my_function(param: Optional[str] = None) -> int:
    return len(param) if param else 0
```

## 6. Creating a Release

```bash
# 1. Update version in pyproject.toml
vim pyproject.toml

# 2. Commit version bump
git add pyproject.toml
git commit -m "chore: Bump version to 1.0.0"
git push

# 3. Create and push tag
git tag -a v1.0.0 -m "Release version 1.0.0"
git push origin v1.0.0

# 4. GitHub Actions automatically builds and creates release
```

## 7. Emergency Fixes

### Skip Pre-commit Hooks (Use Sparingly!)

```bash
git commit --no-verify -m "emergency fix"
```

⚠️ **Warning**: CI will still run all checks. Only skip hooks in true emergencies.

### Force Push (Use with Caution!)

```bash
# Only for your own feature branches, never for main/develop
git push --force-with-lease origin feature/your-branch
```

## 8. Getting Help

### Check CI Logs

1. Go to your PR on GitHub
2. Click "Checks" tab
3. Click failed job to see detailed logs
4. Look for error messages

### Run Same Checks Locally

```bash
# Run all checks that CI runs
make check-all
```

### Common Issues and Solutions

| Issue | Solution |
|-------|----------|
| Black formatting failed | Run `make format-black` |
| Import order wrong | Run `make format-isort` |
| Flake8 errors | Fix manually, run `make lint` |
| Type errors | Add type hints, run `make type-check` |
| Tests failing | Run `make test` locally and fix |
| Coverage too low | Add tests, run `make test-cov` |
| Security issues | Review bandit report, fix issues |

## 9. Best Practices

### ✓ DO

- Run `make test-fast` frequently during development
- Run `make check-all` before pushing
- Write tests for new features
- Keep commits small and focused
- Use semantic commit messages (feat:, fix:, docs:, etc.)
- Review CI logs when checks fail
- Ask for help when stuck

### ✗ DON'T

- Skip pre-commit hooks without good reason
- Push without running local checks
- Ignore security warnings
- Commit with failing tests
- Force push to main/develop branches
- Commit secrets or sensitive data
- Ignore code review feedback

## 10. Semantic Commit Messages

Use these prefixes for better changelogs:

```bash
feat: Add new feature
fix: Fix a bug
docs: Update documentation
style: Format code (no functional change)
refactor: Refactor code (no functional change)
test: Add or update tests
chore: Update dependencies, configs, etc.
perf: Performance improvements
ci: CI/CD changes
```

**Examples:**
```bash
git commit -m "feat: Add patient search with natural language"
git commit -m "fix: Resolve database connection timeout"
git commit -m "docs: Update API documentation"
git commit -m "test: Add tests for prescription generation"
```

## 11. Useful Aliases (Optional)

Add to your `~/.bashrc` or `~/.zshrc`:

```bash
# DocAssist shortcuts
alias dt='make test-fast'
alias dtc='make test-cov'
alias dl='make lint'
alias df='make format'
alias dca='make check-all'
alias dr='make run'
```

Then use:
```bash
dt   # Quick test
df   # Format code
dca  # Run all checks
```

## 12. Next Steps

- Read full documentation: `.github/README.md`
- Review code quality guidelines
- Explore workflow files in `.github/workflows/`
- Join development discussions
- Start contributing!

---

**Questions?** Create an issue or contact dev@docassist.health

**Happy Coding!** 🚀
