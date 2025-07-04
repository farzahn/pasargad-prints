#!/usr/bin/env python3

"""
Backup Notification Script for Pasargad Prints
Sends notifications about backup status via email and logs
"""

import argparse
import sys
import os
import logging
from datetime import datetime, timedelta
from pathlib import Path
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib
import json

# Load environment variables from root .env file
from dotenv import load_dotenv
root_dir = Path(__file__).resolve().parent.parent.parent
env_path = root_dir / '.env'
load_dotenv(env_path)

# Add Django settings
sys.path.append('/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pasargad_prints.settings_production')

import django
django.setup()

from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
# Import config from our custom module
from pathlib import Path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))
from pasargad_prints.config import config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s',
    handlers=[
        logging.FileHandler('/var/log/pasargad_prints_backup_notifications.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def format_size(size_bytes):
    """Format bytes to human readable format"""
    if size_bytes == 0:
        return "0B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    
    return f"{size_bytes:.2f} {size_names[i]}"

def format_duration(seconds):
    """Format seconds to human readable duration"""
    if seconds < 60:
        return f"{seconds} seconds"
    elif seconds < 3600:
        minutes = seconds // 60
        return f"{minutes} minutes"
    else:
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        return f"{hours} hours, {minutes} minutes"

def send_email_notification(status, backup_file, size, duration, error_message=None):
    """Send email notification about backup status"""
    try:
        # Email configuration
        from_email = config('DEFAULT_FROM_EMAIL', default='noreply@pasargadprints.com')
        admin_email = config('ADMIN_EMAIL', default='admin@pasargadprints.com')
        
        # Prepare email content
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        if status == 'success':
            subject = f"✅ Database Backup Successful - {timestamp}"
            template = 'backup_success'
        else:
            subject = f"❌ Database Backup Failed - {timestamp}"
            template = 'backup_failure'
        
        # Context for email template
        context = {
            'status': status,
            'backup_file': backup_file,
            'size': format_size(size) if size else 'N/A',
            'duration': format_duration(duration) if duration else 'N/A',
            'timestamp': timestamp,
            'error_message': error_message,
            'database_name': config('DB_NAME', default='pasargad_prints_prod'),
            'environment': config('ENVIRONMENT', default='production'),
        }
        
        # Prepare email content
        html_content = f"""
        <html>
        <body>
            <h2>Database Backup Report</h2>
            <table border="1" cellpadding="5" cellspacing="0">
                <tr><td><strong>Status:</strong></td><td>{'✅ Success' if status == 'success' else '❌ Failed'}</td></tr>
                <tr><td><strong>Timestamp:</strong></td><td>{timestamp}</td></tr>
                <tr><td><strong>Database:</strong></td><td>{context['database_name']}</td></tr>
                <tr><td><strong>Environment:</strong></td><td>{context['environment']}</td></tr>
                <tr><td><strong>Backup File:</strong></td><td>{backup_file}</td></tr>
                <tr><td><strong>Size:</strong></td><td>{context['size']}</td></tr>
                <tr><td><strong>Duration:</strong></td><td>{context['duration']}</td></tr>
                {'<tr><td><strong>Error:</strong></td><td>' + str(error_message) + '</td></tr>' if error_message else ''}
            </table>
            
            <h3>Backup Details</h3>
            <ul>
                <li><strong>S3 Bucket:</strong> {config('BACKUP_S3_BUCKET', default='N/A')}</li>
                <li><strong>Retention:</strong> {config('BACKUP_RETENTION_DAYS', default='30')} days</li>
                <li><strong>Encryption:</strong> AES-256-CBC</li>
                <li><strong>Compression:</strong> gzip</li>
            </ul>
            
            {'<p><strong>Note:</strong> This was a successful backup. Your data is safely stored in S3.</p>' if status == 'success' else '<p><strong>Action Required:</strong> Please check the backup system and resolve any issues.</p>'}
        </body>
        </html>
        """
        
        text_content = f"""
        Database Backup Report
        =====================
        
        Status: {'✅ Success' if status == 'success' else '❌ Failed'}
        Timestamp: {timestamp}
        Database: {context['database_name']}
        Environment: {context['environment']}
        Backup File: {backup_file}
        Size: {context['size']}
        Duration: {context['duration']}
        {'Error: ' + str(error_message) if error_message else ''}
        
        Backup Details:
        - S3 Bucket: {config('BACKUP_S3_BUCKET', default='N/A')}
        - Retention: {config('BACKUP_RETENTION_DAYS', default='30')} days
        - Encryption: AES-256-CBC
        - Compression: gzip
        
        {'Note: This was a successful backup. Your data is safely stored in S3.' if status == 'success' else 'Action Required: Please check the backup system and resolve any issues.'}
        """
        
        # Send email using Django's send_mail
        send_mail(
            subject=subject,
            message=text_content,
            from_email=from_email,
            recipient_list=[admin_email],
            html_message=html_content,
            fail_silently=False,
        )
        
        logger.info(f"Email notification sent successfully to {admin_email}")
        
    except Exception as e:
        logger.error(f"Failed to send email notification: {str(e)}")
        raise

def send_slack_notification(status, backup_file, size, duration, error_message=None):
    """Send Slack notification about backup status"""
    try:
        slack_webhook_url = config('SLACK_WEBHOOK_URL', default='')
        if not slack_webhook_url:
            logger.info("Slack webhook URL not configured, skipping Slack notification")
            return
        
        import requests
        
        # Prepare Slack message
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        if status == 'success':
            color = 'good'
            emoji = '✅'
            title = 'Database Backup Successful'
        else:
            color = 'danger'
            emoji = '❌'
            title = 'Database Backup Failed'
        
        payload = {
            'username': 'Pasargad Prints Backup Bot',
            'icon_emoji': ':floppy_disk:',
            'attachments': [{
                'color': color,
                'title': f'{emoji} {title}',
                'fields': [
                    {'title': 'Timestamp', 'value': timestamp, 'short': True},
                    {'title': 'Database', 'value': config('DB_NAME', default='pasargad_prints_prod'), 'short': True},
                    {'title': 'Environment', 'value': config('ENVIRONMENT', default='production'), 'short': True},
                    {'title': 'Backup File', 'value': backup_file, 'short': True},
                    {'title': 'Size', 'value': format_size(size) if size else 'N/A', 'short': True},
                    {'title': 'Duration', 'value': format_duration(duration) if duration else 'N/A', 'short': True},
                ],
                'footer': 'Pasargad Prints Backup System',
                'ts': int(datetime.now().timestamp())
            }]
        }
        
        if error_message:
            payload['attachments'][0]['fields'].append({
                'title': 'Error', 'value': str(error_message), 'short': False
            })
        
        response = requests.post(slack_webhook_url, json=payload, timeout=30)
        response.raise_for_status()
        
        logger.info("Slack notification sent successfully")
        
    except Exception as e:
        logger.error(f"Failed to send Slack notification: {str(e)}")
        # Don't raise here, as this is not critical

def log_backup_event(status, backup_file, size, duration, error_message=None):
    """Log backup event to structured log"""
    try:
        event_data = {
            'event_type': 'database_backup',
            'timestamp': datetime.now().isoformat(),
            'status': status,
            'backup_file': backup_file,
            'size_bytes': size,
            'duration_seconds': duration,
            'database_name': config('DB_NAME', default='pasargad_prints_prod'),
            'environment': config('ENVIRONMENT', default='production'),
            'error_message': error_message,
        }
        
        # Log to structured backup log
        backup_logger = logging.getLogger('backup_events')
        backup_logger.info(json.dumps(event_data))
        
    except Exception as e:
        logger.error(f"Failed to log backup event: {str(e)}")

def main():
    parser = argparse.ArgumentParser(description='Send backup notifications')
    parser.add_argument('--status', required=True, choices=['success', 'failure'], 
                       help='Backup status')
    parser.add_argument('--backup-file', required=True, 
                       help='Backup file name')
    parser.add_argument('--size', type=int, default=0, 
                       help='Backup file size in bytes')
    parser.add_argument('--duration', type=int, default=0, 
                       help='Backup duration in seconds')
    parser.add_argument('--error-message', default=None, 
                       help='Error message if backup failed')
    
    args = parser.parse_args()
    
    try:
        logger.info(f"Sending backup notification - Status: {args.status}")
        
        # Log backup event
        log_backup_event(
            status=args.status,
            backup_file=args.backup_file,
            size=args.size,
            duration=args.duration,
            error_message=args.error_message
        )
        
        # Send email notification
        send_email_notification(
            status=args.status,
            backup_file=args.backup_file,
            size=args.size,
            duration=args.duration,
            error_message=args.error_message
        )
        
        # Send Slack notification
        send_slack_notification(
            status=args.status,
            backup_file=args.backup_file,
            size=args.size,
            duration=args.duration,
            error_message=args.error_message
        )
        
        logger.info("Backup notification sent successfully")
        
    except Exception as e:
        logger.error(f"Failed to send backup notification: {str(e)}")
        sys.exit(1)

if __name__ == '__main__':
    main()