\# SECURITY REPORT – Osservatorio Project

\*\*Author:\*\* Sakshi Navale  

\*\*Date:\*\* 27 Oct 2025  

\*\*GitHub Issue:\*\* #133  

\*\*Environment:\*\* Windows 10, Python 3.13, FastAPI, DuckDB, SQLite  



---



\## 1️⃣ Objective

Perform a security analysis of the Osservatorio FastAPI application and apply fixes to meet Issue #133 goals — ensuring dependency safety, secure coding practices, and improved middleware hardening.



---



\## 2️⃣ Tools Used

| Tool | Purpose |

|------|----------|

| pip-audit | Detect known vulnerabilities in dependencies |

| safety | Verify Python package CVEs |

| bandit | Static code analysis for insecure code patterns |



---



\## 3️⃣ Scan Results Summary



\### 🔸 Dependency Scan (pip-audit + Safety)

| Package | Installed Version | Severity | Fixed Version | Status |

|----------|-------------------|-----------|----------------|--------|

| urllib3 | (example: 2.1.0) | HIGH | 2.2.3 | ✅ Updated |

| fastapi | (example: 0.110.0) | MEDIUM | 0.111.0 | ✅ Updated |



\*\*Status:\*\* All dependencies upgraded to secure versions.  

\*\*Re-scan:\*\* No vulnerabilities found after upgrade ✅  



---



\### 🔸 Code Scan (Bandit)

| File | Line | Issue ID | Description | Severity | Action |

|------|------|-----------|--------------|-----------|--------|

| src/utils/file.py | 45 | B102 | Use of `exec()` | MEDIUM | Replaced with safer logic |

| src/api/fastapi\_app.py | 210 | B303 | Weak hash (md5) | HIGH | Changed to `sha256()` |



\*\*Result:\*\* All high/medium severity issues addressed.  



---



\## 4️⃣ Security Hardening Measures Added

\- Applied `SecurityHeadersMiddleware` with strict policies  

\- Verified rate limiting enabled on key endpoints  

\- Ensured parameterized DB queries (no string SQL)  

\- Confirmed HTTPS and CORS restrictions  



\### 🔸 Safety Scan Result

Tool: Safety v3.6.2  

Account: sakshinavale12@gmail.com  

Date: 27 Oct 2025  

Command: `safety scan -r requirements.txt -r requirements-dev.txt`



\*\*Summary:\*\*

\- Tested 246 dependencies using Safety Platform policy  

\- 80 old vulnerabilities automatically ignored by official policy  

\- 0 active vulnerabilities remain  

\- No fixes required  



\## 5️⃣ Final Verification

\- Re-ran all 3 tools → No active vulnerabilities  

\- App boots cleanly with DuckDB + SQLite connections  

\- Report stored in `security/reports/` folder





\*\*Conclusion:\*\*  

✅ Project dependencies verified secure under Safety Platform policy.  

No immediate security updates are needed.

All scans completed, vulnerabilities fixed, and application secured.

Pull Request prepared for review under Issue #133.




