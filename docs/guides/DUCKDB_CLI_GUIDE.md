# 🦆 DuckDB CLI Quick Start Guide

**Database Path**: `C:\Users\Andrea\Documents\Osservatorio\data\databases\osservatorio.duckdb`
**Size**: 7.8MB | **Records**: 128,471 | **Tables**: 1 main table

## Installation & Launch

```bash
# Download DuckDB CLI (if not already done)
wget https://github.com/duckdb/duckdb/releases/latest/download/duckdb_cli-windows-amd64.zip
unzip duckdb_cli-windows-amd64.zip

# Launch with our database
./duckdb.exe "C:\Users\Andrea\Documents\Osservatorio\data\databases\osservatorio.duckdb"
```

## Essential Commands

### Database Overview
```sql
-- Show all tables
.tables

-- Table schema
DESCRIBE main.istat_observations;

-- Quick stats
SELECT COUNT(*) as total_records FROM main.istat_observations;
```

### Data Exploration
```sql
-- Records per dataset
SELECT dataset_id, COUNT(*) as records
FROM main.istat_observations
GROUP BY dataset_id
ORDER BY records DESC;

-- Sample data
SELECT * FROM main.istat_observations LIMIT 5;

-- Time range
SELECT
    MIN(time_period) as earliest,
    MAX(time_period) as latest
FROM main.istat_observations
WHERE time_period NOT LIKE '%T%';
```

### Useful Queries
```sql
-- Data quality check
SELECT
    COUNT(*) as total,
    COUNT(CASE WHEN obs_value = '' THEN 1 END) as empty_values,
    COUNT(CASE WHEN obs_value IS NULL THEN 1 END) as null_values
FROM main.istat_observations;

-- Dataset details
SELECT
    dataset_id,
    COUNT(*) as records,
    MIN(time_period) as first_period,
    MAX(time_period) as last_period,
    COUNT(DISTINCT time_period) as unique_periods
FROM main.istat_observations
GROUP BY dataset_id;

-- Recent ingestions
SELECT
    dataset_id,
    MAX(ingestion_timestamp) as latest_ingestion,
    COUNT(*) as records
FROM main.istat_observations
GROUP BY dataset_id;
```

## CLI Commands
```bash
# Import/Export
.mode csv
.output results.csv
SELECT * FROM main.istat_observations WHERE dataset_id = '101_1015';
.output

# Help
.help

# Exit
.quit
```

## Performance Tips
- Use `LIMIT` for large result sets
- Index on `dataset_id` and `time_period` for fast filtering
- JSON queries: `additional_attributes->>'key'` for attributes
- Use `.timer on` to see query execution time

## Common Issues
- **Path escaping**: Use forward slashes or double backslashes
- **Memory**: DuckDB loads data efficiently, but limit large JOINs
- **JSON parsing**: Use `json_extract()` for complex attributes

---
*Database: 7.8MB | Last updated: 2025-08-30*
