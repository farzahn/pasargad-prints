#!/bin/bash

# =============================================================================
# DATABASE BACKUP SCRIPT FOR PASARGAD PRINTS
# =============================================================================
# This script creates encrypted backups of the PostgreSQL database
# and uploads them to S3 for secure storage.
# =============================================================================

set -euo pipefail

# Load environment variables
if [ -f /app/.env.production ]; then
    source /app/.env.production
else
    echo "Error: .env.production file not found!"
    exit 1
fi

# Configuration
BACKUP_DIR="/tmp/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="pasargad_prints_backup_${TIMESTAMP}.sql"
COMPRESSED_FILE="${BACKUP_FILE}.gz"
ENCRYPTED_FILE="${COMPRESSED_FILE}.enc"
LOG_FILE="/var/log/pasargad_prints_backup.log"
RETENTION_DAYS=${BACKUP_RETENTION_DAYS:-30}
ENCRYPTION_KEY=${BACKUP_ENCRYPTION_KEY:-$(openssl rand -hex 32)}

# S3 Configuration
S3_BUCKET=${BACKUP_S3_BUCKET}
S3_PREFIX="database-backups"

# Logging function
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Error handling
error_exit() {
    log "ERROR: $1"
    cleanup
    exit 1
}

# Cleanup function
cleanup() {
    log "Cleaning up temporary files..."
    rm -f "$BACKUP_DIR/$BACKUP_FILE" "$BACKUP_DIR/$COMPRESSED_FILE" "$BACKUP_DIR/$ENCRYPTED_FILE"
}

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Start backup process
log "Starting database backup process..."
log "Database: $DB_NAME"
log "Host: $DB_HOST"
log "Backup file: $BACKUP_FILE"

# Check if required tools are installed
command -v pg_dump >/dev/null 2>&1 || error_exit "pg_dump is required but not installed"
command -v gzip >/dev/null 2>&1 || error_exit "gzip is required but not installed"
command -v openssl >/dev/null 2>&1 || error_exit "openssl is required but not installed"
command -v aws >/dev/null 2>&1 || error_exit "AWS CLI is required but not installed"

# Create database backup
log "Creating database backup..."
PGPASSWORD="$DB_PASSWORD" pg_dump \
    --host="$DB_HOST" \
    --port="$DB_PORT" \
    --username="$DB_USER" \
    --dbname="$DB_NAME" \
    --verbose \
    --clean \
    --no-owner \
    --no-privileges \
    --format=custom \
    --file="$BACKUP_DIR/$BACKUP_FILE" \
    || error_exit "Database backup failed"

# Verify backup file exists and is not empty
if [ ! -s "$BACKUP_DIR/$BACKUP_FILE" ]; then
    error_exit "Backup file is empty or does not exist"
fi

BACKUP_SIZE=$(stat -f%z "$BACKUP_DIR/$BACKUP_FILE" 2>/dev/null || stat -c%s "$BACKUP_DIR/$BACKUP_FILE" 2>/dev/null)
log "Backup created successfully. Size: $(numfmt --to=iec $BACKUP_SIZE)"

# Compress backup
log "Compressing backup..."
gzip -c "$BACKUP_DIR/$BACKUP_FILE" > "$BACKUP_DIR/$COMPRESSED_FILE" || error_exit "Compression failed"

COMPRESSED_SIZE=$(stat -f%z "$BACKUP_DIR/$COMPRESSED_FILE" 2>/dev/null || stat -c%s "$BACKUP_DIR/$COMPRESSED_FILE" 2>/dev/null)
log "Backup compressed successfully. Size: $(numfmt --to=iec $COMPRESSED_SIZE)"

# Encrypt backup
log "Encrypting backup..."
openssl enc -aes-256-cbc -salt -in "$BACKUP_DIR/$COMPRESSED_FILE" -out "$BACKUP_DIR/$ENCRYPTED_FILE" -pass pass:"$ENCRYPTION_KEY" || error_exit "Encryption failed"

ENCRYPTED_SIZE=$(stat -f%z "$BACKUP_DIR/$ENCRYPTED_FILE" 2>/dev/null || stat -c%s "$BACKUP_DIR/$ENCRYPTED_FILE" 2>/dev/null)
log "Backup encrypted successfully. Size: $(numfmt --to=iec $ENCRYPTED_SIZE)"

# Upload to S3
log "Uploading backup to S3..."
aws s3 cp "$BACKUP_DIR/$ENCRYPTED_FILE" "s3://$S3_BUCKET/$S3_PREFIX/$ENCRYPTED_FILE" \
    --storage-class STANDARD_IA \
    --metadata "database=$DB_NAME,timestamp=$TIMESTAMP,size=$ENCRYPTED_SIZE" \
    || error_exit "S3 upload failed"

log "Backup uploaded to S3 successfully"

# Verify S3 upload
S3_SIZE=$(aws s3 ls "s3://$S3_BUCKET/$S3_PREFIX/$ENCRYPTED_FILE" --summarize | grep "Total Size" | awk '{print $3}')
if [ "$S3_SIZE" != "$ENCRYPTED_SIZE" ]; then
    error_exit "S3 upload verification failed. Local: $ENCRYPTED_SIZE, S3: $S3_SIZE"
fi

log "S3 upload verified successfully"

# Clean up old backups
log "Cleaning up old backups (older than $RETENTION_DAYS days)..."
CUTOFF_DATE=$(date -d "$RETENTION_DAYS days ago" +%Y-%m-%d 2>/dev/null || date -v-${RETENTION_DAYS}d +%Y-%m-%d 2>/dev/null)
aws s3 ls "s3://$S3_BUCKET/$S3_PREFIX/" | while read -r line; do
    BACKUP_DATE=$(echo "$line" | awk '{print $1}')
    BACKUP_KEY=$(echo "$line" | awk '{print $4}')
    
    if [[ "$BACKUP_DATE" < "$CUTOFF_DATE" ]]; then
        log "Deleting old backup: $BACKUP_KEY"
        aws s3 rm "s3://$S3_BUCKET/$S3_PREFIX/$BACKUP_KEY" || log "WARNING: Failed to delete $BACKUP_KEY"
    fi
done

# Send backup notification
log "Sending backup notification..."
python3 /app/scripts/send_backup_notification.py \
    --status "success" \
    --backup-file "$ENCRYPTED_FILE" \
    --size "$ENCRYPTED_SIZE" \
    --duration "$(($(date +%s) - $(date -d "$TIMESTAMP" +%s 2>/dev/null || echo $(date +%s))))" \
    || log "WARNING: Failed to send backup notification"

# Cleanup temporary files
cleanup

log "Database backup completed successfully"
log "Backup file: s3://$S3_BUCKET/$S3_PREFIX/$ENCRYPTED_FILE"
log "Backup size: $(numfmt --to=iec $ENCRYPTED_SIZE)"

exit 0