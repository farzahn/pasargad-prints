"""
Utility views for health checks and monitoring
"""
import os
import psutil
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_http_methods
from django.db import connection
from django.core.cache import cache
from django.conf import settings
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
import logging

logger = logging.getLogger(__name__)


@api_view(['GET'])
@permission_classes([AllowAny])
def health_check(request):
    """
    Basic health check endpoint
    """
    return Response({
        'status': 'healthy',
        'service': 'Pasargad Prints API',
        'version': '1.0.0'
    })


@api_view(['GET'])
@permission_classes([AllowAny])
def detailed_health_check(request):
    """
    Detailed health check with system status
    """
    health_status = {
        'status': 'healthy',
        'service': 'Pasargad Prints API',
        'version': '1.0.0',
        'checks': {}
    }
    
    # Check database connection
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
        health_status['checks']['database'] = {
            'status': 'healthy',
            'message': 'Database connection successful'
        }
    except Exception as e:
        health_status['status'] = 'unhealthy'
        health_status['checks']['database'] = {
            'status': 'unhealthy',
            'message': f'Database connection failed: {str(e)}'
        }
        logger.error(f"Database health check failed: {e}")
    
    # Check cache
    try:
        cache.set('health_check', 'ok', 10)
        if cache.get('health_check') == 'ok':
            health_status['checks']['cache'] = {
                'status': 'healthy',
                'message': 'Cache is working'
            }
        else:
            raise Exception("Cache read/write failed")
    except Exception as e:
        health_status['checks']['cache'] = {
            'status': 'warning',
            'message': f'Cache check failed: {str(e)}'
        }
        logger.warning(f"Cache health check failed: {e}")
    
    # Check Stripe configuration
    if settings.STRIPE_SECRET_KEY:
        health_status['checks']['stripe'] = {
            'status': 'healthy',
            'message': 'Stripe is configured'
        }
    else:
        health_status['checks']['stripe'] = {
            'status': 'warning',
            'message': 'Stripe is not configured'
        }
    
    # Check email configuration
    if settings.EMAIL_HOST_USER:
        health_status['checks']['email'] = {
            'status': 'healthy',
            'message': 'Email is configured'
        }
    else:
        health_status['checks']['email'] = {
            'status': 'warning',
            'message': 'Email is not configured'
        }
    
    # Check disk space
    try:
        disk_usage = psutil.disk_usage('/')
        if disk_usage.percent < 90:
            health_status['checks']['disk_space'] = {
                'status': 'healthy',
                'message': f'Disk usage: {disk_usage.percent}%'
            }
        else:
            health_status['status'] = 'warning'
            health_status['checks']['disk_space'] = {
                'status': 'warning',
                'message': f'High disk usage: {disk_usage.percent}%'
            }
    except Exception as e:
        health_status['checks']['disk_space'] = {
            'status': 'unknown',
            'message': f'Could not check disk space: {str(e)}'
        }
    
    # Check memory usage
    try:
        memory = psutil.virtual_memory()
        if memory.percent < 90:
            health_status['checks']['memory'] = {
                'status': 'healthy',
                'message': f'Memory usage: {memory.percent}%'
            }
        else:
            health_status['status'] = 'warning'
            health_status['checks']['memory'] = {
                'status': 'warning',
                'message': f'High memory usage: {memory.percent}%'
            }
    except Exception as e:
        health_status['checks']['memory'] = {
            'status': 'unknown',
            'message': f'Could not check memory: {str(e)}'
        }
    
    # Overall status
    unhealthy_checks = [
        check for check in health_status['checks'].values()
        if check['status'] == 'unhealthy'
    ]
    
    if unhealthy_checks:
        health_status['status'] = 'unhealthy'
    elif any(check['status'] == 'warning' for check in health_status['checks'].values()):
        health_status['status'] = 'warning'
    
    return Response(health_status)


@require_http_methods(['GET'])
def robots_txt(request):
    """
    Serve robots.txt file
    """
    lines = [
        "User-agent: *",
        "Disallow: /api/",
        "Disallow: /admin/",
        "Disallow: /media/",
        "Allow: /",
    ]
    return HttpResponse("\n".join(lines), content_type="text/plain")