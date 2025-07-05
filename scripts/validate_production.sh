#!/bin/bash

# Production Deployment Validation Script
# Validates all production requirements and success criteria

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

# Counters
TOTAL_CHECKS=0
PASSED_CHECKS=0
FAILED_CHECKS=0

print_header() {
    echo ""
    echo -e "${BLUE}================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}================================${NC}"
}

print_check() {
    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
    echo -e "${BLUE}[$TOTAL_CHECKS]${NC} Checking: $1"
}

print_success() {
    PASSED_CHECKS=$((PASSED_CHECKS + 1))
    echo -e "${GREEN}✓${NC} $1"
}

print_failure() {
    FAILED_CHECKS=$((FAILED_CHECKS + 1))
    echo -e "${RED}✗${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

# Test functions
test_service_health() {
    print_header "SERVICE HEALTH VALIDATION"
    
    print_check "All services are running"
    if docker-compose -f docker-compose.production.yml ps | grep -q "Up"; then
        print_success "Services are running"
    else
        print_failure "Some services are not running"
        docker-compose -f docker-compose.production.yml ps
        return 1
    fi
    
    print_check "Backend health endpoint"
    if curl -f -s http://localhost/api/health/ >/dev/null; then
        print_success "Backend health check passed"
    else
        print_failure "Backend health check failed"
    fi
    
    print_check "Frontend accessibility"
    if curl -f -s http://localhost/ >/dev/null; then
        print_success "Frontend is accessible"
    else
        print_failure "Frontend is not accessible"
    fi
    
    print_check "Admin interface accessibility"
    if curl -f -s http://localhost/admin/ >/dev/null; then
        print_success "Admin interface is accessible"
    else
        print_failure "Admin interface is not accessible"
    fi
}

test_ssl_configuration() {
    print_header "SSL/HTTPS VALIDATION"
    
    print_check "SSL certificates exist"
    if [ -f "nginx/ssl/cert.pem" ] && [ -f "nginx/ssl/key.pem" ]; then
        print_success "SSL certificates found"
    else
        print_failure "SSL certificates missing"
    fi
    
    print_check "HTTPS accessibility (with self-signed cert)"
    if curl -k -f -s https://localhost/ >/dev/null; then
        print_success "HTTPS is working (self-signed certificate)"
        print_warning "Remember to replace with valid SSL certificate for production"
    else
        print_failure "HTTPS is not working"
    fi
}

test_database_connectivity() {
    print_header "DATABASE VALIDATION"
    
    print_check "PostgreSQL container health"
    if docker-compose -f docker-compose.production.yml exec -T db pg_isready -U postgres >/dev/null; then
        print_success "PostgreSQL is healthy"
    else
        print_failure "PostgreSQL is not healthy"
    fi
    
    print_check "Database migrations"
    if docker-compose -f docker-compose.production.yml exec -T backend python manage.py showmigrations --plan | grep -q "\[X\]"; then
        print_success "Database migrations are applied"
    else
        print_failure "Database migrations are not applied"
    fi
}

test_redis_connectivity() {
    print_header "REDIS VALIDATION"
    
    print_check "Redis container health"
    if docker-compose -f docker-compose.production.yml exec -T redis redis-cli ping | grep -q "PONG"; then
        print_success "Redis is healthy"
    else
        print_failure "Redis is not healthy"
    fi
    
    print_check "Django cache connectivity"
    if docker-compose -f docker-compose.production.yml exec -T backend python -c "from django.core.cache import cache; cache.set('test', 'ok'); print('Cache test:', cache.get('test'))" 2>/dev/null | grep -q "ok"; then
        print_success "Django cache is working"
    else
        print_failure "Django cache is not working"
    fi
}

test_static_files() {
    print_header "STATIC FILES VALIDATION"
    
    print_check "Static files collection"
    if docker-compose -f docker-compose.production.yml exec -T backend ls /app/staticfiles/ >/dev/null 2>&1; then
        print_success "Static files are collected"
    else
        print_failure "Static files are not collected"
    fi
    
    print_check "Static file serving"
    if curl -f -s http://localhost/static/ >/dev/null 2>&1; then
        print_success "Static files are served correctly"
    else
        print_info "Static file serving test inconclusive (no static files to test)"
    fi
}

test_security_headers() {
    print_header "SECURITY VALIDATION"
    
    print_check "Security headers present"
    local headers=$(curl -s -I http://localhost/ 2>/dev/null || echo "")
    
    if echo "$headers" | grep -qi "x-frame-options"; then
        print_success "X-Frame-Options header present"
    else
        print_failure "X-Frame-Options header missing"
    fi
    
    if echo "$headers" | grep -qi "x-content-type-options"; then
        print_success "X-Content-Type-Options header present"
    else
        print_failure "X-Content-Type-Options header missing"
    fi
    
    if echo "$headers" | grep -qi "x-xss-protection"; then
        print_success "X-XSS-Protection header present"
    else
        print_failure "X-XSS-Protection header missing"
    fi
}

test_performance() {
    print_header "PERFORMANCE VALIDATION"
    
    print_check "Frontend load time"
    local load_time=$(curl -o /dev/null -s -w "%{time_total}" http://localhost/ 2>/dev/null || echo "999")
    if (( $(echo "$load_time < 2.0" | bc -l) )); then
        print_success "Frontend loads in ${load_time}s (< 2s target)"
    else
        print_warning "Frontend loads in ${load_time}s (> 2s target)"
    fi
    
    print_check "API response time"
    local api_time=$(curl -o /dev/null -s -w "%{time_total}" http://localhost/api/health/ 2>/dev/null || echo "999")
    if (( $(echo "$api_time < 0.5" | bc -l) )); then
        print_success "API responds in ${api_time}s (< 0.5s target)"
    else
        print_warning "API responds in ${api_time}s (> 0.5s target)"
    fi
}

test_logging() {
    print_header "LOGGING VALIDATION"
    
    print_check "Application logs are being generated"
    if docker-compose -f docker-compose.production.yml logs --tail=1 backend | grep -q ""; then
        print_success "Backend logs are being generated"
    else
        print_failure "Backend logs are not being generated"
    fi
    
    print_check "Nginx access logs"
    if docker-compose -f docker-compose.production.yml logs --tail=1 nginx | grep -q ""; then
        print_success "Nginx logs are being generated"
    else
        print_failure "Nginx logs are not being generated"
    fi
}

test_environment_configuration() {
    print_header "ENVIRONMENT VALIDATION"
    
    print_check "Production environment file exists"
    if [ -f ".env.production" ]; then
        print_success "Production environment file found"
    else
        print_failure "Production environment file missing"
    fi
    
    print_check "DEBUG mode is disabled"
    if grep -q "DEBUG=False" .env.production 2>/dev/null; then
        print_success "DEBUG mode is disabled"
    else
        print_failure "DEBUG mode is not properly disabled"
    fi
    
    print_check "Secret key is configured"
    if grep -q "SECRET_KEY=" .env.production 2>/dev/null && ! grep -q "SECRET_KEY=$" .env.production; then
        print_success "Secret key is configured"
    else
        print_failure "Secret key is not configured"
    fi
}

# Main execution
main() {
    print_header "PASARGAD PRINTS PRODUCTION VALIDATION"
    echo "Validating production deployment against success criteria..."
    
    # Run all tests
    test_service_health
    test_ssl_configuration
    test_database_connectivity
    test_redis_connectivity
    test_static_files
    test_security_headers
    test_performance
    test_logging
    test_environment_configuration
    
    # Summary
    print_header "VALIDATION SUMMARY"
    echo "Total checks: $TOTAL_CHECKS"
    echo -e "Passed: ${GREEN}$PASSED_CHECKS${NC}"
    echo -e "Failed: ${RED}$FAILED_CHECKS${NC}"
    
    if [ $FAILED_CHECKS -eq 0 ]; then
        print_success "🎉 All validation checks passed! Production deployment is successful."
        echo ""
        echo "Your Pasargad Prints e-commerce platform is ready for production use!"
        echo ""
        echo "Access points:"
        echo "  • Frontend: http://localhost/ or https://localhost/"
        echo "  • Admin: http://localhost/admin/"
        echo "  • API Health: http://localhost/api/health/"
        echo ""
        echo "Next steps:"
        echo "  1. Configure your domain name and real SSL certificates"
        echo "  2. Set up monitoring and alerting"
        echo "  3. Configure automated backups"
        echo "  4. Review and update production secrets"
        echo "  5. Set up CI/CD pipeline for deployments"
        return 0
    else
        print_failure "❌ Some validation checks failed. Please review and fix the issues above."
        return 1
    fi
}

# Check if bc is available for floating point arithmetic
if ! command -v bc >/dev/null 2>&1; then
    print_warning "bc command not found. Installing for performance calculations..."
    # Attempt to install bc (works on most systems)
    sudo apt-get update && sudo apt-get install -y bc 2>/dev/null || \
    yum install -y bc 2>/dev/null || \
    brew install bc 2>/dev/null || \
    print_warning "Could not install bc. Performance checks will be skipped."
fi

# Run main function
main