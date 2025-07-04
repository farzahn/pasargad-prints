#!/bin/bash

# =============================================================================
# BACKUP CLEANUP SCRIPT FOR PASARGAD PRINTS
# =============================================================================
# This script removes old backups from S3 based on retention policy
# =============================================================================

set -euo pipefail

# Load environment variables from root .env file
if [ -f /app/.env ]; then
    source /app/.env
else
    echo "Error: .env file not found!"
    exit 1
fi

# Configuration
LOG_FILE="/var/log/pasargad_prints_backup_cleanup.log"
RETENTION_DAYS=${BACKUP_RETENTION_DAYS:-30}
DRY_RUN=false

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
    exit 1
}

# Usage function
usage() {
    cat << EOF
Usage: $0 [OPTIONS]

Options:
    --dry-run                   Show what would be deleted without actually deleting
    --retention-days DAYS       Override default retention period (default: $RETENTION_DAYS)
    -h, --help                  Show this help message

Examples:
    $0                                      # Clean up old backups
    $0 --dry-run                           # Show what would be deleted
    $0 --retention-days 60                 # Use 60-day retention

EOF
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --retention-days)
            RETENTION_DAYS="$2"
            shift 2
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

# Check if required tools are installed
command -v aws >/dev/null 2>&1 || error_exit "AWS CLI is required but not installed"

# Start cleanup process
log "Starting backup cleanup process..."
log "Retention period: $RETENTION_DAYS days"
log "S3 Bucket: $S3_BUCKET"
log "S3 Prefix: $S3_PREFIX"

if [ "$DRY_RUN" = true ]; then
    log "DRY RUN MODE: No files will be deleted"
fi

# Calculate cutoff date
CUTOFF_DATE=$(date -d "$RETENTION_DAYS days ago" +%Y-%m-%d 2>/dev/null || date -v-${RETENTION_DAYS}d +%Y-%m-%d 2>/dev/null)
log "Cutoff date: $CUTOFF_DATE (files older than this will be deleted)"

# Get list of all backup files with their dates
log "Fetching backup file list from S3..."
backup_files=$(aws s3 ls "s3://$S3_BUCKET/$S3_PREFIX/" --recursive)

if [ -z "$backup_files" ]; then
    log "No backup files found in S3"
    exit 0
fi

total_files=0
old_files=0
total_size=0
old_size=0

# Process each backup file
while IFS= read -r line; do
    if [[ "$line" =~ \.enc$ ]]; then
        file_date=$(echo "$line" | awk '{print $1}')
        file_time=$(echo "$line" | awk '{print $2}')
        file_size=$(echo "$line" | awk '{print $3}')
        file_path=$(echo "$line" | awk '{print $4}')
        file_name=$(basename "$file_path")
        
        ((total_files++))
        total_size=$((total_size + file_size))
        
        # Compare dates
        if [[ "$file_date" < "$CUTOFF_DATE" ]]; then
            ((old_files++))
            old_size=$((old_size + file_size))
            
            log "OLD FILE: $file_name (Date: $file_date, Size: $(numfmt --to=iec $file_size))"
            
            if [ "$DRY_RUN" = false ]; then
                log "Deleting: s3://$S3_BUCKET/$file_path"
                aws s3 rm "s3://$S3_BUCKET/$file_path" || log "WARNING: Failed to delete $file_path"
            else
                log "WOULD DELETE: s3://$S3_BUCKET/$file_path"
            fi
        else
            log "KEEPING: $file_name (Date: $file_date, Size: $(numfmt --to=iec $file_size))"
        fi
    fi
done <<< "$backup_files"

# Summary
log "Cleanup summary:"
log "  Total files found: $total_files"
log "  Total size: $(numfmt --to=iec $total_size)"
log "  Old files (> $RETENTION_DAYS days): $old_files"
log "  Old files size: $(numfmt --to=iec $old_size)"

if [ "$DRY_RUN" = true ]; then
    log "  Files that WOULD BE deleted: $old_files"
    log "  Space that WOULD BE freed: $(numfmt --to=iec $old_size)"
else
    log "  Files deleted: $old_files"
    log "  Space freed: $(numfmt --to=iec $old_size)"
fi

# Calculate savings
if [ "$total_size" -gt 0 ]; then
    savings_percent=$((old_size * 100 / total_size))
    log "  Storage savings: ${savings_percent}%"
fi

# Send notification about cleanup
log "Sending cleanup notification..."
python3 /app/scripts/send_backup_notification.py \
    --status "success" \
    --backup-file "cleanup_$(date +%Y%m%d)" \
    --size "$old_size" \
    --duration 0 \
    || log "WARNING: Failed to send cleanup notification"

log "Backup cleanup completed successfully"

exit 0