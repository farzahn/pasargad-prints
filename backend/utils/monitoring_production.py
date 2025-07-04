"""
Production Monitoring and Alerting System for Pasargad Prints
Enhanced monitoring with metrics collection, alerting, and health checks
"""

import os
import time
import logging
import json
import traceback
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import asyncio
from concurrent.futures import ThreadPoolExecutor

from django.core.cache import cache
from django.db import connection, connections
from django.conf import settings
from django.core.mail import send_mail
from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.views.decorators.csrf import csrf_exempt

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework import status

import redis
import psutil
import requests
from decouple import config

# Configure logging
logger = logging.getLogger('monitoring')

class MetricsCollector:
    """Collect system and application metrics"""
    
    def __init__(self):
        self.redis_client = redis.from_url(settings.CACHES['default']['LOCATION'])
        self.metrics_cache_key = 'system_metrics'
        self.metrics_ttl = 300  # 5 minutes
        
    def collect_system_metrics(self) -> Dict[str, Any]:
        """Collect system-level metrics"""
        try:
            # CPU metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_count = psutil.cpu_count()
            cpu_freq = psutil.cpu_freq()
            
            # Memory metrics
            memory = psutil.virtual_memory()
            swap = psutil.swap_memory()
            
            # Disk metrics
            disk_usage = psutil.disk_usage('/')
            disk_io = psutil.disk_io_counters()
            
            # Network metrics
            network_io = psutil.net_io_counters()
            
            # Process metrics
            process = psutil.Process()
            process_info = {
                'cpu_percent': process.cpu_percent(),
                'memory_percent': process.memory_percent(),
                'memory_info': process.memory_info()._asdict(),
                'num_threads': process.num_threads(),
                'num_fds': process.num_fds() if hasattr(process, 'num_fds') else None,
                'create_time': process.create_time(),
            }
            
            return {
                'timestamp': datetime.now().isoformat(),
                'cpu': {
                    'percent': cpu_percent,
                    'count': cpu_count,
                    'frequency': cpu_freq._asdict() if cpu_freq else None,
                },
                'memory': {
                    'total': memory.total,
                    'available': memory.available,
                    'percent': memory.percent,
                    'used': memory.used,
                    'free': memory.free,
                    'buffers': memory.buffers,
                    'cached': memory.cached,
                },
                'swap': {
                    'total': swap.total,
                    'used': swap.used,
                    'free': swap.free,
                    'percent': swap.percent,
                },
                'disk': {
                    'total': disk_usage.total,
                    'used': disk_usage.used,
                    'free': disk_usage.free,
                    'percent': disk_usage.percent,
                    'io': disk_io._asdict() if disk_io else None,
                },
                'network': {
                    'bytes_sent': network_io.bytes_sent,
                    'bytes_recv': network_io.bytes_recv,
                    'packets_sent': network_io.packets_sent,
                    'packets_recv': network_io.packets_recv,
                    'errin': network_io.errin,
                    'errout': network_io.errout,
                    'dropin': network_io.dropin,
                    'dropout': network_io.dropout,
                },
                'process': process_info,
            }
            
        except Exception as e:
            logger.error(f"Error collecting system metrics: {str(e)}")
            return {}
    
    def collect_database_metrics(self) -> Dict[str, Any]:
        """Collect database performance metrics"""
        try:
            db_metrics = {}
            
            for db_name, db_config in connections.databases.items():
                try:
                    conn = connections[db_name]
                    with conn.cursor() as cursor:
                        # Connection info
                        cursor.execute("SELECT COUNT(*) FROM pg_stat_activity WHERE datname = %s", [db_config['NAME']])
                        active_connections = cursor.fetchone()[0]
                        
                        # Database size
                        cursor.execute("SELECT pg_size_pretty(pg_database_size(%s))", [db_config['NAME']])
                        db_size = cursor.fetchone()[0]
                        
                        # Query statistics
                        cursor.execute("""
                            SELECT 
                                sum(calls) as total_calls,
                                sum(total_time) as total_time,
                                sum(rows) as total_rows,
                                avg(mean_time) as avg_time
                            FROM pg_stat_statements 
                            WHERE dbid = (SELECT oid FROM pg_database WHERE datname = %s)
                        """, [db_config['NAME']])
                        
                        query_stats = cursor.fetchone()
                        
                        # Table statistics
                        cursor.execute("""
                            SELECT 
                                schemaname,
                                tablename,
                                n_tup_ins + n_tup_upd + n_tup_del as total_dml,
                                n_tup_ins as inserts,
                                n_tup_upd as updates,
                                n_tup_del as deletes,
                                seq_scan as seq_scans,
                                seq_tup_read as seq_reads,
                                idx_scan as idx_scans,
                                idx_tup_fetch as idx_reads
                            FROM pg_stat_user_tables
                            ORDER BY total_dml DESC
                            LIMIT 10
                        """)
                        
                        table_stats = cursor.fetchall()
                        
                        db_metrics[db_name] = {
                            'active_connections': active_connections,
                            'database_size': db_size,
                            'query_stats': {
                                'total_calls': query_stats[0] if query_stats[0] else 0,
                                'total_time': float(query_stats[1]) if query_stats[1] else 0,
                                'total_rows': query_stats[2] if query_stats[2] else 0,
                                'avg_time': float(query_stats[3]) if query_stats[3] else 0,
                            },
                            'table_stats': [
                                {
                                    'schema': row[0],
                                    'table': row[1],
                                    'total_dml': row[2],
                                    'inserts': row[3],
                                    'updates': row[4],
                                    'deletes': row[5],
                                    'seq_scans': row[6],
                                    'seq_reads': row[7],
                                    'idx_scans': row[8],
                                    'idx_reads': row[9],
                                }
                                for row in table_stats
                            ]
                        }
                        
                except Exception as e:
                    logger.error(f"Error collecting metrics for database {db_name}: {str(e)}")
                    db_metrics[db_name] = {'error': str(e)}
            
            return db_metrics
            
        except Exception as e:
            logger.error(f"Error collecting database metrics: {str(e)}")
            return {}
    
    def collect_redis_metrics(self) -> Dict[str, Any]:
        """Collect Redis performance metrics"""
        try:
            redis_metrics = {}
            
            for cache_name, cache_config in settings.CACHES.items():
                try:
                    if 'redis' in cache_config['BACKEND'].lower():
                        r = redis.from_url(cache_config['LOCATION'])
                        info = r.info()
                        
                        redis_metrics[cache_name] = {
                            'memory': {
                                'used_memory': info.get('used_memory', 0),
                                'used_memory_human': info.get('used_memory_human', 'N/A'),
                                'used_memory_peak': info.get('used_memory_peak', 0),
                                'used_memory_peak_human': info.get('used_memory_peak_human', 'N/A'),
                                'memory_fragmentation_ratio': info.get('mem_fragmentation_ratio', 0),
                            },
                            'stats': {
                                'connected_clients': info.get('connected_clients', 0),
                                'blocked_clients': info.get('blocked_clients', 0),
                                'total_connections_received': info.get('total_connections_received', 0),
                                'total_commands_processed': info.get('total_commands_processed', 0),
                                'instantaneous_ops_per_sec': info.get('instantaneous_ops_per_sec', 0),
                                'keyspace_hits': info.get('keyspace_hits', 0),
                                'keyspace_misses': info.get('keyspace_misses', 0),
                                'evicted_keys': info.get('evicted_keys', 0),
                                'expired_keys': info.get('expired_keys', 0),
                            },
                            'persistence': {
                                'rdb_last_save_time': info.get('rdb_last_save_time', 0),
                                'rdb_changes_since_last_save': info.get('rdb_changes_since_last_save', 0),
                                'aof_enabled': info.get('aof_enabled', 0),
                                'aof_rewrite_in_progress': info.get('aof_rewrite_in_progress', 0),
                            }
                        }
                        
                        # Calculate hit rate
                        hits = redis_metrics[cache_name]['stats']['keyspace_hits']
                        misses = redis_metrics[cache_name]['stats']['keyspace_misses']
                        if hits + misses > 0:
                            redis_metrics[cache_name]['stats']['hit_rate'] = (hits / (hits + misses)) * 100
                        else:
                            redis_metrics[cache_name]['stats']['hit_rate'] = 0
                            
                except Exception as e:
                    logger.error(f"Error collecting Redis metrics for {cache_name}: {str(e)}")
                    redis_metrics[cache_name] = {'error': str(e)}
            
            return redis_metrics
            
        except Exception as e:
            logger.error(f"Error collecting Redis metrics: {str(e)}")
            return {}
    
    def collect_application_metrics(self) -> Dict[str, Any]:
        """Collect application-specific metrics"""
        try:
            from django.contrib.auth import get_user_model
            from orders.models import Order
            from products.models import Product
            from payments.models import Payment
            
            User = get_user_model()
            
            # Get basic counts
            total_users = User.objects.count()
            active_users = User.objects.filter(last_login__gte=datetime.now() - timedelta(days=30)).count()
            total_orders = Order.objects.count()
            total_products = Product.objects.count()
            total_payments = Payment.objects.count()
            
            # Recent activity (last 24 hours)
            recent_cutoff = datetime.now() - timedelta(hours=24)
            recent_orders = Order.objects.filter(created_at__gte=recent_cutoff).count()
            recent_users = User.objects.filter(date_joined__gte=recent_cutoff).count()
            recent_payments = Payment.objects.filter(created_at__gte=recent_cutoff).count()
            
            # Order status distribution
            order_statuses = Order.objects.values('status').annotate(count=Count('id'))
            
            # Revenue metrics (last 30 days)
            revenue_cutoff = datetime.now() - timedelta(days=30)
            recent_revenue = Payment.objects.filter(
                created_at__gte=revenue_cutoff,
                status='completed'
            ).aggregate(total=Sum('amount'))['total'] or 0
            
            return {
                'users': {
                    'total': total_users,
                    'active_30_days': active_users,
                    'new_24_hours': recent_users,
                },
                'orders': {
                    'total': total_orders,
                    'new_24_hours': recent_orders,
                    'status_distribution': list(order_statuses),
                },
                'products': {
                    'total': total_products,
                },
                'payments': {
                    'total': total_payments,
                    'new_24_hours': recent_payments,
                    'revenue_30_days': float(recent_revenue),
                },
                'timestamp': datetime.now().isoformat(),
            }
            
        except Exception as e:
            logger.error(f"Error collecting application metrics: {str(e)}")
            return {}
    
    def collect_all_metrics(self) -> Dict[str, Any]:
        """Collect all metrics"""
        return {
            'system': self.collect_system_metrics(),
            'database': self.collect_database_metrics(),
            'redis': self.collect_redis_metrics(),
            'application': self.collect_application_metrics(),
            'collected_at': datetime.now().isoformat(),
        }

class AlertManager:
    """Manage alerts and notifications"""
    
    def __init__(self):
        self.alert_thresholds = {
            'cpu_percent': 85,
            'memory_percent': 85,
            'disk_percent': 85,
            'database_connections': 80,
            'redis_memory_percent': 85,
            'error_rate': 5.0,
            'response_time': 5000,  # milliseconds
        }
        
        self.alert_cache_key = 'active_alerts'
        self.alert_cooldown = 300  # 5 minutes
    
    def check_system_alerts(self, metrics: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Check for system-level alerts"""
        alerts = []
        
        system_metrics = metrics.get('system', {})
        
        # CPU alert
        cpu_percent = system_metrics.get('cpu', {}).get('percent', 0)
        if cpu_percent > self.alert_thresholds['cpu_percent']:
            alerts.append({
                'type': 'system',
                'severity': 'critical' if cpu_percent > 95 else 'warning',
                'metric': 'cpu_percent',
                'value': cpu_percent,
                'threshold': self.alert_thresholds['cpu_percent'],
                'message': f'High CPU usage: {cpu_percent}%',
                'timestamp': datetime.now().isoformat(),
            })
        
        # Memory alert
        memory_percent = system_metrics.get('memory', {}).get('percent', 0)
        if memory_percent > self.alert_thresholds['memory_percent']:
            alerts.append({
                'type': 'system',
                'severity': 'critical' if memory_percent > 95 else 'warning',
                'metric': 'memory_percent',
                'value': memory_percent,
                'threshold': self.alert_thresholds['memory_percent'],
                'message': f'High memory usage: {memory_percent}%',
                'timestamp': datetime.now().isoformat(),
            })
        
        # Disk alert
        disk_percent = system_metrics.get('disk', {}).get('percent', 0)
        if disk_percent > self.alert_thresholds['disk_percent']:
            alerts.append({
                'type': 'system',
                'severity': 'critical' if disk_percent > 95 else 'warning',
                'metric': 'disk_percent',
                'value': disk_percent,
                'threshold': self.alert_thresholds['disk_percent'],
                'message': f'High disk usage: {disk_percent}%',
                'timestamp': datetime.now().isoformat(),
            })
        
        return alerts
    
    def check_database_alerts(self, metrics: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Check for database-level alerts"""
        alerts = []
        
        database_metrics = metrics.get('database', {})
        
        for db_name, db_metrics in database_metrics.items():
            if isinstance(db_metrics, dict) and 'error' not in db_metrics:
                # Connection alert
                connections = db_metrics.get('active_connections', 0)
                max_connections = 100  # This should be configurable
                connection_percent = (connections / max_connections) * 100
                
                if connection_percent > self.alert_thresholds['database_connections']:
                    alerts.append({
                        'type': 'database',
                        'severity': 'critical' if connection_percent > 95 else 'warning',
                        'metric': 'database_connections',
                        'value': connections,
                        'threshold': self.alert_thresholds['database_connections'],
                        'message': f'High database connections for {db_name}: {connections}/{max_connections}',
                        'timestamp': datetime.now().isoformat(),
                    })
        
        return alerts
    
    def check_redis_alerts(self, metrics: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Check for Redis-level alerts"""
        alerts = []
        
        redis_metrics = metrics.get('redis', {})
        
        for cache_name, cache_metrics in redis_metrics.items():
            if isinstance(cache_metrics, dict) and 'error' not in cache_metrics:
                # Memory alert
                memory_percent = cache_metrics.get('memory', {}).get('memory_fragmentation_ratio', 0)
                if memory_percent > 2.0:  # High fragmentation
                    alerts.append({
                        'type': 'redis',
                        'severity': 'warning',
                        'metric': 'redis_memory_fragmentation',
                        'value': memory_percent,
                        'threshold': 2.0,
                        'message': f'High Redis memory fragmentation for {cache_name}: {memory_percent}',
                        'timestamp': datetime.now().isoformat(),
                    })
        
        return alerts
    
    def check_all_alerts(self, metrics: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Check all types of alerts"""
        alerts = []
        alerts.extend(self.check_system_alerts(metrics))
        alerts.extend(self.check_database_alerts(metrics))
        alerts.extend(self.check_redis_alerts(metrics))
        return alerts
    
    def send_alert_notification(self, alert: Dict[str, Any]) -> bool:
        """Send alert notification"""
        try:
            # Check if alert is in cooldown
            alert_key = f"alert:{alert['metric']}:{alert['value']}"
            if cache.get(alert_key):
                return False  # Skip duplicate alerts
            
            # Set cooldown
            cache.set(alert_key, True, self.alert_cooldown)
            
            # Send email notification
            self.send_email_alert(alert)
            
            # Send Slack notification
            self.send_slack_alert(alert)
            
            # Log alert
            logger.warning(f"Alert triggered: {alert}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error sending alert notification: {str(e)}")
            return False
    
    def send_email_alert(self, alert: Dict[str, Any]):
        """Send email alert"""
        subject = f"🚨 {alert['severity'].upper()} Alert: {alert['message']}"
        
        message = f"""
        Alert Details:
        - Type: {alert['type']}
        - Severity: {alert['severity']}
        - Metric: {alert['metric']}
        - Current Value: {alert['value']}
        - Threshold: {alert['threshold']}
        - Timestamp: {alert['timestamp']}
        - Environment: {config('ENVIRONMENT', default='production')}
        
        Message: {alert['message']}
        
        Please investigate and resolve this issue immediately.
        """
        
        send_mail(
            subject=subject,
            message=message,
            from_email=config('DEFAULT_FROM_EMAIL'),
            recipient_list=[config('ADMIN_EMAIL')],
            fail_silently=False,
        )
    
    def send_slack_alert(self, alert: Dict[str, Any]):
        """Send Slack alert"""
        webhook_url = config('SLACK_WEBHOOK_URL', default='')
        if not webhook_url:
            return
        
        color = {
            'critical': 'danger',
            'warning': 'warning',
            'info': 'good'
        }.get(alert['severity'], 'warning')
        
        emoji = {
            'critical': '🚨',
            'warning': '⚠️',
            'info': 'ℹ️'
        }.get(alert['severity'], '⚠️')
        
        payload = {
            'username': 'Pasargad Prints Monitor',
            'icon_emoji': ':warning:',
            'attachments': [{
                'color': color,
                'title': f'{emoji} {alert["severity"].upper()} Alert',
                'fields': [
                    {'title': 'Metric', 'value': alert['metric'], 'short': True},
                    {'title': 'Value', 'value': str(alert['value']), 'short': True},
                    {'title': 'Threshold', 'value': str(alert['threshold']), 'short': True},
                    {'title': 'Type', 'value': alert['type'], 'short': True},
                    {'title': 'Message', 'value': alert['message'], 'short': False},
                ],
                'footer': f'Pasargad Prints {config("ENVIRONMENT", default="production")}',
                'ts': int(datetime.now().timestamp())
            }]
        }
        
        try:
            requests.post(webhook_url, json=payload, timeout=30)
        except Exception as e:
            logger.error(f"Error sending Slack alert: {str(e)}")

# Global instances
metrics_collector = MetricsCollector()
alert_manager = AlertManager()

# Django Views
@api_view(['GET'])
@permission_classes([IsAdminUser])
def system_metrics(request):
    """Get comprehensive system metrics"""
    try:
        metrics = metrics_collector.collect_all_metrics()
        return Response(metrics)
    except Exception as e:
        logger.error(f"Error collecting metrics: {str(e)}")
        return Response({'error': str(e)}, status=500)

@api_view(['GET'])
@permission_classes([IsAdminUser])
def health_check_detailed(request):
    """Detailed health check with all components"""
    try:
        health_data = {
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'checks': {},
            'metrics': {}
        }
        
        # Collect basic metrics
        metrics = metrics_collector.collect_all_metrics()
        health_data['metrics'] = metrics
        
        # Check alerts
        alerts = alert_manager.check_all_alerts(metrics)
        health_data['alerts'] = alerts
        
        # Overall health status
        if any(alert['severity'] == 'critical' for alert in alerts):
            health_data['status'] = 'critical'
        elif any(alert['severity'] == 'warning' for alert in alerts):
            health_data['status'] = 'warning'
        
        return Response(health_data)
        
    except Exception as e:
        logger.error(f"Error in detailed health check: {str(e)}")
        return Response({
            'status': 'error',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }, status=500)

@api_view(['POST'])
@permission_classes([IsAdminUser])
def trigger_alert_check(request):
    """Manually trigger alert check"""
    try:
        metrics = metrics_collector.collect_all_metrics()
        alerts = alert_manager.check_all_alerts(metrics)
        
        # Send notifications for new alerts
        notifications_sent = 0
        for alert in alerts:
            if alert_manager.send_alert_notification(alert):
                notifications_sent += 1
        
        return Response({
            'alerts_found': len(alerts),
            'notifications_sent': notifications_sent,
            'alerts': alerts
        })
        
    except Exception as e:
        logger.error(f"Error triggering alert check: {str(e)}")
        return Response({'error': str(e)}, status=500)

# Scheduled task for monitoring
def run_monitoring_check():
    """Run periodic monitoring check"""
    try:
        logger.info("Starting periodic monitoring check")
        
        # Collect metrics
        metrics = metrics_collector.collect_all_metrics()
        
        # Check for alerts
        alerts = alert_manager.check_all_alerts(metrics)
        
        # Send notifications
        for alert in alerts:
            alert_manager.send_alert_notification(alert)
        
        logger.info(f"Monitoring check completed. Found {len(alerts)} alerts")
        
    except Exception as e:
        logger.error(f"Error in monitoring check: {str(e)}")

# Add to Celery beat schedule
if hasattr(settings, 'CELERY_BEAT_SCHEDULE'):
    settings.CELERY_BEAT_SCHEDULE['monitoring-check'] = {
        'task': 'utils.monitoring_production.run_monitoring_check',
        'schedule': 300.0,  # Every 5 minutes
    }