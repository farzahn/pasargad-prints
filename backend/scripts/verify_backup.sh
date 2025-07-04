#!/bin/bash

# =============================================================================
# BACKUP VERIFICATION SCRIPT FOR PASARGAD PRINTS
# =============================================================================
# This script verifies the integrity of database backups
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
VERIFY_DIR="/tmp/verify"
LOG_FILE="/var/log/pasargad_prints_backup_verify.log"
ENCRYPTION_KEY=${BACKUP_ENCRYPTION_KEY:-$(openssl rand -hex 32)}

# S3 Configuration
S3_BUCKET=${BACKUP_S3_BUCKET}
S3_PREFIX="database-backups"

# Command line arguments
BACKUP_FILE=""
VERIFY_ALL=false

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
    rm -rf "$VERIFY_DIR"
}

# Usage function
usage() {
    cat << EOF
Usage: $0 [OPTIONS]

Options:
    -f, --file BACKUP_FILE      Verify specific backup file
    -a, --all                   Verify all backups in S3
    -h, --help                  Show this help message

Examples:
    $0 --file pasargad_prints_backup_20240101_120000.sql.gz.enc
    $0 --all

EOF
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -f|--file)
            BACKUP_FILE="$2"
            shift 2
            ;;
        -a|--all)
            VERIFY_ALL=true
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

# Create verify directory
mkdir -p "$VERIFY_DIR"

# Check if required tools are installed
command -v gunzip >/dev/null 2>&1 || error_exit "gunzip is required but not installed"
command -v openssl >/dev/null 2>&1 || error_exit "openssl is required but not installed"
command -v aws >/dev/null 2>&1 || error_exit "AWS CLI is required but not installed"

verify_backup_file() {
    local backup_file="$1"
    log "Verifying backup file: $backup_file"
    
    # Download backup from S3
    log "Downloading backup from S3..."
    aws s3 cp "s3://$S3_BUCKET/$S3_PREFIX/$backup_file" "$VERIFY_DIR/$backup_file" \
        || { log "ERROR: Failed to download $backup_file"; return 1; }
    
    # Check file size
    local file_size=$(stat -f%z "$VERIFY_DIR/$backup_file" 2>/dev/null || stat -c%s "$VERIFY_DIR/$backup_file" 2>/dev/null)
    if [ "$file_size" -eq 0 ]; then
        log "ERROR: Backup file is empty"
        return 1
    fi
    
    log "File size: $(numfmt --to=iec $file_size)"
    
    # Verify file can be decrypted
    log "Testing decryption..."
    local compressed_file="${backup_file%.enc}"
    openssl enc -aes-256-cbc -d -salt -in "$VERIFY_DIR/$backup_file" -out "$VERIFY_DIR/$compressed_file" -pass pass:"$ENCRYPTION_KEY" \
        || { log "ERROR: Decryption failed"; return 1; }
    
    # Verify file can be decompressed
    log "Testing decompression..."
    local sql_file="${compressed_file%.gz}"
    gunzip -t "$VERIFY_DIR/$compressed_file" \
        || { log "ERROR: Decompression test failed"; return 1; }
    
    # Extract a small portion to verify SQL structure
    log "Testing SQL structure..."
    gunzip -c "$VERIFY_DIR/$compressed_file" | head -20 | grep -q "PostgreSQL database dump" \
        || { log "ERROR: Invalid SQL structure"; return 1; }
    
    log "✅ Backup verification successful: $backup_file"
    
    # Cleanup this verification
    rm -f "$VERIFY_DIR/$backup_file" "$VERIFY_DIR/$compressed_file"
    
    return 0
}

# Start verification process
log "Starting backup verification process..."

if [ "$VERIFY_ALL" = true ]; then
    log "Verifying all backups in S3..."
    
    # Get list of all backup files
    backup_files=$(aws s3 ls "s3://$S3_BUCKET/$S3_PREFIX/" | grep -E "\.enc$" | awk '{print $4}' | sort -r)
    
    if [ -z "$backup_files" ]; then
        error_exit "No backup files found in S3"
    fi
    
    total_files=$(echo "$backup_files" | wc -l)
    verified_files=0
    failed_files=0
    
    log "Found $total_files backup files to verify"
    
    while IFS= read -r backup_file; do
        if verify_backup_file "$backup_file"; then
            ((verified_files++))
        else
            ((failed_files++))
        fi
    done <<< "$backup_files"
    
    log "Verification complete: $verified_files verified, $failed_files failed"
    
    if [ "$failed_files" -gt 0 ]; then
        error_exit "Some backup verifications failed"
    fi
    
elif [ -n "$BACKUP_FILE" ]; then
    verify_backup_file "$BACKUP_FILE" || error_exit "Backup verification failed"
else
    log "No backup file specified. Use --all to verify all backups or --file to verify specific backup."
    usage
    exit 1
fi

# Cleanup
cleanup

log "Backup verification completed successfully"

exit 0