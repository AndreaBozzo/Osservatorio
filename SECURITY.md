# Security Policy - Osservatorio ISTAT

## 🛡️ Panoramica Sicurezza

Il progetto Osservatorio ISTAT implementa multiple layer di sicurezza per proteggere dati, API e utenti. Questa policy definisce le linee guida, i controlli implementati e le procedure di security response.

## 🔒 Controlli di Sicurezza Implementati

### Security Manager
Il sistema utilizza `SecurityManager` in `src/utils/security_enhanced.py`:

- **Path Validation**: Protezione contro directory traversal
- **Rate Limiting**: Controllo accessi API (ISTAT: 50 req/h, PowerBI: 100 req/h)
- **Input Sanitization**: Validazione e sanitizzazione input utente
- **IP Blocking**: Blocco IP per attività sospette
- **Password Hashing**: PBKDF2 per password sicure

### Circuit Breaker Pattern
Implementato in `src/utils/circuit_breaker.py`:
- Resilienza per chiamate API esterne
- Auto-recovery dopo fallimenti
- Monitoring stato servizi

### Secure File Operations
Tutte le operazioni file usano `SecurePathValidator`:
- Validazione estensioni file (whitelist)
- Prevenzione path traversal (`../`)
- Protezione nomi riservati Windows
- Validazione percorsi assoluti

## 🚨 Vulnerabilità e Mitigazioni

### Input Validation
**Rischi**: XSS, SQL Injection, Command Injection
**Mitigazioni**:
```python
# Automatic input sanitization
from src.utils.security_enhanced import security_manager
clean_input = security_manager.sanitize_input(user_input)

# Path validation
from src.utils.secure_path import SecurePathValidator
validator = SecurePathValidator()
safe_path = validator.validate_path(file_path)
```

### API Security
**Rischi**: Rate limiting bypass, unauthorized access
**Mitigazioni**:
- Rate limiting per endpoint (configurabile)
- HTTPS enforcement su tutte le chiamate
- Token validation per PowerBI
- OAuth per Tableau

### File System Security
**Rischi**: Directory traversal, file overwrites
**Mitigazioni**:
- Path validation su tutti i file operations
- Extension whitelist: `.json, .csv, .xlsx, .xml, .ps1`
- Base directory restrictions
- Temporary file management sicuro

## 🔍 Security Scanning

### Automated Scanning
Il progetto include scanning automatico:

```bash
# Security scan con Bandit
bandit -r src/ -f json -o security_report.json

# Dependency vulnerability scan
safety check --json --output safety_report.json

# Pre-commit security hooks
pre-commit run --all-files
```

### Manual Security Review
Checklist per review manuale:
- [ ] Nuove API endpoints validano input
- [ ] File operations usano SecurePathValidator
- [ ] Secrets non hardcoded nel codice
- [ ] HTTPS enforcement su external calls
- [ ] Proper error handling senza info leak

## 🚨 Vulnerability Response

### Severity Levels

#### CRITICAL (CVSS 9.0-10.0)
- Remote code execution
- Data breach con PII
- Admin privilege escalation
**Response**: Immediate patch + security advisory

#### HIGH (CVSS 7.0-8.9)
- Local privilege escalation
- Significant data exposure
- Authentication bypass
**Response**: 72h patch timeline

#### MEDIUM (CVSS 4.0-6.9)
- Information disclosure
- DoS attacks
- Input validation issues
**Response**: Next release cycle

#### LOW (CVSS 0.1-3.9)
- Minor information leaks
- Non-exploitable weaknesses
**Response**: Best effort in future releases

### Reporting Process

#### Per Vulnerabilità Critiche
1. **Email**: [inserire email sicurezza]
2. **Encrypted**: Usa PGP se possibile
3. **Information**: 
   - Descrizione dettagliata
   - Steps to reproduce
   - Potential impact
   - Suggested fix (if any)

#### Per Issues Meno Critiche
1. GitHub Security Advisory (preferred)
2. Private issue su GitHub
3. Email normale per low severity

### Response Timeline
- **Acknowledgment**: 24h
- **Initial assessment**: 72h
- **Fix timeline**: Based on severity
- **Public disclosure**: After fix released

## 🔐 Development Security Guidelines

### Code Security
```python
# ✅ Good: Input validation
def process_file(file_path):
    validator = SecurePathValidator()
    safe_path = validator.validate_path(file_path)
    return safe_open(safe_path)

# ❌ Bad: Direct file access
def process_file(file_path):
    return open(file_path)  # Vulnerable to path traversal
```

### API Security
```python
# ✅ Good: Rate limiting
@security_manager.rate_limit('istat_api')
def call_istat_api():
    return requests.get(url, verify=True)  # HTTPS

# ❌ Bad: No rate limiting
def call_istat_api():
    return requests.get(url, verify=False)  # HTTP + no rate limit
```

### Environment Variables
```bash
# ✅ Good: Use environment variables
POWERBI_CLIENT_SECRET=your_secret

# ❌ Bad: Hardcoded secrets
client_secret = "actual_secret_here"
```

### Logging Security
```python
# ✅ Good: Safe logging
logger.info(f"Processing file: {filename}")

# ❌ Bad: Sensitive data in logs
logger.info(f"API key: {api_key}")  # Never log secrets
```

## 🛠️ Security Tools Configuration

### Bandit Configuration
File `.bandit`:
```yaml
skips: ['B101']  # Skip assert_used (test files)
exclude_dirs: ['tests', 'venv']
```

### Pre-commit Security Hooks
File `.pre-commit-config.yaml`:
```yaml
repos:
  - repo: https://github.com/PyCQA/bandit
    rev: '1.7.5'
    hooks:
      - id: bandit
        args: ['-r', 'src/']
  - repo: https://github.com/gitguardian/ggshield
    rev: v1.25.0
    hooks:
      - id: ggshield
        language: python
        stages: [commit]
```

### Safety Configuration
File `pyproject.toml`:
```toml
[tool.safety]
ignore = []  # Add CVE IDs to ignore if needed
```

## 📊 Security Monitoring

### Metrics da Monitorare
- Rate limiting triggers per IP
- Failed authentication attempts
- Suspicious file access patterns
- API error rates anomali
- Security scan results trends

### Automated Monitoring
```python
# Security metrics collection
from src.utils.security_enhanced import security_manager

# Get security stats
stats = security_manager.get_security_stats()
# {
#   'rate_limit_violations': 5,
#   'blocked_ips': ['192.168.1.100'],
#   'failed_authentications': 10
# }
```

### Security Alerts
Setup alerts per:
- Multiple rate limit violations
- New vulnerabilities in dependencies
- Failed security scans in CI/CD
- Suspicious access patterns

## ✅ Security Checklist

### Per Ogni Release
- [ ] Security scan passed (bandit + safety)
- [ ] Dependencies updated per vulnerabilities
- [ ] Manual security review per new features
- [ ] Secrets rotation se necessario
- [ ] Security documentation updated

### Per Nuove Features
- [ ] Input validation implementata
- [ ] Rate limiting considerato
- [ ] File operations use SecurePathValidator
- [ ] Error handling non leaka informazioni
- [ ] Tests di sicurezza inclusi

### Per Dependencies
- [ ] Security scan nuove dependencies
- [ ] Source code review se possibile
- [ ] Versioni pinned in requirements.txt
- [ ] Regular updates per security patches

## 📚 Security Training

### Risorse Raccomandate
- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [Python Security Best Practices](https://python.org/dev/security/)
- [Secure Coding Guidelines](https://wiki.sei.cmu.edu/confluence/display/seccode)

### Team Training
- Quarterly security awareness sessions
- Code review security guidelines
- Incident response procedures
- Tool training (bandit, safety, etc.)

## 📞 Contatti Security

- **Security Team**: [inserire contatti]
- **Emergency Response**: [inserire contatti 24/7]
- **PGP Keys**: [link a chiavi pubbliche]

## 📝 Policy Updates

Questa policy viene rivista ogni 6 mesi o dopo:
- Incident di sicurezza significativi
- Cambio architettura/tecnologie
- Update guidelines industry standard
- Feedback da security audits

**Last Updated**: 2025-01-20
**Next Review**: 2025-07-20
**Version**: 1.0
