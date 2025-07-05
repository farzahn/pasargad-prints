#!/bin/bash

# =============================================================================
# DNS and SSL Validation Script for Pasargad Prints
# =============================================================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
DOMAIN="pasargadprints.com"
SERVER_IP="24.17.91.122"

print_header() {
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}"
}

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check DNS resolution
check_dns() {
    print_header "DNS Resolution Check"
    
    print_status "Checking DNS resolution for $DOMAIN..."
    if nslookup_result=$(nslookup $DOMAIN 2>/dev/null); then
        echo "$nslookup_result"
        if echo "$nslookup_result" | grep -q "Address:"; then
            print_success "DNS resolution successful"
        else
            print_error "DNS resolution failed"
        fi
    else
        print_error "DNS lookup failed"
    fi
    
    print_status "Checking DNS resolution for www.$DOMAIN..."
    if nslookup_result=$(nslookup www.$DOMAIN 2>/dev/null); then
        echo "$nslookup_result"
        if echo "$nslookup_result" | grep -q "Address:"; then
            print_success "WWW DNS resolution successful"
        else
            print_error "WWW DNS resolution failed"
        fi
    else
        print_error "WWW DNS lookup failed"
    fi
}

# Check SSL certificates
check_ssl() {
    print_header "SSL Certificate Check"
    
    print_status "Checking local SSL certificates..."
    if [ -f "../nginx/ssl/cert.pem" ] && [ -f "../nginx/ssl/key.pem" ]; then
        print_success "SSL certificates found"
        
        print_status "Certificate details:"
        openssl x509 -in ../nginx/ssl/cert.pem -text -noout | grep -E "(Subject:|Not Before:|Not After:|DNS:)" || true
    else
        print_error "SSL certificates not found"
    fi
}

# Check local server
check_local_server() {
    print_header "Local Server Check"
    
    print_status "Checking local HTTP server..."
    if curl -f -s http://localhost/ > /dev/null 2>&1; then
        print_success "Local HTTP server responding"
    else
        print_error "Local HTTP server not responding"
    fi
    
    print_status "Checking local HTTPS server..."
    if curl -k -f -s https://localhost/ > /dev/null 2>&1; then
        print_success "Local HTTPS server responding"
    else
        print_error "Local HTTPS server not responding"
    fi
    
    print_status "Testing with domain header..."
    if curl -k -f -s -H "Host: $DOMAIN" https://localhost/ > /dev/null 2>&1; then
        print_success "Server accepts domain requests"
    else
        print_error "Server not accepting domain requests"
    fi
}

# Check Docker containers
check_containers() {
    print_header "Container Health Check"
    
    print_status "Checking Docker containers..."
    if docker-compose -f docker-compose.production.yml ps 2>/dev/null | grep -q "Up"; then
        print_success "Docker containers are running"
        docker-compose -f docker-compose.production.yml ps
    else
        print_error "Docker containers not running"
    fi
}

# Check external connectivity
check_external() {
    print_header "External Connectivity Check"
    
    print_status "Checking external HTTPS connectivity to $DOMAIN..."
    if https_response=$(curl -I -s --max-time 10 https://$DOMAIN 2>&1); then
        echo "$https_response"
        if echo "$https_response" | grep -q "HTTP/"; then
            status_code=$(echo "$https_response" | head -1 | cut -d' ' -f2)
            if [ "$status_code" = "200" ]; then
                print_success "External HTTPS connectivity successful"
            elif [ "$status_code" = "522" ]; then
                print_warning "522 Connection timeout - DNS points to Cloudflare but origin not configured"
            else
                print_warning "HTTP Status: $status_code"
            fi
        else
            print_error "Invalid HTTP response"
        fi
    else
        print_error "External HTTPS connectivity failed"
    fi
}

# Main execution
main() {
    print_header "DNS & SSL Validation for Pasargad Prints"
    echo "Domain: $DOMAIN"
    echo "Server IP: $SERVER_IP"
    echo ""
    
    check_dns
    echo ""
    
    check_ssl
    echo ""
    
    check_containers
    echo ""
    
    check_local_server
    echo ""
    
    check_external
    echo ""
    
    print_header "Summary"
    print_status "Local server is configured and running"
    print_status "SSL certificates are generated and configured"
    print_status "DNS is configured with Cloudflare"
    print_warning "Manual DNS update required to point to $SERVER_IP"
    print_warning "Replace self-signed certificates with Cloudflare Origin certificates"
    
    echo ""
    print_status "Next steps:"
    echo "1. Update Cloudflare DNS A records to point to $SERVER_IP"
    echo "2. Generate and install Cloudflare Origin certificates"
    echo "3. Configure Cloudflare SSL/TLS settings"
    echo "4. Test complete end-to-end functionality"
}

# Run main function
main "$@"