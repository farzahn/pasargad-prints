#!/bin/bash

# Production Database Backup Script
# Automatically backs up PostgreSQL database with compression and retention

set -e

# Configuration
BACKUP_DIR="/app/backups"
DB_CONTAINER="pasargad-prints_db_1"
RETENTION_DAYS=30
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="pasargad_prints_backup_${TIMESTAMP}.sql.gz"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

print_status() {
    echo -e "${GREEN}[BACKUP]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Create backup directory if it doesn't exist
mkdir -p "$BACKUP_DIR"

print_status "Starting database backup..."

# Check if database container is running
if ! docker ps | grep -q "$DB_CONTAINER"; then
    print_error "Database container '$DB_CONTAINER' is not running."
    exit 1
fi

# Perform backup
print_status "Creating compressed database dump..."
docker exec "$DB_CONTAINER" pg_dump -U postgres pasargad_prints | gzip > "$BACKUP_DIR/$BACKUP_FILE"

# Verify backup was created
if [ -f "$BACKUP_DIR/$BACKUP_FILE" ]; then
    BACKUP_SIZE=$(du -h "$BACKUP_DIR/$BACKUP_FILE" | cut -f1)
    print_status "Backup created successfully: $BACKUP_FILE ($BACKUP_SIZE)"
else
    print_error "Backup failed to create."
    exit 1
fi

# Clean up old backups
print_status "Cleaning up backups older than $RETENTION_DAYS days..."
find "$BACKUP_DIR" -name "pasargad_prints_backup_*.sql.gz" -type f -mtime +$RETENTION_DAYS -delete

# List current backups
print_status "Current backups:"
ls -lh "$BACKUP_DIR"/pasargad_prints_backup_*.sql.gz 2>/dev/null || print_warning "No backups found."

# Send notification (if configured)
if [ -n "$BACKUP_NOTIFICATION_WEBHOOK" ]; then
    curl -X POST "$BACKUP_NOTIFICATION_WEBHOOK" \
        -H "Content-Type: application/json" \
        -d "{\"text\":\"Database backup completed: $BACKUP_FILE ($BACKUP_SIZE)\"}" \
        >/dev/null 2>&1 || print_warning "Failed to send notification."
fi

print_status "Backup process completed successfully."