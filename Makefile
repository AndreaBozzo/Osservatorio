# Osservatorio ISTAT Data Platform - Makefile
# Development and Testing Commands

.PHONY: help test test-fast test-critical test-integration test-unit test-full clean pre-commit install powerbi examples status docs dev-setup dev-commit dev-push ci dashboard db-init db-status benchmark format lint pipeline-demo pipeline-test process-single process-batch validate-pipeline pipeline-status pipeline-examples

# Default target
help:  ## Show available commands
	@echo "🎯 Osservatorio Data Pipeline Commands"
	@echo "====================================="
	@echo ""
	@echo "🚀 QUICK START (Issue #63 Complete):"
	@echo "  make pipeline-demo       # Demo unified pipeline with real data"
	@echo "  make pipeline-test       # Test pipeline with sample datasets"
	@echo "  make status              # Check system status"
	@echo ""
	@echo "📊 DATA PROCESSING:"
	@echo "  make process-single      # Process single ISTAT dataset"
	@echo "  make process-batch       # Process multiple datasets"
	@echo "  make validate-pipeline   # Validate pipeline functionality"
	@echo ""
	@echo "🛠️  DEVELOPMENT:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# Installation
install:  ## Install project dependencies
	pip install -e .
	pip install -e .[dev]
	pre-commit install

install-performance:  ## Install performance testing dependencies
	pip install -e .[performance]

install-security:  ## Install security testing dependencies
	pip install -e .[security]

install-all:  ## Install all optional dependencies
	pip install -e .[dev,performance,security]

# =============================================================================
# 🚀 END USER COMMANDS - Issue #63 Unified Pipeline (PRODUCTION READY)
# =============================================================================

pipeline-demo:  ## Run unified pipeline demo with real ISTAT data
	@echo "🚀 Running unified pipeline demo (Issue #63)..."
	@echo "Processing real ISTAT datasets with fluent interface..."
	python scripts/test_real_data_processing.py

pipeline-test:  ## Test unified pipeline with sample datasets
	@echo "🧪 Testing unified pipeline functionality..."
	python scripts/production_pipeline_test.py

process-single:  ## Process single ISTAT dataset interactively
	@echo "📊 Processing single ISTAT dataset..."
	@echo "Available datasets: DCCN_PILN (prices), DCIS_POPRES1 (population), DCCV_TAXOCCU (employment)"
	@read -p "Enter dataset ID (or press Enter for DCCN_PILN): " dataset; \
	dataset=$${dataset:-DCCN_PILN}; \
	echo "Processing $$dataset with unified pipeline..."; \
	python -c "import asyncio; from src.pipeline.unified_ingestion import UnifiedDataIngestionPipeline; from src.pipeline.models import PipelineConfig; \
	async def demo(): \
		config = PipelineConfig(enable_quality_checks=True); \
		pipeline = UnifiedDataIngestionPipeline(config); \
		print('✅ Pipeline initialized - fetching real ISTAT data...'); \
		from src.api.production_istat_client import ProductionIstatClient; \
		client = ProductionIstatClient(); \
		try: \
			xml_data = await client.get_dataset_data('$$dataset'); \
			result = await (pipeline.from_istat('$$dataset', xml_data).validate().convert_to(['powerbi']).store()); \
			print(f'✅ Success: {result.records_processed} records, Quality: {result.quality_score.overall_score:.1f}%'); \
		except Exception as e: \
			print(f'❌ Error: {e}'); \
	asyncio.run(demo())"

process-batch:  ## Process multiple ISTAT datasets in batch
	@echo "📦 Processing multiple ISTAT datasets in batch..."
	python -c "import asyncio; from src.pipeline.unified_ingestion import UnifiedDataIngestionPipeline; from src.pipeline.models import PipelineConfig; from src.api.production_istat_client import ProductionIstatClient; \
	async def batch_demo(): \
		config = PipelineConfig(enable_quality_checks=True, max_concurrent=2); \
		pipeline = UnifiedDataIngestionPipeline(config); \
		client = ProductionIstatClient(); \
		datasets = ['DCCN_PILN', 'DCIS_POPRES1']; \
		configs = []; \
		print('✅ Fetching data for batch processing...'); \
		for ds in datasets: \
			try: \
				xml_data = await client.get_dataset_data(ds); \
				configs.append({'dataset_id': ds, 'sdmx_data': xml_data, 'target_formats': ['powerbi']}); \
			except Exception as e: \
				print(f'⚠️  Skipping {ds}: {e}'); \
		if configs: \
			results = await pipeline.process_batch(configs); \
			for ds_id, result in results.items(): \
				status = '✅' if result.status.value == 'completed' else '❌'; \
				print(f'{status} {ds_id}: {result.records_processed} records'); \
		else: \
			print('❌ No datasets available for batch processing'); \
	asyncio.run(batch_demo())"

validate-pipeline:  ## Validate unified pipeline functionality
	@echo "🔍 Validating unified pipeline (Issue #63)..."
	python scripts/full_system_test.py

pipeline-status:  ## Show pipeline and system status
	@echo "📊 Unified Pipeline Status (Issue #63)"
	@echo "===================================="
	@python -c "from src.pipeline.unified_ingestion import UnifiedDataIngestionPipeline; from src.pipeline.models import PipelineConfig; \
	pipeline = UnifiedDataIngestionPipeline(PipelineConfig()); \
	metrics = pipeline.get_pipeline_metrics(); \
	print(f'Pipeline Status: {metrics[\"status\"]}'); \
	print(f'Active Jobs: {metrics[\"active_jobs\"]}'); \
	print(f'Batch Size: {metrics[\"configuration\"][\"batch_size\"]}'); \
	print(f'Max Concurrent: {metrics[\"configuration\"][\"max_concurrent\"]}'); \
	print(f'Quality Checks: {\"Enabled\" if metrics[\"configuration\"][\"quality_checks_enabled\"] else \"Disabled\"}')"
	@echo ""
	@$(MAKE) db-status

# Quick pipeline examples for documentation
pipeline-examples:  ## Show pipeline usage examples
	@echo "📚 Unified Pipeline Examples (Issue #63)"
	@echo "========================================"
	@echo ""
	@echo "🔗 Fluent Interface Pattern:"
	@echo "  result = await (pipeline"
	@echo "      .from_istat('DCCN_PILN', xml_data)"
	@echo "      .validate(min_quality=80.0)"
	@echo "      .convert_to(['powerbi', 'tableau'])"
	@echo "      .store()"
	@echo "  )"
	@echo ""
	@echo "📦 Batch Processing:"
	@echo "  configs = ["
	@echo "      {'dataset_id': 'DS1', 'sdmx_data': data1, 'target_formats': ['powerbi']},"
	@echo "      {'dataset_id': 'DS2', 'sdmx_data': data2, 'target_formats': ['tableau']}"
	@echo "  ]"
	@echo "  results = await pipeline.process_batch(configs)"
	@echo ""
	@echo "For full documentation: docs/SYSTEM_USAGE_GUIDE.md"

# =============================================================================
# 🛠️  DEVELOPMENT AND TESTING COMMANDS
# =============================================================================

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

lint:  ## Run all linting tools
	ruff check .
	black --check .
	isort --check-only --profile=black .
	flake8 .

format:  ## Format code with modern tools
	ruff --fix .
	black .
	isort --profile=black .

type-check:  ## Run type checking with mypy
	mypy src/

security-check:  ## Run security analysis
	bandit -r src/
	safety check

quality:  ## Run all quality checks
	@$(MAKE) format
	@$(MAKE) lint
	@$(MAKE) type-check
	@$(MAKE) security-check

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
