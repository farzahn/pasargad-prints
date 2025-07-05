#!/bin/bash

# Production Monitoring Script
# Monitors system health and sends alerts if issues are detected

set -e

# Configuration
HEALTH_CHECK_URL="http://localhost/api/health/"
ALERT_WEBHOOK_URL="${ALERT_WEBHOOK_URL:-}"
LOG_FILE="/app/logs/monitoring.log"
CHECK_INTERVAL=60  # seconds

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

print_log() {
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo -e "$timestamp $1" | tee -a "$LOG_FILE"
}

print_status() {
    print_log "${BLUE}[MONITOR]${NC} $1"
}

print_success() {
    print_log "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    print_log "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    print_log "${RED}[ERROR]${NC} $1"
}

send_alert() {
    local message="$1"
    local severity="${2:-warning}"
    
    if [ -n "$ALERT_WEBHOOK_URL" ]; then
        curl -X POST "$ALERT_WEBHOOK_URL" \
            -H "Content-Type: application/json" \
            -d "{\"text\":\"[$severity] Pasargad Prints Alert: $message\"}" \
            >/dev/null 2>&1 || print_warning "Failed to send alert notification."
    fi
}

check_docker_containers() {
    print_status "Checking Docker containers..."
    
    local containers=(
        "pasargad-prints_backend_1"
        "pasargad-prints_frontend_1" 
        "pasargad-prints_nginx_1"
        "pasargad-prints_db_1"
        "pasargad-prints_redis_1"
    )
    
    for container in "${containers[@]}"; do
        if docker ps --format "table {{.Names}}" | grep -q "$container"; then
            local status=$(docker inspect --format='{{.State.Health.Status}}' "$container" 2>/dev/null || echo "no-health-check")
            if [ "$status" = "healthy" ] || [ "$status" = "no-health-check" ]; then
                print_success "Container $container is running and healthy"
            else
                print_error "Container $container is unhealthy (status: $status)"
                send_alert "Container $container is unhealthy" "error"
            fi
        else
            print_error "Container $container is not running"
            send_alert "Container $container is not running" "critical"
        fi
    done
}

check_application_health() {
    print_status "Checking application health..."
    
    local http_code=$(curl -s -o /dev/null -w "%{http_code}" "$HEALTH_CHECK_URL" || echo "000")
    
    if [ "$http_code" = "200" ]; then
        print_success "Application health check passed (HTTP $http_code)"
    else
        print_error "Application health check failed (HTTP $http_code)"
        send_alert "Application health check failed with HTTP $http_code" "error"
    fi
}

check_disk_space() {
    print_status "Checking disk space..."
    
    local disk_usage=$(df / | tail -1 | awk '{print $5}' | sed 's/%//')
    
    if [ "$disk_usage" -lt 80 ]; then
        print_success "Disk usage is normal ($disk_usage%)"
    elif [ "$disk_usage" -lt 90 ]; then
        print_warning "Disk usage is high ($disk_usage%)"
        send_alert "Disk usage is high: $disk_usage%" "warning"
    else
        print_error "Disk usage is critical ($disk_usage%)"
        send_alert "Disk usage is critical: $disk_usage%" "critical"
    fi
}

check_memory_usage() {
    print_status "Checking memory usage..."
    
    local memory_usage=$(free | grep Mem | awk '{printf "%.0f", $3/$2 * 100.0}')
    
    if [ "$memory_usage" -lt 80 ]; then
        print_success "Memory usage is normal ($memory_usage%)"
    elif [ "$memory_usage" -lt 90 ]; then
        print_warning "Memory usage is high ($memory_usage%)"
        send_alert "Memory usage is high: $memory_usage%" "warning"
    else
        print_error "Memory usage is critical ($memory_usage%)"
        send_alert "Memory usage is critical: $memory_usage%" "critical"
    fi
}

check_ssl_certificate() {
    print_status "Checking SSL certificate..."
    
    local cert_file="/etc/nginx/ssl/cert.pem"
    if [ -f "$cert_file" ]; then
        local expiry_date=$(openssl x509 -enddate -noout -in "$cert_file" | cut -d= -f2)
        local expiry_epoch=$(date -d "$expiry_date" +%s)
        local current_epoch=$(date +%s)
        local days_until_expiry=$(( (expiry_epoch - current_epoch) / 86400 ))
        
        if [ "$days_until_expiry" -gt 30 ]; then
            print_success "SSL certificate expires in $days_until_expiry days"
        elif [ "$days_until_expiry" -gt 7 ]; then
            print_warning "SSL certificate expires in $days_until_expiry days"
            send_alert "SSL certificate expires in $days_until_expiry days" "warning"
        else
            print_error "SSL certificate expires in $days_until_expiry days"
            send_alert "SSL certificate expires in $days_until_expiry days - URGENT RENEWAL NEEDED" "critical"
        fi
    else
        print_warning "SSL certificate file not found"
    fi
}

# Main monitoring function
run_health_checks() {
    print_status "Starting health checks..."
    
    check_docker_containers
    check_application_health
    check_disk_space
    check_memory_usage
    check_ssl_certificate
    
    print_status "Health checks completed."
    echo ""
}

# Create log directory
mkdir -p "$(dirname "$LOG_FILE")"

# Run checks
if [ "$1" = "--continuous" ]; then
    print_status "Starting continuous monitoring (interval: ${CHECK_INTERVAL}s)"
    while true; do
        run_health_checks
        sleep "$CHECK_INTERVAL"
    done
else
    run_health_checks
fi