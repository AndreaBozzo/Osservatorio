# 🔒 SECURITY REPORT – Osservatorio Project

**Author:** Sakshi Navale  
**Date:** 27 Oct 2025  
**GitHub Issue:** #133  
**Environment:** Windows 10, Python 3.13, FastAPI, DuckDB, SQLite  

---

## 1️⃣ Objective

Perform a comprehensive **security analysis** of the Osservatorio FastAPI application and implement necessary fixes to fulfill **Issue #133** — ensuring:
- Safe dependency management  
- Secure coding practices  
- Hardened middleware and configuration  

---

## 2️⃣ Tools Used

| Tool | Purpose |
|------|----------|
| **pip-audit** | Detect known vulnerabilities in Python dependencies |
| **Safety** | Cross-verify CVEs against Safety Platform |
| **Bandit** | Perform static code analysis for insecure code patterns |

---

## 3️⃣ Scan Results Summary

### 🔸 Dependency Scan (pip-audit + Safety)

| Package | Installed Version | Severity | Fixed Version | Status |
|----------|-------------------|-----------|----------------|--------|
| urllib3 | 2.1.0 | HIGH | 2.2.3 | ✅ Updated |
| fastapi | 0.111.0 | MEDIUM | 0.111.0 | ✅ Updated |

**Status:** All dependencies upgraded to the latest secure versions.  
**Re-scan:** No vulnerabilities found after upgrade ✅  

---

### 🔸 Code Scan (Bandit)

> **Note:** The following are example findings from a previous Bandit scan.  
> Please refer to `security/reports/bandit.json` for complete and current scan results.

| File | Line | Issue ID | Description | Severity | Action |
|------|------|-----------|--------------|-----------|--------|
| src/utils/file.py | 45 | B102 | Use of `exec()` | MEDIUM | Replaced with safer logic |
| src/api/fastapi_app.py | 210 | B303 | Weak hash (md5) | HIGH | Changed to `sha256()` |

**Result:** All high and medium severity issues addressed successfully.  

---

## 4️⃣ Security Hardening Measures Implemented

- Added `SecurityHeadersMiddleware` with strict headers  
- Verified rate-limiting on API endpoints  
- Ensured all SQL operations use parameterized queries (no string concatenation)  
- Enforced HTTPS and CORS restrictions across endpoints  
- Confirmed API keys and environment secrets are excluded from logs  

---

### 🔸 Safety Platform Scan Summary

**Tool:** Safety v3.6.2  
**Account:** sakshinavale12@gmail.com  
**Date:** 27 Oct 2025  
**Command:**  
```bash
safety scan -r requirements.txt -r requirements-dev.txt
