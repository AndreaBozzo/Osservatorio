# Osservatorio ISTAT Data Platform - Makefile
# Development and Testing Commands

.PHONY: help test test-fast test-critical test-integration test-unit test-full clean pre-commit install powerbi examples status docs dev-setup dev-commit dev-push ci dashboard db-init db-status benchmark format lint

# Default target
help:  ## Show available commands
	@echo "🎯 Osservatorio Development Commands"
	@echo "==================================="
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# Installation
install:  ## Install project dependencies
	pip install -r requirements.txt
	pip install -r requirements-dev.txt
	pre-commit install

# Core Testing Commands
test-fast:  ## Run fast unit tests (~20s)
	@echo "🚀 Running fast unit tests..."
	pytest tests/unit/test_sqlite_metadata.py tests/unit/test_config.py --tb=short -q

test-critical:  ## Run critical path tests (~10s)
	@echo "⚡ Running critical path tests..."
	pytest tests/unit/test_sqlite_metadata.py::TestSQLiteMetadataManager::test_dataset_registration \
		tests/integration/test_unified_repository.py::TestUnifiedDataRepository::test_complete_dataset_registration \
		tests/integration/test_unified_repository.py::TestUnifiedDataRepository::test_system_status \
		--tb=short -v

test-integration:  ## Run integration tests (~10s)
	@echo "🔗 Running integration tests..."
	pytest tests/integration/ --tb=short -v

test-unit:  ## Run all unit tests (~90s)
	@echo "🧪 Running all unit tests..."
	pytest tests/unit/ -k "not slow and not performance" --tb=short --maxfail=5

test-performance:  ## Run performance tests (~60s)
	@echo "⚡ Running performance tests..."
	pytest tests/performance/ --tb=short -v

test-full:  ## Run complete test suite with coverage (~300s)
	@echo "🏁 Running full test suite with coverage..."
	pytest --cov=src --cov-report=html --cov-report=term-missing tests/

test:  ## Run optimized development testing workflow (~30s)
	@echo "🎯 Running development testing workflow..."
	@$(MAKE) test-fast
	@echo ""
	@$(MAKE) test-critical
	@echo ""
	@$(MAKE) test-integration
	@echo ""
	@echo "✅ Development testing completed!"

# PowerBI Integration Commands
powerbi-validate:  ## Validate PowerBI integration offline
	@echo "🔍 Validating PowerBI integration..."
	python scripts/validate_powerbi_offline.py

powerbi-demo:  ## Run PowerBI integration demo
	@echo "📊 Running PowerBI integration demo..."
	python examples/powerbi_integration_demo.py

powerbi-test:  ## Run PowerBI specific tests
	@echo "🧪 Running PowerBI tests..."
	pytest tests/unit/test_powerbi_api.py tests/unit/test_powerbi_converter.py -v

# Code Quality and Formatting
pre-commit:  ## Run pre-commit hooks manually
	pre-commit run --all-files

pre-commit-critical:  ## Run only critical pre-commit checks
	pre-commit run pytest-critical

lint:  ## Run linting tools
	black --check .
	isort --check-only --profile=black .
	flake8 .

format:  ## Format code with black and isort
	black .
	isort --profile=black .

# Performance and Benchmarks
benchmark:  ## Run performance benchmarks
	python scripts/performance_regression_detector.py

# Database Management
db-status:  ## Check database status
	@echo "📊 Checking database status..."
	python -c "from src.database.sqlite.repository import get_unified_repository; repo = get_unified_repository(); print(repo.get_system_status())"

db-init:  ## Initialize database schemas
	@echo "🔧 Initializing database schemas..."
	python -c "from src.database.sqlite import SQLiteMetadataManager; manager = SQLiteMetadataManager(); print('✅ SQLite schema ready')"
	python -c "from src.database.duckdb import SimpleDuckDBAdapter; adapter = SimpleDuckDBAdapter(); adapter.create_istat_schema(); print('✅ DuckDB schema ready')"

# Cleanup
clean:  ## Clean up temporary files and caches
	python scripts/cleanup_temp_files.py
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	rm -rf htmlcov/ .coverage .pytest_cache/ 2>/dev/null || true

clean-data:  ## Clean up data files (use with caution)
	@echo "⚠️  This will remove processed data files. Continue? [y/N]"
	@read -r response && [ "$$response" = "y" ] || exit 1
	rm -rf data/processed/* data/cache/*
	@echo "✅ Data files cleaned"

# Development Workflows
dev-setup:  ## Complete development environment setup
	@echo "🚀 Setting up development environment..."
	@$(MAKE) install
	@$(MAKE) db-init
	@$(MAKE) test-fast
	@echo "✅ Development environment ready!"

dev-commit:  ## Pre-commit development workflow
	@echo "🚀 Pre-commit workflow..."
	@$(MAKE) format
	@$(MAKE) test-critical
	@echo "✅ Ready to commit!"

dev-push:  ## Pre-push development workflow
	@echo "🚀 Pre-push workflow..."
	@$(MAKE) format
	@$(MAKE) test
	@$(MAKE) lint
	@echo "✅ Ready to push!"

# CI/CD Simulation
ci:  ## Simulate CI/CD pipeline
	@echo "🤖 Simulating CI/CD pipeline..."
	@$(MAKE) lint
	@$(MAKE) test-full
	@echo "✅ CI/CD simulation completed!"

# Dashboard and Services
dashboard:  ## Run Streamlit dashboard
	streamlit run dashboard/app.py

dashboard-test:  ## Test dashboard functionality
	@echo "🌐 Testing dashboard..."
	python -c "import dashboard.app; print('✅ Dashboard imports successfully')"

# Documentation
docs:  ## Generate or update documentation
	@echo "📚 Documentation commands:"
	@echo "  View testing strategy: cat TESTING.md"
	@echo "  View architecture: cat docs/core/ARCHITECTURE.md"
	@echo "  View API reference: cat docs/core/API_REFERENCE.md"

# Development Examples and Help
examples:  ## Show common development workflow examples
	@echo "📚 Common Development Workflows:"
	@echo ""
	@echo "🚀 First-time setup:"
	@echo "  make dev-setup           # Complete environment setup"
	@echo ""
	@echo "💻 During development:"
	@echo "  make test-fast           # Quick feedback (~20s)"
	@echo "  make powerbi-validate    # Test PowerBI integration"
	@echo ""
	@echo "📝 Before committing:"
	@echo "  make dev-commit          # Format + critical tests (~10s)"
	@echo ""
	@echo "🚀 Before pushing:"
	@echo "  make dev-push            # Complete validation (~30s)"
	@echo ""
	@echo "🔧 Maintenance:"
	@echo "  make clean               # Clean temporary files"
	@echo "  make benchmark           # Check performance"
	@echo "  make db-status           # Check database health"
	@echo ""
	@echo "🤖 CI/CD simulation:"
	@echo "  make ci                  # Full pipeline (~300s)"

# Utility targets
status:  ## Show project status
	@echo "📊 Osservatorio Project Status"
	@echo "============================="
	@echo "📁 Working directory: $(PWD)"
	@echo "🐍 Python version: $(shell python --version 2>/dev/null || echo 'Not found')"
	@echo "🧪 Total tests: $(shell find tests/ -name "test_*.py" | wc -l 2>/dev/null || echo 'Unknown')"
	@echo "📦 Git status:"
	@git status --porcelain | head -5 || echo "Not a git repository"
	@$(MAKE) db-status
