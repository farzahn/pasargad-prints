#!/bin/bash

# =============================================================================
# Cloudflare DNS and SSL Configuration Script for Pasargad Prints
# =============================================================================
# 
# This script configures Cloudflare DNS records and SSL settings for 
# pasargadprints.com using the Cloudflare API.
#
# Prerequisites:
# - Cloudflare API token with Zone:Edit permissions
# - Domain already added to Cloudflare account
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
CLOUDFLARE_API_TOKEN="${CLOUDFLARE_API_TOKEN:-3glht8H4Ki5J5_VWLKkC_R7FyBxkx_t7OikdPAL9}"
CLOUDFLARE_ZONE_ID="${CLOUDFLARE_ZONE_ID:-9aa6c3da8742c5a1a7ee8f2cd760f85e}"
SERVER_IP="${SERVER_IP:-$(curl -s http://checkip.amazonaws.com/)}"

# Function to print colored output
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

# Function to make Cloudflare API calls
cloudflare_api() {
    local method="$1"
    local endpoint="$2"
    local data="$3"
    
    local url="https://api.cloudflare.com/v4$endpoint"
    
    if [ -n "$data" ]; then
        curl -s -X "$method" "$url" \
            -H "Authorization: Bearer $CLOUDFLARE_API_TOKEN" \
            -H "Content-Type: application/json" \
            --data "$data"
    else
        curl -s -X "$method" "$url" \
            -H "Authorization: Bearer $CLOUDFLARE_API_TOKEN" \
            -H "Content-Type: application/json"
    fi
}

# Function to check if API token is valid
check_api_token() {
    print_status "Verifying Cloudflare API token..."
    
    local response=$(cloudflare_api "GET" "/user/tokens/verify")
    local success=$(echo "$response" | jq -r '.success // false')
    
    if [ "$success" = "true" ]; then
        print_success "API token is valid"
    else
        print_error "Invalid API token"
        echo "$response" | jq -r '.errors[]?.message // "Unknown error"'
        exit 1
    fi
}

# Function to get zone information
get_zone_info() {
    print_status "Getting zone information for $DOMAIN..."
    
    local response=$(cloudflare_api "GET" "/zones/$CLOUDFLARE_ZONE_ID")
    local success=$(echo "$response" | jq -r '.success // false')
    
    if [ "$success" = "true" ]; then
        local zone_name=$(echo "$response" | jq -r '.result.name')
        local zone_status=$(echo "$response" | jq -r '.result.status')
        print_success "Zone: $zone_name (Status: $zone_status)"
    else
        print_error "Failed to get zone information"
        echo "$response" | jq -r '.errors[]?.message // "Unknown error"'
        exit 1
    fi
}

# Function to create or update DNS record
manage_dns_record() {
    local record_type="$1"
    local record_name="$2"
    local record_content="$3"
    local record_ttl="${4:-1}"  # 1 = Auto
    local record_proxied="${5:-true}"
    
    print_status "Managing DNS record: $record_type $record_name -> $record_content"
    
    # Check if record exists
    local list_response=$(cloudflare_api "GET" "/zones/$CLOUDFLARE_ZONE_ID/dns_records?type=$record_type&name=$record_name")
    local record_count=$(echo "$list_response" | jq -r '.result | length')
    
    if [ "$record_count" -gt 0 ]; then
        # Update existing record
        local record_id=$(echo "$list_response" | jq -r '.result[0].id')
        print_status "Updating existing DNS record (ID: $record_id)"
        
        local update_data=$(jq -n \
            --arg type "$record_type" \
            --arg name "$record_name" \
            --arg content "$record_content" \
            --argjson ttl "$record_ttl" \
            --argjson proxied "$record_proxied" \
            '{type: $type, name: $name, content: $content, ttl: $ttl, proxied: $proxied}')
        
        local response=$(cloudflare_api "PATCH" "/zones/$CLOUDFLARE_ZONE_ID/dns_records/$record_id" "$update_data")
        local success=$(echo "$response" | jq -r '.success // false')
        
        if [ "$success" = "true" ]; then
            print_success "DNS record updated successfully"
        else
            print_error "Failed to update DNS record"
            echo "$response" | jq -r '.errors[]?.message // "Unknown error"'
        fi
    else
        # Create new record
        print_status "Creating new DNS record"
        
        local create_data=$(jq -n \
            --arg type "$record_type" \
            --arg name "$record_name" \
            --arg content "$record_content" \
            --argjson ttl "$record_ttl" \
            --argjson proxied "$record_proxied" \
            '{type: $type, name: $name, content: $content, ttl: $ttl, proxied: $proxied}')
        
        local response=$(cloudflare_api "POST" "/zones/$CLOUDFLARE_ZONE_ID/dns_records" "$create_data")
        local success=$(echo "$response" | jq -r '.success // false')
        
        if [ "$success" = "true" ]; then
            print_success "DNS record created successfully"
        else
            print_error "Failed to create DNS record"
            echo "$response" | jq -r '.errors[]?.message // "Unknown error"'
        fi
    fi
}

# Function to configure SSL settings
configure_ssl() {
    print_status "Configuring SSL settings..."
    
    # Set SSL mode to Full (Strict)
    local ssl_data='{"value":"full"}'
    local response=$(cloudflare_api "PATCH" "/zones/$CLOUDFLARE_ZONE_ID/settings/ssl" "$ssl_data")
    local success=$(echo "$response" | jq -r '.success // false')
    
    if [ "$success" = "true" ]; then
        print_success "SSL mode set to Full"
    else
        print_warning "Failed to set SSL mode"
    fi
    
    # Enable Always Use HTTPS
    local https_data='{"value":"on"}'
    local response=$(cloudflare_api "PATCH" "/zones/$CLOUDFLARE_ZONE_ID/settings/always_use_https" "$https_data")
    local success=$(echo "$response" | jq -r '.success // false')
    
    if [ "$success" = "true" ]; then
        print_success "Always Use HTTPS enabled"
    else
        print_warning "Failed to enable Always Use HTTPS"
    fi
    
    # Enable Automatic HTTPS Rewrites
    local rewrite_data='{"value":"on"}'
    local response=$(cloudflare_api "PATCH" "/zones/$CLOUDFLARE_ZONE_ID/settings/automatic_https_rewrites" "$rewrite_data")
    local success=$(echo "$response" | jq -r '.success // false')
    
    if [ "$success" = "true" ]; then
        print_success "Automatic HTTPS Rewrites enabled"
    else
        print_warning "Failed to enable Automatic HTTPS Rewrites"
    fi
}

# Function to configure security settings
configure_security() {
    print_status "Configuring security settings..."
    
    # Set security level to Medium
    local security_data='{"value":"medium"}'
    local response=$(cloudflare_api "PATCH" "/zones/$CLOUDFLARE_ZONE_ID/settings/security_level" "$security_data")
    local success=$(echo "$response" | jq -r '.success // false')
    
    if [ "$success" = "true" ]; then
        print_success "Security level set to Medium"
    else
        print_warning "Failed to set security level"
    fi
    
    # Enable Bot Fight Mode
    local bot_data='{"value":"on"}'
    local response=$(cloudflare_api "PATCH" "/zones/$CLOUDFLARE_ZONE_ID/settings/brotli" "$bot_data")
    local success=$(echo "$response" | jq -r '.success // false')
    
    if [ "$success" = "true" ]; then
        print_success "Brotli compression enabled"
    else
        print_warning "Failed to enable Brotli compression"
    fi
}

# Function to configure caching
configure_caching() {
    print_status "Configuring caching settings..."
    
    # Set caching level to Standard
    local cache_data='{"value":"aggressive"}'
    local response=$(cloudflare_api "PATCH" "/zones/$CLOUDFLARE_ZONE_ID/settings/cache_level" "$cache_data")
    local success=$(echo "$response" | jq -r '.success // false')
    
    if [ "$success" = "true" ]; then
        print_success "Cache level set to Aggressive"
    else
        print_warning "Failed to set cache level"
    fi
    
    # Enable Browser Cache TTL
    local browser_cache_data='{"value":31536000}'  # 1 year
    local response=$(cloudflare_api "PATCH" "/zones/$CLOUDFLARE_ZONE_ID/settings/browser_cache_ttl" "$browser_cache_data")
    local success=$(echo "$response" | jq -r '.success // false')
    
    if [ "$success" = "true" ]; then
        print_success "Browser cache TTL set to 1 year"
    else
        print_warning "Failed to set browser cache TTL"
    fi
}

# Function to create page rules
create_page_rules() {
    print_status "Creating page rules..."
    
    # Page rule for static assets caching
    local static_rule_data=$(jq -n \
        --arg url "*pasargadprints.com/static/*" \
        '{
            targets: [{
                target: "url",
                constraint: {
                    operator: "matches",
                    value: $url
                }
            }],
            actions: [
                {
                    id: "cache_level",
                    value: "cache_everything"
                },
                {
                    id: "edge_cache_ttl",
                    value: 31536000
                },
                {
                    id: "browser_cache_ttl",
                    value: 31536000
                }
            ],
            priority: 1,
            status: "active"
        }')
    
    local response=$(cloudflare_api "POST" "/zones/$CLOUDFLARE_ZONE_ID/pagerules" "$static_rule_data")
    local success=$(echo "$response" | jq -r '.success // false')
    
    if [ "$success" = "true" ]; then
        print_success "Static assets page rule created"
    else
        print_warning "Failed to create static assets page rule (may already exist)"
    fi
    
    # Page rule for admin security
    local admin_rule_data=$(jq -n \
        --arg url "*pasargadprints.com/admin/*" \
        '{
            targets: [{
                target: "url",
                constraint: {
                    operator: "matches",
                    value: $url
                }
            }],
            actions: [
                {
                    id: "security_level",
                    value: "high"
                },
                {
                    id: "cache_level",
                    value: "bypass"
                }
            ],
            priority: 2,
            status: "active"
        }')
    
    local response=$(cloudflare_api "POST" "/zones/$CLOUDFLARE_ZONE_ID/pagerules" "$admin_rule_data")
    local success=$(echo "$response" | jq -r '.success // false')
    
    if [ "$success" = "true" ]; then
        print_success "Admin security page rule created"
    else
        print_warning "Failed to create admin security page rule (may already exist)"
    fi
}

# Function to download Cloudflare origin certificate
download_origin_certificate() {
    print_status "Setting up Cloudflare Origin Certificate..."
    
    # Create SSL directory if it doesn't exist
    mkdir -p ../nginx/ssl
    
    # Note: Origin certificates must be generated manually in Cloudflare dashboard
    # for now, we'll create a self-signed certificate and provide instructions
    
    if [ ! -f "../nginx/ssl/cert.pem" ] || [ ! -f "../nginx/ssl/key.pem" ]; then
        print_warning "Cloudflare Origin Certificate not found. Generating self-signed certificate for testing..."
        
        # Generate self-signed certificate
        openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
            -keyout ../nginx/ssl/key.pem \
            -out ../nginx/ssl/cert.pem \
            -subj "/C=US/ST=CA/L=San Francisco/O=Pasargad Prints/CN=pasargadprints.com" \
            -addext "subjectAltName=DNS:pasargadprints.com,DNS:www.pasargadprints.com"
        
        print_success "Self-signed certificate generated"
        print_warning "For production, replace with Cloudflare Origin Certificate:"
        print_warning "1. Go to Cloudflare Dashboard -> SSL/TLS -> Origin Server"
        print_warning "2. Create Certificate for pasargadprints.com and www.pasargadprints.com"
        print_warning "3. Replace nginx/ssl/cert.pem and nginx/ssl/key.pem with downloaded files"
    else
        print_success "SSL certificates already exist"
    fi
}

# Main execution
main() {
    echo "========================================"
    echo "Cloudflare Configuration for Pasargad Prints"
    echo "========================================"
    
    # Check dependencies
    if ! command -v jq >/dev/null 2>&1; then
        print_error "jq is required but not installed. Please install jq and try again."
        exit 1
    fi
    
    if ! command -v curl >/dev/null 2>&1; then
        print_error "curl is required but not installed. Please install curl and try again."
        exit 1
    fi
    
    # Check if we have the required environment variables
    if [ -z "$CLOUDFLARE_API_TOKEN" ] || [ -z "$CLOUDFLARE_ZONE_ID" ]; then
        print_error "CLOUDFLARE_API_TOKEN and CLOUDFLARE_ZONE_ID must be set"
        exit 1
    fi
    
    print_status "Server IP: $SERVER_IP"
    print_status "Domain: $DOMAIN"
    print_status "Zone ID: $CLOUDFLARE_ZONE_ID"
    
    # Verify API token and get zone info
    check_api_token
    get_zone_info
    
    # Manage DNS records
    print_status "Setting up DNS records..."
    manage_dns_record "A" "$DOMAIN" "$SERVER_IP" 1 true
    manage_dns_record "A" "www.$DOMAIN" "$SERVER_IP" 1 true
    
    # Configure SSL settings
    configure_ssl
    
    # Configure security settings
    configure_security
    
    # Configure caching
    configure_caching
    
    # Create page rules
    create_page_rules
    
    # Setup SSL certificates
    download_origin_certificate
    
    print_success "Cloudflare configuration completed successfully!"
    echo ""
    echo "Next steps:"
    echo "1. Wait 5-10 minutes for DNS propagation"
    echo "2. Verify DNS records: dig pasargadprints.com"
    echo "3. Test SSL: https://www.ssllabs.com/ssltest/analyze.html?d=pasargadprints.com"
    echo "4. Deploy your application with docker-compose"
    echo ""
    echo "Cloudflare Dashboard: https://dash.cloudflare.com/"
}

# Run main function
main "$@"