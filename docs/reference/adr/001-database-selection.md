# ADR-001: Database Selection Strategy

**Status**: ~~SUPERSEDED~~ by [ADR-002: Strategic Pivot to SQLite](002-strategic-pivot-sqlite.md)
**Date**: 20 Luglio 2025
**Deciders**: Andrea Bozzo (Maintainer)
**Technical Story**: [Database Foundation Sprint - PROJECT_STATE.md](../project/PROJECT_STATE.md#fase-2-database-foundation-sprint)

**⚠️ NOTICE**: This ADR has been superseded by ADR-002 which implements a more pragmatic SQLite + DuckDB approach based on project experience and @Gasta88's feedback about over-engineering.

## Context

The Osservatorio project currently operates with file-based storage for ISTAT data, which limits analytical capabilities and scalability. We need to implement persistent storage that supports:

- **Data Characteristics**:
  - Primarily structured time-series data from ISTAT SDMX API
  - 509+ available datasets, currently using ~5GB storage
  - High read-to-write ratio (analytics-heavy workload)
  - Geographical and temporal dimensions in most datasets

- **Query Patterns**:
  - Analytical queries predominant (vs transactional)
  - Aggregations by time, territory, demographics
  - Dashboard real-time data loading
  - Bulk data export operations

- **Projected Volume**:
  - Current: ~5GB total (raw + processed)
  - Annual growth: ~1.8GB raw data (approssimativa..)
  - 5-year projection: ~15GB total

- **Access Patterns**:
  - Dashboard: High frequency, small result sets
  - Conversion: Low frequency, large datasets
  - Analytics: Medium frequency, aggregated data
  - Export: Low frequency, full datasets

## Decision Drivers

- **Performance**: Sub-second response for dashboard queries
- **Scalability**: Support for 10+ concurrent users
- **Analytics**: Efficient aggregation and time-series analysis
- **Simplicity**: Minimal operational overhead
- **Cost**: Development/production budget constraints
- **Future-proofing**: Extensible architecture

## Options Considered

### Option 1: DuckDB Only

**Description**: Use DuckDB as single database for all data storage needs.

**Pros**:
- Embedded deployment (no server management)
- Excellent analytical performance (columnar storage)
- Superior compression for time-series data
- OLAP-optimized query execution
- Zero operational overhead
- Fast development iteration

**Cons**:
- Limited concurrent write support
- No built-in user management
- Less ecosystem support vs PostgreSQL
- Potential scalability limits for concurrent users
- No network access by default

### Option 2: PostgreSQL Only

**Description**: Use PostgreSQL as single database for all storage needs.

**Pros**:
- Mature ecosystem and tooling
- Excellent concurrent access support
- Built-in user management and security
- JSON support for flexible schemas
- Full ACID compliance
- Extensive extension ecosystem

**Cons**:
- Row-based storage less optimal for analytics
- More complex deployment and management
- Higher resource requirements
- Slower for analytical workloads
- Less optimal compression for time-series

### Option 3: Hybrid Approach (DuckDB + PostgreSQL)

**Description**: Use both databases for their optimal use cases:
- **DuckDB**: Analytics data warehouse, time-series storage
- **PostgreSQL**: Metadata, user management, configurations

**Pros**:
- Right tool for each workload
- Optimal performance for both analytics and transactions
- Clear separation of concerns
- Independent scaling strategies
- Best of both worlds

**Cons**:
- Increased system complexity
- Two databases to manage
- Potential data synchronization issues
- Higher learning curve
- More complex backup/recovery

## Decision

**Chosen Option**: **Option 3 - Hybrid Approach (DuckDB + PostgreSQL)**

### Rationale

The hybrid approach provides the best balance of performance, scalability, and maintainability for our specific use case:

1. **Performance Optimization**:
   - DuckDB's columnar storage is ideal for our analytics-heavy workload
   - PostgreSQL handles transactional operations efficiently

2. **Clear Workload Separation**:
   - **DuckDB Workloads**: Time-series analysis, aggregations, data warehouse operations, dashboard queries
   - **PostgreSQL Workloads**: User authentication, metadata cataloging, API keys, audit logging

3. **Scalability Path**:
   - DuckDB can be optimized independently for analytics performance
   - PostgreSQL can be scaled for user management as system grows

4. **Development Simplicity**:
   - Each database used for its strengths
   - Clear architectural boundaries

## Implementation Strategy

### Phase 1: DuckDB Implementation (Days 1-2)
```python
# Core DuckDB schema
CREATE TABLE datasets (
    dataset_id VARCHAR PRIMARY KEY,
    name VARCHAR,
    category VARCHAR,
    last_updated TIMESTAMP,
    volume_mb DECIMAL,
    quality_score DECIMAL
);

CREATE TABLE time_series_data (
    dataset_id VARCHAR,
    territorio VARCHAR,
    tempo DATE,
    dimension_values JSON,
    measure_value DECIMAL,
    quality_flags VARCHAR
);

# Indexes for performance
CREATE INDEX idx_dataset_time ON time_series_data(dataset_id, tempo);
CREATE INDEX idx_territorio ON time_series_data(territorio);
```

### Phase 2: PostgreSQL Integration (Days 3-4)
```sql
-- Metadata and user management
CREATE TABLE users (
    user_id SERIAL PRIMARY KEY,
    username VARCHAR UNIQUE,
    email VARCHAR,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE dataset_metadata (
    dataset_id VARCHAR PRIMARY KEY,
    description TEXT,
    source_url VARCHAR,
    last_check TIMESTAMP,
    metadata JSONB
);

CREATE TABLE api_keys (
    key_id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(user_id),
    key_hash VARCHAR,
    permissions JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);
```

### Phase 3: Integration Layer (Days 5-6)
```python
# Storage adapter pattern
class StorageAdapter(ABC):
    @abstractmethod
    def save_dataset(self, dataset_id: str, data: pd.DataFrame): pass

class DuckDBAdapter(StorageAdapter):
    """Analytics-optimized storage"""
    def save_dataset(self, dataset_id: str, data: pd.DataFrame):
        # Optimized for time-series analytics
        pass

class PostgresAdapter(StorageAdapter):
    """Metadata and configuration storage"""
    def save_metadata(self, dataset_id: str, metadata: dict):
        # Transactional metadata operations
        pass
```

## Consequences

### Positive
- **Performance**: Optimal for both analytics and transactions
- **Scalability**: Independent scaling strategies
- **Maintainability**: Clear separation of concerns
- **Flexibility**: Can optimize each database independently
- **Future-proofing**: Architecture supports growth

### Negative
- **Complexity**: Two databases to manage and monitor
- **Development overhead**: Need adapters/abstraction layers
- **Backup strategy**: Must coordinate backup across both systems
- **Debugging**: Potential issues span multiple systems

### Neutral
- **Learning curve**: Team needs to understand both technologies
- **Deployment**: Slightly more complex deployment pipeline

## Monitoring & Success Metrics

### Performance Targets
- Dashboard load time: <2 seconds
- Analytical queries: <500ms for aggregated data
- Bulk operations: <30 seconds for 50MB datasets
- Concurrent users: 10+ simultaneous

### Key Performance Indicators
- Query response times (by type)
- Database sizes and growth rates
- Error rates and availability
- User satisfaction with dashboard performance

## Compliance & Security

### Data Security
- **DuckDB**: File-level encryption for sensitive analytics data
- **PostgreSQL**: Row-level security for user data
- **Backup**: Encrypted backups for both systems

### Compliance
- **GDPR**: User data in PostgreSQL with proper deletion capabilities
- **Data retention**: Automated archival policies in DuckDB

## Migration Plan

### From Current File-Based System
1. **Parallel operation**: New system runs alongside file-based for validation
2. **Gradual migration**: Move datasets to DuckDB incrementally
3. **Validation period**: 2-week validation with both systems
4. **Cutover**: Switch dashboard to database-backed system
5. **Cleanup**: Remove file-based storage after validation

### Rollback Strategy
- **File backup**: Maintain file exports during transition
- **Quick rollback**: Can revert to file-based in <1 hour
- **Data validation**: Automated comparison tools for data integrity

## Related Decisions

- **[Future ADR-002]**: API Authentication Strategy
- **[Future ADR-003]**: Caching Strategy
- **[Future ADR-004]**: Backup and Recovery Strategy

## References

- **[Data Format Analysis](../api-mapping.md)**: Detailed analysis of ISTAT data characteristics
- **[DuckDB Documentation](https://duckdb.org/docs/)**: Official DuckDB documentation
- **[PostgreSQL Best Practices](https://wiki.postgresql.org/wiki/Don%27t_Do_This)**: PostgreSQL optimization guidelines
- **[ISTAT API Documentation](https://www.istat.it/en/methods-and-tools/statistical-data-transmission)**: Source data specifications

---

**Last Updated**: 20 Luglio 2025
**Next Review**: 30 Luglio 2025 (after initial implementation)
**Status**: ✅ **Ready for Implementation**
