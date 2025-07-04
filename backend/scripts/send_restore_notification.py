#!/usr/bin/env python3

"""
Restore Notification Script for Pasargad Prints
Sends notifications about database restore status via email and logs
"""

import argparse
import sys
import os
import logging
from datetime import datetime
import json

# Load environment variables from root .env file
from dotenv import load_dotenv
from pathlib import Path
root_dir = Path(__file__).resolve().parent.parent.parent
env_path = root_dir / '.env'
load_dotenv(env_path)

# Add Django settings
sys.path.append('/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pasargad_prints.settings_production')

import django
django.setup()

from django.core.mail import send_mail
# Import config from our custom module
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))
from pasargad_prints.config import config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s',
    handlers=[
        logging.FileHandler('/var/log/pasargad_prints_restore_notifications.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

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

def send_email_notification(status, backup_file, target_db, duration, error_message=None):
    """Send email notification about restore status"""
    try:
        # Email configuration
        from_email = config('DEFAULT_FROM_EMAIL', default='noreply@pasargadprints.com')
        admin_email = config('ADMIN_EMAIL', default='admin@pasargadprints.com')
        
        # Prepare email content
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        if status == 'success':
            subject = f"✅ Database Restore Successful - {timestamp}"
        else:
            subject = f"❌ Database Restore Failed - {timestamp}"
        
        # Context for email template
        context = {
            'status': status,
            'backup_file': backup_file,
            'target_db': target_db,
            'duration': format_duration(duration) if duration else 'N/A',
            'timestamp': timestamp,
            'error_message': error_message,
            'environment': config('ENVIRONMENT', default='production'),
        }
        
        # Prepare email content
        html_content = f"""
        <html>
        <body>
            <h2>Database Restore Report</h2>
            <table border="1" cellpadding="5" cellspacing="0">
                <tr><td><strong>Status:</strong></td><td>{'✅ Success' if status == 'success' else '❌ Failed'}</td></tr>
                <tr><td><strong>Timestamp:</strong></td><td>{timestamp}</td></tr>
                <tr><td><strong>Target Database:</strong></td><td>{target_db}</td></tr>
                <tr><td><strong>Environment:</strong></td><td>{context['environment']}</td></tr>
                <tr><td><strong>Source Backup:</strong></td><td>{backup_file}</td></tr>
                <tr><td><strong>Duration:</strong></td><td>{context['duration']}</td></tr>
                {'<tr><td><strong>Error:</strong></td><td>' + str(error_message) + '</td></tr>' if error_message else ''}
            </table>
            
            <h3>Restore Details</h3>
            <ul>
                <li><strong>S3 Bucket:</strong> {config('BACKUP_S3_BUCKET', default='N/A')}</li>
                <li><strong>Encryption:</strong> AES-256-CBC</li>
                <li><strong>Compression:</strong> gzip</li>
            </ul>
            
            {'<p><strong>Note:</strong> The database has been successfully restored. Please verify the application is working correctly.</p>' if status == 'success' else '<p><strong>Action Required:</strong> Please check the restore system and resolve any issues.</p>'}
            
            <p><strong>Warning:</strong> If this restore was performed on a production database, please ensure all services are restarted and tested.</p>
        </body>
        </html>
        """
        
        text_content = f"""
        Database Restore Report
        ======================
        
        Status: {'✅ Success' if status == 'success' else '❌ Failed'}
        Timestamp: {timestamp}
        Target Database: {target_db}
        Environment: {context['environment']}
        Source Backup: {backup_file}
        Duration: {context['duration']}
        {'Error: ' + str(error_message) if error_message else ''}
        
        Restore Details:
        - S3 Bucket: {config('BACKUP_S3_BUCKET', default='N/A')}
        - Encryption: AES-256-CBC
        - Compression: gzip
        
        {'Note: The database has been successfully restored. Please verify the application is working correctly.' if status == 'success' else 'Action Required: Please check the restore system and resolve any issues.'}
        
        Warning: If this restore was performed on a production database, please ensure all services are restarted and tested.
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

def send_slack_notification(status, backup_file, target_db, duration, error_message=None):
    """Send Slack notification about restore status"""
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
            title = 'Database Restore Successful'
        else:
            color = 'danger'
            emoji = '❌'
            title = 'Database Restore Failed'
        
        payload = {
            'username': 'Pasargad Prints Restore Bot',
            'icon_emoji': ':arrows_counterclockwise:',
            'attachments': [{
                'color': color,
                'title': f'{emoji} {title}',
                'fields': [
                    {'title': 'Timestamp', 'value': timestamp, 'short': True},
                    {'title': 'Target Database', 'value': target_db, 'short': True},
                    {'title': 'Environment', 'value': config('ENVIRONMENT', default='production'), 'short': True},
                    {'title': 'Source Backup', 'value': backup_file, 'short': True},
                    {'title': 'Duration', 'value': format_duration(duration) if duration else 'N/A', 'short': True},
                ],
                'footer': 'Pasargad Prints Restore System',
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

def log_restore_event(status, backup_file, target_db, duration, error_message=None):
    """Log restore event to structured log"""
    try:
        event_data = {
            'event_type': 'database_restore',
            'timestamp': datetime.now().isoformat(),
            'status': status,
            'backup_file': backup_file,
            'target_database': target_db,
            'duration_seconds': duration,
            'environment': config('ENVIRONMENT', default='production'),
            'error_message': error_message,
        }
        
        # Log to structured restore log
        restore_logger = logging.getLogger('restore_events')
        restore_logger.info(json.dumps(event_data))
        
    except Exception as e:
        logger.error(f"Failed to log restore event: {str(e)}")

def main():
    parser = argparse.ArgumentParser(description='Send restore notifications')
    parser.add_argument('--status', required=True, choices=['success', 'failure'], 
                       help='Restore status')
    parser.add_argument('--backup-file', required=True, 
                       help='Source backup file name')
    parser.add_argument('--target-db', required=True, 
                       help='Target database name')
    parser.add_argument('--duration', type=int, default=0, 
                       help='Restore duration in seconds')
    parser.add_argument('--error-message', default=None, 
                       help='Error message if restore failed')
    
    args = parser.parse_args()
    
    try:
        logger.info(f"Sending restore notification - Status: {args.status}")
        
        # Log restore event
        log_restore_event(
            status=args.status,
            backup_file=args.backup_file,
            target_db=args.target_db,
            duration=args.duration,
            error_message=args.error_message
        )
        
        # Send email notification
        send_email_notification(
            status=args.status,
            backup_file=args.backup_file,
            target_db=args.target_db,
            duration=args.duration,
            error_message=args.error_message
        )
        
        # Send Slack notification
        send_slack_notification(
            status=args.status,
            backup_file=args.backup_file,
            target_db=args.target_db,
            duration=args.duration,
            error_message=args.error_message
        )
        
        logger.info("Restore notification sent successfully")
        
    except Exception as e:
        logger.error(f"Failed to send restore notification: {str(e)}")
        sys.exit(1)

if __name__ == '__main__':
    main()