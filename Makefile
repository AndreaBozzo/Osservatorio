# Osservatorio ISTAT Data Platform - Makefile
# Development and Testing Commands - Updated Sept 2025

.PHONY: help install test lint format clean dev-setup export-test api-test status docs

# Default target
help:  ## Show available commands
	@echo "🎯 Osservatorio Data Pipeline Commands"
	@echo "====================================="
	@echo ""
	@echo "🚀 QUICK START:"
	@echo "  make dev-setup           # Complete development setup"
	@echo "  make test                # Run all tests"
	@echo "  make export-test         # Test export functionality (Issue #150)"
	@echo "  make api-test            # Test FastAPI endpoints"
	@echo "  make status              # Check system status"
	@echo ""
	@echo "🛠️  DEVELOPMENT:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# Installation and Setup
install:  ## Install project dependencies
	pip install -e .
	pip install -e .[dev]
	pre-commit install

dev-setup: install  ## Complete development setup
	@echo "🚀 Setting up development environment..."
	@echo "✅ Dependencies installed"
	@echo "✅ Pre-commit hooks installed"
	@echo "Development environment ready!"

# Testing Commands
test:  ## Run all tests
	@echo "🧪 Running all tests..."
	pytest tests/ -v

test-fast:  ## Run unit tests only (fast)
	@echo "⚡ Running unit tests..."
	pytest tests/unit/ -v

export-test:  ## Test export functionality (Issue #150)
	@echo "📊 Testing export functionality..."
	pytest tests/test_export_functionality.py -v

api-test:  ## Test FastAPI endpoints
	@echo "🌐 Testing API endpoints..."
	pytest tests/integration/test_api_integration.py -v

# Code Quality
lint:  ## Run code linting
	@echo "🔍 Running code linting..."
	ruff check src/ tests/

format:  ## Format code
	@echo "✨ Formatting code..."
	ruff format src/ tests/
	isort src/ tests/

quality: lint format  ## Run all quality checks
	@echo "✅ Code quality checks completed"

# Database and Status
db-status:  ## Check database status
	@echo "💾 Checking database status..."
	@python -c "from src.database.sqlite.repository import get_unified_repository; repo = get_unified_repository(); print('✅ Database connection OK')"

status:  ## Check system status
	@echo "📋 System Status Check"
	@echo "====================="
	@echo "Database:"
	@$(MAKE) db-status
	@echo ""
	@echo "Export System:"
	@python -c "from src.export import UniversalExporter; exporter = UniversalExporter(); print('✅ Export system OK')"
	@echo ""
	@echo "API Server:"
	@python -c "from src.api.fastapi_app import app; print('✅ FastAPI app OK')"

# Development Utilities
clean:  ## Clean temporary files and caches
	@echo "🧹 Cleaning temporary files..."
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name ".pytest_cache" -delete
	find . -type f -name ".coverage" -delete
	rm -rf htmlcov/
	@echo "✅ Cleanup completed"

# Server Commands
serve:  ## Start FastAPI development server
	@echo "🚀 Starting FastAPI server..."
	uvicorn src.api.fastapi_app:app --reload --host 0.0.0.0 --port 8000

# Export Commands
export-csv:  ## Export sample dataset to CSV (requires running server)
	@echo "📊 Testing CSV export..."
	curl -X GET "http://localhost:8000/export/143_222/export?format=csv&limit=10" \
		-H "Authorization: Bearer <your-token-here>" \
		-H "Accept: text/csv"

export-json:  ## Export sample dataset to JSON (requires running server)
	@echo "📊 Testing JSON export..."
	curl -X GET "http://localhost:8000/export/143_222/export?format=json&limit=10" \
		-H "Authorization: Bearer <your-token-here>" \
		-H "Accept: application/json"

# Documentation
docs:  ## Generate documentation
	@echo "📚 Documentation available in docs/ directory"
	@echo "Main documentation: README.md"
	@echo "Architecture: docs/core/ARCHITECTURE.md"
	@echo "API Reference: docs/core/API_REFERENCE.md"

# CI/CD Helpers
ci-test:  ## Run tests suitable for CI
	pytest tests/ --cov=src --cov-report=html --cov-report=term-missing

# Development Validation
validate:  ## Validate complete system
	@echo "🔍 Validating complete system..."
	@echo "Testing export system..."
	@python -c "from src.export import UniversalExporter, StreamingExporter; print('✅ Export system validated')"
	@echo "Testing database..."
	@python -c "from src.database.sqlite.repository import get_unified_repository; repo = get_unified_repository(); print('✅ Database validated')"
	@echo "Testing API..."
	@python -c "from src.api.fastapi_app import app; print('✅ API validated')"
	@echo "Running quick tests..."
	@pytest tests/test_export_functionality.py::TestUniversalExporter::test_csv_export -v
	@echo ""
	@echo "✅ System validation completed successfully!"
