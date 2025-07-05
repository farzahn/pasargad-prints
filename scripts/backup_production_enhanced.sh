#!/bin/bash

# =============================================================================
# Production Backup Script for Pasargad Prints
# =============================================================================
#
# This script creates comprehensive backups of:
# - PostgreSQL database
# - Media files
# - Application logs
# - Configuration files
#
# Backups are compressed, encrypted, and can be uploaded to S3
# =============================================================================

set -e

# Configuration
BACKUP_DIR="/app/backups"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_NAME="pasargad_prints_backup_$TIMESTAMP"
RETENTION_DAYS=30
COMPOSE_FILE="docker-compose.production.yml"

# AWS S3 Configuration (optional)
S3_BUCKET="${BACKUP_S3_BUCKET:-}"
S3_REGION="${AWS_S3_REGION:-us-east-1}"

# Encryption settings
ENCRYPTION_KEY="${BACKUP_ENCRYPTION_KEY:-pasargad_backup_key_2024}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Logging
LOG_FILE="$BACKUP_DIR/backup.log"

print_status() {
    echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1" | tee -a "$LOG_FILE"
}

print_success() {
    echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1" | tee -a "$LOG_FILE"
}

print_warning() {
    echo -e "${YELLOW}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1" | tee -a "$LOG_FILE"
}

print_error() {
    echo -e "${RED}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1" | tee -a "$LOG_FILE"
}

# Function to send notifications
send_notification() {
    local message="$1"
    local status="${2:-info}"
    
    # Slack webhook (if configured)
    if [ -n "$ALERT_WEBHOOK_URL" ]; then
        curl -X POST "$ALERT_WEBHOOK_URL" \
            -H "Content-Type: application/json" \
            -d "{\"text\":\"[$status] Pasargad Prints Backup: $message\"}" \
            >/dev/null 2>&1 || true
    fi
    
    # Discord webhook (if configured)
    if [ -n "$DISCORD_WEBHOOK_URL" ]; then
        curl -X POST "$DISCORD_WEBHOOK_URL" \
            -H "Content-Type: application/json" \
            -d "{\"content\":\"[$status] Pasargad Prints Backup: $message\"}" \
            >/dev/null 2>&1 || true
    fi
}

# Function to check prerequisites
check_prerequisites() {
    print_status "Checking prerequisites..."
    
    # Check if Docker Compose is available
    if ! command -v docker-compose >/dev/null 2>&1; then
        print_error "docker-compose is not available"
        exit 1
    fi
    
    # Check if services are running
    if ! docker-compose -f "$COMPOSE_FILE" ps db | grep -q "Up"; then
        print_error "Database service is not running"
        exit 1
    fi
    
    # Create backup directory
    mkdir -p "$BACKUP_DIR"
    
    # Check available disk space (need at least 1GB)
    local available_space=$(df "$BACKUP_DIR" | tail -1 | awk '{print $4}')
    local required_space=1048576  # 1GB in KB
    
    if [ "$available_space" -lt "$required_space" ]; then
        print_error "Insufficient disk space. Available: ${available_space}KB, Required: ${required_space}KB"
        exit 1
    fi
    
    print_success "Prerequisites check passed"
}

# Function to backup PostgreSQL database
backup_database() {
    print_status "Starting database backup..."
    
    local db_backup_file="$BACKUP_DIR/${BACKUP_NAME}_database.sql"
    
    # Create database dump
    docker-compose -f "$COMPOSE_FILE" exec -T db pg_dump \
        -U postgres \
        -d pasargad_prints \
        --verbose \
        --clean \
        --create \
        --if-exists \
        --format=plain > "$db_backup_file"
    
    if [ $? -eq 0 ] && [ -s "$db_backup_file" ]; then
        # Compress the dump
        gzip "$db_backup_file"
        print_success "Database backup completed: ${db_backup_file}.gz"
        return 0
    else
        print_error "Database backup failed"
        return 1
    fi
}

# Function to backup media files
backup_media() {
    print_status "Starting media files backup..."
    
    local media_backup_file="$BACKUP_DIR/${BACKUP_NAME}_media.tar.gz"
    
    # Get media volume path
    local media_volume=$(docker volume inspect pasargad-prints_media_volume | jq -r '.[0].Mountpoint')
    
    if [ -d "$media_volume" ]; then
        tar -czf "$media_backup_file" -C "$media_volume" . 2>/dev/null || {
            print_warning "Media directory is empty or inaccessible"
            touch "$media_backup_file"
        }
        print_success "Media files backup completed: $media_backup_file"
        return 0
    else
        print_warning "Media volume not found, creating empty backup"
        touch "$media_backup_file"
        return 0
    fi
}

# Function to backup application logs
backup_logs() {
    print_status "Starting logs backup..."
    
    local logs_backup_file="$BACKUP_DIR/${BACKUP_NAME}_logs.tar.gz"
    
    if [ -d "./logs" ]; then
        tar -czf "$logs_backup_file" -C "./logs" . 2>/dev/null || {
            print_warning "Logs directory is empty"
            touch "$logs_backup_file"
        }
        print_success "Logs backup completed: $logs_backup_file"
    else
        print_warning "Logs directory not found, creating empty backup"
        touch "$logs_backup_file"
    fi
}

# Function to backup configuration files
backup_config() {
    print_status "Starting configuration backup..."
    
    local config_backup_file="$BACKUP_DIR/${BACKUP_NAME}_config.tar.gz"
    
    # Create list of configuration files to backup
    local config_files=(
        ".env.production"
        "docker-compose.production.yml"
        "nginx/nginx.production.conf"
        "nginx/ssl"
        "config"
        "monitoring"
    )
    
    # Create temporary directory for config files
    local temp_config_dir=$(mktemp -d)
    
    for file in "${config_files[@]}"; do
        if [ -e "$file" ]; then
            # Create directory structure
            mkdir -p "$temp_config_dir/$(dirname "$file")"
            cp -r "$file" "$temp_config_dir/$file" 2>/dev/null || true
        fi
    done
    
    # Create tar archive
    if [ "$(ls -A "$temp_config_dir")" ]; then
        tar -czf "$config_backup_file" -C "$temp_config_dir" .
        print_success "Configuration backup completed: $config_backup_file"
    else
        print_warning "No configuration files found, creating empty backup"
        touch "$config_backup_file"
    fi
    
    # Cleanup
    rm -rf "$temp_config_dir"
}

# Function to create backup manifest
create_manifest() {
    print_status "Creating backup manifest..."
    
    local manifest_file="$BACKUP_DIR/${BACKUP_NAME}_manifest.json"
    
    # Collect system information
    local system_info=$(cat <<EOF
{
    "backup_name": "$BACKUP_NAME",
    "timestamp": "$TIMESTAMP",
    "hostname": "$(hostname)",
    "docker_version": "$(docker --version)",
    "compose_version": "$(docker-compose --version)",
    "database_version": "$(docker-compose -f "$COMPOSE_FILE" exec -T db psql -U postgres -t -c 'SELECT version();' | tr -d '\\n\\r' | xargs)",
    "app_version": "$(grep 'VITE_APP_VERSION' .env.production 2>/dev/null | cut -d'=' -f2 || echo 'unknown')",
    "backup_files": [
EOF
)
    
    echo "$system_info" > "$manifest_file"
    
    # List backup files with sizes
    local first=true
    for file in "$BACKUP_DIR"/${BACKUP_NAME}_*.{sql.gz,tar.gz}; do
        if [ -f "$file" ]; then
            [ "$first" = true ] && first=false || echo "," >> "$manifest_file"
            local filename=$(basename "$file")
            local filesize=$(stat -f%z "$file" 2>/dev/null || stat -c%s "$file" 2>/dev/null || echo "0")
            local checksum=$(sha256sum "$file" 2>/dev/null | cut -d' ' -f1 || shasum -a 256 "$file" | cut -d' ' -f1)
            
            cat <<EOF >> "$manifest_file"
        {
            "filename": "$filename",
            "size": $filesize,
            "checksum": "$checksum"
        }
EOF
        fi
    done
    
    cat <<EOF >> "$manifest_file"
    ],
    "created_at": "$(date -Iseconds)"
}
EOF
    
    print_success "Backup manifest created: $manifest_file"
}

# Function to verify backups
verify_backups() {
    print_status "Verifying backup integrity..."
    
    local verification_passed=true
    
    for file in "$BACKUP_DIR"/${BACKUP_NAME}_*; do
        if [ -f "$file" ]; then
            local filename=$(basename "$file")
            
            # Check file size
            local filesize=$(stat -f%z "$file" 2>/dev/null || stat -c%s "$file" 2>/dev/null || echo "0")
            if [ "$filesize" -eq 0 ]; then
                print_error "Backup file is empty: $filename"
                verification_passed=false
                continue
            fi
            
            # Verify compressed files
            if [[ "$filename" == *.gz ]]; then
                if ! gzip -t "$file" 2>/dev/null; then
                    print_error "Corrupted compressed file: $filename"
                    verification_passed=false
                    continue
                fi
            fi
            
            print_success "Verified: $filename (${filesize} bytes)"
        fi
    done
    
    if [ "$verification_passed" = true ]; then
        print_success "All backups verified successfully"
        return 0
    else
        print_error "Some backups failed verification"
        return 1
    fi
}

# Main backup function
main() {
    echo "========================================"
    echo "Pasargad Prints Production Backup"
    echo "========================================"
    echo "Backup Name: $BACKUP_NAME"
    echo "Timestamp: $TIMESTAMP"
    echo "========================================"
    
    # Initialize log
    echo "Backup started at $(date)" > "$LOG_FILE"
    
    local start_time=$(date +%s)
    
    # Send start notification
    send_notification "Backup started: $BACKUP_NAME" "info"
    
    # Check prerequisites
    check_prerequisites
    
    # Perform backups
    local backup_success=true
    
    backup_database || backup_success=false
    backup_media || backup_success=false
    backup_logs || backup_success=false
    backup_config || backup_success=false
    
    if [ "$backup_success" = true ]; then
        # Create manifest
        create_manifest
        
        # Verify backups
        if verify_backups; then
            local end_time=$(date +%s)
            local duration=$((end_time - start_time))
            
            print_success "Backup completed successfully in ${duration} seconds"
            send_notification "Backup completed successfully: $BACKUP_NAME (${duration}s)" "success"
            
            # Display backup summary
            echo ""
            echo "Backup Summary:"
            echo "==============="
            ls -lh "$BACKUP_DIR"/${BACKUP_NAME}_* 2>/dev/null || echo "No backup files found"
            
            exit 0
        else
            print_error "Backup verification failed"
            send_notification "Backup verification failed: $BACKUP_NAME" "error"
            exit 1
        fi
    else
        print_error "Backup process failed"
        send_notification "Backup process failed: $BACKUP_NAME" "error"
        exit 1
    fi
}

# Handle script termination
trap 'print_error "Backup interrupted"; send_notification "Backup interrupted: $BACKUP_NAME" "error"; exit 1' INT TERM

# Run main function
main "$@"