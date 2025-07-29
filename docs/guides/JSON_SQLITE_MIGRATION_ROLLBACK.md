# JSON to SQLite Migration Rollback Strategy

## Overview

This document outlines the rollback strategy for the JSON to SQLite dataset configuration migration implemented in Issue #59. The migration includes comprehensive backup and rollback capabilities to ensure zero data loss and minimal downtime.

## Migration Architecture

### Before Migration
- Dataset configurations stored in JSON files (`tableau_istat_datasets_*.json`)
- Converters loaded configurations directly from JSON files
- No centralized configuration management

### After Migration
- Dataset configurations stored in SQLite `dataset_registry` table
- Converters use `DatasetConfigManager` with SQLite-first, JSON-fallback approach
- Automatic backup of JSON files before migration
- Comprehensive migration reporting and validation

## Rollback Scenarios

### 1. Pre-Migration Rollback (Before Migration Starts)

**Situation**: Need to cancel migration before it starts
**Action**: Simply don't run the migration script
**Recovery Time**: Immediate
**Data Impact**: None

### 2. Mid-Migration Rollback (Migration in Progress)

**Situation**: Migration fails or needs to be stopped during execution
**Available Data**:
- Original JSON files backed up in `backups/json_configs_[timestamp]/`
- Partial SQLite data may exist
- Migration report shows progress

**Rollback Steps**:
```bash
# 1. Stop migration if running
# Migration script will have stopped automatically on error

# 2. Clear any partial SQLite data (optional)
PYTHONPATH=. python -c "
from src.database.sqlite.schema import MetadataSchema
schema = MetadataSchema()
schema.drop_schema()
"

# 3. Restore JSON files from backup (if needed)
cp backups/json_configs_[timestamp]/* .

# 4. Verify converters work with JSON files
PYTHONPATH=. python -c "
from src.converters.powerbi_converter import IstatXMLToPowerBIConverter
c = IstatXMLToPowerBIConverter()
print(f'Source: {c.datasets_config.get(\"source\", \"json fallback\")}')
"
```

**Recovery Time**: < 5 minutes
**Data Impact**: None (original JSON files preserved)

### 3. Post-Migration Rollback (Migration Completed)

**Situation**: Issues discovered after successful migration
**Available Data**:
- Original JSON files backed up in `backups/json_configs_[timestamp]/`
- SQLite database with migrated data
- Complete migration report

**Option A: Temporary Rollback (Keep SQLite, Force JSON)**
```bash
# Temporarily force converters to use JSON while debugging
# 1. Restore JSON files to working directory
cp backups/json_configs_[timestamp]/* .

# 2. Temporarily disable SQLite by renaming database
mv data/databases/osservatorio_metadata.db data/databases/osservatorio_metadata.db.backup

# 3. Test converters (should fallback to JSON)
PYTHONPATH=. python -c "
from src.converters.powerbi_converter import IstatXMLToPowerBIConverter
c = IstatXMLToPowerBIConverter()
print(f'Source: {c.datasets_config.get(\"source\", \"json fallback\")}')
"
```

**Option B: Full Rollback (Remove SQLite Changes)**
```bash
# 1. Restore JSON files
cp backups/json_configs_[timestamp]/* .

# 2. Remove SQLite database
rm data/databases/osservatorio_metadata.db

# 3. Checkout pre-migration code (if needed)
git checkout HEAD~1 -- src/converters/powerbi_converter.py
git checkout HEAD~1 -- src/converters/tableau_converter.py

# 4. Remove new SQLite modules (if full rollback needed)
rm -rf src/database/sqlite/dataset_config.py
rm -rf scripts/migrate_json_to_sqlite.py
```

**Recovery Time**: 5-15 minutes
**Data Impact**: Revert to pre-migration state

## Validation After Rollback

After any rollback, validate that the system works correctly:

### 1. Converter Functionality Test
```bash
# Test PowerBI converter
PYTHONPATH=. python -c "
from src.converters.powerbi_converter import IstatXMLToPowerBIConverter
c = IstatXMLToPowerBIConverter()
print(f'✅ PowerBI: {c.datasets_config.get(\"total_datasets\", 0)} datasets')
print(f'   Source: {c.datasets_config.get(\"source\", \"unknown\")}')
"

# Test Tableau converter
PYTHONPATH=. python -c "
from src.converters.tableau_converter import IstatXMLtoTableauConverter
c = IstatXMLtoTableauConverter()
print(f'✅ Tableau: {c.datasets_config.get(\"total_datasets\", 0)} datasets')
print(f'   Source: {c.datasets_config.get(\"source\", \"unknown\")}')
"
```

### 2. Run Existing Tests
```bash
# Run converter tests to ensure no regressions
PYTHONPATH=. python -m pytest tests/unit/test_powerbi_converter.py -v
PYTHONPATH=. python -m pytest tests/unit/test_tableau_converter.py -v
```

### 3. Functionality Verification
```bash
# Test that converters can actually process datasets
# (Run with sample XML data if available)
```

## Backup Files Management

### Backup Location
- **Directory**: `backups/json_configs_[timestamp]/`
- **Contents**: Original JSON configuration files
- **Retention**: Keep indefinitely (small file sizes)

### Backup Verification
Before any rollback, verify backup integrity:
```bash
# Check backup exists and contains expected files
ls -la backups/json_configs_*/
grep -l "total_datasets" backups/json_configs_*/*.json
```

### Migration Report Analysis
Use migration reports to understand what was changed:
```bash
# View migration report
cat logs/json_to_sqlite_migration_[timestamp].json | python -m json.tool

# Check specific migration details
python -c "
import json
with open('logs/json_to_sqlite_migration_[timestamp].json') as f:
    report = json.load(f)
print(f'Datasets migrated: {len(report[\"datasets_migrated\"])}')
print(f'Validation errors: {len(report[\"validation_errors\"])}')
for dataset in report['datasets_migrated']:
    print(f'  - {dataset[\"dataset_id\"]} ({dataset[\"migration_type\"]})')
"
```

## Prevention and Monitoring

### Pre-Migration Checks
Before running migration:
1. Verify current JSON files are valid
2. Ensure sufficient disk space for backups
3. Confirm no other processes are using configuration files
4. Run test migration in development environment

### Post-Migration Monitoring
After successful migration:
1. Monitor converter performance (should be faster with SQLite)
2. Verify all expected datasets are accessible
3. Check logs for any fallback to JSON warnings
4. Validate data integrity periodically

## Emergency Contacts and Procedures

### Immediate Issues
1. **Stop all data processing** that depends on converters
2. **Check migration report** for any errors or incomplete operations
3. **Verify backup files** are complete and accessible
4. **Choose appropriate rollback strategy** based on issue severity

### Communication
- Document any issues found and resolution steps taken
- Update team on rollback status and expected recovery time
- Consider creating incident report for significant rollbacks

## Testing Rollback Procedures

### Development Environment Testing
Regularly test rollback procedures in development:
```bash
# 1. Create test JSON config
echo '{"total_datasets": 1, "categories": {"test": ["TEST1"]}, "datasets": [{"dataflow_id": "TEST1", "name": "Test", "category": "test"}]}' > test_config.json

# 2. Run migration
PYTHONPATH=. python scripts/migrate_json_to_sqlite.py

# 3. Test rollback
mv data/databases/osservatorio_metadata.db data/databases/osservatorio_metadata.db.bak

# 4. Verify fallback
PYTHONPATH=. python -c "from src.converters.powerbi_converter import IstatXMLToPowerBIConverter; print(IstatXMLToPowerBIConverter().datasets_config.get('source', 'unknown'))"

# 5. Restore
mv data/databases/osservatorio_metadata.db.bak data/databases/osservatorio_metadata.db
```

## Conclusion

The migration includes comprehensive rollback capabilities with:
- ✅ Automatic backup of original JSON files
- ✅ Fallback mechanisms in converter code
- ✅ Multiple rollback strategies for different scenarios
- ✅ Validation procedures for post-rollback verification
- ✅ Minimal recovery time (< 15 minutes for complete rollback)
- ✅ Zero data loss guarantee

The dual-mode approach (SQLite-first with JSON fallback) ensures that the system remains functional even if SQLite issues arise, providing robust operational continuity.
