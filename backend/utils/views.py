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
    Comprehensive health check with system status for production monitoring
    """
    import time
    from django.utils import timezone
    
    start_time = time.time()
    
    health_status = {
        'status': 'healthy',
        'service': 'Pasargad Prints API',
        'version': getattr(settings, 'APP_VERSION', '1.0.0'),
        'environment': getattr(settings, 'SENTRY_ENVIRONMENT', 'unknown'),
        'timestamp': timezone.now().isoformat(),
        'checks': {},
        'metrics': {}
    }
    
    # Get health check settings
    health_settings = getattr(settings, 'HEALTH_CHECK_SETTINGS', {})
    db_timeout = health_settings.get('DATABASE_TIMEOUT', 10)
    redis_timeout = health_settings.get('REDIS_TIMEOUT', 5)
    enable_deep_checks = health_settings.get('ENABLE_DEEP_CHECKS', True)
    
    # Database health check with timing
    try:
        db_start = time.time()
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1, NOW(), version()")
            result = cursor.fetchone()
        db_duration = time.time() - db_start
        
        health_status['checks']['database'] = {
            'status': 'healthy',
            'message': 'Database connection successful',
            'response_time_ms': round(db_duration * 1000, 2),
            'version': result[2] if len(result) > 2 else 'unknown'
        }
        health_status['metrics']['database_response_time'] = db_duration
        
        # Additional database checks if enabled
        if enable_deep_checks:
            # Check database connections
            cursor.execute("SELECT count(*) FROM pg_stat_activity WHERE state = 'active'")
            active_connections = cursor.fetchone()[0]
            
            # Check database size
            cursor.execute("SELECT pg_size_pretty(pg_database_size(current_database()))")
            db_size = cursor.fetchone()[0]
            
            health_status['checks']['database'].update({
                'active_connections': active_connections,
                'database_size': db_size
            })
            
    except Exception as e:
        health_status['status'] = 'unhealthy'
        health_status['checks']['database'] = {
            'status': 'unhealthy',
            'message': f'Database connection failed: {str(e)}',
            'error': str(e)
        }
        logger.error(f"Database health check failed: {e}")
    
    # Redis/Cache health check with timing
    try:
        cache_start = time.time()
        test_key = f'health_check_{int(time.time())}'
        cache.set(test_key, 'ok', 10)
        cached_value = cache.get(test_key)
        cache_duration = time.time() - cache_start
        cache.delete(test_key)
        
        if cached_value == 'ok':
            health_status['checks']['cache'] = {
                'status': 'healthy',
                'message': 'Cache is working',
                'response_time_ms': round(cache_duration * 1000, 2)
            }
            health_status['metrics']['cache_response_time'] = cache_duration
            
            # Additional cache checks if enabled
            if enable_deep_checks and hasattr(settings, 'CACHES'):
                try:
                    from django_redis import get_redis_connection
                    redis_conn = get_redis_connection("default")
                    redis_info = redis_conn.info()
                    
                    health_status['checks']['cache'].update({
                        'memory_usage': redis_info.get('used_memory_human', 'unknown'),
                        'connected_clients': redis_info.get('connected_clients', 0),
                        'keyspace_hits': redis_info.get('keyspace_hits', 0),
                        'keyspace_misses': redis_info.get('keyspace_misses', 0)
                    })
                except Exception as redis_error:
                    logger.warning(f"Redis detailed check failed: {redis_error}")
        else:
            raise Exception("Cache read/write test failed")
            
    except Exception as e:
        health_status['checks']['cache'] = {
            'status': 'warning',
            'message': f'Cache check failed: {str(e)}',
            'error': str(e)
        }
        logger.warning(f"Cache health check failed: {e}")
    
    # Celery health check
    if enable_deep_checks:
        try:
            from celery import current_app
            inspect = current_app.control.inspect()
            stats = inspect.stats()
            
            if stats:
                health_status['checks']['celery'] = {
                    'status': 'healthy',
                    'message': 'Celery workers are active',
                    'active_workers': len(stats),
                    'worker_stats': stats
                }
            else:
                health_status['checks']['celery'] = {
                    'status': 'warning',
                    'message': 'No active Celery workers found'
                }
        except Exception as e:
            health_status['checks']['celery'] = {
                'status': 'warning',
                'message': f'Celery check failed: {str(e)}'
            }
    
    # Service integrations check
    services_check = {
        'stripe': {
            'configured': bool(getattr(settings, 'STRIPE_SECRET_KEY', '')),
            'live_mode': getattr(settings, 'STRIPE_LIVE_MODE', False)
        },
        'goshippo': {
            'configured': bool(getattr(settings, 'GOSHIPPO_API_KEY', '')),
            'live_mode': getattr(settings, 'GOSHIPPO_LIVE_MODE', False)
        },
        'email': {
            'configured': bool(getattr(settings, 'EMAIL_HOST_USER', ''))
        }
    }
    
    all_services_ok = all(service['configured'] for service in services_check.values())
    health_status['checks']['services'] = {
        'status': 'healthy' if all_services_ok else 'warning',
        'message': 'All services configured' if all_services_ok else 'Some services not configured',
        'details': services_check
    }
    
    # System resources check
    try:
        # CPU usage
        cpu_percent = psutil.cpu_percent(interval=0.1)
        
        # Memory usage
        memory = psutil.virtual_memory()
        
        # Disk usage
        disk_usage = psutil.disk_usage('/')
        
        # Load average (Unix only)
        try:
            load_avg = os.getloadavg()
        except (AttributeError, OSError):
            load_avg = None
        
        # Network I/O
        net_io = psutil.net_io_counters()
        
        system_metrics = {
            'cpu_percent': cpu_percent,
            'memory_percent': memory.percent,
            'memory_available_gb': round(memory.available / (1024**3), 2),
            'disk_percent': disk_usage.percent,
            'disk_free_gb': round(disk_usage.free / (1024**3), 2),
            'load_average': load_avg,
            'network_bytes_sent': net_io.bytes_sent if net_io else None,
            'network_bytes_recv': net_io.bytes_recv if net_io else None
        }
        
        health_status['metrics']['system'] = system_metrics
        
        # Determine system health status
        cpu_threshold = health_settings.get('CPU_USAGE_THRESHOLD', 85)
        memory_threshold = health_settings.get('MEMORY_USAGE_THRESHOLD', 85)
        disk_threshold = health_settings.get('DISK_USAGE_THRESHOLD', 85)
        
        if (cpu_percent > cpu_threshold or 
            memory.percent > memory_threshold or 
            disk_usage.percent > disk_threshold):
            system_status = 'warning'
            system_message = 'High resource usage detected'
        else:
            system_status = 'healthy'
            system_message = 'System resources within normal limits'
        
        health_status['checks']['system'] = {
            'status': system_status,
            'message': system_message,
            'metrics': system_metrics
        }
        
    except Exception as e:
        health_status['checks']['system'] = {
            'status': 'unknown',
            'message': f'Could not check system resources: {str(e)}'
        }
    
    # Calculate overall health status
    check_statuses = [check['status'] for check in health_status['checks'].values()]
    
    if 'unhealthy' in check_statuses:
        health_status['status'] = 'unhealthy'
    elif 'warning' in check_statuses:
        health_status['status'] = 'warning'
    else:
        health_status['status'] = 'healthy'
    
    # Add timing metrics
    total_duration = time.time() - start_time
    health_status['metrics']['health_check_duration'] = round(total_duration, 3)
    
    # Set appropriate HTTP status code
    if health_status['status'] == 'unhealthy':
        status_code = 503  # Service Unavailable
    elif health_status['status'] == 'warning':
        status_code = 200  # OK but with warnings
    else:
        status_code = 200  # OK
    
    return Response(health_status, status=status_code)


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