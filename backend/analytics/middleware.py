from django.utils.deprecation import MiddlewareMixin
from django.urls import resolve
from .models import PageView
from .utils import parse_user_agent, get_client_ip
import re


class AnalyticsMiddleware(MiddlewareMixin):
    """
    Middleware to automatically track page views and collect analytics data
    """
    
    # URLs to exclude from tracking
    EXCLUDED_PATHS = [
        r'^/admin/',
        r'^/api/analytics/track/',
        r'^/static/',
        r'^/media/',
        r'^/favicon\.ico$',
    ]
    
    # Content types to track
    TRACKED_CONTENT_TYPES = [
        'text/html',
        'application/json',
    ]
    
    def __init__(self, get_response):
        super().__init__(get_response)
        self.excluded_patterns = [re.compile(pattern) for pattern in self.EXCLUDED_PATHS]
    
    def process_request(self, request):
        """Store analytics data in request for later use"""
        # Check if this path should be tracked
        if self._should_track_request(request):
            # Store UTM parameters in session for attribution
            self._store_utm_parameters(request)
            
            # Store landing page if it's the first page view in session
            if not request.session.get('landing_page'):
                request.session['landing_page'] = request.build_absolute_uri()
    
    def process_response(self, request, response):
        """Track page view after response is generated"""
        if (self._should_track_request(request) and 
            self._should_track_response(response) and
            request.method == 'GET'):
            
            try:
                self._track_page_view(request, response)
            except Exception:
                # Don't let analytics tracking break the app
                pass
        
        return response
    
    def _should_track_request(self, request):
        """Determine if this request should be tracked"""
        path = request.path
        
        # Check excluded patterns
        for pattern in self.excluded_patterns:
            if pattern.match(path):
                return False
        
        # Only track GET requests for page views
        if request.method != 'GET':
            return False
        
        return True
    
    def _should_track_response(self, response):
        """Determine if this response should be tracked"""
        # Only track successful responses
        if response.status_code >= 400:
            return False
        
        # Check content type
        content_type = response.get('Content-Type', '').split(';')[0]
        
        return content_type in self.TRACKED_CONTENT_TYPES
    
    def _store_utm_parameters(self, request):
        """Store UTM parameters in session for attribution tracking"""
        utm_params = ['utm_source', 'utm_medium', 'utm_campaign', 'utm_term', 'utm_content']
        
        for param in utm_params:
            value = request.GET.get(param)
            if value:
                request.session[param] = value
    
    def _track_page_view(self, request, response):
        """Create a page view record"""
        # Parse user agent
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        device_info = parse_user_agent(user_agent)
        
        # Get client IP
        ip_address = get_client_ip(request)
        
        # Get session ID
        session_id = request.session.session_key or ''
        
        # Ensure we have a session key
        if not session_id:
            request.session.save()
            session_id = request.session.session_key
        
        # Get page title from response if it's HTML
        page_title = ''
        content_type = response.get('Content-Type', '').split(';')[0]
        if content_type == 'text/html' and hasattr(response, 'content'):
            try:
                content = response.content.decode('utf-8')
                title_match = re.search(r'<title[^>]*>([^<]+)</title>', content, re.IGNORECASE)
                if title_match:
                    page_title = title_match.group(1).strip()
            except:
                pass
        
        # Create page view record
        PageView.objects.create(
            user=request.user if request.user.is_authenticated else None,
            session_id=session_id,
            page_url=request.build_absolute_uri(),
            page_title=page_title,
            referrer=request.META.get('HTTP_REFERER', ''),
            ip_address=ip_address,
            user_agent=user_agent,
            device_type=device_info.get('device_type', ''),
            browser=device_info.get('browser', ''),
            os=device_info.get('os', '')
        )