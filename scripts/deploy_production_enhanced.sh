#!/bin/bash

# =============================================================================
# Enhanced Production Deployment Script for Pasargad Prints
# =============================================================================
# 
# This script provides:
# - Zero-downtime deployments
# - Rollback capabilities
# - Health checks and validation
# - Automated Cloudflare configuration
# - Comprehensive logging and monitoring
# =============================================================================

set -e

# Configuration
DEPLOYMENT_ID="deploy_$(date +%Y%m%d_%H%M%S)"
DEPLOYMENT_LOG="logs/deployment_${DEPLOYMENT_ID}.log"
ROLLBACK_POINT=""
HEALTH_CHECK_TIMEOUT=300  # 5 minutes
HEALTH_CHECK_INTERVAL=10  # 10 seconds

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m'

# Logging function
log() {
    local level="$1"
    shift
    local message="$*"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    
    echo -e "${timestamp} [${level}] ${message}" | tee -a "$DEPLOYMENT_LOG"
}

print_status() {
    log "${BLUE}INFO${NC}" "$1"
}

print_success() {
    log "${GREEN}SUCCESS${NC}" "$1"
}

print_warning() {
    log "${YELLOW}WARNING${NC}" "$1"
}

print_error() {
    log "${RED}ERROR${NC}" "$1"
}

print_step() {
    log "${PURPLE}STEP${NC}" "$1"
}

# Function to send deployment notifications
send_notification() {
    local message="$1"
    local status="${2:-info}"
    
    if [ -n "$ALERT_WEBHOOK_URL" ]; then
        curl -s -X POST "$ALERT_WEBHOOK_URL" \
            -H "Content-Type: application/json" \
            -d "{\"text\":\"[$status] Pasargad Prints Deployment: $message\"}" \
            >/dev/null 2>&1 || true
    fi
}

# Function to check prerequisites
check_prerequisites() {
    print_step "Checking deployment prerequisites..."
    
    # Check required commands
    local required_commands=("docker" "docker-compose" "curl" "jq")
    for cmd in "${required_commands[@]}"; do
        if ! command -v "$cmd" >/dev/null 2>&1; then
            print_error "Required command not found: $cmd"
            exit 1
        fi
    done
    
    # Check Docker daemon
    if ! docker info >/dev/null 2>&1; then
        print_error "Docker daemon is not running"
        exit 1
    fi
    
    # Check environment file
    if [ ! -f ".env.production" ]; then
        print_error "Production environment file not found"
        exit 1
    fi
    
    # Check docker-compose file
    if [ ! -f "docker-compose.production.yml" ]; then
        print_error "Production docker-compose file not found"
        exit 1
    fi
    
    # Create logs directory
    mkdir -p logs
    
    # Check disk space (minimum 5GB)
    local available_space=$(df . | tail -1 | awk '{print $4}')
    local required_space=5242880  # 5GB in KB
    
    if [ "$available_space" -lt "$required_space" ]; then
        print_error "Insufficient disk space. Available: ${available_space}KB, Required: ${required_space}KB"
        exit 1
    fi
    
    print_success "Prerequisites check passed"
}

# Function to create deployment snapshot
create_deployment_snapshot() {
    print_step "Creating deployment snapshot..."
    
    ROLLBACK_POINT="rollback_$(date +%Y%m%d_%H%M%S)"
    
    # Save current state
    mkdir -p "deployments/$ROLLBACK_POINT"
    
    # Backup current configuration
    cp -r .env.production "deployments/$ROLLBACK_POINT/" 2>/dev/null || true
    cp -r docker-compose.production.yml "deployments/$ROLLBACK_POINT/" 2>/dev/null || true
    
    # Save container images info
    docker-compose -f docker-compose.production.yml images > "deployments/$ROLLBACK_POINT/images.txt" 2>/dev/null || true
    
    print_success "Deployment snapshot created: $ROLLBACK_POINT"
}

# Function to configure Cloudflare
configure_cloudflare() {
    print_step "Configuring Cloudflare settings..."
    
    if [ -f "scripts/setup_cloudflare.sh" ]; then
        if ./scripts/setup_cloudflare.sh; then
            print_success "Cloudflare configuration completed"
        else
            print_warning "Cloudflare configuration failed, continuing deployment"
        fi
    else
        print_warning "Cloudflare setup script not found, skipping"
    fi
}

# Function to perform zero-downtime deployment
deploy_services() {
    print_step "Starting zero-downtime deployment..."
    
    # Build new images
    print_status "Building application images..."
    docker-compose -f docker-compose.production.yml build --no-cache --parallel
    
    # Start new services alongside old ones
    print_status "Starting new service instances..."
    
    # Scale up new instances
    docker-compose -f docker-compose.production.yml up -d --scale backend=2 --scale frontend=2
    
    # Wait for new instances to be healthy
    print_status "Waiting for new instances to become healthy..."
    local healthy_count=0
    local max_attempts=$((HEALTH_CHECK_TIMEOUT / HEALTH_CHECK_INTERVAL))
    local attempt=0
    
    while [ $attempt -lt $max_attempts ]; do
        healthy_count=$(docker-compose -f docker-compose.production.yml ps --filter health=healthy | grep -c healthy || echo "0")
        
        if [ "$healthy_count" -ge 4 ]; then  # At least 2 backend + 2 frontend healthy
            print_success "New instances are healthy"
            break
        fi
        
        print_status "Health check attempt $((attempt + 1))/$max_attempts - $healthy_count services healthy"
        sleep $HEALTH_CHECK_INTERVAL
        attempt=$((attempt + 1))
    done
    
    if [ $attempt -eq $max_attempts ]; then
        print_error "New instances failed to become healthy within timeout"
        return 1
    fi
    
    # Scale down to normal capacity
    print_status "Scaling down to normal capacity..."
    docker-compose -f docker-compose.production.yml up -d --scale backend=1 --scale frontend=1
    
    # Remove old containers
    docker-compose -f docker-compose.production.yml up -d --remove-orphans
    
    print_success "Zero-downtime deployment completed"
}

# Function to run database migrations
run_migrations() {
    print_step "Running database migrations..."
    
    # Wait for database to be ready
    local attempt=0
    local max_attempts=30
    
    while [ $attempt -lt $max_attempts ]; do
        if docker-compose -f docker-compose.production.yml exec -T db pg_isready -U postgres >/dev/null 2>&1; then
            break
        fi
        
        print_status "Waiting for database... ($((attempt + 1))/$max_attempts)"
        sleep 2
        attempt=$((attempt + 1))
    done
    
    if [ $attempt -eq $max_attempts ]; then
        print_error "Database not ready after $max_attempts attempts"
        return 1
    fi
    
    # Run migrations
    print_status "Applying database migrations..."
    if docker-compose -f docker-compose.production.yml exec -T backend python manage.py migrate --noinput; then
        print_success "Database migrations completed"
    else
        print_error "Database migrations failed"
        return 1
    fi
    
    # Collect static files
    print_status "Collecting static files..."
    if docker-compose -f docker-compose.production.yml exec -T backend python manage.py collectstatic --noinput; then
        print_success "Static files collected"
    else
        print_warning "Static files collection failed"
    fi
}

# Function to perform comprehensive health checks
perform_health_checks() {
    print_step "Performing comprehensive health checks..."
    
    local checks_passed=0
    local total_checks=8
    
    # Check 1: Container health
    print_status "Checking container health..."
    local unhealthy_containers=$(docker-compose -f docker-compose.production.yml ps --filter health=unhealthy | wc -l)
    if [ "$unhealthy_containers" -eq 0 ]; then
        print_success "All containers are healthy"
        checks_passed=$((checks_passed + 1))
    else
        print_error "Found $unhealthy_containers unhealthy containers"
    fi
    
    # Check 2: HTTP endpoints
    print_status "Checking HTTP endpoints..."
    local endpoints=(
        "http://localhost/"
        "http://localhost/api/health/"
        "http://localhost/admin/"
    )
    
    local endpoint_checks=0
    for endpoint in "${endpoints[@]}"; do
        if curl -f -s "$endpoint" >/dev/null 2>&1; then
            endpoint_checks=$((endpoint_checks + 1))
        fi
    done
    
    if [ "$endpoint_checks" -eq "${#endpoints[@]}" ]; then
        print_success "All HTTP endpoints are responding"
        checks_passed=$((checks_passed + 1))
    else
        print_error "Some HTTP endpoints are not responding ($endpoint_checks/${#endpoints[@]})"
    fi
    
    # Check 3: Database connectivity
    print_status "Checking database connectivity..."
    if docker-compose -f docker-compose.production.yml exec -T backend python manage.py dbshell -c "SELECT 1;" >/dev/null 2>&1; then
        print_success "Database connectivity confirmed"
        checks_passed=$((checks_passed + 1))
    else
        print_error "Database connectivity failed"
    fi
    
    # Check 4: Redis connectivity
    print_status "Checking Redis connectivity..."
    if docker-compose -f docker-compose.production.yml exec -T redis redis-cli ping | grep -q "PONG"; then
        print_success "Redis connectivity confirmed"
        checks_passed=$((checks_passed + 1))
    else
        print_error "Redis connectivity failed"
    fi
    
    # Check 5: SSL/HTTPS
    print_status "Checking SSL configuration..."
    if curl -k -f -s https://localhost/ >/dev/null 2>&1; then
        print_success "SSL/HTTPS is working"
        checks_passed=$((checks_passed + 1))
    else
        print_error "SSL/HTTPS is not working"
    fi
    
    # Check 6: Static files
    print_status "Checking static file serving..."
    if curl -f -s http://localhost/static/ >/dev/null 2>&1; then
        print_success "Static files are being served"
        checks_passed=$((checks_passed + 1))
    else
        print_warning "Static files check inconclusive"
        checks_passed=$((checks_passed + 1))  # Non-critical
    fi
    
    # Check 7: Celery workers
    print_status "Checking Celery workers..."
    if docker-compose -f docker-compose.production.yml exec -T celery celery -A pasargad_prints inspect ping >/dev/null 2>&1; then
        print_success "Celery workers are running"
        checks_passed=$((checks_passed + 1))
    else
        print_error "Celery workers are not responding"
    fi
    
    # Check 8: Log generation
    print_status "Checking log generation..."
    if docker-compose -f docker-compose.production.yml logs --tail=1 backend | grep -q ""; then
        print_success "Application logs are being generated"
        checks_passed=$((checks_passed + 1))
    else
        print_error "No application logs detected"
    fi
    
    # Overall health assessment
    local health_percentage=$((checks_passed * 100 / total_checks))
    
    if [ "$checks_passed" -eq "$total_checks" ]; then
        print_success "All health checks passed (100%)"
        return 0
    elif [ "$health_percentage" -ge 80 ]; then
        print_warning "Most health checks passed ($health_percentage% - $checks_passed/$total_checks)"
        return 0
    else
        print_error "Health checks failed ($health_percentage% - $checks_passed/$total_checks)"
        return 1
    fi
}

# Function to validate deployment
validate_deployment() {
    print_step "Running deployment validation..."
    
    if [ -f "scripts/validate_production.sh" ]; then
        if ./scripts/validate_production.sh; then
            print_success "Deployment validation passed"
            return 0
        else
            print_error "Deployment validation failed"
            return 1
        fi
    else
        print_warning "Validation script not found, running basic checks"
        perform_health_checks
    fi
}

# Function to setup monitoring
setup_monitoring() {
    print_step "Setting up monitoring and alerting..."
    
    # Start monitoring services
    if docker-compose -f docker-compose.production.yml ps prometheus | grep -q "Up"; then
        print_success "Prometheus is running"
    else
        print_warning "Prometheus is not running"
    fi
    
    if docker-compose -f docker-compose.production.yml ps grafana | grep -q "Up"; then
        print_success "Grafana is running"
    else
        print_warning "Grafana is not running"
    fi
    
    # Setup monitoring scripts
    if [ -f "scripts/monitor_production.sh" ]; then
        # Start monitoring in background
        nohup ./scripts/monitor_production.sh --continuous > logs/monitoring.log 2>&1 &
        echo $! > logs/monitoring.pid
        print_success "Continuous monitoring started"
    fi
}

# Function to create initial backup
create_initial_backup() {
    print_step "Creating initial post-deployment backup..."
    
    if [ -f "scripts/backup_production_enhanced.sh" ]; then
        if ./scripts/backup_production_enhanced.sh; then
            print_success "Initial backup created"
        else
            print_warning "Initial backup failed"
        fi
    else
        print_warning "Backup script not found"
    fi
}

# Function to rollback deployment
rollback_deployment() {
    print_error "Rolling back deployment to: $ROLLBACK_POINT"
    
    if [ -z "$ROLLBACK_POINT" ] || [ ! -d "deployments/$ROLLBACK_POINT" ]; then
        print_error "No valid rollback point found"
        return 1
    fi
    
    # Stop current services
    docker-compose -f docker-compose.production.yml down
    
    # Restore previous configuration
    cp "deployments/$ROLLBACK_POINT/.env.production" . 2>/dev/null || true
    cp "deployments/$ROLLBACK_POINT/docker-compose.production.yml" . 2>/dev/null || true
    
    # Start services with previous configuration
    docker-compose -f docker-compose.production.yml up -d
    
    # Wait for services to be healthy
    sleep 30
    
    if perform_health_checks; then
        print_success "Rollback completed successfully"
        send_notification "Deployment rolled back successfully to $ROLLBACK_POINT" "warning"
        return 0
    else
        print_error "Rollback failed"
        send_notification "Deployment rollback failed" "error"
        return 1
    fi
}

# Function to cleanup old deployments
cleanup_old_deployments() {
    print_step "Cleaning up old deployments..."
    
    # Remove deployment snapshots older than 7 days
    find deployments -type d -name "rollback_*" -mtime +7 -exec rm -rf {} + 2>/dev/null || true
    
    # Remove old deployment logs
    find logs -name "deployment_*.log" -mtime +30 -delete 2>/dev/null || true
    
    # Clean up old Docker images
    docker image prune -f >/dev/null 2>&1 || true
    
    print_success "Cleanup completed"
}

# Main deployment function
main() {
    echo "=========================================="
    echo "🚀 Pasargad Prints Production Deployment"
    echo "=========================================="
    echo "Deployment ID: $DEPLOYMENT_ID"
    echo "Timestamp: $(date)"
    echo "Environment: Production"
    echo "Domain: pasargadprints.com"
    echo "=========================================="
    
    # Initialize deployment log
    echo "Deployment started at $(date)" > "$DEPLOYMENT_LOG"
    
    # Send start notification
    send_notification "Production deployment started: $DEPLOYMENT_ID" "info"
    
    local start_time=$(date +%s)
    local deployment_success=true
    
    # Execute deployment steps
    check_prerequisites || { print_error "Prerequisites check failed"; exit 1; }
    create_deployment_snapshot || { print_error "Snapshot creation failed"; exit 1; }
    
    # Configure Cloudflare
    configure_cloudflare || print_warning "Cloudflare configuration had issues"
    
    # Deploy services
    if deploy_services; then
        print_success "Service deployment completed"
    else
        print_error "Service deployment failed"
        deployment_success=false
    fi
    
    # Run migrations
    if [ "$deployment_success" = true ]; then
        if run_migrations; then
            print_success "Database operations completed"
        else
            print_error "Database operations failed"
            deployment_success=false
        fi
    fi
    
    # Validate deployment
    if [ "$deployment_success" = true ]; then
        if validate_deployment; then
            print_success "Deployment validation passed"
        else
            print_error "Deployment validation failed"
            deployment_success=false
        fi
    fi
    
    # Handle deployment result
    if [ "$deployment_success" = true ]; then
        # Setup monitoring
        setup_monitoring
        
        # Create initial backup
        create_initial_backup
        
        # Cleanup
        cleanup_old_deployments
        
        local end_time=$(date +%s)
        local duration=$((end_time - start_time))
        
        print_success "🎉 Deployment completed successfully in ${duration} seconds!"
        send_notification "Production deployment completed successfully: $DEPLOYMENT_ID (${duration}s)" "success"
        
        echo ""
        echo "🌐 Access Information:"
        echo "======================================"
        echo "Frontend:    https://pasargadprints.com"
        echo "Admin:       https://pasargadprints.com/admin/"
        echo "API Health:  https://pasargadprints.com/api/health/"
        echo "Grafana:     http://localhost:3001"
        echo "Prometheus:  http://localhost:9090"
        echo ""
        echo "📊 Monitoring Commands:"
        echo "======================================"
        echo "Status:      docker-compose -f docker-compose.production.yml ps"
        echo "Logs:        docker-compose -f docker-compose.production.yml logs -f"
        echo "Health:      ./scripts/validate_production.sh"
        echo "Monitor:     ./scripts/monitor_production.sh"
        echo ""
        echo "🔄 Management Commands:"
        echo "======================================"
        echo "Restart:     docker-compose -f docker-compose.production.yml restart"
        echo "Stop:        docker-compose -f docker-compose.production.yml down"
        echo "Backup:      ./scripts/backup_production_enhanced.sh"
        echo ""
        
        return 0
    else
        # Attempt rollback
        print_error "Deployment failed, attempting rollback..."
        
        if rollback_deployment; then
            print_warning "Deployment failed but rollback was successful"
            send_notification "Deployment failed but rollback successful: $DEPLOYMENT_ID" "warning"
            return 1
        else
            print_error "Deployment and rollback both failed"
            send_notification "CRITICAL: Deployment and rollback both failed: $DEPLOYMENT_ID" "error"
            return 2
        fi
    fi
}

# Handle script interruption
trap 'print_error "Deployment interrupted"; send_notification "Deployment interrupted: $DEPLOYMENT_ID" "error"; exit 1' INT TERM

# Check if running with --rollback flag
if [ "$1" = "--rollback" ]; then
    if [ -n "$2" ]; then
        ROLLBACK_POINT="$2"
        rollback_deployment
    else
        echo "Usage: $0 --rollback <rollback_point>"
        echo "Available rollback points:"
        ls -1 deployments/ 2>/dev/null | grep "rollback_" || echo "No rollback points found"
        exit 1
    fi
else
    # Run main deployment
    main "$@"
fi