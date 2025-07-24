# Osservatorio ISTAT Data Platform - Makefile
# Day 5 Optimized Testing Strategy

.PHONY: help test test-fast test-critical test-integration test-full clean pre-commit install

# Default target
help:  ## Show this help message
	@echo "🎯 Osservatorio Testing Commands (Day 5 Optimized)"
	@echo "=================================================="
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# Installation
install:  ## Install dependencies
	pip install -r requirements.txt
	pip install -r requirements-dev.txt
	pre-commit install

# Testing Commands (Day 5 Strategy)
test-fast:  ## Run fast unit tests (development workflow) - ~20s
	@echo "🚀 Running FAST unit tests..."
	pytest -c pytest-fast.ini tests/unit/test_sqlite_metadata.py tests/unit/test_config.py --tb=short -q

test-critical:  ## Run critical path tests - ~5s
	@echo "⚡ Running CRITICAL PATH tests..."
	pytest -c pytest-fast.ini \
		tests/unit/test_sqlite_metadata.py::TestSQLiteMetadataManager::test_dataset_registration \
		tests/integration/test_unified_repository.py::TestUnifiedDataRepository::test_complete_dataset_registration \
		tests/integration/test_unified_repository.py::TestUnifiedDataRepository::test_system_status \
		--tb=short -v

test-integration:  ## Run integration tests sample - ~5s
	@echo "🔗 Running INTEGRATION tests..."
	pytest tests/integration/test_unified_repository.py::TestUnifiedDataRepository::test_user_preferences_with_cache \
		tests/integration/test_unified_repository.py::TestUnifiedDataRepository::test_cache_operations \
		--tb=short -v

test-unit-all:  ## Run all unit tests with fast config - ~90s
	@echo "🧪 Running ALL unit tests (fast config)..."
	pytest -c pytest-fast.ini tests/unit/ -k "not slow and not performance" --tb=short --maxfail=5

test-full:  ## Run complete test suite with coverage (CI/CD) - ~300s
	@echo "🏁 Running FULL test suite with coverage..."
	pytest --cov=src --cov-report=html --cov-report=term-missing tests/

test:  ## Run Day 5 optimized workflow (fast + critical + integration) - ~30s
	@echo "🎯 Running Day 5 optimized testing workflow..."
	@$(MAKE) test-fast
	@echo ""
	@$(MAKE) test-critical
	@echo ""
	@$(MAKE) test-integration
	@echo ""
	@echo "✅ Day 5 testing workflow completed!"

# Pre-commit and Quality
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

# Day 5 Specific Commands
day5-validate:  ## Validate Day 5 implementation
	@echo "🔍 Validating Day 5 implementation..."
	python scripts/day5_migration_script.py --validate-only

day5-migrate:  ## Run Day 5 migration (with backup)
	@echo "🔄 Running Day 5 migration..."
	python scripts/day5_migration_script.py

day5-test-strategy:  ## Test Day 5 strategy (all workflows)
	@echo "📊 Testing Day 5 strategy..."
	python scripts/test_day5_strategy.py all

# Performance and Benchmarks
benchmark:  ## Run performance benchmarks
	python scripts/performance_regression_detector.py

# Cleanup
clean:  ## Clean up temporary files and caches
	python scripts/cleanup_temp_files.py
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	rm -rf htmlcov/ .coverage .pytest_cache/ 2>/dev/null || true

# Development Workflow Examples
dev-commit:  ## Development pre-commit workflow
	@echo "🚀 Development commit workflow..."
	@$(MAKE) format
	@$(MAKE) test-critical
	@echo "✅ Ready to commit!"

dev-push:  ## Development pre-push workflow
	@echo "🚀 Development push workflow..."
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

# Documentation
docs-test-strategy:  ## Show testing strategy documentation
	@echo "📋 Opening Day 5 Testing Strategy..."
	@cat TESTING_STRATEGY.md

# Development Examples
examples:  ## Show usage examples
	@echo "📚 Development Workflow Examples:"
	@echo ""
	@echo "During development:"
	@echo "  make test-fast          # Quick feedback (~20s)"
	@echo ""
	@echo "Before commit:"
	@echo "  make dev-commit         # Format + critical tests (~5s)"
	@echo ""
	@echo "Before push:"
	@echo "  make dev-push           # Complete development validation (~30s)"
	@echo ""
	@echo "CI/CD:"
	@echo "  make ci                 # Full pipeline simulation (~300s)"
	@echo ""
	@echo "Day 5 specific:"
	@echo "  make day5-validate      # Validate Day 5 implementation"
	@echo "  make day5-test-strategy # Test all Day 5 strategies"
