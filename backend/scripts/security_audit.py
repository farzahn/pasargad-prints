#!/usr/bin/env python3

"""
Security Audit Script for Pasargad Prints Production
Performs automated security checks and generates a security report
"""

import os
import sys
import json
import logging
import subprocess
import hashlib
import socket
import ssl
import urllib.request
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Tuple

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pasargad_prints.settings_production')
import django
django.setup()

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.db import connection

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s',
    handlers=[
        logging.FileHandler('/var/log/pasargad_prints_security_audit.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class SecurityAuditor:
    """Comprehensive security audit system"""
    
    def __init__(self):
        self.results = {
            'timestamp': datetime.now().isoformat(),
            'checks': [],
            'summary': {
                'total_checks': 0,
                'passed': 0,
                'failed': 0,
                'warnings': 0,
                'critical': 0
            }
        }
    
    def add_result(self, check_name: str, status: str, message: str, 
                   severity: str = 'info', details: Dict = None):
        """Add security check result"""
        result = {
            'check': check_name,
            'status': status,  # pass, fail, warning
            'severity': severity,  # critical, high, medium, low, info
            'message': message,
            'details': details or {},
            'timestamp': datetime.now().isoformat()
        }
        
        self.results['checks'].append(result)
        self.results['summary']['total_checks'] += 1
        
        if status == 'pass':
            self.results['summary']['passed'] += 1
        elif status == 'fail':
            self.results['summary']['failed'] += 1
            if severity == 'critical':
                self.results['summary']['critical'] += 1
        elif status == 'warning':
            self.results['summary']['warnings'] += 1
        
        # Log result
        log_level = {
            'pass': logging.INFO,
            'fail': logging.ERROR,
            'warning': logging.WARNING
        }[status]
        
        logger.log(log_level, f"{check_name}: {message}")
    
    def check_django_security_settings(self):
        """Check Django security configuration"""
        logger.info("Checking Django security settings...")
        
        security_checks = [
            ('DEBUG', False, 'critical', 'DEBUG should be False in production'),
            ('SECURE_SSL_REDIRECT', True, 'high', 'SSL redirect should be enabled'),
            ('SECURE_HSTS_SECONDS', 31536000, 'medium', 'HSTS should be set to 1 year'),
            ('SECURE_HSTS_INCLUDE_SUBDOMAINS', True, 'medium', 'HSTS should include subdomains'),
            ('SECURE_CONTENT_TYPE_NOSNIFF', True, 'medium', 'Content type sniffing should be disabled'),
            ('SECURE_BROWSER_XSS_FILTER', True, 'medium', 'XSS filter should be enabled'),
            ('SESSION_COOKIE_SECURE', True, 'high', 'Session cookies should be secure'),
            ('CSRF_COOKIE_SECURE', True, 'high', 'CSRF cookies should be secure'),
            ('SESSION_COOKIE_HTTPONLY', True, 'medium', 'Session cookies should be HTTP only'),
            ('CSRF_COOKIE_HTTPONLY', True, 'medium', 'CSRF cookies should be HTTP only'),
        ]
        
        failed_checks = []
        passed_checks = []
        
        for setting_name, expected_value, severity, description in security_checks:
            actual_value = getattr(settings, setting_name, None)
            
            if isinstance(expected_value, bool):
                check_passed = actual_value is expected_value
            elif isinstance(expected_value, int):
                check_passed = actual_value >= expected_value
            else:
                check_passed = actual_value == expected_value
            
            if check_passed:
                passed_checks.append(setting_name)
            else:
                failed_checks.append({
                    'setting': setting_name,
                    'expected': expected_value,
                    'actual': actual_value,
                    'severity': severity,
                    'description': description
                })
        
        if failed_checks:
            critical_failures = [f for f in failed_checks if f['severity'] == 'critical']
            if critical_failures:
                self.add_result(
                    'django_security_settings',
                    'fail',
                    f"Critical security settings misconfigured: {len(critical_failures)} issues",
                    'critical',
                    {'failed_checks': failed_checks, 'passed_checks': passed_checks}
                )
            else:
                self.add_result(
                    'django_security_settings',
                    'warning',
                    f"Some security settings need attention: {len(failed_checks)} issues",
                    'medium',
                    {'failed_checks': failed_checks, 'passed_checks': passed_checks}
                )
        else:
            self.add_result(
                'django_security_settings',
                'pass',
                f"All {len(passed_checks)} security settings configured correctly",
                'info',
                {'passed_checks': passed_checks}
            )
    
    def check_secret_key_security(self):
        """Check secret key security"""
        logger.info("Checking secret key security...")
        
        secret_key = getattr(settings, 'SECRET_KEY', '')
        
        issues = []
        
        # Check length
        if len(secret_key) < 50:
            issues.append("Secret key is too short (should be at least 50 characters)")
        
        # Check for default Django secret key
        if 'django-insecure' in secret_key:
            issues.append("Using default Django insecure secret key")
        
        # Check entropy (simplified check)
        unique_chars = len(set(secret_key))
        if unique_chars < 20:
            issues.append("Secret key has low entropy (too few unique characters)")
        
        # Check for common patterns
        if secret_key.lower() in ['changeme', 'secret', 'password', 'key']:
            issues.append("Secret key appears to be a common/weak value")
        
        if issues:
            self.add_result(
                'secret_key_security',
                'fail',
                f"Secret key security issues: {'; '.join(issues)}",
                'critical',
                {'issues': issues}
            )
        else:
            self.add_result(
                'secret_key_security',
                'pass',
                "Secret key appears to be secure",
                'info'
            )
    
    def check_database_security(self):
        """Check database security configuration"""
        logger.info("Checking database security...")
        
        db_config = settings.DATABASES['default']
        
        security_issues = []
        security_good = []
        
        # Check SSL usage
        ssl_mode = db_config.get('OPTIONS', {}).get('sslmode', 'disable')
        if ssl_mode in ['disable', 'allow', 'prefer']:
            security_issues.append(f"Database SSL mode is '{ssl_mode}' (should be 'require' or higher)")
        else:
            security_good.append(f"Database SSL mode is '{ssl_mode}'")
        
        # Check password strength (basic check)
        password = db_config.get('PASSWORD', '')
        if len(password) < 12:
            security_issues.append("Database password is too short (should be at least 12 characters)")
        else:
            security_good.append("Database password length is adequate")
        
        # Check if using default credentials
        username = db_config.get('USER', '')
        if username.lower() in ['postgres', 'admin', 'root', 'user']:
            security_issues.append(f"Using common database username '{username}'")
        else:
            security_good.append("Database username is not a common default")
        
        # Test connection security
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT ssl, client_addr FROM pg_stat_ssl WHERE pid = pg_backend_pid()")
                result = cursor.fetchone()
                if result:
                    ssl_enabled, client_addr = result
                    if ssl_enabled:
                        security_good.append("Database connection is using SSL")
                    else:
                        security_issues.append("Database connection is not using SSL")
                
        except Exception as e:
            logger.warning(f"Could not check database SSL status: {e}")
        
        if security_issues:
            severity = 'critical' if any('SSL' in issue for issue in security_issues) else 'high'
            self.add_result(
                'database_security',
                'fail',
                f"Database security issues found: {len(security_issues)} issues",
                severity,
                {'issues': security_issues, 'good_practices': security_good}
            )
        else:
            self.add_result(
                'database_security',
                'pass',
                f"Database security configuration is good: {len(security_good)} checks passed",
                'info',
                {'good_practices': security_good}
            )
    
    def check_user_security(self):
        """Check user account security"""
        logger.info("Checking user account security...")
        
        User = get_user_model()
        
        # Check for weak admin passwords (basic checks)
        admin_users = User.objects.filter(is_superuser=True)
        weak_password_users = []
        inactive_admin_users = []
        
        for user in admin_users:
            if not user.is_active:
                inactive_admin_users.append(user.username)
            
            # Check for obviously weak passwords (can't check actual passwords due to hashing)
            if user.username.lower() in ['admin', 'administrator', 'root', 'user']:
                weak_password_users.append(f"Admin user has common username: {user.username}")
        
        # Check for users with no last login (potential unused accounts)
        never_logged_in = User.objects.filter(last_login__isnull=True).count()
        
        # Check for old inactive accounts
        old_cutoff = datetime.now() - timedelta(days=90)
        old_inactive = User.objects.filter(
            last_login__lt=old_cutoff,
            is_active=True
        ).count()
        
        issues = []
        good_practices = []
        
        if weak_password_users:
            issues.extend(weak_password_users)
        
        if inactive_admin_users:
            issues.append(f"Inactive admin users found: {', '.join(inactive_admin_users)}")
        
        if never_logged_in > 10:  # Threshold for concern
            issues.append(f"Many users never logged in: {never_logged_in} accounts")
        
        if old_inactive > 20:  # Threshold for concern
            issues.append(f"Many old inactive accounts: {old_inactive} accounts")
        
        good_practices.append(f"Total admin users: {admin_users.count()}")
        good_practices.append(f"Active admin users: {admin_users.filter(is_active=True).count()}")
        
        if issues:
            self.add_result(
                'user_security',
                'warning',
                f"User security issues found: {len(issues)} issues",
                'medium',
                {'issues': issues, 'good_practices': good_practices}
            )
        else:
            self.add_result(
                'user_security',
                'pass',
                "User account security looks good",
                'info',
                {'good_practices': good_practices}
            )
    
    def check_file_permissions(self):
        """Check file and directory permissions"""
        logger.info("Checking file permissions...")
        
        critical_paths = [
            {'path': settings.BASE_DIR, 'name': 'Project directory'},
            {'path': settings.STATIC_ROOT, 'name': 'Static files'},
            {'path': '/var/log', 'name': 'Log directory'},
        ]
        
        if hasattr(settings, 'MEDIA_ROOT'):
            critical_paths.append({'path': settings.MEDIA_ROOT, 'name': 'Media files'})
        
        permission_issues = []
        secure_paths = []
        
        for path_info in critical_paths:
            path = Path(path_info['path'])
            name = path_info['name']
            
            if not path.exists():
                permission_issues.append(f"{name} does not exist: {path}")
                continue
            
            # Check if world-writable
            stat_info = path.stat()
            mode = stat_info.st_mode
            
            if mode & 0o002:  # World writable
                permission_issues.append(f"{name} is world-writable: {path}")
            elif mode & 0o022:  # Group and other writable
                permission_issues.append(f"{name} is group/other writable: {path}")
            else:
                secure_paths.append(f"{name} has secure permissions")
        
        # Check for sensitive files with wrong permissions
        sensitive_files = [
            '.env',
            '.env.production',
            'settings_production.py'
        ]
        
        for filename in sensitive_files:
            file_path = settings.BASE_DIR / filename
            if file_path.exists():
                stat_info = file_path.stat()
                mode = stat_info.st_mode
                
                if mode & 0o044:  # Readable by group or others
                    permission_issues.append(f"Sensitive file {filename} is readable by group/others")
                else:
                    secure_paths.append(f"Sensitive file {filename} has secure permissions")
        
        if permission_issues:
            self.add_result(
                'file_permissions',
                'fail',
                f"File permission issues found: {len(permission_issues)} issues",
                'high',
                {'issues': permission_issues, 'secure_paths': secure_paths}
            )
        else:
            self.add_result(
                'file_permissions',
                'pass',
                f"File permissions are secure: {len(secure_paths)} checks passed",
                'info',
                {'secure_paths': secure_paths}
            )
    
    def check_ssl_certificate(self):
        """Check SSL certificate security"""
        logger.info("Checking SSL certificate...")
        
        # Get the domain from ALLOWED_HOSTS
        allowed_hosts = getattr(settings, 'ALLOWED_HOSTS', [])
        domains = [host for host in allowed_hosts if not host.startswith('.') and host != '*']
        
        if not domains:
            self.add_result(
                'ssl_certificate',
                'warning',
                "No domains found in ALLOWED_HOSTS to check SSL",
                'medium'
            )
            return
        
        ssl_results = []
        
        for domain in domains[:3]:  # Check up to 3 domains
            try:
                # Create SSL context
                context = ssl.create_default_context()
                
                # Connect and get certificate
                with socket.create_connection((domain, 443), timeout=10) as sock:
                    with context.wrap_socket(sock, server_hostname=domain) as ssock:
                        cert = ssock.getpeercert()
                        
                        # Check expiration
                        not_after = datetime.strptime(cert['notAfter'], '%b %d %H:%M:%S %Y %Z')
                        days_until_expiry = (not_after - datetime.now()).days
                        
                        # Check subject
                        subject = dict(x[0] for x in cert['subject'])
                        common_name = subject.get('commonName', 'Unknown')
                        
                        # Check issuer
                        issuer = dict(x[0] for x in cert['issuer'])
                        issuer_name = issuer.get('organizationName', 'Unknown')
                        
                        ssl_info = {
                            'domain': domain,
                            'common_name': common_name,
                            'issuer': issuer_name,
                            'expires': not_after.isoformat(),
                            'days_until_expiry': days_until_expiry,
                            'version': cert.get('version', 'Unknown')
                        }
                        
                        if days_until_expiry < 30:
                            ssl_info['status'] = 'expiring_soon'
                            ssl_info['severity'] = 'high'
                        elif days_until_expiry < 7:
                            ssl_info['status'] = 'critical_expiry'
                            ssl_info['severity'] = 'critical'
                        else:
                            ssl_info['status'] = 'valid'
                            ssl_info['severity'] = 'info'
                        
                        ssl_results.append(ssl_info)
                        
            except Exception as e:
                ssl_results.append({
                    'domain': domain,
                    'status': 'error',
                    'error': str(e),
                    'severity': 'high'
                })
        
        # Determine overall status
        critical_issues = [r for r in ssl_results if r.get('severity') == 'critical']
        high_issues = [r for r in ssl_results if r.get('severity') == 'high']
        
        if critical_issues:
            self.add_result(
                'ssl_certificate',
                'fail',
                f"Critical SSL certificate issues: {len(critical_issues)} domains",
                'critical',
                {'ssl_results': ssl_results}
            )
        elif high_issues:
            self.add_result(
                'ssl_certificate',
                'warning',
                f"SSL certificate warnings: {len(high_issues)} domains",
                'high',
                {'ssl_results': ssl_results}
            )
        else:
            self.add_result(
                'ssl_certificate',
                'pass',
                f"SSL certificates are valid for {len(ssl_results)} domains",
                'info',
                {'ssl_results': ssl_results}
            )
    
    def check_dependency_vulnerabilities(self):
        """Check for known vulnerabilities in dependencies"""
        logger.info("Checking dependency vulnerabilities...")
        
        try:
            # Run safety check if available
            result = subprocess.run(
                ['safety', 'check', '--json'],
                capture_output=True,
                text=True,
                cwd=settings.BASE_DIR
            )
            
            if result.returncode == 0:
                # No vulnerabilities found
                self.add_result(
                    'dependency_vulnerabilities',
                    'pass',
                    "No known vulnerabilities found in dependencies",
                    'info'
                )
            else:
                try:
                    vulnerabilities = json.loads(result.stdout)
                    vulnerability_count = len(vulnerabilities)
                    
                    self.add_result(
                        'dependency_vulnerabilities',
                        'fail',
                        f"Found {vulnerability_count} known vulnerabilities in dependencies",
                        'high',
                        {'vulnerabilities': vulnerabilities}
                    )
                except json.JSONDecodeError:
                    self.add_result(
                        'dependency_vulnerabilities',
                        'warning',
                        f"Safety check failed with output: {result.stderr}",
                        'medium'
                    )
                    
        except FileNotFoundError:
            # Safety not installed
            self.add_result(
                'dependency_vulnerabilities',
                'warning',
                "Safety package not installed - cannot check for vulnerabilities",
                'medium'
            )
        except Exception as e:
            self.add_result(
                'dependency_vulnerabilities',
                'warning',
                f"Could not check dependency vulnerabilities: {str(e)}",
                'medium'
            )
    
    def check_security_headers(self):
        """Check security headers configuration"""
        logger.info("Checking security headers...")
        
        # This would normally test actual HTTP responses
        # For now, we'll check Django settings that control headers
        
        header_checks = []
        
        # Check CSP settings
        if hasattr(settings, 'CSP_DEFAULT_SRC'):
            header_checks.append("Content Security Policy is configured")
        else:
            header_checks.append("Content Security Policy not configured")
        
        # Check other security-related settings
        if getattr(settings, 'SECURE_REFERRER_POLICY', None):
            header_checks.append(f"Referrer Policy set to: {settings.SECURE_REFERRER_POLICY}")
        else:
            header_checks.append("Referrer Policy not configured")
        
        # Check X-Frame-Options
        x_frame_options = getattr(settings, 'X_FRAME_OPTIONS', 'DENY')
        if x_frame_options in ['DENY', 'SAMEORIGIN']:
            header_checks.append(f"X-Frame-Options properly set to: {x_frame_options}")
        else:
            header_checks.append(f"X-Frame-Options may be insecure: {x_frame_options}")
        
        self.add_result(
            'security_headers',
            'pass',
            f"Security headers checked: {len(header_checks)} items",
            'info',
            {'header_checks': header_checks}
        )
    
    def check_logging_security(self):
        """Check logging configuration for security"""
        logger.info("Checking logging security...")
        
        logging_config = getattr(settings, 'LOGGING', {})
        
        issues = []
        good_practices = []
        
        # Check if sensitive data might be logged
        handlers = logging_config.get('handlers', {})
        
        for handler_name, handler_config in handlers.items():
            # Check log file permissions would be done at runtime
            if 'filename' in handler_config:
                log_file = Path(handler_config['filename'])
                good_practices.append(f"Log file configured: {log_file}")
                
                # Check if log directory exists and is writable
                if log_file.parent.exists():
                    if not os.access(log_file.parent, os.W_OK):
                        issues.append(f"Log directory not writable: {log_file.parent}")
                else:
                    issues.append(f"Log directory does not exist: {log_file.parent}")
        
        # Check log levels
        loggers = logging_config.get('loggers', {})
        for logger_name, logger_config in loggers.items():
            level = logger_config.get('level', 'INFO')
            if level == 'DEBUG':
                issues.append(f"Logger '{logger_name}' set to DEBUG level in production")
        
        if issues:
            self.add_result(
                'logging_security',
                'warning',
                f"Logging security issues: {len(issues)} issues",
                'medium',
                {'issues': issues, 'good_practices': good_practices}
            )
        else:
            self.add_result(
                'logging_security',
                'pass',
                f"Logging configuration looks secure: {len(good_practices)} checks",
                'info',
                {'good_practices': good_practices}
            )
    
    def run_full_audit(self) -> Dict[str, Any]:
        """Run complete security audit"""
        logger.info("Starting comprehensive security audit...")
        
        audit_checks = [
            self.check_django_security_settings,
            self.check_secret_key_security,
            self.check_database_security,
            self.check_user_security,
            self.check_file_permissions,
            self.check_ssl_certificate,
            self.check_dependency_vulnerabilities,
            self.check_security_headers,
            self.check_logging_security,
        ]
        
        for check in audit_checks:
            try:
                check()
            except Exception as e:
                logger.error(f"Security check {check.__name__} failed: {str(e)}")
                self.add_result(
                    check.__name__,
                    'fail',
                    f"Check failed with exception: {str(e)}",
                    'high'
                )
        
        # Calculate security score
        total_checks = self.results['summary']['total_checks']
        passed_checks = self.results['summary']['passed']
        critical_failures = self.results['summary']['critical']
        
        if total_checks > 0:
            security_score = (passed_checks / total_checks) * 100
            if critical_failures > 0:
                security_score = max(0, security_score - (critical_failures * 20))
        else:
            security_score = 0
        
        self.results['summary']['security_score'] = round(security_score, 2)
        self.results['summary']['security_grade'] = self.calculate_security_grade(security_score, critical_failures)
        
        logger.info(f"Security audit completed. Score: {security_score:.1f}%, Grade: {self.results['summary']['security_grade']}")
        
        return self.results
    
    def calculate_security_grade(self, score: float, critical_failures: int) -> str:
        """Calculate security grade based on score and critical failures"""
        if critical_failures > 0:
            return 'F'
        elif score >= 95:
            return 'A+'
        elif score >= 90:
            return 'A'
        elif score >= 85:
            return 'A-'
        elif score >= 80:
            return 'B+'
        elif score >= 75:
            return 'B'
        elif score >= 70:
            return 'B-'
        elif score >= 65:
            return 'C+'
        elif score >= 60:
            return 'C'
        else:
            return 'D'
    
    def generate_report(self, output_file: str = None) -> str:
        """Generate security audit report"""
        report = {
            'audit_summary': self.results['summary'],
            'audit_timestamp': self.results['timestamp'],
            'detailed_results': self.results['checks'],
            'recommendations': self.generate_recommendations()
        }
        
        if output_file:
            with open(output_file, 'w') as f:
                json.dump(report, f, indent=2)
            logger.info(f"Security audit report saved to: {output_file}")
        
        return json.dumps(report, indent=2)
    
    def generate_recommendations(self) -> List[str]:
        """Generate security recommendations based on audit results"""
        recommendations = []
        
        critical_issues = [r for r in self.results['checks'] if r['severity'] == 'critical']
        high_issues = [r for r in self.results['checks'] if r['severity'] == 'high']
        
        if critical_issues:
            recommendations.append("URGENT: Address critical security issues immediately before deployment")
            for issue in critical_issues:
                recommendations.append(f"  - {issue['check']}: {issue['message']}")
        
        if high_issues:
            recommendations.append("HIGH PRIORITY: Address high-severity security issues")
            for issue in high_issues:
                recommendations.append(f"  - {issue['check']}: {issue['message']}")
        
        # General recommendations
        recommendations.extend([
            "Regularly update dependencies to patch security vulnerabilities",
            "Implement security monitoring and alerting",
            "Conduct regular security audits and penetration testing",
            "Ensure all team members are trained on security best practices",
            "Implement automated security scanning in CI/CD pipeline"
        ])
        
        return recommendations

def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Security audit for Pasargad Prints')
    parser.add_argument('--output', '-o', help='Output file for audit report (JSON)')
    parser.add_argument('--fail-on-critical', action='store_true', 
                       help='Exit with error code if critical issues found')
    
    args = parser.parse_args()
    
    auditor = SecurityAuditor()
    results = auditor.run_full_audit()
    
    # Generate and save report
    output_file = args.output or f"security_audit_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    auditor.generate_report(output_file)
    
    # Print summary
    summary = results['summary']
    print(f"\n{'='*60}")
    print("SECURITY AUDIT SUMMARY")
    print(f"{'='*60}")
    print(f"Security Score: {summary['security_score']:.1f}%")
    print(f"Security Grade: {summary['security_grade']}")
    print(f"Total Checks: {summary['total_checks']}")
    print(f"Passed: {summary['passed']}")
    print(f"Failed: {summary['failed']}")
    print(f"Warnings: {summary['warnings']}")
    print(f"Critical Issues: {summary['critical']}")
    
    if summary['critical'] > 0:
        print(f"\n⚠️  CRITICAL SECURITY ISSUES FOUND: {summary['critical']}")
        print("These must be addressed before production deployment!")
    
    # Exit with appropriate code
    if args.fail_on_critical and summary['critical'] > 0:
        sys.exit(1)
    elif summary['failed'] > 0:
        sys.exit(1)
    else:
        sys.exit(0)

if __name__ == '__main__':
    main()