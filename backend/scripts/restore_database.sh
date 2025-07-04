#!/bin/bash

# =============================================================================
# DATABASE RESTORE SCRIPT FOR PASARGAD PRINTS
# =============================================================================
# This script restores the PostgreSQL database from encrypted S3 backups
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
RESTORE_DIR="/tmp/restore"
LOG_FILE="/var/log/pasargad_prints_restore.log"
ENCRYPTION_KEY=${BACKUP_ENCRYPTION_KEY:-$(openssl rand -hex 32)}

# S3 Configuration
S3_BUCKET=${BACKUP_S3_BUCKET}
S3_PREFIX="database-backups"

# Command line arguments
BACKUP_FILE=""
FORCE_RESTORE=false
LIST_BACKUPS=false
RESTORE_TO_NEW_DB=false
NEW_DB_NAME=""

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
    rm -rf "$RESTORE_DIR"
}

# Usage function
usage() {
    cat << EOF
Usage: $0 [OPTIONS]

Options:
    -f, --file BACKUP_FILE      Specific backup file to restore
    -l, --list                  List available backups
    -n, --new-db DB_NAME        Restore to a new database
    --force                     Force restore without confirmation
    -h, --help                  Show this help message

Examples:
    $0 --list                                           # List available backups
    $0 --file pasargad_prints_backup_20240101_120000.sql.gz.enc  # Restore specific backup
    $0 --new-db pasargad_prints_test --file backup.sql.gz.enc    # Restore to new database
    $0 --force --file backup.sql.gz.enc                          # Force restore without confirmation

EOF
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -f|--file)
            BACKUP_FILE="$2"
            shift 2
            ;;
        -l|--list)
            LIST_BACKUPS=true
            shift
            ;;
        -n|--new-db)
            RESTORE_TO_NEW_DB=true
            NEW_DB_NAME="$2"
            shift 2
            ;;
        --force)
            FORCE_RESTORE=true
            shift
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            usage
            exit 1
            ;;
    esac
done

# Create restore directory
mkdir -p "$RESTORE_DIR"

# List available backups
if [ "$LIST_BACKUPS" = true ]; then
    log "Available backups in S3:"
    aws s3 ls "s3://$S3_BUCKET/$S3_PREFIX/" --human-readable --summarize | grep -E "\.enc$" | sort -r
    exit 0
fi

# Validate backup file
if [ -z "$BACKUP_FILE" ]; then
    log "No backup file specified. Use --list to see available backups."
    usage
    exit 1
fi

# Check if required tools are installed
command -v pg_restore >/dev/null 2>&1 || error_exit "pg_restore is required but not installed"
command -v psql >/dev/null 2>&1 || error_exit "psql is required but not installed"
command -v gunzip >/dev/null 2>&1 || error_exit "gunzip is required but not installed"
command -v openssl >/dev/null 2>&1 || error_exit "openssl is required but not installed"
command -v aws >/dev/null 2>&1 || error_exit "AWS CLI is required but not installed"

# Determine target database
if [ "$RESTORE_TO_NEW_DB" = true ]; then
    TARGET_DB="$NEW_DB_NAME"
    log "Restoring to new database: $TARGET_DB"
else
    TARGET_DB="$DB_NAME"
    log "Restoring to existing database: $TARGET_DB"
fi

# Confirmation prompt
if [ "$FORCE_RESTORE" = false ]; then
    echo "WARNING: This will restore the database '$TARGET_DB' from backup '$BACKUP_FILE'."
    echo "This operation will overwrite all existing data in the database."
    read -p "Are you sure you want to continue? (yes/no): " -r
    if [[ ! $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
        log "Restore cancelled by user"
        exit 0
    fi
fi

# Start restore process
log "Starting database restore process..."
log "Source backup: $BACKUP_FILE"
log "Target database: $TARGET_DB"

# Download backup from S3
log "Downloading backup from S3..."
aws s3 cp "s3://$S3_BUCKET/$S3_PREFIX/$BACKUP_FILE" "$RESTORE_DIR/$BACKUP_FILE" \
    || error_exit "Failed to download backup from S3"

# Verify download
if [ ! -f "$RESTORE_DIR/$BACKUP_FILE" ]; then
    error_exit "Downloaded backup file not found"
fi

ENCRYPTED_SIZE=$(stat -f%z "$RESTORE_DIR/$BACKUP_FILE" 2>/dev/null || stat -c%s "$RESTORE_DIR/$BACKUP_FILE" 2>/dev/null)
log "Backup downloaded successfully. Size: $(numfmt --to=iec $ENCRYPTED_SIZE)"

# Decrypt backup
log "Decrypting backup..."
COMPRESSED_FILE="${BACKUP_FILE%.enc}"
openssl enc -aes-256-cbc -d -salt -in "$RESTORE_DIR/$BACKUP_FILE" -out "$RESTORE_DIR/$COMPRESSED_FILE" -pass pass:"$ENCRYPTION_KEY" \
    || error_exit "Decryption failed"

# Decompress backup
log "Decompressing backup..."
SQL_FILE="${COMPRESSED_FILE%.gz}"
gunzip -c "$RESTORE_DIR/$COMPRESSED_FILE" > "$RESTORE_DIR/$SQL_FILE" \
    || error_exit "Decompression failed"

RESTORE_SIZE=$(stat -f%z "$RESTORE_DIR/$SQL_FILE" 2>/dev/null || stat -c%s "$RESTORE_DIR/$SQL_FILE" 2>/dev/null)
log "Backup decompressed successfully. Size: $(numfmt --to=iec $RESTORE_SIZE)"

# Create new database if needed
if [ "$RESTORE_TO_NEW_DB" = true ]; then
    log "Creating new database: $NEW_DB_NAME"
    PGPASSWORD="$DB_PASSWORD" psql \
        --host="$DB_HOST" \
        --port="$DB_PORT" \
        --username="$DB_USER" \
        --dbname="postgres" \
        --command="CREATE DATABASE \"$NEW_DB_NAME\";" \
        || error_exit "Failed to create new database"
fi

# Drop existing connections to target database
log "Dropping existing connections to database..."
PGPASSWORD="$DB_PASSWORD" psql \
    --host="$DB_HOST" \
    --port="$DB_PORT" \
    --username="$DB_USER" \
    --dbname="postgres" \
    --command="SELECT pg_terminate_backend(pg_stat_activity.pid) FROM pg_stat_activity WHERE pg_stat_activity.datname = '$TARGET_DB' AND pid <> pg_backend_pid();" \
    || log "WARNING: Failed to drop some connections"

# Restore database
log "Restoring database..."
PGPASSWORD="$DB_PASSWORD" pg_restore \
    --host="$DB_HOST" \
    --port="$DB_PORT" \
    --username="$DB_USER" \
    --dbname="$TARGET_DB" \
    --verbose \
    --clean \
    --no-owner \
    --no-privileges \
    --single-transaction \
    "$RESTORE_DIR/$SQL_FILE" \
    || error_exit "Database restore failed"

# Verify restore
log "Verifying restore..."
TABLE_COUNT=$(PGPASSWORD="$DB_PASSWORD" psql \
    --host="$DB_HOST" \
    --port="$DB_PORT" \
    --username="$DB_USER" \
    --dbname="$TARGET_DB" \
    --tuples-only \
    --command="SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';" \
    | tr -d ' ')

if [ "$TABLE_COUNT" -eq 0 ]; then
    error_exit "Restore verification failed: No tables found"
fi

log "Restore verification successful. Tables restored: $TABLE_COUNT"

# Update database statistics
log "Updating database statistics..."
PGPASSWORD="$DB_PASSWORD" psql \
    --host="$DB_HOST" \
    --port="$DB_PORT" \
    --username="$DB_USER" \
    --dbname="$TARGET_DB" \
    --command="ANALYZE;" \
    || log "WARNING: Failed to update database statistics"

# Send restore notification
log "Sending restore notification..."
python3 /app/scripts/send_restore_notification.py \
    --status "success" \
    --backup-file "$BACKUP_FILE" \
    --target-db "$TARGET_DB" \
    --duration "$(($(date +%s) - $(date -d "$TIMESTAMP" +%s 2>/dev/null || echo $(date +%s))))" \
    || log "WARNING: Failed to send restore notification"

# Cleanup temporary files
cleanup

log "Database restore completed successfully"
log "Source backup: $BACKUP_FILE"
log "Target database: $TARGET_DB"
log "Tables restored: $TABLE_COUNT"

exit 0