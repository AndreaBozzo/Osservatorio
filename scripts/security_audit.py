#!/usr/bin/env python3
"""
Security Audit Script for Day 5 - Issue #84

Performs comprehensive security audit of authentication & security standardization:
- Authentication patterns validation
- Security middleware configuration
- Error handling consistency
- Circuit breaker implementation
- Structured logging security
- Legacy component removal verification
"""
import json
import sys
from datetime import datetime
from pathlib import Path

# Issue #84: Use proper package imports without sys.path manipulation
try:
    from src.utils.structured_logger import get_structured_logger
except ImportError:
    # Fallback for development environment
    project_root = Path(__file__).parent.parent
    sys.path.insert(0, str(project_root))
    from src.utils.structured_logger import get_structured_logger


class SecurityAuditReport:
    """Security audit report generator"""

    def __init__(self):
        self.logger = get_structured_logger("security_audit")
        self.findings = []
        self.passed_checks = []
        self.failed_checks = []

    def add_finding(
        self, severity: str, category: str, description: str, details: dict = None
    ):
        """Add security finding"""
        finding = {
            "timestamp": datetime.now().isoformat(),
            "severity": severity,
            "category": category,
            "description": description,
            "details": details or {},
        }
        self.findings.append(finding)

        if severity in ["HIGH", "CRITICAL"]:
            self.failed_checks.append(finding)
        else:
            self.passed_checks.append(finding)

    def audit_authentication_patterns(self) -> bool:
        """Audit authentication patterns"""
        print("\n🔐 Auditing Authentication Patterns...")

        # Check JWT manager implementation
        jwt_manager_path = project_root / "src" / "auth" / "jwt_manager.py"
        if jwt_manager_path.exists():
            content = jwt_manager_path.read_text()

            # Check for secure practices
            security_checks = [
                ("secret_key", "Secret key handling"),
                ("RS256", "Strong JWT algorithm"),
                ("token_expires", "Token expiration"),
                ("blacklist", "Token blacklisting"),
            ]

            for check, description in security_checks:
                if check in content:
                    self.add_finding(
                        "INFO", "authentication", f"✅ {description} implemented"
                    )
                else:
                    self.add_finding(
                        "MEDIUM", "authentication", f"⚠️ {description} may need review"
                    )

        # Check middleware integration
        fastapi_app_path = project_root / "src" / "api" / "fastapi_app.py"
        if fastapi_app_path.exists():
            content = fastapi_app_path.read_text()

            if "SecurityHeadersMiddleware" in content:
                self.add_finding(
                    "INFO",
                    "authentication",
                    "✅ Security headers middleware integrated",
                )
            else:
                self.add_finding(
                    "HIGH", "authentication", "❌ Security headers middleware missing"
                )

        return (
            len([f for f in self.findings if f["severity"] in ["HIGH", "CRITICAL"]])
            == 0
        )

    def audit_error_handling(self) -> bool:
        """Audit error handling standardization"""
        print("\n⚠️ Auditing Error Handling...")

        error_handler_path = project_root / "src" / "utils" / "error_handler.py"
        if error_handler_path.exists():
            self.add_finding(
                "INFO", "error_handling", "✅ Centralized error handler implemented"
            )

            content = error_handler_path.read_text()

            # Check for security-aware error handling
            security_features = [
                ("ErrorCategory.SECURITY", "Security error categorization"),
                ("correlation_id", "Request correlation tracking"),
                ("sanitize", "Error message sanitization"),
                ("audit", "Security audit logging"),
            ]

            for feature, description in security_features:
                if feature in content:
                    self.add_finding(
                        "INFO", "error_handling", f"✅ {description} present"
                    )
                else:
                    self.add_finding(
                        "LOW", "error_handling", f"ℹ️ {description} could be enhanced"
                    )
        else:
            self.add_finding(
                "HIGH", "error_handling", "❌ Centralized error handler missing"
            )

        return True

    def audit_circuit_breakers(self) -> bool:
        """Audit circuit breaker implementation"""
        print("\n🔄 Auditing Circuit Breakers...")

        circuit_breaker_path = project_root / "src" / "utils" / "circuit_breaker.py"
        if circuit_breaker_path.exists():
            self.add_finding(
                "INFO", "resilience", "✅ Circuit breaker utility available"
            )

        # Check PowerBI API integration
        powerbi_api_path = project_root / "src" / "api" / "powerbi_api.py"
        if powerbi_api_path.exists():
            content = powerbi_api_path.read_text()

            if "CircuitBreaker" in content and "circuit_breaker" in content:
                self.add_finding(
                    "INFO", "resilience", "✅ Circuit breaker integrated in PowerBI API"
                )
            else:
                self.add_finding(
                    "MEDIUM", "resilience", "⚠️ Circuit breaker missing in PowerBI API"
                )

        # Check ISTAT client (should already have it)
        istat_client_path = project_root / "src" / "api" / "production_istat_client.py"
        if istat_client_path.exists():
            content = istat_client_path.read_text()

            if "CircuitBreaker" in content:
                self.add_finding(
                    "INFO", "resilience", "✅ Circuit breaker present in ISTAT client"
                )
            else:
                self.add_finding(
                    "MEDIUM", "resilience", "⚠️ Circuit breaker missing in ISTAT client"
                )

        return True

    def audit_structured_logging(self) -> bool:
        """Audit structured logging implementation"""
        print("\n📋 Auditing Structured Logging...")

        structured_logger_path = project_root / "src" / "utils" / "structured_logger.py"
        if structured_logger_path.exists():
            content = structured_logger_path.read_text()

            # Check for security features
            security_features = [
                ("LogCategory.SECURITY", "Security log categorization"),
                ("correlation_id", "Request correlation"),
                ("security_event", "Security event logging"),
                ("audit_log", "Audit logging"),
                ("user_id", "User tracking"),
            ]

            for feature, description in security_features:
                if feature in content:
                    self.add_finding("INFO", "logging", f"✅ {description} implemented")
                else:
                    self.add_finding("LOW", "logging", f"ℹ️ {description} available")
        else:
            self.add_finding(
                "MEDIUM", "logging", "⚠️ Structured logging module missing"
            )

        return True

    def audit_legacy_removal(self) -> bool:
        """Audit legacy component removal"""
        print("\n🗑️ Auditing Legacy Component Removal...")

        # Check for moved legacy scripts
        legacy_dir = project_root / "scripts" / "legacy"
        if legacy_dir.exists():
            legacy_files = list(legacy_dir.glob("*.py"))
            if len(legacy_files) >= 4:  # Should have moved validation scripts
                self.add_finding(
                    "INFO",
                    "maintenance",
                    f"✅ {len(legacy_files)} legacy scripts properly isolated",
                )
            else:
                self.add_finding(
                    "LOW", "maintenance", f"ℹ️ {len(legacy_files)} legacy scripts found"
                )

        # Check that main scripts directory is clean
        scripts_dir = project_root / "scripts"
        problematic_patterns = ["validate_issue", "migrate_", "legacy_", "deprecated_"]

        for script_file in scripts_dir.glob("*.py"):
            if any(pattern in script_file.name for pattern in problematic_patterns):
                self.add_finding(
                    "MEDIUM",
                    "maintenance",
                    f"⚠️ Potentially legacy script: {script_file.name}",
                )

        return True

    def audit_configuration_security(self) -> bool:
        """Audit configuration security"""
        print("\n⚙️ Auditing Configuration Security...")

        config_path = project_root / "src" / "utils" / "config.py"
        if config_path.exists():
            content = config_path.read_text()

            # Check for environment variable usage
            if "os.getenv" in content:
                self.add_finding(
                    "INFO",
                    "configuration",
                    "✅ Environment variables used for sensitive config",
                )

            # Check for hardcoded credentials (should not exist)
            suspicious_patterns = ["password", "secret", "key", "token", "credential"]

            lines = content.split("\n")
            for i, line in enumerate(lines):
                if "=" in line and any(
                    pattern in line.lower() for pattern in suspicious_patterns
                ):
                    if not ("getenv" in line or "config" in line.lower()):
                        self.add_finding(
                            "HIGH",
                            "configuration",
                            f"⚠️ Potential hardcoded secret at line {i+1}: {line.strip()}",
                        )

        return True

    def audit_api_security(self) -> bool:
        """Audit API security implementation"""
        print("\n🌐 Auditing API Security...")

        # Check dependencies for security functions
        dependencies_path = project_root / "src" / "api" / "dependencies.py"
        if dependencies_path.exists():
            content = dependencies_path.read_text()

            security_functions = [
                ("get_current_user", "User authentication"),
                ("check_rate_limit", "Rate limiting"),
                ("require_admin", "Authorization controls"),
                ("validate_", "Input validation"),
            ]

            for func, description in security_functions:
                if func in content:
                    self.add_finding(
                        "INFO", "api_security", f"✅ {description} implemented"
                    )

        # Check for CORS configuration
        fastapi_app_path = project_root / "src" / "api" / "fastapi_app.py"
        if fastapi_app_path.exists():
            content = fastapi_app_path.read_text()

            if "CORSMiddleware" in content:
                if 'allow_origins=["*"]' in content:
                    self.add_finding(
                        "MEDIUM",
                        "api_security",
                        "⚠️ CORS allows all origins - review for production",
                    )
                else:
                    self.add_finding(
                        "INFO", "api_security", "✅ CORS properly configured"
                    )

        return True

    def generate_report(self) -> dict:
        """Generate comprehensive security audit report"""
        total_checks = len(self.findings)
        critical_issues = len([f for f in self.findings if f["severity"] == "CRITICAL"])
        high_issues = len([f for f in self.findings if f["severity"] == "HIGH"])
        medium_issues = len([f for f in self.findings if f["severity"] == "MEDIUM"])
        low_issues = len([f for f in self.findings if f["severity"] == "LOW"])
        info_items = len([f for f in self.findings if f["severity"] == "INFO"])

        report = {
            "audit_timestamp": datetime.now().isoformat(),
            "summary": {
                "total_checks": total_checks,
                "critical_issues": critical_issues,
                "high_issues": high_issues,
                "medium_issues": medium_issues,
                "low_issues": low_issues,
                "info_items": info_items,
                "overall_status": (
                    "PASS" if critical_issues == 0 and high_issues == 0 else "FAIL"
                ),
            },
            "findings": self.findings,
        }

        return report

    def run_full_audit(self) -> bool:
        """Run complete security audit"""
        print(
            "🔍 Starting Day 5 Security Audit - Authentication & Security Standardization"
        )
        print("=" * 80)

        self.logger.security_event(
            "Security audit started", action="audit_start", result="initiated"
        )

        # Run audit checks
        audit_results = []
        audit_results.append(self.audit_authentication_patterns())
        audit_results.append(self.audit_error_handling())
        audit_results.append(self.audit_circuit_breakers())
        audit_results.append(self.audit_structured_logging())
        audit_results.append(self.audit_legacy_removal())
        audit_results.append(self.audit_configuration_security())
        audit_results.append(self.audit_api_security())

        # Generate report
        report = self.generate_report()

        # Print summary
        print("\n" + "=" * 80)
        print("📊 SECURITY AUDIT SUMMARY")
        print("=" * 80)

        summary = report["summary"]
        print(f"Total Checks Performed: {summary['total_checks']}")
        print(f"Critical Issues: {summary['critical_issues']}")
        print(f"High Issues: {summary['high_issues']}")
        print(f"Medium Issues: {summary['medium_issues']}")
        print(f"Low Issues: {summary['low_issues']}")
        print(f"Info Items: {summary['info_items']}")
        print(
            f"\nOverall Status: {'🟢 PASS' if summary['overall_status'] == 'PASS' else '🔴 FAIL'}"
        )

        # Print findings by severity
        if summary["critical_issues"] > 0 or summary["high_issues"] > 0:
            print("\n⚠️ HIGH PRIORITY FINDINGS:")
            for finding in self.findings:
                if finding["severity"] in ["CRITICAL", "HIGH"]:
                    print(f"  [{finding['severity']}] {finding['description']}")

        # Save report
        report_path = (
            project_root
            / "logs"
            / f"security_audit_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )
        report_path.parent.mkdir(exist_ok=True)

        with open(report_path, "w") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        print(f"\n📄 Detailed report saved to: {report_path}")

        self.logger.security_event(
            "Security audit completed",
            action="audit_complete",
            result=summary["overall_status"],
            metadata={
                "total_checks": summary["total_checks"],
                "critical_issues": summary["critical_issues"],
                "high_issues": summary["high_issues"],
            },
        )

        return summary["overall_status"] == "PASS"


def main():
    """Main function"""
    auditor = SecurityAuditReport()
    success = auditor.run_full_audit()

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
