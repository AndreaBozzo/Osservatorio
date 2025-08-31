# 🦆 DuckDB CLI Quick Start Guide

**Database Path**: `C:\Users\Andrea\Documents\Osservatorio\data\databases\osservatorio.duckdb`
**Size**: 52MB | **Records**: 176,610 | **Tables**: 1 main table

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
DESCRIBE osservatorio.istat_observations;

-- Quick stats
SELECT COUNT(*) as total_records FROM osservatorio.istat_observations;
```

### Data Exploration
```sql
-- Records per dataset
SELECT dataset_id, COUNT(*) as records
FROM osservatorio.istat_observations
GROUP BY dataset_id
ORDER BY records DESC;

-- Sample data
SELECT * FROM osservatorio.istat_observations LIMIT 5;

-- Time range
SELECT
    MIN(time_period) as earliest,
    MAX(time_period) as latest
FROM osservatorio.istat_observations
WHERE time_period NOT LIKE '%T%';
```

### Useful Queries
```sql
-- Data quality check
SELECT
    COUNT(*) as total,
    COUNT(CASE WHEN obs_value = '' THEN 1 END) as empty_values,
    COUNT(CASE WHEN obs_value IS NULL THEN 1 END) as null_values
FROM osservatorio.istat_observations;

-- Dataset details
SELECT
    dataset_id,
    COUNT(*) as records,
    MIN(time_period) as first_period,
    MAX(time_period) as last_period,
    COUNT(DISTINCT time_period) as unique_periods
FROM osservatorio.istat_observations
GROUP BY dataset_id;

-- Recent ingestions
SELECT
    dataset_id,
    MAX(ingestion_timestamp) as latest_ingestion,
    COUNT(*) as records
FROM osservatorio.istat_observations
GROUP BY dataset_id;
```

### Duplicate Detection & Management
```sql
-- Check for exact duplicates
SELECT
    COUNT(*) - COUNT(DISTINCT (dataset_id, obs_value, time_period, record_id)) as exact_duplicates
FROM osservatorio.istat_observations;

-- Find business logic duplicates (same dataset + time period)
SELECT
    dataset_id,
    time_period,
    COUNT(*) as occurrences,
    STRING_AGG(DISTINCT obs_value, ', ') as different_values
FROM osservatorio.istat_observations
GROUP BY dataset_id, time_period
HAVING COUNT(*) > 1
ORDER BY occurrences DESC
LIMIT 20;

-- Identify potential duplicates by similarity
SELECT
    dataset_id,
    COUNT(DISTINCT record_id) as unique_records,
    COUNT(*) as total_records,
    COUNT(*) - COUNT(DISTINCT record_id) as potential_duplicates
FROM osservatorio.istat_observations
GROUP BY dataset_id
HAVING COUNT(*) > COUNT(DISTINCT record_id);

-- Remove exact duplicates (use with caution)
-- DELETE FROM osservatorio.istat_observations
-- WHERE record_id IN (
--     SELECT record_id FROM (
--         SELECT record_id,
--                ROW_NUMBER() OVER (
--                    PARTITION BY dataset_id, obs_value, time_period
--                    ORDER BY ingestion_timestamp
--                ) as rn
--         FROM osservatorio.istat_observations
--     ) WHERE rn > 1
-- );

-- Backup before cleanup
-- CREATE TABLE istat_observations_backup AS
-- SELECT * FROM osservatorio.istat_observations;
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
*Database: 52MB | 176,610 records | Last updated: 2025-08-31*
