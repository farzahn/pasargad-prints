#!/usr/bin/env python3
"""
Database Backup and Recovery Manager for Pasargad Prints

This script handles:
- Automated database backups
- Backup compression and encryption
- Backup rotation and cleanup
- S3 upload for offsite storage
- Database restoration
- Backup verification
"""

import os
import sys
import time
import subprocess
import logging
import argparse
import gzip
import shutil
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
import json

# Add Django to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pasargad_prints.settings_production')

import django
django.setup()

from django.conf import settings
from django.core.mail import send_mail

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('backup.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class BackupManager:
    """Handles database backup and recovery operations"""
    
    def __init__(self):
        self.backup_settings = getattr(settings, 'BACKUP_SETTINGS', {})
        self.backup_dir = Path(self.backup_settings.get('BACKUP_DIR', 'backups'))
        self.backup_dir.mkdir(exist_ok=True)
        
        # Database settings
        self.db_config = settings.DATABASES['default']
        
        # S3 settings
        self.s3_bucket = self.backup_settings.get('S3_BUCKET', '')
        self.use_s3 = bool(self.s3_bucket)
        
        # Backup settings
        self.retention_days = self.backup_settings.get('RETENTION_DAYS', 30)
        self.compress = self.backup_settings.get('COMPRESS', True)
        self.encrypt = self.backup_settings.get('ENCRYPT', False)
        self.encryption_key = self.backup_settings.get('ENCRYPTION_KEY', '')
        
        logger.info(f"Backup directory: {self.backup_dir}")
        logger.info(f"S3 enabled: {self.use_s3}")
        logger.info(f"Compression enabled: {self.compress}")
        logger.info(f"Encryption enabled: {self.encrypt}")
    
    def generate_backup_filename(self, backup_type='full'):
        """Generate backup filename with timestamp"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        hostname = os.uname().nodename if hasattr(os, 'uname') else 'unknown'
        db_name = self.db_config['NAME']
        
        filename = f"{db_name}_{backup_type}_{hostname}_{timestamp}.sql"
        
        if self.compress:
            filename += '.gz'
        
        if self.encrypt:
            filename += '.enc'
        
        return filename
    
    def create_database_dump(self, output_file):
        """Create PostgreSQL database dump"""
        logger.info(f"Creating database dump: {output_file}")
        
        # Build pg_dump command
        pg_dump_cmd = [
            'pg_dump',
            '-h', self.db_config['HOST'],
            '-p', str(self.db_config['PORT']),
            '-U', self.db_config['USER'],
            '-d', self.db_config['NAME'],
            '--no-password',
            '--clean',
            '--if-exists',
            '--verbose'
        ]
        
        # Set environment variables
        env = os.environ.copy()
        env['PGPASSWORD'] = self.db_config['PASSWORD']
        
        try:
            # Create the dump
            with open(output_file, 'w') as f:
                result = subprocess.run(
                    pg_dump_cmd,
                    stdout=f,
                    stderr=subprocess.PIPE,
                    env=env,
                    text=True,
                    timeout=3600  # 1 hour timeout
                )
            
            if result.returncode != 0:
                logger.error(f"pg_dump failed: {result.stderr}")
                return False
            
            logger.info(f"✅ Database dump created: {output_file}")
            return True
            
        except subprocess.TimeoutExpired:
            logger.error("Database dump timed out")
            return False
        except Exception as e:
            logger.error(f"Database dump failed: {str(e)}")
            return False
    
    def compress_file(self, input_file, output_file):
        """Compress file using gzip"""
        logger.info(f"Compressing {input_file} to {output_file}")
        
        try:
            with open(input_file, 'rb') as f_in:
                with gzip.open(output_file, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            
            # Remove original file
            os.remove(input_file)
            
            logger.info(f"✅ File compressed: {output_file}")
            return True
            
        except Exception as e:
            logger.error(f"Compression failed: {str(e)}")
            return False
    
    def encrypt_file(self, input_file, output_file):
        """Encrypt file using AES"""
        if not self.encryption_key:
            logger.error("Encryption key not provided")
            return False
        
        logger.info(f"Encrypting {input_file} to {output_file}")
        
        try:
            # Use OpenSSL for encryption
            encrypt_cmd = [
                'openssl', 'enc', '-aes-256-cbc',
                '-salt',
                '-in', str(input_file),
                '-out', str(output_file),
                '-pass', f'pass:{self.encryption_key}'
            ]
            
            result = subprocess.run(
                encrypt_cmd,
                capture_output=True,
                text=True,
                timeout=600  # 10 minute timeout
            )
            
            if result.returncode != 0:
                logger.error(f"Encryption failed: {result.stderr}")
                return False
            
            # Remove original file
            os.remove(input_file)
            
            logger.info(f"✅ File encrypted: {output_file}")
            return True
            
        except Exception as e:
            logger.error(f"Encryption failed: {str(e)}")
            return False
    
    def calculate_checksum(self, file_path):
        """Calculate SHA256 checksum of file"""
        sha256_hash = hashlib.sha256()
        
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        
        return sha256_hash.hexdigest()
    
    def upload_to_s3(self, local_file, s3_key):
        """Upload backup to S3"""
        if not self.use_s3:
            return True
        
        logger.info(f"Uploading {local_file} to S3: s3://{self.s3_bucket}/{s3_key}")
        
        try:
            import boto3
            from botocore.exceptions import ClientError
            
            s3_client = boto3.client('s3')
            
            # Upload file with metadata
            extra_args = {
                'Metadata': {
                    'backup_date': datetime.now().isoformat(),
                    'database': self.db_config['NAME'],
                    'version': getattr(settings, 'APP_VERSION', '1.0.0')
                }
            }
            
            s3_client.upload_file(
                str(local_file),
                self.s3_bucket,
                s3_key,
                ExtraArgs=extra_args
            )
            
            logger.info(f"✅ Backup uploaded to S3")
            return True
            
        except ImportError:
            logger.warning("boto3 not installed, skipping S3 upload")
            return False
        except ClientError as e:
            logger.error(f"S3 upload failed: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"S3 upload failed: {str(e)}")
            return False
    
    def create_backup_metadata(self, backup_file, metadata):
        """Create backup metadata file"""
        metadata_file = backup_file.with_suffix('.metadata.json')
        
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2, default=str)
        
        logger.info(f"Backup metadata created: {metadata_file}")
        return metadata_file
    
    def backup(self, backup_type='full'):
        """Create complete backup"""
        logger.info(f"🗄️ Starting {backup_type} backup...")
        start_time = datetime.now()
        
        try:
            # Generate backup filename
            backup_filename = self.generate_backup_filename(backup_type)
            temp_file = self.backup_dir / f"temp_{backup_filename}"
            final_file = self.backup_dir / backup_filename
            
            # Remove temp extensions for processing
            if backup_filename.endswith('.gz'):
                temp_file = temp_file.with_suffix('')
            if backup_filename.endswith('.enc'):
                temp_file = temp_file.with_suffix('')
            
            # Create database dump
            if not self.create_database_dump(temp_file):
                return False
            
            current_file = temp_file
            
            # Compress if enabled
            if self.compress:
                compressed_file = current_file.with_suffix('.sql.gz')
                if not self.compress_file(current_file, compressed_file):
                    return False
                current_file = compressed_file
            
            # Encrypt if enabled
            if self.encrypt:
                encrypted_file = current_file.with_suffix(current_file.suffix + '.enc')
                if not self.encrypt_file(current_file, encrypted_file):
                    return False
                current_file = encrypted_file
            
            # Move to final location
            shutil.move(str(current_file), str(final_file))
            
            # Calculate file size and checksum
            file_size = final_file.stat().st_size
            checksum = self.calculate_checksum(final_file)
            
            # Create metadata
            metadata = {
                'backup_date': start_time.isoformat(),
                'backup_type': backup_type,
                'database': self.db_config['NAME'],
                'file_size': file_size,
                'file_size_human': self.format_bytes(file_size),
                'checksum': checksum,
                'compressed': self.compress,
                'encrypted': self.encrypt,
                'version': getattr(settings, 'APP_VERSION', '1.0.0'),
                'duration_seconds': (datetime.now() - start_time).total_seconds()
            }
            
            metadata_file = self.create_backup_metadata(final_file, metadata)
            
            # Upload to S3 if configured
            s3_key = f"backups/{backup_filename}"
            self.upload_to_s3(final_file, s3_key)
            
            # Upload metadata to S3
            if self.use_s3:
                metadata_s3_key = f"backups/{backup_filename}.metadata.json"
                self.upload_to_s3(metadata_file, metadata_s3_key)
            
            duration = datetime.now() - start_time
            logger.info(f"✅ Backup completed successfully in {duration}")
            logger.info(f"Backup file: {final_file}")
            logger.info(f"File size: {self.format_bytes(file_size)}")
            
            # Send notification
            self.send_backup_notification(True, metadata)
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Backup failed: {str(e)}")
            self.send_backup_notification(False, {'error': str(e)})
            return False
    
    def cleanup_old_backups(self):
        """Remove old backup files"""
        logger.info(f"🧹 Cleaning up backups older than {self.retention_days} days...")
        
        cutoff_date = datetime.now() - timedelta(days=self.retention_days)
        removed_count = 0
        
        for backup_file in self.backup_dir.glob('*.sql*'):
            if backup_file.stat().st_mtime < cutoff_date.timestamp():
                try:
                    backup_file.unlink()
                    removed_count += 1
                    logger.info(f"Removed old backup: {backup_file}")
                    
                    # Remove metadata file if exists
                    metadata_file = backup_file.with_suffix('.metadata.json')
                    if metadata_file.exists():
                        metadata_file.unlink()
                        
                except Exception as e:
                    logger.error(f"Failed to remove {backup_file}: {str(e)}")
        
        logger.info(f"✅ Cleaned up {removed_count} old backup files")
    
    def verify_backup(self, backup_file):
        """Verify backup integrity"""
        logger.info(f"🔍 Verifying backup: {backup_file}")
        
        backup_path = Path(backup_file)
        if not backup_path.exists():
            logger.error(f"Backup file not found: {backup_file}")
            return False
        
        # Check metadata
        metadata_file = backup_path.with_suffix('.metadata.json')
        if metadata_file.exists():
            try:
                with open(metadata_file, 'r') as f:
                    metadata = json.load(f)
                
                # Verify checksum
                current_checksum = self.calculate_checksum(backup_path)
                stored_checksum = metadata.get('checksum')
                
                if current_checksum == stored_checksum:
                    logger.info("✅ Backup checksum verified")
                    return True
                else:
                    logger.error("❌ Backup checksum mismatch")
                    return False
                    
            except Exception as e:
                logger.error(f"Failed to verify backup metadata: {str(e)}")
                return False
        else:
            logger.warning("No metadata file found, skipping checksum verification")
            return True
    
    def list_backups(self):
        """List available backups"""
        logger.info("📋 Available backups:")
        
        backups = []
        for backup_file in sorted(self.backup_dir.glob('*.sql*')):
            if backup_file.suffix == '.json':
                continue
                
            metadata_file = backup_file.with_suffix('.metadata.json')
            metadata = {}
            
            if metadata_file.exists():
                try:
                    with open(metadata_file, 'r') as f:
                        metadata = json.load(f)
                except:
                    pass
            
            backup_info = {
                'file': str(backup_file),
                'size': self.format_bytes(backup_file.stat().st_size),
                'date': metadata.get('backup_date', 'unknown'),
                'type': metadata.get('backup_type', 'unknown'),
                'compressed': metadata.get('compressed', False),
                'encrypted': metadata.get('encrypted', False)
            }
            
            backups.append(backup_info)
            
            logger.info(f"  {backup_file.name}")
            logger.info(f"    Size: {backup_info['size']}")
            logger.info(f"    Date: {backup_info['date']}")
            logger.info(f"    Type: {backup_info['type']}")
            logger.info("")
        
        return backups
    
    def restore_backup(self, backup_file, confirm=False):
        """Restore database from backup"""
        if not confirm:
            logger.error("Database restoration requires --confirm flag")
            return False
        
        logger.warning("🚨 DANGER: This will completely replace the current database!")
        logger.info(f"Restoring from backup: {backup_file}")
        
        backup_path = Path(backup_file)
        if not backup_path.exists():
            logger.error(f"Backup file not found: {backup_file}")
            return False
        
        # Verify backup first
        if not self.verify_backup(backup_path):
            logger.error("Backup verification failed")
            return False
        
        try:
            # Determine if file is compressed/encrypted
            temp_file = None
            restore_file = backup_path
            
            # Decrypt if needed
            if backup_path.suffix == '.enc':
                if not self.encryption_key:
                    logger.error("Encryption key required for encrypted backup")
                    return False
                
                temp_file = backup_path.with_suffix('')
                decrypt_cmd = [
                    'openssl', 'enc', '-aes-256-cbc', '-d',
                    '-in', str(backup_path),
                    '-out', str(temp_file),
                    '-pass', f'pass:{self.encryption_key}'
                ]
                
                result = subprocess.run(decrypt_cmd, capture_output=True, text=True)
                if result.returncode != 0:
                    logger.error(f"Decryption failed: {result.stderr}")
                    return False
                
                restore_file = temp_file
            
            # Decompress if needed
            if restore_file.suffix == '.gz':
                decompressed_file = restore_file.with_suffix('')
                
                with gzip.open(restore_file, 'rb') as f_in:
                    with open(decompressed_file, 'wb') as f_out:
                        shutil.copyfileobj(f_in, f_out)
                
                if temp_file:
                    os.remove(temp_file)
                temp_file = decompressed_file
                restore_file = decompressed_file
            
            # Restore database
            psql_cmd = [
                'psql',
                '-h', self.db_config['HOST'],
                '-p', str(self.db_config['PORT']),
                '-U', self.db_config['USER'],
                '-d', self.db_config['NAME'],
                '-f', str(restore_file)
            ]
            
            env = os.environ.copy()
            env['PGPASSWORD'] = self.db_config['PASSWORD']
            
            result = subprocess.run(
                psql_cmd,
                env=env,
                capture_output=True,
                text=True,
                timeout=3600  # 1 hour timeout
            )
            
            # Clean up temporary file
            if temp_file and temp_file.exists():
                os.remove(temp_file)
            
            if result.returncode != 0:
                logger.error(f"Database restoration failed: {result.stderr}")
                return False
            
            logger.info("✅ Database restoration completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Database restoration failed: {str(e)}")
            return False
    
    def send_backup_notification(self, success, metadata):
        """Send backup notification email"""
        try:
            if success:
                subject = "✅ Database Backup Successful"
                message = f"""
                Database backup completed successfully!
                
                Database: {metadata.get('database', 'unknown')}
                Backup Type: {metadata.get('backup_type', 'unknown')}
                File Size: {metadata.get('file_size_human', 'unknown')}
                Duration: {metadata.get('duration_seconds', 0):.2f} seconds
                Compressed: {metadata.get('compressed', False)}
                Encrypted: {metadata.get('encrypted', False)}
                Timestamp: {metadata.get('backup_date', 'unknown')}
                """
            else:
                subject = "❌ Database Backup Failed"
                message = f"""
                Database backup failed!
                
                Error: {metadata.get('error', 'Unknown error')}
                Timestamp: {datetime.now().isoformat()}
                
                Please check the backup logs and take corrective action.
                """
            
            admin_email = getattr(settings, 'ADMIN_EMAIL', 'admin@pasargadprints.com')
            
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[admin_email],
                fail_silently=True
            )
            
        except Exception as e:
            logger.error(f"Failed to send backup notification: {str(e)}")
    
    @staticmethod
    def format_bytes(bytes_value):
        """Format bytes in human readable format"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if bytes_value < 1024.0:
                return f"{bytes_value:.1f} {unit}"
            bytes_value /= 1024.0
        return f"{bytes_value:.1f} PB"

def main():
    """Main backup script entry point"""
    parser = argparse.ArgumentParser(description='Database backup and recovery manager')
    parser.add_argument('action', choices=['backup', 'restore', 'list', 'cleanup', 'verify'])
    parser.add_argument('--type', default='full', choices=['full', 'incremental'], help='Backup type')
    parser.add_argument('--file', help='Backup file path for restore/verify operations')
    parser.add_argument('--confirm', action='store_true', help='Confirm destructive operations')
    
    args = parser.parse_args()
    
    backup_manager = BackupManager()
    
    if args.action == 'backup':
        success = backup_manager.backup(args.type)
        return 0 if success else 1
    
    elif args.action == 'restore':
        if not args.file:
            logger.error("--file argument required for restore operation")
            return 1
        success = backup_manager.restore_backup(args.file, args.confirm)
        return 0 if success else 1
    
    elif args.action == 'list':
        backup_manager.list_backups()
        return 0
    
    elif args.action == 'cleanup':
        backup_manager.cleanup_old_backups()
        return 0
    
    elif args.action == 'verify':
        if not args.file:
            logger.error("--file argument required for verify operation")
            return 1
        success = backup_manager.verify_backup(args.file)
        return 0 if success else 1

if __name__ == '__main__':
    sys.exit(main())