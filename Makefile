# Osservatorio ISTAT Data Platform - Makefile
# Development and Testing Commands

.PHONY: help install test lint format clean dev-setup export-test api-test status docs

# Default target
help:  ## Show available commands
	@echo "🎯 Osservatorio Data Pipeline Commands"
	@echo "====================================="
	@echo ""
	@echo "🚀 QUICK START:"
	@echo "  make dev-setup           # Complete development setup"
	@echo "  make serve               # Start FastAPI development server"
	@echo "  make test                # Run all tests"
	@echo "  make status              # Check complete system status"
	@echo ""
	@echo "📊 MAIN FEATURES:"
	@echo "  make export-test         # Test export system"
	@echo "  make api-test            # Test FastAPI ISTAT endpoints"
	@echo "  make ingestion-test      # Test data ingestion pipeline"
	@echo "  make auth-test           # Test authentication system"
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

# Server Commands
serve:  ## Start FastAPI development server
	@echo "🚀 Starting FastAPI server with ISTAT endpoints..."
	uvicorn src.api.fastapi_app:app --reload --host 0.0.0.0 --port 8000

serve-prod:  ## Start production server
	@echo "🚀 Starting production FastAPI server..."
	uvicorn src.api.fastapi_app:app --host 0.0.0.0 --port 8000 --workers 4

# Testing Commands
test:  ## Run all tests
	@echo "🧪 Running complete test suite..."
	pytest tests/ -v --tb=short

test-fast:  ## Run unit tests only (fast)
	@echo "⚡ Running unit tests..."
	pytest tests/unit/ -v

test-integration:  ## Run integration tests
	@echo "🔗 Running integration tests..."
	pytest tests/integration/ -v

export-test:  ## Test export functionality
	@echo "📊 Testing export system..."
	pytest tests/test_export_functionality.py -v

api-test:  ## Test FastAPI ISTAT endpoints
	@echo "🌐 Testing ISTAT API endpoints..."
	pytest tests/integration/test_fastapi_istat_endpoints.py -v

ingestion-test:  ## Test data ingestion pipeline
	@echo "📥 Testing ingestion pipeline..."
	pytest tests/integration/test_simple_pipeline_real.py -v

auth-test:  ## Test authentication system
	@echo "🔐 Testing authentication system..."
	pytest tests/unit/ -k "auth or jwt" -v

db-test:  ## Test database systems
	@echo "💾 Testing database systems..."
	pytest tests/integration/test_unified_repository.py -v

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

# Database Commands
db-status:  ## Check database status
	@echo "💾 Checking database systems..."
	@python -c "from src.database.sqlite.repository import get_unified_repository; repo = get_unified_repository(); print('✅ SQLite + DuckDB unified repository OK')"

db-init:  ## Initialize database schemas
	@echo "💾 Initializing database schemas..."
	@python -c "from src.database.sqlite.manager import get_metadata_manager; manager = get_metadata_manager(); print('✅ SQLite schema initialized')"
	@python -c "from src.database.duckdb.manager import get_manager; manager = get_manager(); print('✅ DuckDB connection verified')"

# System Status
status:  ## Check complete system status
	@echo "📋 Complete System Status Check"
	@echo "==============================="
	@echo ""
	@echo "💾 Database Systems:"
	@$(MAKE) db-status
	@echo ""
	@echo "📊 Export System:"
	@python -c "from src.export import UniversalExporter; exporter = UniversalExporter(); print('✅ Export system OK')"
	@echo ""
	@echo "🌐 API Server:"
	@python -c "from src.api.fastapi_app import app; print('✅ FastAPI ISTAT endpoints OK')"
	@echo ""
	@echo "🔐 Authentication:"
	@python -c "from src.auth.jwt_manager import JWTManager; jwt = JWTManager(); print('✅ JWT authentication OK')"
	@echo ""
	@echo "📥 Ingestion Pipeline:"
	@python -c "from src.ingestion.simple_pipeline import SimpleIngestionPipeline; print('✅ Ingestion pipeline OK')"

# Export System Commands
export-validate:  ## Validate export system
	@echo "🔍 Validating export functionality..."
	@python -c "from src.export import UniversalExporter, StreamingExporter; print('✅ Export system validated')"

export-demo:  ## Show export usage examples
	@echo "📊 Export System Usage Examples"
	@echo "==============================="
	@echo "CSV Export:"
	@echo "  curl -X GET 'http://localhost:8000/export/DATASET_ID/export?format=csv&limit=10' \\"
	@echo "    -H 'Authorization: Bearer YOUR_TOKEN' \\"
	@echo "    -H 'Accept: text/csv'"
	@echo ""
	@echo "JSON Export:"
	@echo "  curl -X GET 'http://localhost:8000/export/DATASET_ID/export?format=json&limit=10' \\"
	@echo "    -H 'Authorization: Bearer YOUR_TOKEN' \\"
	@echo "    -H 'Accept: application/json'"

# Development Utilities
clean:  ## Clean temporary files and caches
	@echo "🧹 Cleaning temporary files..."
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name ".pytest_cache" -delete
	find . -type f -name ".coverage" -delete
	rm -rf htmlcov/
	@echo "✅ Cleanup completed"

# Documentation
docs:  ## Show documentation structure
	@echo "📚 Documentation Structure"
	@echo "=========================="
	@echo "Main: README.md"
	@echo "Developer Guide: docs/project/CLAUDE.md"
	@echo "Architecture: docs/core/ARCHITECTURE.md"
	@echo "API Reference: docs/core/API_REFERENCE.md"

# Validation
validate:  ## Validate complete system functionality
	@echo "🔍 Complete System Validation"
	@echo "============================"
	@echo ""
	@echo "🧪 Testing core components..."
	@python -c "from src.export import UniversalExporter, StreamingExporter; print('✅ Export system')"
	@python -c "from src.database.sqlite.repository import get_unified_repository; repo = get_unified_repository(); print('✅ Database layer')"
	@python -c "from src.api.fastapi_app import app; print('✅ FastAPI application')"
	@python -c "from src.auth.jwt_manager import JWTManager; print('✅ Authentication')"
	@python -c "from src.ingestion.simple_pipeline import SimpleIngestionPipeline; print('✅ Ingestion pipeline')"
	@echo ""
	@echo "🧪 Running critical path tests..."
	@pytest tests/test_export_functionality.py::TestUniversalExporter::test_csv_export -v
	@echo ""
	@echo "✅ System validation completed successfully!"

# Development Workflow
dev-test:  ## Quick development testing workflow
	@echo "🔄 Development Testing Workflow"
	@echo "==============================="
	@$(MAKE) clean
	@$(MAKE) format
	@$(MAKE) lint
	@$(MAKE) test-fast
	@echo ""
	@echo "✅ Development workflow completed!"

ci-test:  ## Run tests suitable for CI
	pytest tests/ --cov=src --cov-report=html --cov-report=term-missing --maxfail=5
