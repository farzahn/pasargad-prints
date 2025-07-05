"""
Production settings for Pasargad Prints

This file contains production-specific Django settings.
It imports from the base settings.py and overrides certain values for production.
"""

import os
import warnings
from pathlib import Path

# Use custom config loader that points to root .env file
from .config import config

# Optional Sentry integration
try:
    import sentry_sdk
    from sentry_sdk.integrations.django import DjangoIntegration
    from sentry_sdk.integrations.celery import CeleryIntegration
    from sentry_sdk.integrations.redis import RedisIntegration
    from sentry_sdk.integrations.logging import LoggingIntegration
    SENTRY_AVAILABLE = True
except ImportError:
    SENTRY_AVAILABLE = False

# Import base settings
from .settings import *

# Production environment validation
REQUIRED_PRODUCTION_VARS = [
    'SECRET_KEY',
    'DB_NAME',
    'DB_USER', 
    'DB_PASSWORD',
    'DB_HOST',
    'ALLOWED_HOSTS',
    'EMAIL_HOST_USER',
    'EMAIL_HOST_PASSWORD',
    'STRIPE_SECRET_KEY',
    'STRIPE_WEBHOOK_SECRET',
    'REDIS_URL',
    'CELERY_BROKER_URL',
]

# Validate all required production variables
missing_vars = []
for var in REQUIRED_PRODUCTION_VARS:
    if not config(var, default=None):
        missing_vars.append(var)

if missing_vars:
    raise ValueError(
        f"Missing required production environment variables: {', '.join(missing_vars)}. "
        "These must be set for production deployment."
    )

# =============================================================================
# SECURITY SETTINGS
# =============================================================================

# Force DEBUG to False in production
DEBUG = False

# Security headers
SECURE_SSL_REDIRECT = config('SECURE_SSL_REDIRECT', default=True, cast=bool)
SECURE_HSTS_SECONDS = config('SECURE_HSTS_SECONDS', default=31536000, cast=int)
SECURE_HSTS_INCLUDE_SUBDOMAINS = config('SECURE_HSTS_INCLUDE_SUBDOMAINS', default=True, cast=bool)
SECURE_HSTS_PRELOAD = config('SECURE_HSTS_PRELOAD', default=True, cast=bool)
SECURE_CONTENT_TYPE_NOSNIFF = config('SECURE_CONTENT_TYPE_NOSNIFF', default=True, cast=bool)
SECURE_BROWSER_XSS_FILTER = config('SECURE_BROWSER_XSS_FILTER', default=True, cast=bool)
SECURE_REFERRER_POLICY = config('SECURE_REFERRER_POLICY', default='strict-origin-when-cross-origin')

# Cookie security
SESSION_COOKIE_SECURE = config('SESSION_COOKIE_SECURE', default=True, cast=bool)
CSRF_COOKIE_SECURE = config('CSRF_COOKIE_SECURE', default=True, cast=bool)
CSRF_COOKIE_HTTPONLY = config('CSRF_COOKIE_HTTPONLY', default=True, cast=bool)
SESSION_COOKIE_HTTPONLY = config('SESSION_COOKIE_HTTPONLY', default=True, cast=bool)

# Additional security settings
CSRF_TRUSTED_ORIGINS = [
    f"https://{host}" for host in config('ALLOWED_HOSTS', default='').split(',')
]

# =============================================================================
# DATABASE SETTINGS
# =============================================================================

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': config('DB_NAME'),
        'USER': config('DB_USER'),
        'PASSWORD': config('DB_PASSWORD'),
        'HOST': config('DB_HOST'),
        'PORT': config('DB_PORT', default='5432'),
        'OPTIONS': {
            'connect_timeout': config('DB_CONNECT_TIMEOUT', default=10, cast=int),
        },
        'CONN_MAX_AGE': config('DB_CONN_MAX_AGE', default=600, cast=int),
        'CONN_HEALTH_CHECKS': config('DB_CONN_HEALTH_CHECKS', default=True, cast=bool),
        'ATOMIC_REQUESTS': config('DB_ATOMIC_REQUESTS', default=True, cast=bool),
        'AUTOCOMMIT': True,
        'TIME_ZONE': None,
        'TEST': {
            'NAME': config('DB_TEST_NAME', default=None),
            'CHARSET': None,
            'COLLATION': None,
            'CREATE_DB': True,
            'USER': config('DB_TEST_USER', default=None),
            'PASSWORD': config('DB_TEST_PASSWORD', default=None),
            'HOST': config('DB_TEST_HOST', default=None),
            'PORT': config('DB_TEST_PORT', default=None),
            'TBLSPACE': None,
            'TBLSPACE_TMP': None,
            'ENGINE': None,
        },
    }
}

# Database query optimization
DATABASE_QUERY_TIMEOUT = config('DATABASE_QUERY_TIMEOUT', default=30, cast=int)
DATABASE_POOL_SIZE = config('DB_POOL_SIZE', default=20, cast=int)
DATABASE_MAX_OVERFLOW = config('DB_MAX_OVERFLOW', default=10, cast=int)

# Database monitoring and debugging in production
if config('DB_ENABLE_QUERY_LOGGING', default=False, cast=bool):
    DATABASES['default']['OPTIONS']['log_statement'] = 'all'
    DATABASES['default']['OPTIONS']['log_min_duration_statement'] = 100  # Log queries > 100ms

# =============================================================================
# CACHE SETTINGS
# =============================================================================

# Redis connection settings
REDIS_CACHE_URL = config('REDIS_CACHE_URL', default=config('REDIS_URL'))
REDIS_SESSION_URL = config('REDIS_SESSION_URL', default=REDIS_CACHE_URL)
REDIS_API_URL = config('REDIS_API_URL', default=REDIS_CACHE_URL)

# Connection pool settings
REDIS_POOL_SIZE = config('REDIS_POOL_SIZE', default=30, cast=int)
REDIS_CONNECTION_TIMEOUT = config('REDIS_CONNECTION_TIMEOUT', default=5, cast=int)
REDIS_SOCKET_TIMEOUT = config('REDIS_SOCKET_TIMEOUT', default=5, cast=int)

CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': REDIS_CACHE_URL,
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'PARSER_CLASS': 'redis.connection.HiredisParser',
            'CONNECTION_POOL_CLASS': 'redis.BlockingConnectionPool',
            'CONNECTION_POOL_CLASS_KWARGS': {
                'max_connections': REDIS_POOL_SIZE,
                'retry_on_timeout': True,
                'retry_on_error': [ConnectionError, TimeoutError],
                'socket_connect_timeout': REDIS_CONNECTION_TIMEOUT,
                'socket_timeout': REDIS_SOCKET_TIMEOUT,
                'socket_keepalive': True,
                'socket_keepalive_options': {},
                'health_check_interval': 30,
            },
            'MAX_CONNECTIONS': REDIS_POOL_SIZE,
            'KEY_PREFIX': 'pasargad_prod',
            'VERSION': 1,
            'TIMEOUT': config('CACHE_TIMEOUT', default=300, cast=int),
            'COMPRESS_MIN_LEN': 10,
            'COMPRESS_LEVEL': 6,
            'IGNORE_EXCEPTIONS': config('REDIS_IGNORE_EXCEPTIONS', default=True, cast=bool),
            'SERIALIZER': 'django_redis.serializers.json.JSONSerializer',
            'COMPRESSOR': 'django_redis.compressors.zlib.ZlibCompressor',
        },
        'TIMEOUT': config('CACHE_TIMEOUT', default=300, cast=int),
        'KEY_PREFIX': 'pasargad_prod',
        'VERSION': 1,
    },
    'session': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': REDIS_SESSION_URL,
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'PARSER_CLASS': 'redis.connection.HiredisParser',
            'CONNECTION_POOL_CLASS': 'redis.BlockingConnectionPool',
            'CONNECTION_POOL_CLASS_KWARGS': {
                'max_connections': config('REDIS_SESSION_POOL_SIZE', default=20, cast=int),
                'retry_on_timeout': True,
                'socket_connect_timeout': REDIS_CONNECTION_TIMEOUT,
                'socket_timeout': REDIS_SOCKET_TIMEOUT,
                'socket_keepalive': True,
                'health_check_interval': 30,
            },
            'KEY_PREFIX': 'session_prod',
            'TIMEOUT': config('SESSION_CACHE_TIMEOUT', default=3600, cast=int),
            'IGNORE_EXCEPTIONS': True,
        },
        'TIMEOUT': config('SESSION_CACHE_TIMEOUT', default=3600, cast=int),
    },
    'api': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': REDIS_API_URL,
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'PARSER_CLASS': 'redis.connection.HiredisParser',
            'CONNECTION_POOL_CLASS': 'redis.BlockingConnectionPool',
            'CONNECTION_POOL_CLASS_KWARGS': {
                'max_connections': config('REDIS_API_POOL_SIZE', default=15, cast=int),
                'retry_on_timeout': True,
                'socket_connect_timeout': REDIS_CONNECTION_TIMEOUT,
                'socket_timeout': REDIS_SOCKET_TIMEOUT,
                'socket_keepalive': True,
                'health_check_interval': 30,
            },
            'KEY_PREFIX': 'api_prod',
            'TIMEOUT': config('API_CACHE_TIMEOUT', default=60, cast=int),
            'IGNORE_EXCEPTIONS': True,
            'SERIALIZER': 'django_redis.serializers.json.JSONSerializer',
            'COMPRESSOR': 'django_redis.compressors.zlib.ZlibCompressor',
        },
        'TIMEOUT': config('API_CACHE_TIMEOUT', default=60, cast=int),
    }
}

# Use Redis for sessions
SESSION_ENGINE = 'django.contrib.sessions.backends.db'
SESSION_CACHE_ALIAS = 'session'
SESSION_COOKIE_AGE = config('SESSION_COOKIE_AGE', default=86400, cast=int)  # 24 hours
SESSION_SAVE_EVERY_REQUEST = False
SESSION_EXPIRE_AT_BROWSER_CLOSE = False

# =============================================================================
# CELERY SETTINGS
# =============================================================================

CELERY_BROKER_URL = config('CELERY_BROKER_URL')
CELERY_RESULT_BACKEND = config('CELERY_RESULT_BACKEND', default=CELERY_BROKER_URL)
CELERY_TASK_ALWAYS_EAGER = config('CELERY_TASK_ALWAYS_EAGER', default=False, cast=bool)
CELERY_TASK_EAGER_PROPAGATES = config('CELERY_TASK_EAGER_PROPAGATES', default=True, cast=bool)

# Production-specific Celery settings for reliability
CELERY_WORKER_PREFETCH_MULTIPLIER = config('CELERY_PREFETCH_MULTIPLIER', default=1, cast=int)
CELERY_WORKER_MAX_TASKS_PER_CHILD = config('CELERY_MAX_TASKS_PER_CHILD', default=1000, cast=int)
CELERY_WORKER_MAX_MEMORY_PER_CHILD = config('CELERY_MAX_MEMORY_PER_CHILD', default=200000, cast=int)  # 200MB
CELERY_TASK_REJECT_ON_WORKER_LOST = True
CELERY_TASK_ACKS_LATE = True
CELERY_TASK_REJECT_ON_WORKER_LOST = True
CELERY_WORKER_DISABLE_RATE_LIMITS = False
CELERY_TASK_COMPRESSION = 'gzip'
CELERY_RESULT_COMPRESSION = 'gzip'

# Task execution settings
CELERY_TASK_TIME_LIMIT = config('CELERY_TASK_TIME_LIMIT', default=3600, cast=int)  # 1 hour
CELERY_TASK_SOFT_TIME_LIMIT = config('CELERY_TASK_SOFT_TIME_LIMIT', default=3300, cast=int)  # 55 minutes
CELERY_TASK_MAX_RETRIES = config('CELERY_TASK_MAX_RETRIES', default=3, cast=int)
CELERY_TASK_DEFAULT_RETRY_DELAY = config('CELERY_TASK_DEFAULT_RETRY_DELAY', default=60, cast=int)

# Result backend settings
CELERY_RESULT_EXPIRES = config('CELERY_RESULT_EXPIRES', default=3600, cast=int)  # 1 hour
CELERY_RESULT_PERSISTENT = config('CELERY_RESULT_PERSISTENT', default=True, cast=bool)

# Broker settings
CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP = True
CELERY_BROKER_CONNECTION_RETRY = True
CELERY_BROKER_CONNECTION_MAX_RETRIES = config('CELERY_BROKER_MAX_RETRIES', default=10, cast=int)
CELERY_BROKER_HEARTBEAT = config('CELERY_BROKER_HEARTBEAT', default=30, cast=int)
CELERY_BROKER_POOL_LIMIT = config('CELERY_BROKER_POOL_LIMIT', default=10, cast=int)

# Worker settings
CELERY_WORKER_CONCURRENCY = config('CELERY_WORKER_CONCURRENCY', default=4, cast=int)
CELERY_WORKER_POOL = config('CELERY_WORKER_POOL', default='prefork')
CELERY_WORKER_POOL_RESTARTS = True

# Security settings
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE

# Monitoring and logging
CELERY_SEND_EVENTS = config('CELERY_SEND_EVENTS', default=True, cast=bool)
CELERY_SEND_TASK_EVENTS = config('CELERY_SEND_TASK_EVENTS', default=True, cast=bool)
CELERY_TRACK_STARTED = True
CELERY_TASK_TRACK_STARTED = True
CELERY_WORKER_SEND_TASK_EVENTS = True

# Error handling
CELERY_ANNOTATIONS = {
    '*': {
        'rate_limit': config('CELERY_DEFAULT_RATE_LIMIT', default='100/s'),
        'time_limit': CELERY_TASK_TIME_LIMIT,
        'soft_time_limit': CELERY_TASK_SOFT_TIME_LIMIT,
    },
    'utils.email.*': {
        'rate_limit': config('CELERY_EMAIL_RATE_LIMIT', default='10/m'),
        'max_retries': 5,
        'default_retry_delay': 300,  # 5 minutes
    },
    'orders.tasks.*': {
        'rate_limit': config('CELERY_ORDERS_RATE_LIMIT', default='50/s'),
        'max_retries': 3,
    },
    'payments.tasks.*': {
        'rate_limit': config('CELERY_PAYMENTS_RATE_LIMIT', default='20/s'),
        'max_retries': 5,
        'default_retry_delay': 60,  # 1 minute
    },
}

# =============================================================================
# LOGGING SETTINGS
# =============================================================================

LOG_LEVEL = config('LOG_LEVEL', default='INFO')

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'json': {
            '()': 'pythonjsonlogger.jsonlogger.JsonFormatter',
            'format': '%(asctime)s %(name)s %(levelname)s %(message)s %(pathname)s %(lineno)d %(funcName)s %(process)d %(thread)d'
        },
        'verbose': {
            'format': '[{levelname}] {asctime} {name} {module} {process:d} {thread:d} {message}',
            'style': '{',
            'datefmt': '%Y-%m-%d %H:%M:%S'
        },
        'simple': {
            'format': '[{levelname}] {asctime} {name} {message}',
            'style': '{',
            'datefmt': '%Y-%m-%d %H:%M:%S'
        },
        'security': {
            'format': '[SECURITY] {asctime} {levelname} {name} {message} | IP: {request.client_ip} | User: {request.user} | Path: {request.path}',
            'style': '{',
            'datefmt': '%Y-%m-%d %H:%M:%S'
        },
    },
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse',
        },
        'require_debug_true': {
            '()': 'django.utils.log.RequireDebugTrue',
        },
        'skip_unreadable_posts': {
            '()': 'django.utils.log.CallbackFilter',
            'callback': lambda record: 'Invalid HTTP_HOST header' not in record.getMessage(),
        },
    },
    'handlers': {
        'console': {
            'level': LOG_LEVEL,
            'class': 'logging.StreamHandler',
            'formatter': 'json' if config('ENABLE_JSON_LOGGING', default=True, cast=bool) else 'simple',
            'filters': ['skip_unreadable_posts'],
        },
        'file': {
            'level': LOG_LEVEL,
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(BASE_DIR, 'logs', 'pasargad_prints.log'),
            'maxBytes': 1024 * 1024 * config('LOG_FILE_SIZE_MB', default=50, cast=int),
            'backupCount': config('LOG_BACKUP_COUNT', default=20, cast=int),
            'formatter': 'json' if config('ENABLE_JSON_LOGGING', default=True, cast=bool) else 'verbose',
            'filters': ['skip_unreadable_posts'],
        },
        'error_file': {
            'level': 'ERROR',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(BASE_DIR, 'logs', 'errors.log'),
            'maxBytes': 1024 * 1024 * config('LOG_FILE_SIZE_MB', default=50, cast=int),
            'backupCount': config('LOG_BACKUP_COUNT', default=20, cast=int),
            'formatter': 'json' if config('ENABLE_JSON_LOGGING', default=True, cast=bool) else 'verbose',
        },
        'security_file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(BASE_DIR, 'logs', 'security.log'),
            'maxBytes': 1024 * 1024 * config('LOG_FILE_SIZE_MB', default=50, cast=int),
            'backupCount': config('LOG_BACKUP_COUNT', default=20, cast=int),
            'formatter': 'json' if config('ENABLE_JSON_LOGGING', default=True, cast=bool) else 'security',
        },
        'performance_file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(BASE_DIR, 'logs', 'performance.log'),
            'maxBytes': 1024 * 1024 * config('LOG_FILE_SIZE_MB', default=50, cast=int),
            'backupCount': config('LOG_BACKUP_COUNT', default=20, cast=int),
            'formatter': 'json' if config('ENABLE_JSON_LOGGING', default=True, cast=bool) else 'verbose',
        },
        'celery_file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(BASE_DIR, 'logs', 'celery.log'),
            'maxBytes': 1024 * 1024 * config('LOG_FILE_SIZE_MB', default=50, cast=int),
            'backupCount': config('LOG_BACKUP_COUNT', default=20, cast=int),
            'formatter': 'json' if config('ENABLE_JSON_LOGGING', default=True, cast=bool) else 'verbose',
        },
        'mail_admins': {
            'level': 'ERROR',
            'filters': ['require_debug_false'],
            'class': 'django.utils.log.AdminEmailHandler',
            'include_html': True,
        },
        'syslog': {
            'level': 'INFO',
            'class': 'logging.handlers.SysLogHandler',
            'formatter': 'verbose',
            'address': config('SYSLOG_ADDRESS', default='/dev/log'),
            'facility': 'local0',
        } if config('ENABLE_SYSLOG', default=False, cast=bool) else None,
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': LOG_LEVEL,
            'propagate': True,
        },
        'django.request': {
            'handlers': ['error_file', 'mail_admins'] + (['syslog'] if config('ENABLE_SYSLOG', default=False, cast=bool) else []),
            'level': 'ERROR',
            'propagate': False,
        },
        'django.security': {
            'handlers': ['security_file'] + (['syslog'] if config('ENABLE_SYSLOG', default=False, cast=bool) else []),
            'level': 'INFO',
            'propagate': False,
        },
        'django.db.backends': {
            'handlers': ['file'],
            'level': 'WARNING' if config('DB_ENABLE_QUERY_LOGGING', default=False, cast=bool) else 'ERROR',
            'propagate': False,
        },
        'payments': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
        'orders': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
        'cart': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
        'users': {
            'handlers': ['console', 'file', 'security_file'],
            'level': 'INFO',
            'propagate': False,
        },
        'security': {
            'handlers': ['security_file'] + (['syslog'] if config('ENABLE_SYSLOG', default=False, cast=bool) else []),
            'level': 'INFO',
            'propagate': False,
        },
        'performance': {
            'handlers': ['performance_file'],
            'level': 'INFO',
            'propagate': False,
        },
        'celery': {
            'handlers': ['console', 'celery_file'],
            'level': 'INFO',
            'propagate': False,
        },
        'celery.worker': {
            'handlers': ['celery_file'],
            'level': 'INFO',
            'propagate': False,
        },
        'celery.task': {
            'handlers': ['celery_file'],
            'level': 'INFO',
            'propagate': False,
        },
        'utils.email': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
        'utils.goshippo_service': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
        'stripe': {
            'handlers': ['console', 'file'],
            'level': 'WARNING',
            'propagate': False,
        },
        'requests': {
            'handlers': ['file'],
            'level': 'WARNING',
            'propagate': False,
        },
    },
    'root': {
        'handlers': ['console', 'file'],
        'level': LOG_LEVEL,
    },
}

# Remove None handlers
if LOGGING['handlers'].get('syslog') is None:
    del LOGGING['handlers']['syslog']

# =============================================================================
# SENTRY CONFIGURATION
# =============================================================================

SENTRY_DSN = config('SENTRY_DSN', default='')
if SENTRY_DSN and SENTRY_AVAILABLE:
    # Enhanced Sentry configuration for production
    sentry_logging = LoggingIntegration(
        level=logging.INFO,  # Capture info and above as breadcrumbs
        event_level=logging.ERROR  # Send errors and above as events
    )
    
    def before_send(event, hint):
        """Filter out non-critical events and add additional context"""
        # Skip certain types of errors
        if 'exc_info' in hint:
            exc_type, exc_value, tb = hint['exc_info']
            if isinstance(exc_value, (KeyboardInterrupt, SystemExit)):
                return None
            
        # Add custom tags and context
        event.setdefault('tags', {}).update({
            'server_name': config('SERVER_NAME', default='unknown'),
            'deployment_type': 'production',
        })
        
        # Filter sensitive data
        if event.get('request', {}).get('data'):
            sensitive_fields = ['password', 'token', 'secret', 'key']
            for field in sensitive_fields:
                if field in str(event['request']['data']).lower():
                    event['request']['data'] = '[Filtered]'
                    break
        
        return event
    
    sentry_sdk.init(
        dsn=SENTRY_DSN,
        environment=config('SENTRY_ENVIRONMENT', default='production'),
        release=config('SENTRY_RELEASE', default='1.0.0'),
        server_name=config('SERVER_NAME', default='pasargad-prints-prod'),
        integrations=[
            DjangoIntegration(
                transaction_style='url',
                middleware_spans=config('SENTRY_MIDDLEWARE_SPANS', default=True, cast=bool),
                cache_spans=config('SENTRY_CACHE_SPANS', default=True, cast=bool),
            ),
            CeleryIntegration(
                monitor_beat_tasks=True,
                propagate_traces=True,
            ),
            RedisIntegration(),
            sentry_logging,
        ],
        traces_sample_rate=config('SENTRY_TRACES_SAMPLE_RATE', default=0.05, cast=float),
        profiles_sample_rate=config('SENTRY_PROFILES_SAMPLE_RATE', default=0.05, cast=float),
        send_default_pii=config('SENTRY_SEND_PII', default=False, cast=bool),
        attach_stacktrace=True,
        max_breadcrumbs=config('SENTRY_MAX_BREADCRUMBS', default=50, cast=int),
        before_send=before_send,
        # Performance monitoring
        enable_tracing=config('SENTRY_ENABLE_TRACING', default=True, cast=bool),
        # Error monitoring
        max_request_body_size='always',
        with_locals=config('SENTRY_WITH_LOCALS', default=False, cast=bool),
        # Additional options
        shutdown_timeout=2,
        in_app_include=['pasargad_prints', 'orders', 'products', 'payments', 'cart', 'users'],
        in_app_exclude=['django', 'celery', 'redis', 'stripe'],
    )
    
    # Set additional context
    sentry_sdk.set_context("app", {
        "name": "Pasargad Prints",
        "version": config('APP_VERSION', default='1.0.0'),
        "build": config('BUILD_NUMBER', default='unknown'),
    })
    
elif SENTRY_DSN and not SENTRY_AVAILABLE:
    warnings.warn(
        "Sentry DSN configured but sentry-sdk not installed. "
        "Install with: pip install sentry-sdk",
        UserWarning
    )

# =============================================================================
# PERFORMANCE SETTINGS
# =============================================================================

# Database connection pooling is handled by Django, not PostgreSQL
# MAX_CONNS is not a valid PostgreSQL option

# Template caching
TEMPLATES[0]['APP_DIRS'] = False
TEMPLATES[0]['OPTIONS']['loaders'] = [
    ('django.template.loaders.cached.Loader', [
        'django.template.loaders.filesystem.Loader',
        'django.template.loaders.app_directories.Loader',
    ]),
]

# Static files optimization
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
WHITENOISE_USE_FINDERS = True
WHITENOISE_AUTOREFRESH = False
WHITENOISE_MAX_AGE = 31536000  # 1 year

# Middleware optimization
MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'csp.middleware.CSPMiddleware',  # Add django-csp middleware
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'allauth.account.middleware.AccountMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'utils.middleware.RequestLoggingMiddleware',
    'utils.middleware.CacheMiddleware',
    # 'utils.security_middleware.SecurityMiddleware',  # Disabled to avoid conflicts
]

# =============================================================================
# RATE LIMITING
# =============================================================================

REST_FRAMEWORK['DEFAULT_THROTTLE_RATES'] = {
    'anon': config('RATE_LIMIT_ANON', default='100/hour'),
    'user': config('RATE_LIMIT_USER', default='1000/hour'),
    'burst': config('RATE_LIMIT_BURST', default='20/minute'),
    'sustained': config('RATE_LIMIT_SUSTAINED', default='1000/day'),
    'login': config('RATE_LIMIT_LOGIN', default='5/minute'),
    'register': config('RATE_LIMIT_REGISTER', default='3/minute'),
    'password_reset': config('RATE_LIMIT_PASSWORD_RESET', default='3/hour'),
}

# =============================================================================
# SECURITY SETTINGS ENHANCEMENT
# =============================================================================

# Enhanced security headers
SECURE_REFERRER_POLICY = 'strict-origin-when-cross-origin'
SECURE_CROSS_ORIGIN_OPENER_POLICY = 'same-origin'
SECURE_PERMISSIONS_POLICY = {
    'accelerometer': '()',
    'camera': '()',
    'geolocation': '()',
    'gyroscope': '()',
    'magnetometer': '()',
    'microphone': '()',
    'payment': '(self)',
    'usb': '()',
}

# Content Security Policy - Re-enabled with django-csp
CSP_DEFAULT_SRC = ("'self'",)
CSP_SCRIPT_SRC = ("'self'", "'unsafe-inline'", "'unsafe-eval'", "https://js.stripe.com", "https://www.google-analytics.com", "https://www.googletagmanager.com", "https://region1.google-analytics.com", "https://script.hotjar.com")
CSP_STYLE_SRC = ("'self'", "'unsafe-inline'", "https://fonts.googleapis.com")
CSP_IMG_SRC = ("'self'", "data:", "https:")
CSP_FONT_SRC = ("'self'", "https://fonts.gstatic.com")
CSP_CONNECT_SRC = ("'self'", "https://api.stripe.com", "https://www.google-analytics.com", "https://analytics.google.com", "https://region1.google-analytics.com", "https://region1.analytics.google.com", "https://www.googletagmanager.com", "https://api.goshippo.com", "https://static.hotjar.com", "https://script.hotjar.com", "https://vars.hotjar.com", "https://connect.facebook.net", "https://snap.licdn.com")
CSP_FRAME_SRC = ("https://js.stripe.com", "https://hooks.stripe.com")
CSP_OBJECT_SRC = ("'none'",)
CSP_BASE_URI = ("'self'",)
CSP_FORM_ACTION = ("'self'",)
CSP_FRAME_ANCESTORS = ("'none'",)
CSP_UPGRADE_INSECURE_REQUESTS = True

# Security middleware settings
SECURITY_BLACKLISTED_NETWORKS = config('SECURITY_BLACKLISTED_NETWORKS', default='', cast=lambda v: v.split(',') if v else [])
SECURITY_ALERT_EMAIL = config('SECURITY_ALERT_EMAIL', default=config('ADMIN_EMAIL', default='admin@pasargadprints.com'))

# =============================================================================
# API OPTIMIZATION
# =============================================================================

# DRF optimizations
REST_FRAMEWORK.update({
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.LimitOffsetPagination',
    'PAGE_SIZE': config('API_PAGE_SIZE', default=20, cast=int),
    'MAX_PAGE_SIZE': config('API_MAX_PAGE_SIZE', default=100, cast=int),
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
    'SEARCH_PARAM': 'q',
    'ORDERING_PARAM': 'ordering',
    'DEFAULT_VERSIONING_CLASS': 'rest_framework.versioning.NamespaceVersioning',
})

# =============================================================================
# SERVICE INTEGRATIONS
# =============================================================================

# Stripe production settings
STRIPE_LIVE_MODE = config('STRIPE_LIVE_MODE', default=True, cast=bool)
STRIPE_TEST_SECRET_KEY = config('STRIPE_TEST_SECRET_KEY', default='')
STRIPE_TEST_PUBLISHABLE_KEY = config('STRIPE_TEST_PUBLISHABLE_KEY', default='')

# Use live keys if in live mode
if STRIPE_LIVE_MODE:
    STRIPE_SECRET_KEY = config('STRIPE_SECRET_KEY')
    STRIPE_PUBLISHABLE_KEY = config('STRIPE_PUBLISHABLE_KEY')
else:
    STRIPE_SECRET_KEY = STRIPE_TEST_SECRET_KEY
    STRIPE_PUBLISHABLE_KEY = STRIPE_TEST_PUBLISHABLE_KEY

# Goshippo production settings
GOSHIPPO_LIVE_MODE = config('GOSHIPPO_LIVE_MODE', default=True, cast=bool)
GOSHIPPO_TEST_API_KEY = config('GOSHIPPO_TEST_API_KEY', default='')

if GOSHIPPO_LIVE_MODE:
    GOSHIPPO_API_KEY = config('GOSHIPPO_API_KEY')
else:
    GOSHIPPO_API_KEY = GOSHIPPO_TEST_API_KEY

# Email production settings
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_TIMEOUT = config('EMAIL_TIMEOUT', default=30, cast=int)
EMAIL_USE_LOCALTIME = True
EMAIL_MAX_RETRIES = config('EMAIL_MAX_RETRIES', default=3, cast=int)

# =============================================================================
# MONITORING AND HEALTH CHECKS
# =============================================================================

HEALTH_CHECK_SETTINGS = {
    'DATABASE_TIMEOUT': config('HEALTH_CHECK_DB_TIMEOUT', default=10, cast=int),
    'REDIS_TIMEOUT': config('HEALTH_CHECK_REDIS_TIMEOUT', default=5, cast=int),
    'CELERY_TIMEOUT': config('HEALTH_CHECK_CELERY_TIMEOUT', default=30, cast=int),
    'DISK_USAGE_THRESHOLD': config('HEALTH_CHECK_DISK_THRESHOLD', default=85, cast=int),
    'MEMORY_USAGE_THRESHOLD': config('HEALTH_CHECK_MEMORY_THRESHOLD', default=85, cast=int),
    'CPU_USAGE_THRESHOLD': config('HEALTH_CHECK_CPU_THRESHOLD', default=85, cast=int),
    'LOAD_AVERAGE_THRESHOLD': config('HEALTH_CHECK_LOAD_THRESHOLD', default=5.0, cast=float),
    'ENABLE_DEEP_CHECKS': config('HEALTH_CHECK_ENABLE_DEEP', default=True, cast=bool),
}

# =============================================================================
# BACKUP AND RECOVERY
# =============================================================================

BACKUP_SETTINGS = {
    'ENABLED': config('BACKUP_ENABLED', default=True, cast=bool),
    'S3_BUCKET': config('BACKUP_S3_BUCKET', default=''),
    'RETENTION_DAYS': config('BACKUP_RETENTION_DAYS', default=30, cast=int),
    'SCHEDULE': config('BACKUP_SCHEDULE', default='0 2 * * *'),
    'COMPRESS': config('BACKUP_COMPRESS', default=True, cast=bool),
    'ENCRYPT': config('BACKUP_ENCRYPT', default=True, cast=bool),
    'ENCRYPTION_KEY': config('BACKUP_ENCRYPTION_KEY', default=''),
    'WEBHOOK_URL': config('BACKUP_WEBHOOK_URL', default=''),
    'INCLUDE_MEDIA': config('BACKUP_INCLUDE_MEDIA', default=True, cast=bool),
    'PARALLEL_UPLOAD': config('BACKUP_PARALLEL_UPLOAD', default=True, cast=bool),
}

# =============================================================================
# FEATURE FLAGS
# =============================================================================

ENABLE_API_DOCS = config('ENABLE_API_DOCS', default=False, cast=bool)
ENABLE_DEBUG_TOOLBAR = config('ENABLE_DEBUG_TOOLBAR', default=False, cast=bool)
ENABLE_ADMIN_INTERFACE = config('ENABLE_ADMIN_INTERFACE', default=True, cast=bool)
ENABLE_MONITORING_ENDPOINTS = config('ENABLE_MONITORING_ENDPOINTS', default=True, cast=bool)
ENABLE_MAINTENANCE_MODE = config('ENABLE_MAINTENANCE_MODE', default=False, cast=bool)
ENABLE_FEATURE_FLAGS = config('ENABLE_FEATURE_FLAGS', default=True, cast=bool)

# Remove debug toolbar from installed apps and middleware in production
if not ENABLE_DEBUG_TOOLBAR and 'debug_toolbar' in INSTALLED_APPS:
    INSTALLED_APPS = [app for app in INSTALLED_APPS if app != 'debug_toolbar']
    MIDDLEWARE = [mw for mw in MIDDLEWARE if 'debug_toolbar' not in mw]

# =============================================================================
# CUSTOM SETTINGS VALIDATION
# =============================================================================

# Validate critical production settings
def validate_production_settings():
    """Validate that all critical production settings are properly configured"""
    errors = []
    
    # Check secret key strength
    if len(SECRET_KEY) < 50:
        errors.append("SECRET_KEY should be at least 50 characters long for production")
    
    # Check database configuration
    if not all([config('DB_NAME'), config('DB_USER'), config('DB_PASSWORD'), config('DB_HOST')]):
        errors.append("Database configuration incomplete")
    
    # Check Redis configuration
    if not config('REDIS_CACHE_URL'):
        errors.append("Redis cache URL not configured")
    
    # Check email configuration
    if not all([config('EMAIL_HOST_USER'), config('EMAIL_HOST_PASSWORD')]):
        errors.append("Email configuration incomplete")
    
    # Check Stripe configuration if enabled
    if STRIPE_LIVE_MODE and not all([config('STRIPE_SECRET_KEY'), config('STRIPE_PUBLISHABLE_KEY')]):
        errors.append("Stripe live mode enabled but keys not configured")
    
    # Check allowed hosts
    if not config('ALLOWED_HOSTS'):
        errors.append("ALLOWED_HOSTS not configured")
    
    if errors:
        raise ValueError(f"Production configuration errors: {'; '.join(errors)}")

# Run validation
try:
    validate_production_settings()
except ValueError as e:
    warnings.warn(str(e), UserWarning)

# =============================================================================
# ADMIN SETTINGS
# =============================================================================

ADMINS = [
    (config('ADMIN_NAME', default='Admin'), config('ADMIN_EMAIL', default='admin@pasargadprints.com')),
]

MANAGERS = ADMINS

# Admin customization
ADMIN_SITE_HEADER = config('ADMIN_SITE_HEADER', default='Pasargad Prints Administration')
ADMIN_SITE_TITLE = config('ADMIN_SITE_TITLE', default='Pasargad Prints Admin')
ADMIN_INDEX_TITLE = config('ADMIN_INDEX_TITLE', default='Welcome to Pasargad Prints Administration')

# =============================================================================
# FEATURE FLAGS
# =============================================================================

ENABLE_API_DOCS = config('ENABLE_API_DOCS', default=False, cast=bool)
ENABLE_DEBUG_TOOLBAR = config('ENABLE_DEBUG_TOOLBAR', default=False, cast=bool)
ENABLE_ADMIN_INTERFACE = config('ENABLE_ADMIN_INTERFACE', default=True, cast=bool)
ENABLE_MONITORING_ENDPOINTS = config('ENABLE_MONITORING_ENDPOINTS', default=True, cast=bool)

# Remove debug toolbar from installed apps and middleware in production
if not ENABLE_DEBUG_TOOLBAR and 'debug_toolbar' in INSTALLED_APPS:
    INSTALLED_APPS.remove('debug_toolbar')

# =============================================================================
# ADMIN SETTINGS
# =============================================================================

ADMINS = [
    ('Admin', config('ADMIN_EMAIL', default='admin@pasargadprints.com')),
]

MANAGERS = ADMINS

# =============================================================================
# SESSION SETTINGS
# =============================================================================

SESSION_COOKIE_AGE = 1209600  # 2 weeks
SESSION_EXPIRE_AT_BROWSER_CLOSE = False
SESSION_SAVE_EVERY_REQUEST = False

# =============================================================================
# STATIC AND MEDIA FILES
# =============================================================================

# Use WhiteNoise for static files
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# S3 settings for media files
if config('USE_S3', default=True, cast=bool):
    DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
    AWS_DEFAULT_ACL = 'public-read'
    AWS_QUERYSTRING_AUTH = False
    AWS_S3_OBJECT_PARAMETERS = {
        'CacheControl': 'max-age=31536000',  # 1 year
    }
    AWS_S3_FILE_OVERWRITE = False
    AWS_S3_SECURE_URLS = True
    AWS_S3_USE_SSL = True

# =============================================================================
# EMAIL SETTINGS
# =============================================================================

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_TIMEOUT = 30
EMAIL_USE_LOCALTIME = True

# =============================================================================
# MONITORING AND HEALTH CHECKS
# =============================================================================

HEALTH_CHECK_SETTINGS = {
    'DATABASE_TIMEOUT': 10,
    'REDIS_TIMEOUT': 5,
    'CELERY_TIMEOUT': 30,
    'DISK_USAGE_THRESHOLD': 85,
    'MEMORY_USAGE_THRESHOLD': 85,
    'CPU_USAGE_THRESHOLD': 85,
}

# =============================================================================
# BACKUP SETTINGS
# =============================================================================

BACKUP_SETTINGS = {
    'ENABLED': True,
    'S3_BUCKET': config('BACKUP_S3_BUCKET', default=''),
    'RETENTION_DAYS': config('BACKUP_RETENTION_DAYS', default=30, cast=int),
    'SCHEDULE': config('BACKUP_SCHEDULE', default='0 2 * * *'),
    'COMPRESS': True,
    'ENCRYPT': True,
}