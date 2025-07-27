# Security Policy

## 🛡️ Security Overview

La sicurezza è una priorità fondamentale per il progetto Osservatorio ISTAT Data Platform. Questo documento descrive le nostre politiche di sicurezza, come segnalare vulnerabilità e le best practices per sviluppatori.

## 🚨 Reporting Security Vulnerabilities

### How to Report

**🔴 NON aprire issue pubbliche per vulnerabilità di sicurezza.**

Per segnalare vulnerabilità di sicurezza:

1. **Email**: Invia una email a [security@osservatorio-istat.it](mailto:security@osservatorio-istat.it)
2. **GitHub Security**: Usa [GitHub Security Advisories](https://github.com/AndreaBozzo/Osservatorio/security/advisories)
3. **Private Disclosure**: Includi tutti i dettagli possibili per la riproduzione

### Response Timeline

| Timeframe | Action |
|-----------|--------|
| **24 hours** | Acknowledgment della segnalazione |
| **7 days** | Valutazione iniziale e severità |
| **30 days** | Fix development e testing |
| **60 days** | Release patch e disclosure coordinata |

## 🔒 Supported Versions

Le seguenti versioni ricevono aggiornamenti di sicurezza:

| Version | Supported | End of Life |
|---------|-----------|-------------|
| 10.x.x (FastAPI) | ✅ Yes | Active |
| 9.x.x (Streamlit) | ✅ Yes | 2024-12-31 |
| 8.x.x | ❌ No | 2024-06-30 |
| < 8.0 | ❌ No | End of Life |

## 🛡️ Security Architecture

### Authentication & Authorization

#### Security Features

- **JWT Authentication**: Secure token-based authentication
- **API Key Management**: Cryptographically secure API keys
- **Scope-Based Access**: Granular permission system
- **Rate Limiting**: DDoS protection and resource management
- **Audit Logging**: Comprehensive security event tracking

### Data Protection

#### At Rest
- **SQLite Encryption**: Sensitive data encrypted using AES-256
- **Configuration Security**: Secrets managed via environment variables
- **File Permissions**: Restrictive file system permissions

#### In Transit
- **HTTPS Only**: All API communications over TLS 1.2+
- **CORS Configuration**: Strict origin policies
- **Header Security**: Security headers (HSTS, CSP, etc.)

## 🔍 Security Testing

### Automated Security Scanning

```bash
# Dependency vulnerability scanning
pip-audit

# Code security analysis
bandit -r src/

# Docker security scanning (if applicable)
docker scan osservatorio:latest
```

### Manual Security Testing

#### Authentication Testing
```bash
# Test JWT token validation
curl -H "Authorization: Bearer invalid_token" \
     http://localhost:8000/datasets

# Test rate limiting
for i in {1..200}; do
  curl -H "Authorization: Bearer $TOKEN" \
       http://localhost:8000/datasets &
done
```

## 🔧 Security Configuration

### Environment Variables

```bash
# .env file - NEVER commit to git
SECRET_KEY=your-256-bit-secret-key
JWT_SECRET_KEY=your-jwt-secret-key
DATABASE_ENCRYPTION_KEY=your-db-encryption-key

# Optional security settings
SECURITY_HSTS_MAX_AGE=31536000
SECURITY_CONTENT_TYPE_OPTIONS=nosniff
SECURITY_FRAME_OPTIONS=DENY
```

## 🚨 Security Incidents

### Incident Response Plan

1. **Detection**: Automated monitoring e manual reports
2. **Assessment**: Valutazione severità e impatto
3. **Containment**: Isolamento del problema
4. **Eradication**: Rimozione della vulnerabilità
5. **Recovery**: Ripristino servizi sicuri
6. **Lessons Learned**: Post-incident review

## 🔐 Developer Security Guidelines

### Secure Coding Practices

#### Input Validation
```python
# Sempre validare input utente
def validate_dataset_id(dataset_id: str) -> str:
    if not re.match(r'^[A-Z0-9_]+$', dataset_id):
        raise ValueError("Invalid dataset ID format")
    return dataset_id
```

#### Secret Management
```python
# Mai hardcode secrets
# ❌ Bad
api_key = "sk-1234567890abcdef"

# ✅ Good
api_key = os.getenv("API_KEY")
if not api_key:
    raise ValueError("API_KEY environment variable required")
```

## 📊 Security Metrics

### Monitoring

- Failed authentication attempts per hour
- Rate limit violations per endpoint
- Invalid JWT tokens per day
- SQL injection attempts per request
- Abnormal request patterns (continuous)

### Alerting Thresholds

| Metric | Warning | Critical |
|--------|---------|----------|
| Failed auth attempts | >10/hour | >50/hour |
| Rate limit violations | >5/minute | >20/minute |
| Invalid JWT tokens | >20/day | >100/day |
| Error rate | >5% | >10% |

## 📚 Security Resources

### Documentation
- [OWASP API Security Top 10](https://owasp.org/www-project-api-security/)
- [FastAPI Security Best Practices](https://fastapi.tiangolo.com/tutorial/security/)
- [SQLite Security Guidelines](https://www.sqlite.org/security.html)

### Tools
- **Static Analysis**: `bandit`, `semgrep`
- **Dependency Scanning**: `pip-audit`, `safety`
- **Runtime Protection**: `rate-limiting`, `input-validation`

---

## 📞 Security Contact

- **Security Email**: [security@osservatorio-istat.it](mailto:security@osservatorio-istat.it)
- **Project Maintainer**: [Andrea Bozzo](https://github.com/AndreaBozzo)
- **Security Advisories**: [GitHub Security Tab](https://github.com/AndreaBozzo/Osservatorio/security)

**Remember: Security is everyone's responsibility! 🛡️**
