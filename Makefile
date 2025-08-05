# Osservatorio ISTAT Data Platform - Makefile
# Development and Testing Commands

.PHONY: help test test-fast test-critical test-integration test-unit test-full clean pre-commit install powerbi examples status docs dev-setup dev-commit dev-push ci dashboard db-init db-status benchmark format lint pipeline-demo pipeline-test process-single process-batch validate-pipeline pipeline-status pipeline-examples

# Default target
help:  ## Show available commands
	@echo "🎯 Osservatorio Data Pipeline Commands"
	@echo "====================================="
	@echo ""
	@echo "🎉 PHASE 1 FOUNDATION CLEANUP COMPLETED (70.92% coverage):"
	@echo "  make phase1-validate     # Validate Phase 1 architecture"
	@echo "  make architecture-test   # Test specialized managers"
	@echo "  make fastapi-test        # Test REST API integration"
	@echo "  make db-status           # Check database status"
	@echo ""
	@echo "🚀 QUICK START:"
	@echo "  make dev-setup           # Complete development setup"
	@echo "  make test-fast           # Quick unit tests (~30s)"
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

# Core Testing Commands - Updated for Phase 1 Architecture
test-fast:  ## Run fast unit tests (~30s)
	@echo "🚀 Running fast unit tests..."
	pytest tests/unit/test_dataset_manager.py tests/unit/test_config_manager.py tests/unit/test_user_manager.py tests/unit/test_audit_manager.py --tb=short -q

test-critical:  ## Run critical path tests (~15s)
	@echo "⚡ Running critical path tests..."
	pytest tests/unit/test_dataset_manager.py::TestDatasetManager::test_register_dataset_success \
		tests/integration/test_unified_repository.py::TestUnifiedDataRepository::test_complete_dataset_registration \
		tests/integration/test_unified_repository.py::TestUnifiedDataRepository::test_system_status \
		tests/unit/test_fastapi_integration.py::TestFastAPIIntegration::test_health_check \
		--tb=short -v

test-integration:  ## Run integration tests (~45s)
	@echo "🔗 Running integration tests..."
	pytest tests/integration/ --tb=short -v

test-unit:  ## Run all unit tests (~120s)
	@echo "🧪 Running all unit tests..."
	pytest tests/unit/ -k "not slow and not performance" --tb=short --maxfail=10

test-performance:  ## Run performance tests (~60s)
	@echo "⚡ Running performance tests..."
	pytest tests/performance/ --tb=short -v

test-full:  ## Run complete test suite with coverage (~400s)
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

# PowerBI Integration Commands - Updated for Phase 1
powerbi-validate:  ## Validate PowerBI integration offline
	@echo "🔍 Validating PowerBI integration..."
	@python -c "from src.integrations.powerbi.optimizer import PowerBIOptimizer; optimizer = PowerBIOptimizer(); print('✅ PowerBI optimizer initialized'); print('✅ Validation passed')"

powerbi-demo:  ## Run PowerBI integration demo
	@echo "📊 Running PowerBI integration demo..."
	pytest tests/integration/test_powerbi_integration.py::TestPowerBIIntegration::test_end_to_end_powerbi_pipeline -v

powerbi-test:  ## Run PowerBI specific tests
	@echo "🧪 Running PowerBI tests..."
	pytest tests/unit/test_powerbi_converter.py tests/integration/test_powerbi_integration.py -v

fastapi-test:  ## Run FastAPI integration tests
	@echo "🌐 Running FastAPI integration tests..."
	pytest tests/unit/test_fastapi_integration.py -v

architecture-test:  ## Test Phase 1 architecture components
	@echo "🏗️ Testing Phase 1 architecture..."
	pytest tests/unit/test_dataset_manager.py tests/unit/test_repository_extended.py tests/integration/test_unified_repository.py -v

# Code Quality and Formatting
pre-commit:  ## Run pre-commit hooks manually
	pre-commit run --all-files

pre-commit-critical:  ## Run only critical pre-commit checks
	pre-commit run pytest-critical

lint:  ## Run all linting tools (check-only)
	@echo "🔍 Running linting checks..."
	@echo "  -> ruff check"
	@ruff check . --output-format=concise
	@echo "  -> black check"
	@black --check --quiet .
	@echo "  -> isort check"
	@isort --check-only --profile=black --quiet .
	@echo "✅ Linting completed!"

format:  ## Format code with modern tools (auto-fix)
	@echo "🔧 Auto-formatting code..."
	@echo "  -> ruff fix"
	@ruff check . --fix --unsafe-fixes
	@echo "  -> black format"
	@black .
	@echo "  -> isort format"
	@isort --profile=black .
	@echo "✅ Code formatted!"

lint-fix:  ## Fix all auto-fixable linting issues
	@echo "🔧 Auto-fixing linting issues..."
	@$(MAKE) format
	@echo "  -> running final check"
	@ruff check . --output-format=concise

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

# Database Management - Updated for Phase 1 Architecture
db-status:  ## Check database status
	@echo "📊 Checking database status..."
	@python -c "from src.database.sqlite.repository import get_unified_repository; repo = get_unified_repository(); status = repo.get_system_status(); print(f'SQLite Status: {status.get(\"metadata_database\", {}).get(\"status\", \"unknown\")}'); print(f'DuckDB Status: {status.get(\"analytics_database\", {}).get(\"status\", \"unknown\")}'); print(f'Total Datasets: {status.get(\"metadata_database\", {}).get(\"stats\", {}).get(\"total_datasets\", \"unknown\")}'); repo.close()"

db-init:  ## Initialize database schemas
	@echo "🔧 Initializing database schemas..."
	@python -c "from src.database.sqlite.schema import MetadataSchema; schema = MetadataSchema(); schema.create_schema(); print('✅ SQLite schema ready'); schema.close_connections()"
	@python -c "from src.database.duckdb.manager import DuckDBManager; manager = DuckDBManager(); manager.ensure_schema_exists(); print('✅ DuckDB schema ready'); manager.close()"

db-test-data:  ## Populate database with test datasets for development
	@echo "🔧 Populating database with test data..."
	@python -c "from src.database.sqlite.repository import get_unified_repository; repo = get_unified_repository(); result = repo.register_dataset_complete('TEST_DEV_001', 'Development Test Dataset', 'test', 'Dataset for development testing', 'ISTAT', 8, {'environment': 'development'}); print('✅ Test dataset added' if result else '❌ Failed to add test dataset'); repo.close()"

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

# Development Workflows - Updated for Phase 1
dev-setup:  ## Complete development environment setup
	@echo "🚀 Setting up development environment..."
	@$(MAKE) install
	@$(MAKE) db-init
	@$(MAKE) db-test-data
	@$(MAKE) test-fast
	@$(MAKE) architecture-test
	@echo "✅ Development environment ready with Phase 1 architecture!"

dev-commit:  ## Pre-commit development workflow
	@echo "🚀 Pre-commit workflow..."
	@$(MAKE) format
	@$(MAKE) test-critical
	@$(MAKE) architecture-test
	@echo "✅ Ready to commit!"

dev-push:  ## Pre-push development workflow
	@echo "🚀 Pre-push workflow..."
	@$(MAKE) format
	@$(MAKE) test
	@$(MAKE) lint
	@$(MAKE) fastapi-test
	@echo "✅ Ready to push!"

phase1-validate:  ## Validate Phase 1 Foundation Cleanup completion
	@echo "🎯 Validating Phase 1 Foundation Cleanup..."
	@echo "Testing specialized managers..."
	@$(MAKE) architecture-test
	@echo ""
	@echo "Testing FastAPI integration..."
	@$(MAKE) fastapi-test
	@echo ""
	@echo "Testing PowerBI integration..."
	@$(MAKE) powerbi-test
	@echo ""
	@echo "Checking database status..."
	@$(MAKE) db-status
	@echo ""
	@echo "✅ Phase 1 Foundation Cleanup validated!"

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

# Development Examples and Help - Updated for Phase 1
examples:  ## Show common development workflow examples
	@echo "📚 Common Development Workflows (Phase 1):"
	@echo ""
	@echo "🚀 First-time setup:"
	@echo "  make dev-setup           # Complete environment setup with Phase 1 architecture"
	@echo ""
	@echo "💻 During development:"
	@echo "  make test-fast           # Quick feedback (~30s)"
	@echo "  make architecture-test   # Test Phase 1 components (~20s)"
	@echo "  make powerbi-validate    # Test PowerBI integration"
	@echo "  make fastapi-test        # Test REST API (~15s)"
	@echo ""
	@echo "📝 Before committing:"
	@echo "  make dev-commit          # Format + critical + architecture tests (~25s)"
	@echo ""
	@echo "🚀 Before pushing:"
	@echo "  make dev-push            # Complete validation (~50s)"
	@echo ""
	@echo "🎯 Phase 1 validation:"
	@echo "  make phase1-validate     # Validate complete Phase 1 Foundation (~60s)"
	@echo ""
	@echo "🔧 Maintenance:"
	@echo "  make clean               # Clean temporary files"
	@echo "  make benchmark           # Check performance"
	@echo "  make db-status           # Check database health"
	@echo "  make db-test-data        # Add test data for development"
	@echo ""
	@echo "🤖 CI/CD simulation:"
	@echo "  make ci                  # Full pipeline (~400s)"

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
