#!/usr/bin/env python3

"""
Production Migration Manager for Pasargad Prints
Handles database migrations, data migrations, and rollbacks safely in production
"""

import os
import sys
import django
import logging
import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

# Load environment variables from root .env file
from dotenv import load_dotenv
root_dir = Path(__file__).resolve().parent.parent.parent
env_path = root_dir / '.env'
load_dotenv(env_path)

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pasargad_prints.settings_production')
django.setup()

from django.core.management import execute_from_command_line, call_command
from django.db import connection, transaction
from django.conf import settings
from django.core.management.base import CommandError
from django.apps import apps

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s',
    handlers=[
        logging.FileHandler('/var/log/pasargad_prints_migrations.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class MigrationManager:
    """Manage database migrations with safety checks and rollback capabilities"""
    
    def __init__(self, dry_run: bool = False):
        self.dry_run = dry_run
        self.backup_dir = Path('/tmp/migration_backups')
        self.backup_dir.mkdir(exist_ok=True)
        
    def get_migration_status(self) -> Dict[str, Any]:
        """Get current migration status for all apps"""
        status = {}
        
        try:
            with connection.cursor() as cursor:
                # Check if migration table exists
                cursor.execute("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_name = 'django_migrations'
                    )
                """)
                
                if not cursor.fetchone()[0]:
                    logger.warning("Migration table does not exist. Database not initialized.")
                    return {'initialized': False}
                
                # Get applied migrations
                cursor.execute("""
                    SELECT app, name, applied 
                    FROM django_migrations 
                    ORDER BY app, name
                """)
                
                migrations = cursor.fetchall()
                
                for app, name, applied in migrations:
                    if app not in status:
                        status[app] = {'applied': [], 'pending': []}
                    status[app]['applied'].append({
                        'name': name,
                        'applied': applied.isoformat()
                    })
        
        except Exception as e:
            logger.error(f"Error getting migration status: {str(e)}")
            return {'error': str(e)}
        
        # Get pending migrations
        try:
            from django.db.migrations.executor import MigrationExecutor
            executor = MigrationExecutor(connection)
            plan = executor.migration_plan(executor.loader.graph.leaf_nodes())
            
            for migration, backwards in plan:
                app_label = migration.app_label
                if app_label not in status:
                    status[app_label] = {'applied': [], 'pending': []}
                status[app_label]['pending'].append({
                    'name': migration.name,
                    'backwards': backwards
                })
                
        except Exception as e:
            logger.error(f"Error getting pending migrations: {str(e)}")
        
        status['initialized'] = True
        return status
    
    def create_pre_migration_backup(self) -> str:
        """Create database backup before migration"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_file = self.backup_dir / f"pre_migration_backup_{timestamp}.sql"
        
        if self.dry_run:
            logger.info(f"DRY RUN: Would create backup at {backup_file}")
            return str(backup_file)
        
        try:
            logger.info("Creating pre-migration database backup...")
            
            # Use pg_dump to create backup
            cmd = [
                'pg_dump',
                '--host', settings.DATABASES['default']['HOST'],
                '--port', str(settings.DATABASES['default']['PORT']),
                '--username', settings.DATABASES['default']['USER'],
                '--dbname', settings.DATABASES['default']['NAME'],
                '--verbose',
                '--clean',
                '--no-owner',
                '--no-privileges',
                '--format=custom',
                '--file', str(backup_file)
            ]
            
            env = os.environ.copy()
            env['PGPASSWORD'] = settings.DATABASES['default']['PASSWORD']
            
            import subprocess
            result = subprocess.run(cmd, env=env, capture_output=True, text=True)
            
            if result.returncode != 0:
                raise Exception(f"Backup failed: {result.stderr}")
            
            logger.info(f"Backup created successfully: {backup_file}")
            return str(backup_file)
            
        except Exception as e:
            logger.error(f"Failed to create backup: {str(e)}")
            raise
    
    def validate_migration_safety(self, app_name: str = None) -> List[str]:
        """Validate migrations for potential issues"""
        warnings = []
        
        try:
            from django.db.migrations.loader import MigrationLoader
            from django.db.migrations.executor import MigrationExecutor
            
            loader = MigrationLoader(connection)
            executor = MigrationExecutor(connection)
            
            # Get migration plan
            targets = executor.loader.graph.leaf_nodes()
            if app_name:
                targets = [node for node in targets if node[0] == app_name]
            
            plan = executor.migration_plan(targets)
            
            for migration, backwards in plan:
                migration_obj = loader.get_migration(migration.app_label, migration.name)
                
                # Check for potentially dangerous operations
                for operation in migration_obj.operations:
                    op_name = operation.__class__.__name__
                    
                    # Check for data-destructive operations
                    if op_name in ['DeleteModel', 'RemoveField']:
                        warnings.append(f"DESTRUCTIVE: {migration}: {op_name}")
                    
                    # Check for operations that might cause downtime
                    elif op_name in ['AddField', 'AlterField'] and hasattr(operation, 'field'):
                        if getattr(operation.field, 'null', True) is False and not hasattr(operation.field, 'default'):
                            warnings.append(f"POTENTIAL DOWNTIME: {migration}: Adding non-nullable field without default")
                    
                    # Check for index operations
                    elif op_name in ['AddIndex', 'RemoveIndex']:
                        warnings.append(f"INDEX OPERATION: {migration}: {op_name} (may cause locks)")
                    
                    # Check for constraint operations
                    elif op_name in ['AddConstraint', 'RemoveConstraint']:
                        warnings.append(f"CONSTRAINT OPERATION: {migration}: {op_name} (may cause locks)")
        
        except Exception as e:
            warnings.append(f"Error validating migrations: {str(e)}")
        
        return warnings
    
    def run_migrations(self, app_name: str = None, fake: bool = False, backup: bool = True) -> bool:
        """Run database migrations with safety checks"""
        try:
            logger.info(f"Starting migration process for {app_name or 'all apps'}")
            
            # Get current status
            status = self.get_migration_status()
            if not status.get('initialized', False):
                logger.error("Database not properly initialized")
                return False
            
            # Validate migration safety
            warnings = self.validate_migration_safety(app_name)
            if warnings:
                logger.warning("Migration warnings found:")
                for warning in warnings:
                    logger.warning(f"  - {warning}")
                
                if not self.dry_run:
                    response = input("Continue with migrations? (yes/no): ")
                    if response.lower() != 'yes':
                        logger.info("Migration cancelled by user")
                        return False
            
            # Create backup
            backup_file = None
            if backup and not fake:
                backup_file = self.create_pre_migration_backup()
            
            # Run migrations
            if self.dry_run:
                logger.info("DRY RUN: Would run migrations now")
                # Show migration plan
                self.show_migration_plan(app_name)
                return True
            
            logger.info("Running migrations...")
            
            cmd_args = ['migrate']
            if app_name:
                cmd_args.append(app_name)
            if fake:
                cmd_args.append('--fake')
            
            call_command(*cmd_args, verbosity=2)
            
            logger.info("Migrations completed successfully")
            
            # Log migration event
            self.log_migration_event('success', app_name, backup_file)
            
            return True
            
        except Exception as e:
            logger.error(f"Migration failed: {str(e)}")
            self.log_migration_event('failure', app_name, backup_file, str(e))
            return False
    
    def show_migration_plan(self, app_name: str = None):
        """Show migration plan without executing"""
        try:
            from django.db.migrations.executor import MigrationExecutor
            
            executor = MigrationExecutor(connection)
            targets = executor.loader.graph.leaf_nodes()
            
            if app_name:
                targets = [node for node in targets if node[0] == app_name]
            
            plan = executor.migration_plan(targets)
            
            if not plan:
                logger.info("No migrations to apply")
                return
            
            logger.info("Migration plan:")
            for migration, backwards in plan:
                direction = "REVERSE" if backwards else "APPLY"
                logger.info(f"  {direction}: {migration}")
                
        except Exception as e:
            logger.error(f"Error showing migration plan: {str(e)}")
    
    def rollback_migration(self, app_name: str, migration_name: str) -> bool:
        """Rollback to a specific migration"""
        try:
            if self.dry_run:
                logger.info(f"DRY RUN: Would rollback {app_name} to {migration_name}")
                return True
            
            logger.info(f"Rolling back {app_name} to {migration_name}")
            
            # Create backup before rollback
            backup_file = self.create_pre_migration_backup()
            
            # Run rollback
            call_command('migrate', app_name, migration_name, verbosity=2)
            
            logger.info(f"Rollback completed successfully")
            self.log_migration_event('rollback', app_name, backup_file, migration_name)
            
            return True
            
        except Exception as e:
            logger.error(f"Rollback failed: {str(e)}")
            self.log_migration_event('rollback_failure', app_name, None, str(e))
            return False
    
    def fake_migration(self, app_name: str, migration_name: str = None) -> bool:
        """Mark migrations as applied without running them"""
        try:
            if self.dry_run:
                logger.info(f"DRY RUN: Would fake migration {app_name} {migration_name or '(all)'}")
                return True
            
            logger.info(f"Faking migration {app_name} {migration_name or '(all)'}")
            
            cmd_args = ['migrate', app_name]
            if migration_name:
                cmd_args.append(migration_name)
            cmd_args.append('--fake')
            
            call_command(*cmd_args, verbosity=2)
            
            logger.info("Fake migration completed")
            self.log_migration_event('fake', app_name, None, migration_name)
            
            return True
            
        except Exception as e:
            logger.error(f"Fake migration failed: {str(e)}")
            return False
    
    def log_migration_event(self, event_type: str, app_name: str = None, 
                          backup_file: str = None, details: str = None):
        """Log migration event for audit trail"""
        try:
            event_data = {
                'timestamp': datetime.now().isoformat(),
                'event_type': event_type,
                'app_name': app_name,
                'backup_file': backup_file,
                'details': details,
                'user': os.getenv('USER', 'unknown'),
                'environment': settings.ENVIRONMENT if hasattr(settings, 'ENVIRONMENT') else 'unknown'
            }
            
            # Log to file
            migration_logger = logging.getLogger('migration_events')
            migration_logger.info(json.dumps(event_data))
            
            # Store in database if possible
            try:
                with connection.cursor() as cursor:
                    cursor.execute("""
                        INSERT INTO migration_log 
                        (timestamp, event_type, app_name, backup_file, details, username, environment)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """, [
                        event_data['timestamp'],
                        event_data['event_type'],
                        event_data['app_name'],
                        event_data['backup_file'],
                        event_data['details'],
                        event_data['user'],
                        event_data['environment']
                    ])
            except Exception:
                # Table might not exist, skip database logging
                pass
                
        except Exception as e:
            logger.error(f"Failed to log migration event: {str(e)}")

class DataMigrationManager:
    """Manage data migrations and transformations"""
    
    def __init__(self, dry_run: bool = False):
        self.dry_run = dry_run
    
    def run_data_migration(self, script_name: str) -> bool:
        """Run a specific data migration script"""
        try:
            script_path = Path(__file__).parent / 'data_migrations' / f"{script_name}.py"
            
            if not script_path.exists():
                logger.error(f"Data migration script not found: {script_path}")
                return False
            
            if self.dry_run:
                logger.info(f"DRY RUN: Would run data migration {script_name}")
                return True
            
            logger.info(f"Running data migration: {script_name}")
            
            # Import and run the script
            spec = importlib.util.spec_from_file_location(script_name, script_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            if hasattr(module, 'run_migration'):
                module.run_migration()
                logger.info(f"Data migration {script_name} completed successfully")
                return True
            else:
                logger.error(f"Data migration script {script_name} missing run_migration function")
                return False
                
        except Exception as e:
            logger.error(f"Data migration {script_name} failed: {str(e)}")
            return False

def main():
    parser = argparse.ArgumentParser(description='Production Migration Manager')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be done without executing')
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Status command
    status_parser = subparsers.add_parser('status', help='Show migration status')
    status_parser.add_argument('--app', help='Show status for specific app')
    
    # Plan command
    plan_parser = subparsers.add_parser('plan', help='Show migration plan')
    plan_parser.add_argument('--app', help='Show plan for specific app')
    
    # Migrate command
    migrate_parser = subparsers.add_parser('migrate', help='Run migrations')
    migrate_parser.add_argument('--app', help='Migrate specific app')
    migrate_parser.add_argument('--fake', action='store_true', help='Fake migrations')
    migrate_parser.add_argument('--no-backup', action='store_true', help='Skip backup creation')
    
    # Rollback command
    rollback_parser = subparsers.add_parser('rollback', help='Rollback migrations')
    rollback_parser.add_argument('app', help='App to rollback')
    rollback_parser.add_argument('migration', help='Migration to rollback to')
    
    # Data migration command
    data_parser = subparsers.add_parser('data', help='Run data migration')
    data_parser.add_argument('script', help='Data migration script name')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    migration_manager = MigrationManager(dry_run=args.dry_run)
    
    if args.command == 'status':
        status = migration_manager.get_migration_status()
        print(json.dumps(status, indent=2))
    
    elif args.command == 'plan':
        migration_manager.show_migration_plan(args.app)
    
    elif args.command == 'migrate':
        success = migration_manager.run_migrations(
            app_name=args.app,
            fake=args.fake,
            backup=not args.no_backup
        )
        sys.exit(0 if success else 1)
    
    elif args.command == 'rollback':
        success = migration_manager.rollback_migration(args.app, args.migration)
        sys.exit(0 if success else 1)
    
    elif args.command == 'data':
        data_manager = DataMigrationManager(dry_run=args.dry_run)
        success = data_manager.run_data_migration(args.script)
        sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()