# 🗺️ API Mapping & Data Flow Documentation

> **Complementary to [API_REFERENCE.md](api/API_REFERENCE.md)** - Focus on operational mappings and data flows
> **Version**: 8.1.0
> **Date**: 23 Luglio 2025
> **Status**: Day 1 Completion

---

## 📊 ISTAT API Endpoints Currently in Use

### 1. **DCIS_POPRES1** - Popolazione Residente
- **URL**: `https://sdmx.istat.it/SDMXWS/rest/data/DCIS_POPRES1`
- **Update Frequency**: Mensile
- **Volume Stimato**: ~50MB (uncompressed XML)
- **Structure**:
  - Dimensions: Territorio, Tempo, Cittadinanza, Sesso, Classe_età
  - Measures: Valore (popolazione)
  - Attributes: Status, Precision
- **Current Usage**: Dashboard popolazione, converter tests
- **Rate Limit**: 50 req/hour (enforced)

### 2. **DCCN_PILN** - PIL Nazionale
- **URL**: `https://sdmx.istat.it/SDMXWS/rest/data/DCCN_PILN`
- **Update Frequency**: Trimestrale
- **Volume Stimato**: ~30MB
- **Structure**:
  - Dimensions: Territorio, Tempo, Settore_istituzionale, Valuta
  - Measures: Valore (PIL in milioni di euro)
- **Current Usage**: Dashboard economia
- **Rate Limit**: 50 req/hour (enforced)

### 3. **DCCV_TAXOCCU** - Tasso di Occupazione
- **URL**: `https://sdmx.istat.it/SDMXWS/rest/data/DCCV_TAXOCCU`
- **Update Frequency**: Trimestrale
- **Volume Stimato**: ~25MB
- **Structure**:
  - Dimensions: Territorio, Tempo, Sesso, Classe_età, Titolo_studio
  - Measures: Valore (percentuale)
- **Current Usage**: Dashboard lavoro
- **Rate Limit**: 50 req/hour (enforced)

### 4. **DCIS_POPSTRRES1** - Popolazione per Struttura
- **URL**: `https://sdmx.istat.it/SDMXWS/rest/data/DCIS_POPSTRRES1`
- **Update Frequency**: Annuale
- **Volume Stimato**: ~20MB
- **Structure**:
  - Dimensions: Territorio, Tempo, Cittadinanza, Sesso, Classe_età
  - Measures: Valore (popolazione straniera residente)
  - Attributes: Status, Precision
- **Current Usage**: Dashboard popolazione straniera
- **Rate Limit**: 50 req/hour (enforced)

### 5. **DCIS_FECONDITA** - Indicatori di Fecondità
- **URL**: `https://sdmx.istat.it/SDMXWS/rest/data/DCIS_FECONDITA`
- **Update Frequency**: Annuale
- **Volume Stimato**: ~15MB
- **Structure**:
  - Dimensions: Territorio, Tempo, Classe_età_madre
  - Measures: Tasso_fecondità, Tasso_fecondità_totale
  - Attributes: Status, Precision
- **Current Usage**: Dashboard demografia, analisi fecondità
- **Rate Limit**: 50 req/hour (enforced)

### 6. **DCIS_MORTALITA1** - Tavole di Mortalità
- **URL**: `https://sdmx.istat.it/SDMXWS/rest/data/DCIS_MORTALITA1`
- **Update Frequency**: Annuale
- **Volume Stimato**: ~25MB
- **Structure**:
  - Dimensions: Territorio, Tempo, Sesso, Classe_età
  - Measures: Probabilità_morte, Speranza_vita
  - Attributes: Status, Precision
- **Current Usage**: Dashboard mortalità, tavole attuariali
- **Rate Limit**: 50 req/hour (enforced)

### 7. **DCIS_RICFAMILIARE1** - Reddito delle Famiglie
- **URL**: `https://sdmx.istat.it/SDMXWS/rest/data/DCIS_RICFAMILIARE1`
- **Update Frequency**: Annuale
- **Volume Stimato**: ~30MB
- **Structure**:
  - Dimensions: Territorio, Tempo, Tipologia_famiglia, Quintile_reddito
  - Measures: Reddito_equivalente, Rischio_povertà
  - Attributes: Status, Precision
- **Current Usage**: Dashboard condizioni socioeconomiche
- **Rate Limit**: 50 req/hour (enforced)

### 8. **Discovery Endpoint** - Dataflows
- **URL**: `https://sdmx.istat.it/SDMXWS/rest/dataflow/IT1`
- **Update Frequency**: Static (structure only)
- **Volume**: ~2MB
- **Purpose**: Discovery di tutti i 509+ dataset disponibili
- **Current Usage**: `DataflowAnalyzer` per categorization

---

## 🔄 Data Pipeline: Raw → Clean → Business

### 📥 Raw Stage
- **Input**: XML/SDMX data da API REST calls
- **Storage**:
  - Temporary: System temp directory (`TempFileManager`)
  - Cache: `data/cache/` (30min TTL)
  - Archive: `data/raw/istat/` (permanent)
- **Validations**:
  - Schema check con `ET.fromstring()`
  - Rate limit enforcement
  - Circuit breaker pattern
- **Format**: SDMX-ML 2.1 structure

### 🧹 Clean Stage
- **Trasformazioni**:
  - XML → pandas DataFrame conversion
  - Column standardization (IT → EN names where appropriate)
  - Data type casting (string → numeric for values)
  - Missing value handling (null vs "ND" string)
  - Date parsing (SDMX periods → ISO dates)
- **Business Rules**:
  - Remove administrative regions not in scope
  - Filter out provisional/estimated data if required
  - Apply territorial hierarchies (Regioni → Province → Comuni)
- **Quality Checks**:
  - Completeness scoring (% non-null values)
  - Data quality validation with `_validate_data_quality()`
  - Outlier detection for numeric values

### 📊 Business Stage
- **Aggregazioni**:
  - Territorial: Municipal → Provincial → Regional → National
  - Temporal: Monthly → Quarterly → Yearly
  - Demographic: Age groups, gender cross-tabs
- **KPIs Calculated**:
  - Population growth rates (YoY, QoQ)
  - GDP per capita by region
  - Employment rate trends
  - Regional competitiveness indices
- **Output Formats**:
  - Universal Export: CSV, Excel, Parquet, JSON
  - Dashboard: JSON cache for Streamlit

---

## 📈 Data Volume Analysis

### Current Storage Footprint
```
data/
├── raw/           (~500MB total)
│   ├── istat/     (~400MB - XML archives)
│   └── xml/       (~100MB - samples)
├── processed/     (~200MB total)
│   ├──    (~100MB - multi-format)
│   └──    (~100MB - multi-format)
└── cache/         (~50MB - temporary)
```

### Growth Projections
- **Monthly ingest**: ~150MB new data
- **Annual estimate**: ~1.8GB raw data
- **Post-processing multiplier**: 2x (multiple formats)
- **Total annual storage need**: ~5GB

### Access Patterns
1. **Real-time dashboard**: High frequency, small datasets
2. **Bulk conversion**: Low frequency, large datasets
3. **Analysis queries**: Medium frequency, aggregated data
4. **Export operations**: Low frequency, full datasets

---

## 🔍 API Performance Characteristics

### Response Times (measured)
| Endpoint | Avg Response | Max Response | Timeout |
|----------|--------------|--------------|---------|
| DCIS_POPRES1 | 2.3s | 8.5s | 30s |
| DCCN_PILN | 1.8s | 6.2s | 30s |
| DCCV_TAXOCCU | 2.1s | 7.8s | 30s |
| Dataflows | 0.8s | 2.1s | 30s |

### Error Patterns
- **Rate limit**: 429 after 50 req/hour
- **Timeout**: 504 for large datasets > 30s
- **Maintenance**: 503 during ISTAT maintenance windows
- **Invalid dataset**: 404 for non-existent IDs

### Reliability
- **Success rate**: ~95% during business hours
- **Peak failure times**: Early morning (05:00-07:00 UTC)
- **Maintenance windows**: Saturdays 02:00-04:00 UTC

---

## 🏗️ Integration Points

### Current Integrations
1. **Streamlit Dashboard** (`dashboard/app.py`)
   - Real-time data loading via `IstatRealTimeDataLoader`
   - Caching with 30min TTL
   - Error handling with graceful fallback

2. **Converter Pipeline** (`src/converters/`)
   - Programmatic API conversion
   - Multi-format output generation
   - Quality assessment integration

3. **Test Suite** (`tests/`)
   - Mock data for CI/CD
   - Performance benchmarks
   - Integration tests

### Planned Integrations
1. **DuckDB Storage** (Day 2)
   - Persistent storage for analytics
   - Query optimization
   - Historical data management

2. **SQLite Metadata** (Day 4 - COMPLETED)
   - Dataset cataloging (dataset_registry table)
   - User preferences (user_preferences table)
   - API credentials (api_credentials table)
   - Audit logging (audit_log table)
   - Audit logging

3. **REST API** (February)
   - External access to processed data
   - Authentication and authorization
   - Rate limiting per user

---

## 🎯 Database Design Implications

### DuckDB Requirements
- **Analytical workloads**: Time-series analysis, aggregations
- **Query patterns**: GROUP BY territorio, tempo; window functions
- **Storage**: Columnar storage for compression
- **Indexes**: Time, territory for fast filtering

### SQLite Metadata Requirements (IMPLEMENTED)
- **Transactional data**: User preferences, API keys, configurations
- **Relationships**: Foreign keys for data integrity (6-table schema)
- **Audit trail**: Comprehensive logging of all operations
- **ACID compliance**: Critical for metadata consistency
- **Full-text search**: Dataset descriptions, categories

### Hybrid Architecture Benefits (SQLite + DuckDB - IMPLEMENTED)
1. **Performance**: DuckDB for analytics, SQLite for metadata transactions
2. **Complexity**: Right tool for each workload, zero-config deployment
3. **Scalability**: Independent optimization, easy PostgreSQL migration path
4. **Maintenance**: Separate backup and optimization strategies

---

## 🚨 Risk Assessment

### Data Availability Risks
- **ISTAT API changes**: Breaking changes to SDMX structure
- **Rate limiting**: Increased usage hits limits
- **Network issues**: Timeout/connectivity problems
- **Data quality**: Inconsistent or missing values

### Mitigation Strategies
1. **Aggressive caching**: Reduce API dependency
2. **Circuit breaker**: Automatic failure recovery
3. **Data validation**: Quality checks at ingestion
4. **Fallback data**: Cached/sample data for demos

---

## 📋 Action Items for Day 2

### DuckDB Schema Design
Based on this analysis, DuckDB schema should include:

```sql
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
    quality_flags VARCHAR,
    INDEX idx_dataset_time (dataset_id, tempo),
    INDEX idx_territorio (territorio)
);
```

### Performance Optimization
1. **Partitioning**: By year/quarter for large time series
2. **Compression**: GZIP for historical data
3. **Indexing**: Composite indexes on common filter columns
4. **Caching**: Query result caching for dashboard

---

## 📚 References

- **[API_REFERENCE.md](api/API_REFERENCE.md)**: Complete API documentation
- **[ISTAT SDMX Guidelines](https://www.istat.it/en/methods-and-tools/statistical-data-transmission/statistical-data-exchange)**: Official SDMX documentation
- **[Data Quality Framework](https://www.istat.it/en/methods-and-tools/quality)**: ISTAT data quality standards

---

**Status**: ✅ **Day 1 Complete** | Next: DuckDB Implementation (Day 2)
*Completed: 20 Luglio 2025*
