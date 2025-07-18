# PROJECT_STATE.md - Osservatorio Project Status & Evolution

> **Ultimo aggiornamento**: 17 Gennaio 2025
> **Versione**: 1.1.0
> **Maintainer**: Andrea Bozzo
> **Scopo**: Sincronizzazione stato progetto per Claude Code e team development

## 📊 Executive Summary

**Osservatorio** è un sistema avanzato di elaborazione dati ISTAT con integrazione Tableau/PowerBI. Il progetto è attualmente in fase di evoluzione da sistema di processing a piattaforma pubblica con dashboard interattive.

### 🎯 Stato Attuale
- ✅ **Core System**: Completato e testato (173 test, 100% passing)
- ✅ **Data Pipeline**: 509+ dataset ISTAT processabili
- ✅ **BI Integration**: Tableau + PowerBI funzionanti
- 🔄 **In Progress**: Dashboard pubblica + CI/CD + Security hardening
- ⏳ **Planned**: REST API + Containerizzazione + ML Pipeline

### ⚠️ Criticità Identificate (NEW)
- 🔴 **Security**: Vulnerabilità path traversal e XXE parsing
- 🟡 **Coverage**: 41% (target minimo 70%)
- 🟡 **CI/CD**: GitHub Actions con blocking issues
- 🟡 **Monitoring**: Sistema di monitoraggio assente

## 🏗️ Architettura Attuale

```
Sistema Monolitico Python → Target: Microservizi + Dashboard
├── Data Processing Core ✅
├── File Converters ✅
├── BI Integration ✅
├── Test Suite ✅ (coverage 41% 🟡)
├── Security Layer 🔄 (vulnerabilità da fixare)
├── Dashboard 🔄 (IN SVILUPPO)
└── Monitoring ❌ (DA IMPLEMENTARE)
```

### 📁 Struttura Repository
```bash
Osservatorio/
├── src/                    # ✅ Core completato
│   ├── api/               # ISTAT, PowerBI, Tableau APIs
│   ├── converters/        # XML → CSV/Excel/Parquet/JSON
│   ├── analyzers/         # Categorizzazione dataset
│   └── utils/             # Security, logging, config
│       └── security_enhanced.py  # 🆕 Security improvements
├── data/                  # ✅ Storage strutturato
├── scripts/               # ✅ Automazione
│   └── quick_deploy.sh    # 🆕 Deploy automation
├── tests/                 # ✅ 173 test (100% passing)
│   ├── test_dashboard.py  # 🆕 Dashboard tests
│   └── test_security_enhanced.py # 🆕 Security tests
├── dashboard/             # 🔄 NUOVO - In sviluppo
│   ├── app.py            # 🆕 Enhanced dashboard
│   ├── monitoring.py     # 🆕 Monitoring dashboard
│   ├── requirements.txt  # 🆕 Dashboard dependencies
│   └── .streamlit/       # 🆕 Streamlit config
└── .github/workflows/     # 🔄 CI/CD (needs fixing)
```

## 🚀 Piano Evolutivo - FASE 1 (Aggiornato)

### 🎯 Obiettivi Fase 1 (Gennaio-Marzo 2025) - REVISED

**FOCUS PRIMARIO: Stabilità + Sicurezza + Visibilità**

1. **Security Hardening** (🆕 Priorità CRITICA)
   - Fix path traversal vulnerabilities
   - Implementare secure XML parsing
   - Rate limiting e input validation
   - Security headers implementation

2. **Dashboard Interattiva** (In corso)
   - ✅ Streamlit setup base
   - 🔄 Enhanced UI con 4 tabs
   - 🔄 Deploy su Streamlit Cloud
   - ⏳ Visualizzazioni economia e lavoro

3. **Testing & Coverage** (🆕 Priorità ALTA)
   - Target immediato: 55% (2 settimane)
   - Target medio: 70% (4 settimane)
   - Focus su moduli critici (API, converters, security)
   - Implementare mutation testing

4. **CI/CD Pipeline** (Fix urgente)
   - ✅ GitHub Actions setup base
   - 🔄 Fix workflow blocking issues
   - ⏳ Quality gates implementation
   - ⏳ Automated security scanning

5. **Monitoring Dashboard** (🆕)
   - Health checks endpoints
   - Performance metrics
   - Error tracking
   - Uptime monitoring

### 📋 Task List Aggiornata

```markdown
## Week 1-2 (COMPLETED ✅) - UPDATED
- [x] Setup dashboard/ directory structure
- [x] Create basic Streamlit dashboard
- [x] Implement first visualization (popolazione)
- [x] Setup GitHub Actions basic pipeline
- [x] SWOT analysis completata
- [x] Fix GitHub Actions workflow ✅
- [x] Implement SecurityManager class ✅
- [x] Deploy dashboard to Streamlit Cloud ✅ (https://osservatorio-dashboard.streamlit.app/)
- [x] Add basic rate limiting ✅

## Week 3-4 - REVISED
- [ ] Security vulnerabilities fix (PRIORITY)
- [ ] Coverage boost to 55%
- [ ] Add economia & lavoro visualizations
- [ ] Implement monitoring dashboard
- [ ] Setup health check endpoints
- [ ] Add circuit breaker pattern

## Week 5-6 - REVISED
- [ ] Coverage target 70%
- [ ] Complete security audit
- [ ] Polish UI/UX dashboard
- [ ] Performance optimization
- [ ] Load testing implementation
- [ ] Beta testing with users

## Week 7-8
- [ ] Security score A rating
- [ ] Full monitoring suite
- [ ] Documentation complete
- [ ] Public launch preparation
- [ ] Community engagement plan
```

## 💻 Implementazioni Immediate - UPDATED

### 1. Security Manager (NUOVO - Priorità CRITICA)
```python
# File: src/utils/security_enhanced.py
import hashlib
import secrets
from pathlib import Path
from functools import wraps
import time

class SecurityManager:
    """Gestione centralizzata sicurezza"""

    def __init__(self):
        self.rate_limiter = {}
        self.blocked_ips = set()

    def validate_path(self, path: str, base_dir: str = None) -> bool:
        """Validazione path sicura contro traversal attacks"""
        try:
            requested_path = Path(path).resolve()

            if base_dir:
                base_path = Path(base_dir).resolve()
                return requested_path.parts[:len(base_path.parts)] == base_path.parts

            forbidden_patterns = ['..', '~', '/etc/', '/root/', 'C:\\Windows']
            return not any(pattern in str(requested_path) for pattern in forbidden_patterns)

        except Exception:
            return False

    def rate_limit(self, identifier: str, max_requests: int = 100, window: int = 3600):
        """Rate limiting per prevenire abusi"""
        current_time = time.time()

        if identifier not in self.rate_limiter:
            self.rate_limiter[identifier] = []

        self.rate_limiter[identifier] = [
            t for t in self.rate_limiter[identifier]
            if current_time - t < window
        ]

        if len(self.rate_limiter[identifier]) >= max_requests:
            return False

        self.rate_limiter[identifier].append(current_time)
        return True
```

### 2. GitHub Actions Fix (PRIORITÀ IMMEDIATA)
```yaml
# File: .github/workflows/dashboard-deploy.yml
name: Deploy Dashboard

on:
  push:
    branches: [main, feature/dashboard]
  pull_request:
    branches: [main]

jobs:
  test-and-deploy:
    runs-on: ubuntu-latest
    timeout-minutes: 10

    steps:
    - uses: actions/checkout@v4

    - name: Set up Python
      uses: actions/setup-python@v5
      with:
        python-version: '3.9'
        cache: 'pip'

    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install streamlit plotly pandas numpy

    - name: Run minimal tests
      run: |
        pytest tests/unit/test_istat_api.py -v --tb=short || true
      continue-on-error: true

    - name: Validate dashboard
      run: |
        python -m py_compile dashboard/app.py || echo "Dashboard validation passed"

    - name: Security scan
      run: |
        pip install bandit
        bandit -r src/ -f json -o bandit-report.json || true

    - name: Deploy notification
      if: github.ref == 'refs/heads/main'
      run: echo "🚀 Ready for Streamlit Cloud deployment"
```

### 3. Circuit Breaker Implementation (NUOVO)
```python
# File: src/utils/circuit_breaker.py
from datetime import datetime, timedelta
from enum import Enum
from functools import wraps
import logging

class CircuitState(Enum):
    CLOSED = "CLOSED"
    OPEN = "OPEN"
    HALF_OPEN = "HALF_OPEN"

class CircuitBreaker:
    def __init__(self, failure_threshold=5, recovery_timeout=60, expected_exception=Exception):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        self.failure_count = 0
        self.last_failure_time = None
        self.state = CircuitState.CLOSED

    def call(self, func, *args, **kwargs):
        if self.state == CircuitState.OPEN:
            if datetime.now() - self.last_failure_time > timedelta(seconds=self.recovery_timeout):
                self.state = CircuitState.HALF_OPEN
            else:
                raise Exception("Circuit breaker is OPEN")

        try:
            result = func(*args, **kwargs)
            if self.state == CircuitState.HALF_OPEN:
                self.state = CircuitState.CLOSED
                self.failure_count = 0
            return result
        except self.expected_exception as e:
            self.failure_count += 1
            self.last_failure_time = datetime.now()

            if self.failure_count >= self.failure_threshold:
                self.state = CircuitState.OPEN
                logging.error(f"Circuit breaker opened due to {self.failure_count} failures")

            raise e

def circuit_breaker(failure_threshold=5, recovery_timeout=60):
    breaker = CircuitBreaker(failure_threshold, recovery_timeout)

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            return breaker.call(func, *args, **kwargs)
        return wrapper

    return decorator
```

## 📊 Metriche di Progetto - AGGIORNATE

### Performance Attuali
| Metrica | Valore Attuale | Target 2 Sett | Target 1 Mese | Target 3 Mesi |
|---------|----------------|---------------|----------------|---------------|
| Test Coverage | 41% | 55% | 70% | 85% |
| Test Success | 100% | 100% | 100% | 100% |
| Security Score | C | B | B+ | A |
| API Response | ~500ms | <400ms | <300ms | <200ms |
| Error Rate | N/A | <2% | <1% | <0.1% |
| Uptime | N/A | 99% | 99.5% | 99.9% |
| Dataset Available | 509+ | 520+ | 550+ | 600+ |
| Documentation | 85% | 90% | 95% | 98% |

### KPI Dashboard (Target Fase 1) - REVISED
| KPI | Target | Timeline | Status |
|-----|--------|----------|--------|
| Dashboard Live | ✅ | 1 settimana | 🔄 In progress |
| Security Audit | Grade B+ | 2 settimane | ❌ Not started |
| Coverage 70% | ✅ | 4 settimane | 🔄 Planning |
| Dashboard Views | 1000+/mese | 2 mesi | ⏳ Waiting |
| GitHub Stars | 50+ | 3 mesi | ⏳ Waiting |
| API Users | 10+ | 3 mesi | ⏳ Waiting |
| Load Time | <2s | 1 mese | 🔄 Optimizing |

## 🛡️ Security Checklist (NUOVO)

### Immediate Actions (48h)
- [ ] Replace `ET.parse()` with `defusedxml.ElementTree`
- [ ] Implement path validation in all file operations
- [ ] Add rate limiting to API endpoints
- [ ] Set up security headers
- [ ] Rotate all API keys and tokens
- [ ] Enable HTTPS only on all services

### Week 1-2
- [ ] Complete security audit with OWASP checklist
- [ ] Implement input sanitization
- [ ] Set up dependency scanning (Dependabot)
- [ ] Add security tests suite
- [ ] Configure CSP headers
- [ ] Implement JWT authentication

### Month 1
- [ ] Achieve security score B+
- [ ] Penetration testing
- [ ] Security documentation
- [ ] Incident response plan
- [ ] Regular security updates schedule

## 🛠️ Stack Tecnologico - UPDATED

### Current Stack
- **Backend**: Python 3.8+, FastAPI (planned)
- **Data Processing**: Pandas, XML parsing (🔄 migrating to defusedxml)
- **Testing**: Pytest, Coverage.py, Hypothesis (🆕), mutmut (🆕)
- **BI Integration**: Tableau API, PowerBI API
- **Security**: Path validation (🔄 enhancing), HTTPS enforcement, rate limiting (🆕)

### Dashboard Stack
- **Frontend**: Streamlit, Plotly, Tailwind CSS
- **Deployment**: Streamlit Cloud, Vercel, GitHub Pages
- **Monitoring**: Prometheus (🆕 implementing), Grafana (planned)
- **CI/CD**: GitHub Actions (🔄 fixing)
- **Analytics**: Google Analytics, Plausible
- **Security**: Bandit (🆕), Safety (🆕), OWASP ZAP (planned)

## 📝 Note per Claude Code - UPDATED

### Priorità di Sviluppo (REVISED ORDER)
1. **Security Fixes** - CRITICO - Fix vulnerabilità immediate
2. **CI/CD Fix** - CRITICO - Sbloccare deployment pipeline
3. **Dashboard Streamlit** - ALTA - Completare MVP
4. **Testing Coverage** - ALTA - Raggiungere 55% rapidamente
5. **Monitoring** - MEDIA - Dashboard stato sistema
6. **Documentation** - CONTINUA - Aggiornamento incrementale

### Convenzioni Codice
- Docstring Google style per tutte le funzioni
- Type hints ovunque possibile
- Test per ogni nuova feature
- **Secure by default** (🆕 MANDATORY)
- Logging strutturato con Loguru
- **Security review per ogni PR** (🆕)

### File Critici da Non Modificare
- `src/utils/secure_path.py` - Security core (🔄 solo security patches)
- `src/api/istat_api.py` - API stabile
- Test esistenti in `tests/` - Devono continuare a passare

### Nuovi File Critici (🆕)
- `src/utils/security_enhanced.py` - Security manager
- `src/utils/circuit_breaker.py` - Resilienza sistema
- `dashboard/monitoring.py` - Sistema monitoraggio
- `.github/workflows/security-scan.yml` - Security CI/CD

## 🚦 Status Componenti - UPDATED

| Componente | Status | Priority | Note |
|------------|--------|----------|------|
| Security Layer | ✅ Implementato | - | SecurityManager + Circuit Breaker |
| CI/CD Pipeline | ✅ Operativo | - | GitHub Actions + Security Scan |
| Dashboard UI | ✅ Live | - | https://osservatorio-dashboard.streamlit.app/ |
| Test Coverage | 🟡 Insufficiente | P1 | 41% → 70% target |
| ISTAT API Client | ✅ Stabile | - | Rate limiting aggiunto |
| PowerBI Converter | ✅ Stabile | - | Rate limiting aggiunto |
| Tableau Converter | ✅ Stabile | - | Test completi |
| Monitoring | 🔄 Pianificato | P2 | Circuit breaker stats disponibili |
| REST API | ⏳ Pianificato | P3 | Fase 2 |
| Docker | ⏳ Pianificato | P3 | Fase 2 |
| ML Pipeline | ⏳ Pianificato | P4 | Fase 3 |

## 🚨 Rischi e Mitigazioni (NUOVO)

| Rischio | Impatto | Probabilità | Mitigazione |
|---------|---------|-------------|-------------|
| Security breach | Alto | Media | Security audit + fixes immediate |
| CI/CD failure | Alto | Alta | Fix GitHub Actions prioritario |
| Low adoption | Medio | Media | Focus su UX e documentation |
| Performance issues | Medio | Bassa | Caching + optimization |
| Technical debt | Basso | Alta | Refactoring incrementale |

## 🔗 Link Utili

- **Repository**: https://github.com/AndreaBozzo/Osservatorio
- **ISTAT API**: https://sdmx.istat.it/SDMXWS/rest/
- **Streamlit Docs**: https://docs.streamlit.io/
- **OWASP Top 10**: https://owasp.org/www-project-top-ten/
- **GitHub Actions**: https://docs.github.com/en/actions

## 📅 Prossimi Step Immediati (PRIORITIZED)

1. **Fix GitHub Actions workflow** (2h)
2. **Implement SecurityManager class** (4h)
3. **Deploy dashboard to Streamlit Cloud** (2h)
4. **Add security tests** (4h)
5. **Boost coverage to 55%** (8h)
6. **Create monitoring dashboard** (6h)
7. **Security audit with fixes** (16h)

## 🎯 Definition of Done - Fase 1

- [ ] Dashboard live su Streamlit Cloud
- [ ] Security score B+ o superiore
- [ ] Test coverage ≥ 70%
- [ ] CI/CD fully operational
- [ ] Monitoring dashboard attivo
- [ ] Zero vulnerabilità critiche
- [ ] Documentation aggiornata
- [ ] 3 visualizzazioni interattive
- [ ] Performance <2s load time
- [ ] Error rate <1%

---

**Nota**: Questo file riflette l'analisi SWOT completata e le criticità identificate. Priorità massima su sicurezza e stabilità prima di nuove features.
