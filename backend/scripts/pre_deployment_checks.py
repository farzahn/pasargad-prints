#!/usr/bin/env python3

"""
Pre-deployment Checks for Pasargad Prints
Validates system readiness before production deployment
"""

import os
import sys
import django
import logging
import json
import time
from typing import Dict, List, Any, Tuple
from pathlib import Path

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pasargad_prints.settings_production')
django.setup()

from django.core.management import call_command
from django.db import connection, connections
from django.conf import settings
from django.core.cache import cache
from django.test.utils import override_settings

import redis
import requests
from decouple import config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s'
)
logger = logging.getLogger(__name__)

class PreDeploymentChecker:
    """Comprehensive pre-deployment validation"""
    
    def __init__(self):
        self.checks = []
        self.results = {
            'passed': 0,
            'failed': 0,
            'warnings': 0,
            'checks': []
        }
    
    def add_check_result(self, name: str, status: str, message: str, details: Dict = None):
        """Add check result"""
        result = {
            'name': name,
            'status': status,  # 'pass', 'fail', 'warning'
            'message': message,
            'details': details or {},
            'timestamp': time.time()
        }
        
        self.results['checks'].append(result)
        
        if status == 'pass':
            self.results['passed'] += 1
        elif status == 'fail':
            self.results['failed'] += 1
        elif status == 'warning':
            self.results['warnings'] += 1
        
        # Log result
        log_level = {
            'pass': logging.INFO,
            'fail': logging.ERROR,
            'warning': logging.WARNING
        }[status]
        
        logger.log(log_level, f"{name}: {message}")
    
    def check_environment_variables(self) -> None:
        """Check required environment variables"""
        logger.info("Checking environment variables...")
        
        required_vars = [
            'SECRET_KEY',
            'DB_NAME', 'DB_USER', 'DB_PASSWORD', 'DB_HOST',
            'REDIS_URL',
            'EMAIL_HOST_USER', 'EMAIL_HOST_PASSWORD',
            'STRIPE_SECRET_KEY', 'STRIPE_PUBLISHABLE_KEY',
            'AWS_ACCESS_KEY_ID', 'AWS_SECRET_ACCESS_KEY', 'AWS_STORAGE_BUCKET_NAME'
        ]
        
        missing_vars = []
        insecure_vars = []
        
        for var in required_vars:
            value = config(var, default=None)
            if not value:
                missing_vars.append(var)
            elif var == 'SECRET_KEY' and ('django-insecure' in value or len(value) < 50):
                insecure_vars.append(var)
        
        if missing_vars:
            self.add_check_result(
                'environment_variables',
                'fail',
                f"Missing required environment variables: {', '.join(missing_vars)}",
                {'missing': missing_vars}
            )
        elif insecure_vars:
            self.add_check_result(
                'environment_variables',
                'warning',
                f"Insecure environment variables: {', '.join(insecure_vars)}",
                {'insecure': insecure_vars}
            )
        else:
            self.add_check_result(
                'environment_variables',
                'pass',
                "All required environment variables are set"
            )
    
    def check_database_connection(self) -> None:
        """Check database connectivity and configuration"""
        logger.info("Checking database connection...")
        
        try:
            # Test connection
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()
            
            # Check database configuration
            with connection.cursor() as cursor:
                # Check PostgreSQL version
                cursor.execute("SELECT version()")
                version = cursor.fetchone()[0]
                
                # Check database size
                cursor.execute("SELECT pg_size_pretty(pg_database_size(current_database()))")
                db_size = cursor.fetchone()[0]
                
                # Check connection limits
                cursor.execute("SHOW max_connections")
                max_connections = int(cursor.fetchone()[0])
                
                # Check current connections
                cursor.execute("SELECT count(*) FROM pg_stat_activity")
                current_connections = cursor.fetchone()[0]
                
                connection_usage = (current_connections / max_connections) * 100
                
                details = {
                    'version': version,
                    'size': db_size,
                    'max_connections': max_connections,
                    'current_connections': current_connections,
                    'connection_usage_percent': round(connection_usage, 2)
                }
                
                if connection_usage > 80:
                    self.add_check_result(
                        'database_connection',
                        'warning',
                        f"High database connection usage: {connection_usage:.1f}%",
                        details
                    )
                else:
                    self.add_check_result(
                        'database_connection',
                        'pass',
                        "Database connection is healthy",
                        details
                    )
                    
        except Exception as e:
            self.add_check_result(
                'database_connection',
                'fail',
                f"Database connection failed: {str(e)}"
            )
    
    def check_redis_connection(self) -> None:
        """Check Redis connectivity and configuration"""
        logger.info("Checking Redis connection...")
        
        try:
            r = redis.from_url(settings.CACHES['default']['LOCATION'])
            
            # Test connection
            r.ping()
            
            # Get Redis info
            info = r.info()
            
            memory_usage = info.get('used_memory_human', 'Unknown')
            max_memory = info.get('maxmemory_human', 'No limit')
            connected_clients = info.get('connected_clients', 0)
            
            details = {
                'memory_usage': memory_usage,
                'max_memory': max_memory,
                'connected_clients': connected_clients,
                'version': info.get('redis_version', 'Unknown')
            }
            
            self.add_check_result(
                'redis_connection',
                'pass',
                "Redis connection is healthy",
                details
            )
            
        except Exception as e:
            self.add_check_result(
                'redis_connection',
                'fail',
                f"Redis connection failed: {str(e)}"
            )
    
    def check_static_files(self) -> None:
        """Check static files configuration"""
        logger.info("Checking static files...")
        
        try:
            # Check static files directory
            static_root = Path(settings.STATIC_ROOT)
            if not static_root.exists():
                self.add_check_result(
                    'static_files',
                    'warning',
                    f"Static files directory does not exist: {static_root}"
                )
                return
            
            # Count static files
            static_files = list(static_root.rglob('*'))
            static_file_count = len([f for f in static_files if f.is_file()])
            
            # Check for critical files
            critical_files = [
                'admin/css/base.css',
                'admin/js/core.js'
            ]
            
            missing_files = []
            for file_path in critical_files:
                if not (static_root / file_path).exists():
                    missing_files.append(file_path)
            
            details = {
                'static_root': str(static_root),
                'file_count': static_file_count,
                'missing_critical_files': missing_files
            }
            
            if missing_files:
                self.add_check_result(
                    'static_files',
                    'warning',
                    f"Missing critical static files: {', '.join(missing_files)}",
                    details
                )
            elif static_file_count == 0:
                self.add_check_result(
                    'static_files',
                    'warning',
                    "No static files found. Run collectstatic?",
                    details
                )
            else:
                self.add_check_result(
                    'static_files',
                    'pass',
                    f"Static files configured correctly ({static_file_count} files)",
                    details
                )
                
        except Exception as e:
            self.add_check_result(
                'static_files',
                'fail',
                f"Static files check failed: {str(e)}"
            )
    
    def check_migrations(self) -> None:
        """Check migration status"""
        logger.info("Checking migrations...")
        
        try:
            from django.db.migrations.executor import MigrationExecutor
            
            executor = MigrationExecutor(connection)
            plan = executor.migration_plan(executor.loader.graph.leaf_nodes())
            
            if plan:
                unapplied_migrations = [f"{migration.app_label}.{migration.name}" for migration, _ in plan]
                self.add_check_result(
                    'migrations',
                    'fail',
                    f"Unapplied migrations found: {', '.join(unapplied_migrations)}",
                    {'unapplied': unapplied_migrations}
                )
            else:
                self.add_check_result(
                    'migrations',
                    'pass',
                    "All migrations are applied"
                )
                
        except Exception as e:
            self.add_check_result(
                'migrations',
                'fail',
                f"Migration check failed: {str(e)}"
            )
    
    def check_email_configuration(self) -> None:
        """Check email configuration"""
        logger.info("Checking email configuration...")
        
        try:
            from django.core.mail import send_mail
            from django.core.mail.backends.base import BaseEmailBackend
            
            # Test email configuration
            email_host = getattr(settings, 'EMAIL_HOST', None)
            email_port = getattr(settings, 'EMAIL_PORT', None)
            email_user = getattr(settings, 'EMAIL_HOST_USER', None)
            
            if not all([email_host, email_port, email_user]):
                self.add_check_result(
                    'email_configuration',
                    'warning',
                    "Email configuration incomplete"
                )
                return
            
            # Try to connect to SMTP server
            import smtplib
            
            server = smtplib.SMTP(email_host, email_port)
            server.starttls()
            server.quit()
            
            self.add_check_result(
                'email_configuration',
                'pass',
                "Email configuration is valid",
                {
                    'host': email_host,
                    'port': email_port,
                    'user': email_user
                }
            )
            
        except Exception as e:
            self.add_check_result(
                'email_configuration',
                'warning',
                f"Email configuration check failed: {str(e)}"
            )
    
    def check_stripe_configuration(self) -> None:
        """Check Stripe payment configuration"""
        logger.info("Checking Stripe configuration...")
        
        try:
            import stripe
            
            stripe.api_key = settings.STRIPE_SECRET_KEY
            
            # Test Stripe connection
            stripe.Account.retrieve()
            
            # Check for live keys in production
            is_live_key = not settings.STRIPE_SECRET_KEY.startswith('sk_test_')
            
            if not is_live_key:
                self.add_check_result(
                    'stripe_configuration',
                    'warning',
                    "Using Stripe test keys in production environment"
                )
            else:
                self.add_check_result(
                    'stripe_configuration',
                    'pass',
                    "Stripe configuration is valid"
                )
                
        except Exception as e:
            self.add_check_result(
                'stripe_configuration',
                'fail',
                f"Stripe configuration failed: {str(e)}"
            )
    
    def check_security_settings(self) -> None:
        """Check security configuration"""
        logger.info("Checking security settings...")
        
        security_issues = []
        
        # Check DEBUG setting
        if getattr(settings, 'DEBUG', True):
            security_issues.append("DEBUG is enabled")
        
        # Check ALLOWED_HOSTS
        allowed_hosts = getattr(settings, 'ALLOWED_HOSTS', [])
        if '*' in allowed_hosts:
            security_issues.append("ALLOWED_HOSTS contains wildcard")
        
        # Check HTTPS settings
        if not getattr(settings, 'SECURE_SSL_REDIRECT', False):
            security_issues.append("SECURE_SSL_REDIRECT is disabled")
        
        if not getattr(settings, 'SESSION_COOKIE_SECURE', False):
            security_issues.append("SESSION_COOKIE_SECURE is disabled")
        
        if not getattr(settings, 'CSRF_COOKIE_SECURE', False):
            security_issues.append("CSRF_COOKIE_SECURE is disabled")
        
        # Check HSTS settings
        if not getattr(settings, 'SECURE_HSTS_SECONDS', 0):
            security_issues.append("SECURE_HSTS_SECONDS not set")
        
        if security_issues:
            self.add_check_result(
                'security_settings',
                'warning',
                f"Security issues found: {', '.join(security_issues)}",
                {'issues': security_issues}
            )
        else:
            self.add_check_result(
                'security_settings',
                'pass',
                "Security settings are properly configured"
            )
    
    def check_dependencies(self) -> None:
        """Check Python dependencies"""
        logger.info("Checking dependencies...")
        
        try:
            import pkg_resources
            
            requirements_file = Path(__file__).parent.parent / 'requirements.txt'
            
            if not requirements_file.exists():
                self.add_check_result(
                    'dependencies',
                    'warning',
                    "requirements.txt not found"
                )
                return
            
            with open(requirements_file) as f:
                requirements = f.read().splitlines()
            
            missing_packages = []
            outdated_packages = []
            
            for requirement in requirements:
                if requirement.strip() and not requirement.startswith('#'):
                    try:
                        pkg_resources.require(requirement)
                    except pkg_resources.DistributionNotFound:
                        missing_packages.append(requirement)
                    except pkg_resources.VersionConflict:
                        outdated_packages.append(requirement)
            
            if missing_packages:
                self.add_check_result(
                    'dependencies',
                    'fail',
                    f"Missing packages: {', '.join(missing_packages)}",
                    {'missing': missing_packages}
                )
            elif outdated_packages:
                self.add_check_result(
                    'dependencies',
                    'warning',
                    f"Version conflicts: {', '.join(outdated_packages)}",
                    {'conflicts': outdated_packages}
                )
            else:
                self.add_check_result(
                    'dependencies',
                    'pass',
                    "All dependencies are satisfied"
                )
                
        except Exception as e:
            self.add_check_result(
                'dependencies',
                'warning',
                f"Dependency check failed: {str(e)}"
            )
    
    def run_all_checks(self) -> Dict[str, Any]:
        """Run all pre-deployment checks"""
        logger.info("Starting pre-deployment checks...")
        
        checks = [
            self.check_environment_variables,
            self.check_database_connection,
            self.check_redis_connection,
            self.check_migrations,
            self.check_static_files,
            self.check_email_configuration,
            self.check_stripe_configuration,
            self.check_security_settings,
            self.check_dependencies,
        ]
        
        for check in checks:
            try:
                check()
            except Exception as e:
                logger.error(f"Check {check.__name__} failed with exception: {str(e)}")
                self.add_check_result(
                    check.__name__,
                    'fail',
                    f"Check failed with exception: {str(e)}"
                )
        
        # Add summary
        self.results['summary'] = {
            'total_checks': len(self.results['checks']),
            'success_rate': (self.results['passed'] / len(self.results['checks']) * 100) if self.results['checks'] else 0,
            'ready_for_deployment': self.results['failed'] == 0,
            'timestamp': time.time()
        }
        
        logger.info(f"Pre-deployment checks completed: {self.results['passed']} passed, {self.results['failed']} failed, {self.results['warnings']} warnings")
        
        return self.results

def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Pre-deployment checks')
    parser.add_argument('--output', help='Output file for results (JSON)')
    parser.add_argument('--fail-on-warnings', action='store_true', help='Fail if warnings are found')
    
    args = parser.parse_args()
    
    checker = PreDeploymentChecker()
    results = checker.run_all_checks()
    
    # Output results
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(results, f, indent=2)
        logger.info(f"Results written to {args.output}")
    
    # Print summary
    print("\nDeployment Readiness Summary:")
    print(f"Total Checks: {results['summary']['total_checks']}")
    print(f"Passed: {results['passed']}")
    print(f"Failed: {results['failed']}")
    print(f"Warnings: {results['warnings']}")
    print(f"Success Rate: {results['summary']['success_rate']:.1f}%")
    print(f"Ready for Deployment: {'Yes' if results['summary']['ready_for_deployment'] else 'No'}")
    
    # Exit with appropriate code
    if results['failed'] > 0:
        sys.exit(1)
    elif args.fail_on_warnings and results['warnings'] > 0:
        sys.exit(1)
    else:
        sys.exit(0)

if __name__ == '__main__':
    main()