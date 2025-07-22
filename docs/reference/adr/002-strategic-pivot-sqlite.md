# ADR-002: Strategic Pivot to SQLite + DuckDB Architecture

**Status**: Accepted
**Date**: 2025-07-22
**Deciders**: Andrea Bozzo, @Gasta88
**Technical Story**: [Strategic Pivot Discussion](https://github.com/AndreaBozzo/Osservatorio/discussions)

## Summary

We are pivoting from the planned PostgreSQL + Docker architecture to a **SQLite + DuckDB** hybrid approach for metadata and analytics management respectively. This decision prioritizes pragmatism and immediate business value over architectural complexity.

## Context and Problem Statement

After completing Day 3 (DuckDB Performance Testing & Optimization) with outstanding results, we faced a strategic decision for Days 4-11:

### Original Plan (PostgreSQL + Docker)
- PostgreSQL for metadata management
- Docker containerization
- Complex setup and deployment
- Over-engineered for current scale

### Identified Issues
1. **Over-complexity**: Docker + PostgreSQL adds operational overhead
2. **Delayed Value**: Time spent on infrastructure vs. business features
3. **Scale Mismatch**: PostgreSQL overkill for <10 concurrent users
4. **Learning Curve**: Additional technologies for contributors

## Decision Drivers

### Key Insight from @Gasta88
**Critical contribution**: @Gasta88 provided the decisive insight that highlighted our architectural over-engineering. Their analysis showed that:

> "For a metadata layer handling configuration, API keys, and audit trails with <100 concurrent operations/minute, SQLite provides identical functionality with zero operational complexity. PostgreSQL benefits only materialize at enterprise scale (1000+ concurrent users), which we won't reach in 2025."

This insight crystallized our understanding that we were solving tomorrow's problems instead of today's needs.

### Technical Rationale
1. **Right-sized Architecture**: SQLite perfect for metadata scale
2. **Deployment Simplicity**: Single file databases, no servers
3. **Development Velocity**: Zero configuration overhead
4. **Migration Path**: Standard SQL enables easy PostgreSQL upgrade
5. **Performance Adequacy**: SQLite <10ms for metadata queries

### Business Value Focus
1. **Faster Time-to-Market**: Skip Docker complexity
2. **PowerBI Integration**: Focus on core business value
3. **Italian Data Expertise**: Leverage ISTAT API specialization
4. **Contributor Accessibility**: Lower barrier to entry

## Considered Options

### Option A: Continue PostgreSQL + Docker (Rejected)
- **Pros**: "Industry standard", scalable from day 1
- **Cons**: Over-engineered, complex deployment, delayed value
- **Time Cost**: 3-4 days on infrastructure

### Option B: SQLite + DuckDB Hybrid (Selected)
- **Pros**: Right-sized, zero configuration, immediate value
- **Cons**: Future migration needed if >10 concurrent users
- **Time Cost**: 1-2 days on infrastructure

### Option C: DuckDB-Only (Considered)
- **Pros**: Single technology, optimal for analytics
- **Cons**: Not optimized for OLTP operations (metadata)
- **Risk**: Performance issues for concurrent writes

## Decision Outcome

**Chosen Option**: SQLite + DuckDB Hybrid Architecture

### Architecture Design
```
┌─────────────────────┐     ┌─────────────────────┐
│   DuckDB Engine     │     │  SQLite Metadata    │
├─────────────────────┤     ├─────────────────────┤
│ • ISTAT Analytics   │     │ • Dataset Registry  │
│ • Time Series       │     │ • User Preferences  │
│ • Aggregations      │     │ • API Keys/Auth     │
│ • Performance Data  │     │ • Audit Logging     │
└─────────────────────┘     └─────────────────────┘
         ↓                           ↓
    ┌────────────────────────────────┐
    │   Unified Data Repository      │
    │   (Facade Pattern)             │
    └────────────────────────────────┘
```

### Implementation Strategy
- **Day 4**: SQLite metadata layer implementation
- **Day 5**: Unified data access pattern
- **Days 6-8**: PowerBI integration & FastAPI
- **Migration Path**: Documented PostgreSQL upgrade when needed

## Positive Consequences

### Immediate Benefits
- **Zero Configuration**: No database servers to manage
- **Simplified Deployment**: Copy files for backup/restore
- **Development Velocity**: Contributors can start immediately
- **Cost Efficiency**: No cloud database costs during development

### Technical Advantages
- **Performance**: SQLite <10ms for metadata, DuckDB >2k records/sec
- **Reliability**: Both technologies battle-tested in production
- **Standards Compliance**: Standard SQL ensures migration flexibility
- **Backup Strategy**: Simple file-based backup/restore

### Business Value
- **Faster MVP**: Focus on PowerBI integration vs. infrastructure
- **Lower Barrier**: Easier for Italian data analysts to contribute
- **BI-First Design**: Architecture optimized for business intelligence

## Negative Consequences

### Technical Limitations
- **Concurrent Writes**: SQLite write serialization (mitigated with queueing)
- **Scale Ceiling**: Manual migration needed at enterprise scale
- **Feature Gaps**: No built-in connection pooling (implemented in application)

### Future Technical Debt
- **Migration Complexity**: Eventually need PostgreSQL for enterprise features
- **Monitoring**: Custom monitoring vs. PostgreSQL native tools
- **Backup Strategy**: File-based vs. enterprise backup solutions

## Compliance and Monitoring

### Success Metrics
- **Performance**: SQLite queries <10ms, DuckDB analytics >2k records/sec
- **Reliability**: 99.9% uptime during development phase
- **Developer Experience**: Contributors can setup environment <5 minutes
- **Business Value**: PowerBI integration delivered by Day 8

### Review Triggers
1. **Concurrent Users**: >5 simultaneous users
2. **Data Volume**: >1M records in metadata
3. **Write Throughput**: >100 writes/minute
4. **Enterprise Features**: Need for advanced permissions/audit

### Migration Path
```sql
-- Documented upgrade path to PostgreSQL
-- All tables use standard SQL data types
-- Migration scripts prepared for schema transfer
-- Zero downtime migration strategy documented
```

## Implementation Notes

### Contributors Recognition
- **@Gasta88**: Strategic architecture insight and pragmatic analysis
- **Andrea Bozzo**: Architecture implementation and documentation

### Communication Plan
1. **Internal**: Update PROJECT_STATE.md with new roadmap
2. **Community**: GitHub Discussions post explaining decision
3. **Documentation**: ADR published and roadmap updated
4. **Sprint Adjustment**: Days 4-11 refocused on SQLite implementation

## References

- [Original Database Selection ADR-001](001-database-selection.md)
- [PROJECT_STATE.md v8.0.0](../project/PROJECT_STATE.md)
- [Performance Testing Results](../../core/PERFORMANCE.md)
- [@Gasta88 GitHub Profile](https://github.com/Gasta88)

---

**Decision Impact**: ⭐⭐⭐⭐⭐ (High - Strategic pivot)
**Implementation Effort**: 🔧🔧 (Medium - 7 days refactor)
**Business Value**: 💰💰💰💰💰 (Very High - Faster time-to-market)

*ADR-002 approved on 2025-07-22 by project maintainers*
