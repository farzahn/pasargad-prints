"""
Security Middleware for Pasargad Prints Production
Enhanced security measures including rate limiting, intrusion detection, and security headers
"""

import logging
import json
import time
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from collections import defaultdict
from ipaddress import ip_address, ip_network

from django.http import HttpResponse, JsonResponse
from django.core.cache import cache
from django.conf import settings
from django.utils.deprecation import MiddlewareMixin
from django.contrib.auth.signals import user_login_failed
from django.dispatch import receiver
from django.core.mail import send_mail

import requests
from user_agents import parse

logger = logging.getLogger('security')

class SecurityMiddleware(MiddlewareMixin):
    """Enhanced security middleware with multiple protection layers"""
    
    def __init__(self, get_response):
        super().__init__(get_response)
        self.rate_limiter = RateLimiter()
        self.intrusion_detector = IntrusionDetector()
        self.security_headers = SecurityHeaders()
        
    def process_request(self, request):
        """Process incoming request for security checks"""
        
        # Get client IP
        client_ip = self.get_client_ip(request)
        request.client_ip = client_ip
        
        # Check IP whitelist/blacklist
        if self.is_blocked_ip(client_ip):
            logger.warning(f"Blocked request from blacklisted IP: {client_ip}")
            return JsonResponse({'error': 'Access denied'}, status=403)
        
        # Rate limiting
        if not self.rate_limiter.allow_request(request):
            logger.warning(f"Rate limit exceeded for IP: {client_ip}")
            return JsonResponse({'error': 'Rate limit exceeded'}, status=429)
        
        # Intrusion detection
        threat_detected = self.intrusion_detector.analyze_request(request)
        if threat_detected:
            logger.warning(f"Potential threat detected from IP: {client_ip}")
            self.handle_threat(request, threat_detected)
        
        return None
    
    def process_response(self, request, response):
        """Process outgoing response to add security headers"""
        response = self.security_headers.add_headers(response)
        
        # Log security events
        self.log_request(request, response)
        
        return response
    
    def get_client_ip(self, request) -> str:
        """Get the real client IP address"""
        # Check for IP in various headers (for load balancers/proxies)
        ip_headers = [
            'HTTP_X_FORWARDED_FOR',
            'HTTP_X_REAL_IP',
            'HTTP_CF_CONNECTING_IP',  # Cloudflare
            'HTTP_X_CLUSTER_CLIENT_IP',
            'REMOTE_ADDR'
        ]
        
        for header in ip_headers:
            ip = request.META.get(header)
            if ip:
                # Handle comma-separated IPs (X-Forwarded-For)
                ip = ip.split(',')[0].strip()
                try:
                    # Validate IP address
                    ip_address(ip)
                    return ip
                except ValueError:
                    continue
        
        return request.META.get('REMOTE_ADDR', '127.0.0.1')
    
    def is_blocked_ip(self, ip: str) -> bool:
        """Check if IP is in blacklist"""
        try:
            # Check cache first
            cache_key = f"blocked_ip:{ip}"
            if cache.get(cache_key):
                return True
            
            # Check against configured blacklists
            blacklisted_networks = getattr(settings, 'SECURITY_BLACKLISTED_NETWORKS', [])
            
            for network in blacklisted_networks:
                try:
                    if ip_address(ip) in ip_network(network):
                        cache.set(cache_key, True, 3600)  # Cache for 1 hour
                        return True
                except ValueError:
                    continue
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking IP blacklist: {str(e)}")
            return False
    
    def handle_threat(self, request, threat_info: Dict):
        """Handle detected security threat"""
        client_ip = request.client_ip
        
        # Temporarily block IP
        cache.set(f"blocked_ip:{client_ip}", True, 3600)  # Block for 1 hour
        
        # Send security alert
        self.send_security_alert(request, threat_info)
        
        # Log detailed threat information
        threat_data = {
            'timestamp': datetime.now().isoformat(),
            'ip': client_ip,
            'user_agent': request.META.get('HTTP_USER_AGENT', ''),
            'path': request.path,
            'method': request.method,
            'threat_type': threat_info.get('type'),
            'threat_details': threat_info.get('details'),
            'severity': threat_info.get('severity', 'medium')
        }
        
        security_logger = logging.getLogger('security.threats')
        security_logger.warning(json.dumps(threat_data))
    
    def send_security_alert(self, request, threat_info: Dict):
        """Send security alert notification"""
        try:
            subject = f"🚨 Security Threat Detected - {threat_info.get('type', 'Unknown')}"
            
            message = f"""
            Security Threat Detected:
            
            IP Address: {request.client_ip}
            User Agent: {request.META.get('HTTP_USER_AGENT', 'N/A')}
            Path: {request.path}
            Method: {request.method}
            Threat Type: {threat_info.get('type', 'Unknown')}
            Severity: {threat_info.get('severity', 'Medium')}
            Details: {threat_info.get('details', 'No details available')}
            Timestamp: {datetime.now()}
            
            The IP has been temporarily blocked.
            """
            
            admin_email = getattr(settings, 'SECURITY_ALERT_EMAIL', 
                                getattr(settings, 'ADMIN_EMAIL', 'admin@pasargadprints.com'))
            
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[admin_email],
                fail_silently=True
            )
            
        except Exception as e:
            logger.error(f"Failed to send security alert: {str(e)}")
    
    def log_request(self, request, response):
        """Log request for security analysis"""
        try:
            # Only log potentially suspicious requests
            if self.should_log_request(request, response):
                log_data = {
                    'timestamp': datetime.now().isoformat(),
                    'ip': request.client_ip,
                    'method': request.method,
                    'path': request.path,
                    'status_code': response.status_code,
                    'user_agent': request.META.get('HTTP_USER_AGENT', ''),
                    'referer': request.META.get('HTTP_REFERER', ''),
                    'content_length': len(response.content) if hasattr(response, 'content') else 0,
                }
                
                # Add user info if authenticated
                if hasattr(request, 'user') and request.user.is_authenticated:
                    log_data['user_id'] = request.user.id
                    log_data['username'] = request.user.username
                
                security_logger = logging.getLogger('security.access')
                security_logger.info(json.dumps(log_data))
                
        except Exception as e:
            logger.error(f"Error logging request: {str(e)}")
    
    def should_log_request(self, request, response) -> bool:
        """Determine if request should be logged"""
        # Log error responses
        if response.status_code >= 400:
            return True
        
        # Log admin access
        if request.path.startswith('/admin/'):
            return True
        
        # Log API access
        if request.path.startswith('/api/'):
            return True
        
        # Log authentication attempts
        if request.path in ['/login/', '/register/', '/api/auth/']:
            return True
        
        return False

class RateLimiter:
    """Advanced rate limiting with multiple strategies"""
    
    def __init__(self):
        self.rate_limits = {
            'default': {'requests': 100, 'window': 3600},  # 100 requests per hour
            'api': {'requests': 1000, 'window': 3600},     # 1000 API requests per hour
            'auth': {'requests': 5, 'window': 300},        # 5 auth attempts per 5 minutes
            'admin': {'requests': 50, 'window': 3600},     # 50 admin requests per hour
        }
    
    def allow_request(self, request) -> bool:
        """Check if request is allowed based on rate limits"""
        try:
            client_ip = request.client_ip
            rate_limit_key = self.get_rate_limit_key(request)
            limits = self.rate_limits.get(rate_limit_key, self.rate_limits['default'])
            
            # Create cache key
            cache_key = f"rate_limit:{rate_limit_key}:{client_ip}"
            
            # Get current count
            current_count = cache.get(cache_key, 0)
            
            # Check if limit exceeded
            if current_count >= limits['requests']:
                return False
            
            # Increment counter
            cache.set(cache_key, current_count + 1, limits['window'])
            
            return True
            
        except Exception as e:
            logger.error(f"Error in rate limiting: {str(e)}")
            return True  # Allow request on error
    
    def get_rate_limit_key(self, request) -> str:
        """Determine which rate limit category to use"""
        path = request.path.lower()
        
        if path.startswith('/admin/'):
            return 'admin'
        elif path.startswith('/api/'):
            return 'api'
        elif any(auth_path in path for auth_path in ['/login', '/register', '/auth']):
            return 'auth'
        else:
            return 'default'

class IntrusionDetector:
    """Detect and analyze potential security threats"""
    
    def __init__(self):
        self.sql_injection_patterns = [
            r"(\s|^)(select|insert|update|delete|drop|create|alter|exec|execute)\s",
            r"(\s|^)(union|having|group\s+by|order\s+by)\s",
            r"(\s|^)(-{2,}|\/\*|\*\/)",
            r"(\s|^)(or|and)\s+\d+\s*=\s*\d+",
            r"(\s|^)(or|and)\s+['\"][^'\"]*['\"]",
        ]
        
        self.xss_patterns = [
            r"<script[^>]*>",
            r"javascript:",
            r"on\w+\s*=",
            r"expression\s*\(",
            r"<iframe[^>]*>",
        ]
        
        self.path_traversal_patterns = [
            r"\.\./",
            r"\.\.\\",
            r"%2e%2e%2f",
            r"%2e%2e\\",
        ]
        
        self.suspicious_user_agents = [
            'nikto', 'sqlmap', 'nmap', 'masscan', 'zap', 'burp',
            'havij', 'acunetix', 'nessus', 'openvas', 'w3af'
        ]
    
    def analyze_request(self, request) -> Optional[Dict]:
        """Analyze request for potential threats"""
        threats = []
        
        # Check for SQL injection
        sql_threat = self.check_sql_injection(request)
        if sql_threat:
            threats.append(sql_threat)
        
        # Check for XSS
        xss_threat = self.check_xss(request)
        if xss_threat:
            threats.append(xss_threat)
        
        # Check for path traversal
        path_threat = self.check_path_traversal(request)
        if path_threat:
            threats.append(path_threat)
        
        # Check user agent
        ua_threat = self.check_user_agent(request)
        if ua_threat:
            threats.append(ua_threat)
        
        # Check for brute force
        bf_threat = self.check_brute_force(request)
        if bf_threat:
            threats.append(bf_threat)
        
        if threats:
            return {
                'type': 'multiple' if len(threats) > 1 else threats[0]['type'],
                'details': threats,
                'severity': max(threat.get('severity_level', 1) for threat in threats)
            }
        
        return None
    
    def check_sql_injection(self, request) -> Optional[Dict]:
        """Check for SQL injection attempts"""
        import re
        
        # Check query parameters
        query_string = request.META.get('QUERY_STRING', '').lower()
        
        # Check POST data
        post_data = ''
        if hasattr(request, 'body'):
            try:
                post_data = request.body.decode('utf-8', errors='ignore').lower()
            except:
                pass
        
        # Check path
        path = request.path.lower()
        
        data_to_check = f"{query_string} {post_data} {path}"
        
        for pattern in self.sql_injection_patterns:
            if re.search(pattern, data_to_check, re.IGNORECASE):
                return {
                    'type': 'sql_injection',
                    'pattern': pattern,
                    'severity_level': 3
                }
        
        return None
    
    def check_xss(self, request) -> Optional[Dict]:
        """Check for XSS attempts"""
        import re
        
        # Check query parameters and POST data
        query_string = request.META.get('QUERY_STRING', '')
        
        post_data = ''
        if hasattr(request, 'body'):
            try:
                post_data = request.body.decode('utf-8', errors='ignore')
            except:
                pass
        
        data_to_check = f"{query_string} {post_data}"
        
        for pattern in self.xss_patterns:
            if re.search(pattern, data_to_check, re.IGNORECASE):
                return {
                    'type': 'xss',
                    'pattern': pattern,
                    'severity_level': 2
                }
        
        return None
    
    def check_path_traversal(self, request) -> Optional[Dict]:
        """Check for path traversal attempts"""
        import re
        
        path = request.path
        query_string = request.META.get('QUERY_STRING', '')
        
        data_to_check = f"{path} {query_string}"
        
        for pattern in self.path_traversal_patterns:
            if re.search(pattern, data_to_check, re.IGNORECASE):
                return {
                    'type': 'path_traversal',
                    'pattern': pattern,
                    'severity_level': 2
                }
        
        return None
    
    def check_user_agent(self, request) -> Optional[Dict]:
        """Check for suspicious user agents"""
        user_agent = request.META.get('HTTP_USER_AGENT', '').lower()
        
        for suspicious_ua in self.suspicious_user_agents:
            if suspicious_ua in user_agent:
                return {
                    'type': 'suspicious_user_agent',
                    'user_agent': user_agent,
                    'severity_level': 2
                }
        
        return None
    
    def check_brute_force(self, request) -> Optional[Dict]:
        """Check for brute force attempts"""
        # Check for repeated failed login attempts
        if any(path in request.path for path in ['/login', '/auth', '/admin']):
            client_ip = request.client_ip
            cache_key = f"failed_attempts:{client_ip}"
            
            failed_attempts = cache.get(cache_key, 0)
            
            if failed_attempts > 10:  # More than 10 attempts
                return {
                    'type': 'brute_force',
                    'failed_attempts': failed_attempts,
                    'severity_level': 3
                }
        
        return None

class SecurityHeaders:
    """Add security headers to responses"""
    
    def __init__(self):
        self.headers = {
            'X-Content-Type-Options': 'nosniff',
            'X-Frame-Options': 'DENY',
            'X-XSS-Protection': '1; mode=block',
            'Referrer-Policy': 'strict-origin-when-cross-origin',
            'Content-Security-Policy': self.get_csp_header(),
            'Permissions-Policy': self.get_permissions_policy(),
            'X-Permitted-Cross-Domain-Policies': 'none',
            'Cross-Origin-Embedder-Policy': 'require-corp',
            'Cross-Origin-Opener-Policy': 'same-origin',
            'Cross-Origin-Resource-Policy': 'same-origin',
        }
    
    def add_headers(self, response) -> HttpResponse:
        """Add security headers to response"""
        for header, value in self.headers.items():
            response[header] = value
        
        # Add HSTS header for HTTPS
        if getattr(settings, 'SECURE_SSL_REDIRECT', False):
            hsts_seconds = getattr(settings, 'SECURE_HSTS_SECONDS', 31536000)
            hsts_header = f'max-age={hsts_seconds}'
            
            if getattr(settings, 'SECURE_HSTS_INCLUDE_SUBDOMAINS', True):
                hsts_header += '; includeSubDomains'
            
            if getattr(settings, 'SECURE_HSTS_PRELOAD', True):
                hsts_header += '; preload'
            
            response['Strict-Transport-Security'] = hsts_header
        
        return response
    
    def get_csp_header(self) -> str:
        """Generate Content Security Policy header"""
        # Basic CSP - should be customized based on application needs
        csp_directives = [
            "default-src 'self'",
            "script-src 'self' 'unsafe-inline' https://js.stripe.com",
            "style-src 'self' 'unsafe-inline'",
            "img-src 'self' data: https:",
            "font-src 'self'",
            "connect-src 'self' https://api.stripe.com",
            "frame-src https://js.stripe.com",
            "object-src 'none'",
            "base-uri 'self'",
            "form-action 'self'",
            "frame-ancestors 'none'",
            "upgrade-insecure-requests"
        ]
        
        return '; '.join(csp_directives)
    
    def get_permissions_policy(self) -> str:
        """Generate Permissions Policy header"""
        permissions = [
            'accelerometer=()',
            'camera=()',
            'geolocation=()',
            'gyroscope=()',
            'magnetometer=()',
            'microphone=()',
            'payment=(self)',
            'usb=()'
        ]
        
        return ', '.join(permissions)

# Signal handlers for security events
@receiver(user_login_failed)
def handle_failed_login(sender, credentials, request, **kwargs):
    """Handle failed login attempts"""
    try:
        # Get client IP
        middleware = SecurityMiddleware(None)
        client_ip = middleware.get_client_ip(request)
        
        # Increment failed attempt counter
        cache_key = f"failed_attempts:{client_ip}"
        failed_attempts = cache.get(cache_key, 0) + 1
        cache.set(cache_key, failed_attempts, 3600)  # Reset after 1 hour
        
        # Log failed attempt
        logger.warning(f"Failed login attempt from {client_ip} for user {credentials.get('username', 'unknown')}")
        
        # Block IP after too many failures
        if failed_attempts > 5:
            cache.set(f"blocked_ip:{client_ip}", True, 3600)
            logger.warning(f"IP {client_ip} blocked due to repeated failed login attempts")
            
            # Send security alert
            try:
                admin_email = getattr(settings, 'SECURITY_ALERT_EMAIL', 
                                    getattr(settings, 'ADMIN_EMAIL', 'admin@pasargadprints.com'))
                
                send_mail(
                    subject=f"🚨 Repeated Failed Login Attempts - IP Blocked",
                    message=f"""
                    IP Address {client_ip} has been temporarily blocked due to {failed_attempts} failed login attempts.
                    
                    Last attempted username: {credentials.get('username', 'unknown')}
                    Time: {datetime.now()}
                    User Agent: {request.META.get('HTTP_USER_AGENT', 'N/A')}
                    
                    The IP will be automatically unblocked after 1 hour.
                    """,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[admin_email],
                    fail_silently=True
                )
            except Exception as e:
                logger.error(f"Failed to send security alert: {str(e)}")
                
    except Exception as e:
        logger.error(f"Error handling failed login: {str(e)}")

# Custom security decorators
def security_check(view_func):
    """Decorator to add additional security checks to views"""
    def wrapper(request, *args, **kwargs):
        # Add custom security checks here
        return view_func(request, *args, **kwargs)
    return wrapper