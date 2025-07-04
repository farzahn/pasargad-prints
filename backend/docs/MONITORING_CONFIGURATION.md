# Production Monitoring Configuration - Pasargad Prints

## Overview

This document outlines the comprehensive monitoring and alerting configuration for Pasargad Prints production environment. The system monitors application performance, infrastructure health, and business metrics.

## Monitoring Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Application   │───▶│   Metrics       │───▶│   Alerting      │
│   Components    │    │   Collection    │    │   System        │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │                        │
                                ▼                        ▼
                       ┌─────────────────┐    ┌─────────────────┐
                       │   Dashboards    │    │  Notifications  │
                       │   (Grafana)     │    │  (Email/Slack)  │
                       └─────────────────┘    └─────────────────┘
```

## Components Monitored

### 1. System Metrics
- **CPU Usage**: Per-core and overall utilization
- **Memory Usage**: RAM, swap, and buffer/cache utilization
- **Disk Usage**: Space utilization and I/O performance
- **Network**: Traffic, errors, and connection statistics
- **Process Metrics**: Application-specific resource usage

### 2. Database Metrics
- **Connection Pool**: Active connections, connection limits
- **Query Performance**: Slow queries, execution times
- **Database Size**: Growth trends and space utilization
- **Transaction Statistics**: Commits, rollbacks, deadlocks
- **Index Usage**: Scan ratios and optimization opportunities

### 3. Redis Metrics
- **Memory Usage**: Used memory, fragmentation ratio
- **Performance**: Operations per second, hit/miss ratios
- **Connections**: Client connections, blocked clients
- **Persistence**: RDB/AOF status and timing
- **Keyspace Statistics**: Key expiration and eviction

### 4. Application Metrics
- **User Activity**: Active users, registration rates
- **Order Processing**: Order volumes, completion rates
- **Payment Processing**: Transaction success rates
- **API Performance**: Response times, error rates
- **Background Tasks**: Celery queue lengths and processing times

### 5. Business Metrics
- **Revenue**: Daily/weekly/monthly revenue trends
- **Conversion Rates**: Visitor to customer conversion
- **Product Performance**: Best-selling products
- **Customer Satisfaction**: Order completion rates
- **Inventory**: Stock levels and reorder alerts

## Alerting Configuration

### Alert Thresholds

```yaml
system:
  cpu_percent: 85
  memory_percent: 85
  disk_percent: 85
  load_average: 2.0

database:
  connection_utilization: 80
  slow_query_threshold: 1000  # milliseconds
  deadlock_threshold: 5       # per hour

redis:
  memory_fragmentation: 2.0
  hit_rate_threshold: 85      # percentage
  blocked_clients: 10

application:
  error_rate: 5.0            # percentage
  response_time: 5000        # milliseconds
  queue_length: 100          # Celery queue

business:
  order_failure_rate: 10     # percentage
  payment_failure_rate: 5    # percentage
  low_stock_threshold: 10    # items
```

### Alert Severity Levels

1. **Critical**: Service-affecting issues requiring immediate attention
2. **Warning**: Performance degradation or potential issues
3. **Info**: Informational alerts for tracking trends

### Notification Channels

- **Email**: Admin notifications for all alerts
- **Slack**: Real-time notifications for critical alerts
- **SMS**: Critical alerts for on-call engineers
- **Dashboard**: Visual alerts on monitoring dashboard

## Monitoring Endpoints

### Health Check Endpoints

```python
# Basic health check
GET /api/health/

# Detailed health check with metrics
GET /api/health/detailed/

# Component-specific health checks
GET /api/health/database/
GET /api/health/redis/
GET /api/health/celery/
```

### Metrics Endpoints

```python
# System metrics
GET /api/monitoring/system/

# Database metrics
GET /api/monitoring/database/

# Redis metrics
GET /api/monitoring/redis/

# Application metrics
GET /api/monitoring/application/

# Business metrics
GET /api/monitoring/business/
```

## Monitoring Setup

### 1. Prometheus Configuration

```yaml
# prometheus.yml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

rule_files:
  - "alert_rules.yml"

scrape_configs:
  - job_name: 'pasargad-prints'
    static_configs:
      - targets: ['localhost:8000']
    metrics_path: '/api/monitoring/prometheus/'
    scrape_interval: 30s

alerting:
  alertmanagers:
    - static_configs:
        - targets:
          - alertmanager:9093
```

### 2. Grafana Dashboard Configuration

```json
{
  "dashboard": {
    "title": "Pasargad Prints - Production Monitoring",
    "panels": [
      {
        "title": "System Overview",
        "type": "stat",
        "targets": [
          {
            "expr": "cpu_usage_percent",
            "legendFormat": "CPU Usage"
          },
          {
            "expr": "memory_usage_percent",
            "legendFormat": "Memory Usage"
          },
          {
            "expr": "disk_usage_percent",
            "legendFormat": "Disk Usage"
          }
        ]
      },
      {
        "title": "Request Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(http_requests_total[5m])",
            "legendFormat": "Requests/sec"
          }
        ]
      },
      {
        "title": "Error Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(http_errors_total[5m])",
            "legendFormat": "Errors/sec"
          }
        ]
      },
      {
        "title": "Database Connections",
        "type": "graph",
        "targets": [
          {
            "expr": "database_connections_active",
            "legendFormat": "Active Connections"
          }
        ]
      }
    ]
  }
}
```

### 3. Alert Rules

```yaml
# alert_rules.yml
groups:
  - name: system
    rules:
      - alert: HighCpuUsage
        expr: cpu_usage_percent > 85
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High CPU usage detected"
          description: "CPU usage is above 85% for more than 5 minutes"

      - alert: HighMemoryUsage
        expr: memory_usage_percent > 85
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High memory usage detected"
          description: "Memory usage is above 85% for more than 5 minutes"

      - alert: HighDiskUsage
        expr: disk_usage_percent > 85
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "High disk usage detected"
          description: "Disk usage is above 85% for more than 5 minutes"

  - name: application
    rules:
      - alert: HighErrorRate
        expr: error_rate > 5
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "High error rate detected"
          description: "Error rate is above 5% for more than 2 minutes"

      - alert: SlowResponseTime
        expr: response_time_p95 > 5000
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Slow response time detected"
          description: "95th percentile response time is above 5 seconds"

  - name: database
    rules:
      - alert: HighDatabaseConnections
        expr: database_connections_percent > 80
        for: 2m
        labels:
          severity: warning
        annotations:
          summary: "High database connection usage"
          description: "Database connection usage is above 80%"

      - alert: SlowQueries
        expr: slow_queries_per_minute > 10
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High number of slow queries"
          description: "More than 10 slow queries per minute"
```

## Log Monitoring

### 1. Structured Logging

```python
# Example structured log entry
{
  "timestamp": "2024-01-01T12:00:00Z",
  "level": "ERROR",
  "logger": "payments",
  "message": "Payment processing failed",
  "user_id": 12345,
  "order_id": "ORDER-12345",
  "payment_method": "stripe",
  "error_code": "card_declined",
  "request_id": "req-abc123",
  "environment": "production"
}
```

### 2. Log Aggregation

- **ELK Stack**: Elasticsearch, Logstash, Kibana
- **Fluentd**: Log collection and forwarding
- **Retention**: 90 days for application logs, 30 days for access logs

### 3. Log Monitoring Rules

```yaml
# Log-based alerts
- name: error_monitoring
  rules:
    - alert: HighErrorRate
      expr: increase(log_errors_total[5m]) > 50
      labels:
        severity: critical
      annotations:
        summary: "High error rate in logs"

    - alert: PaymentFailures
      expr: increase(payment_errors_total[5m]) > 10
      labels:
        severity: warning
      annotations:
        summary: "Multiple payment failures detected"

    - alert: DatabaseErrors
      expr: increase(database_errors_total[5m]) > 5
      labels:
        severity: critical
      annotations:
        summary: "Database errors detected"
```

## Performance Monitoring

### 1. Application Performance Monitoring (APM)

- **New Relic**: Application performance and error tracking
- **Datadog**: Infrastructure and application monitoring
- **Sentry**: Error tracking and performance monitoring

### 2. Synthetic Monitoring

```python
# Synthetic monitoring checks
health_checks = [
    {
        "name": "homepage_load",
        "url": "https://pasargadprints.com",
        "expected_status": 200,
        "timeout": 5000,
        "interval": 60  # seconds
    },
    {
        "name": "api_health",
        "url": "https://api.pasargadprints.com/health/",
        "expected_status": 200,
        "timeout": 3000,
        "interval": 30
    },
    {
        "name": "user_login",
        "url": "https://pasargadprints.com/login",
        "expected_status": 200,
        "timeout": 10000,
        "interval": 300
    }
]
```

### 3. Real User Monitoring (RUM)

- **Google Analytics**: User behavior and performance
- **Mixpanel**: User engagement and conversion tracking
- **Hotjar**: User session recordings and heatmaps

## Security Monitoring

### 1. Security Events

- **Failed Login Attempts**: Monitor for brute force attacks
- **Privilege Escalation**: Track admin access and permissions
- **Suspicious Activity**: Unusual user behavior patterns
- **File System Changes**: Monitor critical file modifications

### 2. Intrusion Detection

```python
# Security monitoring rules
security_rules = [
    {
        "name": "multiple_failed_logins",
        "condition": "failed_login_attempts > 5 in 5 minutes",
        "action": "alert_and_block_ip"
    },
    {
        "name": "admin_access_after_hours",
        "condition": "admin_login outside business_hours",
        "action": "alert_security_team"
    },
    {
        "name": "unusual_api_usage",
        "condition": "api_requests > 1000 per minute from single IP",
        "action": "rate_limit_and_alert"
    }
]
```

## Maintenance Windows

### 1. Scheduled Maintenance

- **Weekly**: Database maintenance and optimization
- **Monthly**: Security patches and system updates
- **Quarterly**: Major version upgrades and testing

### 2. Maintenance Procedures

```bash
# Pre-maintenance checklist
1. Create database backup
2. Scale down non-essential services
3. Enable maintenance mode
4. Notify stakeholders
5. Document maintenance window

# Post-maintenance checklist
1. Verify all services are running
2. Run smoke tests
3. Check monitoring dashboards
4. Disable maintenance mode
5. Document any issues
```

## Monitoring Best Practices

### 1. Alerting Guidelines

- **Actionable**: Every alert should require action
- **Meaningful**: Avoid alert fatigue with false positives
- **Timely**: Alerts should fire before users are affected
- **Contextual**: Provide enough information to troubleshoot

### 2. Dashboard Design

- **Overview First**: Start with high-level metrics
- **Drill Down**: Allow investigation of specific issues
- **Consistent**: Use standard colors and layouts
- **Responsive**: Design for different screen sizes

### 3. Monitoring Responsibilities

- **DevOps Team**: Infrastructure and system monitoring
- **Development Team**: Application performance monitoring
- **Product Team**: Business metrics and user experience
- **Security Team**: Security monitoring and incident response

## Troubleshooting Guide

### Common Issues

1. **High CPU Usage**
   - Check for runaway processes
   - Review recent deployments
   - Analyze query performance

2. **Memory Leaks**
   - Monitor memory usage trends
   - Check for memory-intensive operations
   - Review application logs

3. **Database Performance**
   - Analyze slow query log
   - Check connection pool usage
   - Review index usage

4. **Network Issues**
   - Monitor network latency
   - Check DNS resolution
   - Verify firewall rules

### Escalation Procedures

1. **Level 1**: Automated response (restart services)
2. **Level 2**: On-call engineer notification
3. **Level 3**: Senior engineer escalation
4. **Level 4**: Management and customer notification

## Contact Information

- **Primary**: DevOps Team (devops@pasargadprints.com)
- **Secondary**: Development Team (dev@pasargadprints.com)
- **Emergency**: On-call Engineer (oncall@pasargadprints.com)

## Documentation Updates

- **Version**: 1.0
- **Last Updated**: 2024-01-01
- **Next Review**: 2024-04-01
- **Owner**: DevOps Team