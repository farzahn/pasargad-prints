from django.contrib.admin.views.decorators import staff_member_required
from django.http import JsonResponse
from django.core.cache import cache
from django.db import connection
from django.conf import settings
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
import redis
import psutil
import time

@api_view(['GET'])
@permission_classes([IsAdminUser])
def system_health_check(request):
    """
    Health check endpoint for monitoring system status
    """
    health_status = {
        'status': 'healthy',
        'timestamp': time.time(),
        'checks': {}
    }
    
    # Database check
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
        health_status['checks']['database'] = {
            'status': 'healthy',
            'response_time': connection.queries[-1]['time'] if connection.queries else 0
        }
    except Exception as e:
        health_status['checks']['database'] = {
            'status': 'unhealthy',
            'error': str(e)
        }
        health_status['status'] = 'unhealthy'
    
    # Redis check
    try:
        r = redis.from_url(settings.CACHES['default']['LOCATION'])
        start_time = time.time()
        r.ping()
        response_time = time.time() - start_time
        health_status['checks']['redis'] = {
            'status': 'healthy',
            'response_time': round(response_time * 1000, 2)  # ms
        }
    except Exception as e:
        health_status['checks']['redis'] = {
            'status': 'unhealthy',
            'error': str(e)
        }
        health_status['status'] = 'unhealthy'
    
    # System resources
    health_status['checks']['system'] = {
        'cpu_percent': psutil.cpu_percent(interval=1),
        'memory_percent': psutil.virtual_memory().percent,
        'disk_percent': psutil.disk_usage('/').percent,
    }
    
    # Check if any resource is critical
    if (health_status['checks']['system']['cpu_percent'] > 90 or
        health_status['checks']['system']['memory_percent'] > 90 or
        health_status['checks']['system']['disk_percent'] > 90):
        health_status['status'] = 'degraded'
    
    return Response(health_status)

@api_view(['GET'])
@permission_classes([IsAdminUser])
def cache_statistics(request):
    """
    Get cache statistics and performance metrics
    """
    try:
        r = redis.from_url(settings.CACHES['default']['LOCATION'])
        info = r.info()
        
        stats = {
            'memory': {
                'used_memory': info.get('used_memory_human', 'N/A'),
                'used_memory_peak': info.get('used_memory_peak_human', 'N/A'),
                'memory_fragmentation_ratio': info.get('mem_fragmentation_ratio', 'N/A'),
            },
            'stats': {
                'total_connections_received': info.get('total_connections_received', 0),
                'total_commands_processed': info.get('total_commands_processed', 0),
                'instantaneous_ops_per_sec': info.get('instantaneous_ops_per_sec', 0),
                'keyspace_hits': info.get('keyspace_hits', 0),
                'keyspace_misses': info.get('keyspace_misses', 0),
                'evicted_keys': info.get('evicted_keys', 0),
                'expired_keys': info.get('expired_keys', 0),
            },
            'clients': {
                'connected_clients': info.get('connected_clients', 0),
                'blocked_clients': info.get('blocked_clients', 0),
            }
        }
        
        # Calculate hit rate
        hits = stats['stats']['keyspace_hits']
        misses = stats['stats']['keyspace_misses']
        if hits + misses > 0:
            stats['stats']['hit_rate'] = round((hits / (hits + misses)) * 100, 2)
        else:
            stats['stats']['hit_rate'] = 0
        
        return Response(stats)
        
    except Exception as e:
        return Response({
            'error': 'Failed to retrieve cache statistics',
            'detail': str(e)
        }, status=500)

@api_view(['GET'])
@permission_classes([IsAdminUser])
def database_statistics(request):
    """
    Get database performance statistics
    """
    stats = {
        'query_count': len(connection.queries),
        'total_time': sum(float(query['time']) for query in connection.queries),
        'slow_queries': [],
        'table_sizes': {}
    }
    
    # Find slow queries
    for query in connection.queries:
        if float(query['time']) > 0.1:  # Queries taking more than 100ms
            stats['slow_queries'].append({
                'sql': query['sql'][:200] + '...' if len(query['sql']) > 200 else query['sql'],
                'time': query['time']
            })
    
    # Get table sizes
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT 
                schemaname,
                tablename,
                pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
            FROM pg_tables
            WHERE schemaname = 'public'
            ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
            LIMIT 10
        """)
        stats['table_sizes'] = {
            row[1]: row[2] for row in cursor.fetchall()
        }
    
    return Response(stats)

@api_view(['POST'])
@permission_classes([IsAdminUser])
def clear_cache(request):
    """
    Clear specific cache or all caches
    """
    cache_type = request.data.get('cache_type', 'all')
    
    try:
        if cache_type == 'all':
            cache.clear()
            message = 'All caches cleared successfully'
        elif cache_type == 'api':
            # Clear API cache
            r = redis.from_url(settings.CACHES['api']['LOCATION'])
            r.flushdb()
            message = 'API cache cleared successfully'
        elif cache_type == 'session':
            # Clear session cache
            r = redis.from_url(settings.CACHES['session']['LOCATION'])
            r.flushdb()
            message = 'Session cache cleared successfully'
        else:
            # Clear specific pattern
            pattern = request.data.get('pattern', '*')
            if hasattr(cache._cache.get_client(), 'delete_pattern'):
                deleted = cache._cache.get_client().delete_pattern(pattern)
                message = f'Deleted {deleted} keys matching pattern: {pattern}'
            else:
                return Response({
                    'error': 'Pattern deletion not supported by cache backend'
                }, status=400)
        
        return Response({
            'success': True,
            'message': message
        })
        
    except Exception as e:
        return Response({
            'error': 'Failed to clear cache',
            'detail': str(e)
        }, status=500)