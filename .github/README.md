# CI/CD Pipeline Documentation

This directory contains the complete CI/CD configuration for DocAssist EMR, including GitHub Actions workflows, code quality tools, and automation scripts.

## Overview

DocAssist EMR uses a comprehensive CI/CD pipeline that ensures code quality, security, and reliability across all changes. The pipeline includes:

- **Continuous Integration**: Automated testing and code quality checks on every push and PR
- **Security Scanning**: Daily security scans and vulnerability checks
- **Automated Releases**: Multi-platform builds for desktop and mobile
- **Nightly Testing**: Comprehensive testing including load tests and memory profiling

## Workflows

### 1. CI Pipeline (`.github/workflows/ci.yml`)

**Triggers:**
- Push to `main` or `develop` branches
- All pull requests

**Jobs:**
- **lint**: Runs flake8, black --check, and isort --check
- **type-check**: Runs mypy type checker
- **test-unit**: Runs pytest with coverage (fails if <70%)
- **test-integration**: Runs integration tests with real database
- **security-scan**: Runs bandit and safety checks
- **build**: Verifies app builds on Windows, macOS, and Linux

**Key Features:**
- Parallel test execution with pytest-xdist
- Coverage uploaded to Codecov
- Test artifacts retained for 30 days
- Python 3.11 and 3.12 compatibility testing

### 2. Security Scanning (`.github/workflows/security.yml`)

**Triggers:**
- Push to `main` or `develop` branches
- All pull requests
- Scheduled daily at 2 AM UTC
- Manual trigger via workflow_dispatch

**Jobs:**
- **bandit-scan**: Python security analysis
- **dependency-scan**: Checks for vulnerable dependencies (safety, pip-audit)
- **semgrep-scan**: Code pattern analysis with security rules
- **secret-scan**: Detects accidentally committed secrets
- **trufflehog-scan**: Git history secret scanning

**Outputs:**
- Security reports as artifacts (retained 90 days)
- PR comments with security summary
- GitHub issues created on failures

### 3. Release Pipeline (`.github/workflows/release.yml`)

**Triggers:**
- Push tags matching `v*.*.*` pattern
- Manual trigger with version input

**Jobs:**
- **create-release**: Generates changelog and creates GitHub release
- **build-windows**: Builds Windows desktop app
- **build-macos**: Builds macOS desktop app
- **build-linux**: Builds Linux desktop app
- **build-android**: Builds Android APK
- **build-ios**: Builds iOS app (requires certificates)

**Artifacts:**
- `DocAssist-EMR-Windows-{version}.zip`
- `DocAssist-EMR-macOS-{version}.zip`
- `DocAssist-EMR-Linux-{version}.tar.gz`
- `DocAssist-EMR-Android-{version}.apk`

**Release Process:**
```bash
# 1. Create and push tag
git tag -a v1.0.0 -m "Release version 1.0.0"
git push origin v1.0.0

# 2. GitHub Actions automatically builds and creates release
# 3. Download artifacts from the release page
```

### 4. Nightly Tests (`.github/workflows/nightly.yml`)

**Triggers:**
- Scheduled daily at 2 AM UTC
- Manual trigger via workflow_dispatch

**Jobs:**
- **full-test-suite**: All tests including slow tests
- **integration-tests**: Real database with 100 test patients
- **load-tests**: Performance benchmarks and bulk operations
- **rag-performance-tests**: ChromaDB embedding performance
- **memory-leak-tests**: Memory profiling with memray
- **compatibility-tests**: Multi-OS and Python version testing

**Failure Handling:**
- Creates GitHub issue on test failures
- Sends notifications (configure Slack/email webhook)
- Retains artifacts for debugging

## Code Quality Tools

### Black (Code Formatter)

```bash
# Check formatting
make lint-black
# or
black --check src/

# Auto-format code
make format-black
# or
black src/
```

**Configuration:** `pyproject.toml` → `[tool.black]`
- Line length: 127
- Target: Python 3.11+

### isort (Import Sorter)

```bash
# Check import sorting
make lint-isort
# or
isort --check-only src/

# Auto-sort imports
make format-isort
# or
isort src/
```

**Configuration:** `pyproject.toml` → `[tool.isort]`
- Profile: black
- Line length: 127

### Flake8 (Linter)

```bash
# Run linter
make lint-flake8
# or
flake8 src/
```

**Configuration:** `pyproject.toml` → `[tool.flake8]`
- Max line length: 127
- Max complexity: 10
- Ignores: E203, E266, E501, W503

### Mypy (Type Checker)

```bash
# Run type checker
make type-check
# or
mypy src/
```

**Configuration:** `pyproject.toml` → `[tool.mypy]`
- Python version: 3.11
- Ignore missing imports: True

### Bandit (Security Scanner)

```bash
# Run security scan
make security-bandit
# or
bandit -r src/ -ll
```

**Configuration:** `pyproject.toml` → `[tool.bandit]`
- Severity level: Low/Low

### Pytest (Test Runner)

```bash
# Run all tests
make test

# Run with coverage
make test-cov

# Run fast tests only
make test-fast

# Run integration tests
make test-integration
```

**Configuration:** `pyproject.toml` → `[tool.pytest.ini_options]`
- Coverage threshold: 70%
- Parallel execution enabled

## Pre-commit Hooks

Pre-commit hooks run automatically before each commit to ensure code quality.

### Installation

```bash
# Install pre-commit
pip install pre-commit

# Install hooks
pre-commit install

# or use Makefile
make pre-commit-install
```

### Manual Run

```bash
# Run on all files
pre-commit run --all-files

# Run specific hook
pre-commit run black --all-files
```

### Hooks Included

1. **trailing-whitespace**: Remove trailing whitespace
2. **end-of-file-fixer**: Ensure files end with newline
3. **check-yaml**: Validate YAML files
4. **check-json**: Validate JSON files
5. **check-toml**: Validate TOML files
6. **check-added-large-files**: Prevent large files (>1MB)
7. **check-merge-conflict**: Detect merge conflicts
8. **debug-statements**: Detect debug statements
9. **black**: Format Python code
10. **isort**: Sort imports
11. **flake8**: Lint Python code
12. **mypy**: Type check Python code
13. **bandit**: Security scan Python code
14. **detect-secrets**: Detect secrets in code
15. **pyupgrade**: Upgrade Python syntax
16. **markdownlint**: Lint Markdown files
17. **yamllint**: Lint YAML files
18. **prettier**: Format JSON/YAML/Markdown

### Skipping Hooks

```bash
# Skip all hooks
git commit --no-verify

# Skip specific hook (not recommended)
SKIP=black git commit -m "message"
```

## Makefile Commands

The `Makefile` provides convenient commands for common development tasks.

### Setup

```bash
make install              # Install dependencies
make pre-commit-install   # Install pre-commit hooks
make dev-setup           # Complete dev environment setup
```

### Testing

```bash
make test                # Run all tests
make test-fast           # Run fast tests only
make test-slow           # Run slow/integration tests
make test-cov            # Run tests with coverage
make test-watch          # Run tests in watch mode
```

### Code Quality

```bash
make lint                # Run all linters
make format              # Auto-format code
make type-check          # Run type checker
make security            # Run security scans
make check-all           # Run all checks
```

### Running

```bash
make run                 # Run desktop app
make run-mobile          # Run mobile app
make run-cloud-api       # Run cloud API
```

### Building

```bash
make build               # Build for current platform
make build-windows       # Build Windows app
make build-macos         # Build macOS app
make build-linux         # Build Linux app
make build-android       # Build Android APK
```

### Utilities

```bash
make clean               # Clean build artifacts
make clean-db            # Clean test databases
make reset               # Full reset + reinstall
make docs                # Generate documentation
```

## Coverage Reports

Coverage reports are generated automatically during CI and can be viewed:

1. **Codecov Dashboard**: https://codecov.io/gh/{org}/docassist-emr
2. **Local HTML Report**: `htmlcov/index.html` (after running `make test-cov`)
3. **CI Artifacts**: Download from GitHub Actions run

### Coverage Requirements

- **Minimum**: 70% overall coverage (enforced by CI)
- **Target**: 80%+ coverage for production code
- **Excluded**: Tests, migrations, `__init__.py` files

## Security Scanning

### Automated Scans

- **Daily**: Full security scan at 2 AM UTC
- **PR Checks**: Security scan on every pull request
- **Release**: Security scan before every release

### Tools Used

1. **Bandit**: Finds common security issues in Python code
2. **Safety**: Checks dependencies against vulnerability database
3. **pip-audit**: PyPI vulnerability scanner
4. **Semgrep**: Code pattern analysis with security rules
5. **detect-secrets**: Prevents secrets from being committed
6. **TruffleHog**: Scans git history for secrets

### Handling Security Issues

1. Review security scan artifacts
2. Fix identified vulnerabilities
3. Update dependencies if needed
4. Re-run scans to verify fixes
5. Document any false positives

## Release Process

### Creating a Release

1. **Update Version**
   ```bash
   # Update version in pyproject.toml
   vim pyproject.toml
   ```

2. **Commit Changes**
   ```bash
   git add .
   git commit -m "Prepare release v1.0.0"
   git push
   ```

3. **Create Tag**
   ```bash
   git tag -a v1.0.0 -m "Release version 1.0.0"
   git push origin v1.0.0
   ```

4. **GitHub Actions Builds**
   - Automatically triggered by tag push
   - Builds for all platforms
   - Creates GitHub release
   - Uploads artifacts

5. **Verify Release**
   - Check GitHub Releases page
   - Download and test artifacts
   - Update release notes if needed

### Versioning Scheme

We use Semantic Versioning (SemVer): `MAJOR.MINOR.PATCH`

- **MAJOR**: Breaking changes
- **MINOR**: New features (backward compatible)
- **PATCH**: Bug fixes (backward compatible)

## Troubleshooting

### CI Failures

**Lint Failures:**
```bash
# Fix formatting
make format

# Check what would change
make lint
```

**Test Failures:**
```bash
# Run tests locally
make test-cov

# Run specific test
pytest tests/test_specific.py -v
```

**Coverage Failures:**
```bash
# Generate coverage report
make test-cov

# View HTML report
open htmlcov/index.html
```

**Build Failures:**
```bash
# Verify app structure
python -c "import src.ui.app; import src.services.database"

# Check dependencies
pip install -r requirements.txt
```

### Pre-commit Issues

**Hook Failures:**
```bash
# Run specific hook manually
pre-commit run black --all-files

# Update hooks
pre-commit autoupdate

# Clear cache
pre-commit clean
```

**Slow Hooks:**
```bash
# Skip slow hooks locally
SKIP=pip-audit,python-safety-dependencies-check git commit -m "message"
```

## Configuration Files

- **`ci.yml`**: Main CI pipeline
- **`security.yml`**: Security scanning
- **`release.yml`**: Release automation
- **`nightly.yml`**: Nightly comprehensive tests
- **`CODEOWNERS`**: Code ownership rules
- **`pull_request_template.md`**: PR template
- **`../Makefile`**: Developer commands
- **`../pyproject.toml`**: Tool configuration
- **`../.pre-commit-config.yaml`**: Pre-commit hooks

## Best Practices

1. **Always run tests locally** before pushing
2. **Use pre-commit hooks** to catch issues early
3. **Keep coverage above 70%** for all new code
4. **Review security scan results** before merging
5. **Test on multiple platforms** for UI changes
6. **Update documentation** when changing workflows
7. **Use semantic commit messages** for better changelogs
8. **Tag releases properly** using SemVer

## Support

For issues or questions:
- Create GitHub issue
- Check CI logs for detailed error messages
- Review this documentation
- Contact: dev@docassist.health

---

**Last Updated:** 2026-01-05
**Maintained By:** @drshailesh88
