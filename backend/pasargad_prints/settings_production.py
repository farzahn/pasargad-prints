"""
Production settings for Pasargad Prints

This file contains production-specific Django settings.
It imports from the base settings.py and overrides certain values for production.
"""

import os
import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration
from sentry_sdk.integrations.celery import CeleryIntegration
from sentry_sdk.integrations.redis import RedisIntegration
from decouple import config

# Import base settings
from .settings import *

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
            'sslmode': 'require',
            'connect_timeout': 10,
            'application_name': 'pasargad_prints_prod',
        },
        'CONN_MAX_AGE': config('DB_CONN_MAX_AGE', default=600, cast=int),
        'CONN_HEALTH_CHECKS': config('DB_CONN_HEALTH_CHECKS', default=True, cast=bool),
    }
}

# =============================================================================
# CACHE SETTINGS
# =============================================================================

CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': config('REDIS_CACHE_URL'),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'PARSER_CLASS': 'redis.connection.HiredisParser',
            'CONNECTION_POOL_CLASS': 'redis.BlockingConnectionPool',
            'CONNECTION_POOL_CLASS_KWARGS': {
                'max_connections': config('DB_POOL_SIZE', default=20, cast=int),
                'retry_on_timeout': True,
            },
            'MAX_CONNECTIONS': config('DB_POOL_SIZE', default=20, cast=int),
            'KEY_PREFIX': 'pasargad_prod',
            'VERSION': 1,
            'TIMEOUT': config('CACHE_TIMEOUT', default=300, cast=int),
            'COMPRESS_MIN_LEN': 10,
            'COMPRESS_LEVEL': 6,
        }
    },
    'session': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': config('REDIS_SESSION_URL'),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'KEY_PREFIX': 'session_prod',
            'TIMEOUT': config('SESSION_CACHE_TIMEOUT', default=3600, cast=int),
        }
    },
    'api': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': config('REDIS_API_URL'),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'KEY_PREFIX': 'api_prod',
            'TIMEOUT': config('API_CACHE_TIMEOUT', default=60, cast=int),
        }
    }
}

# =============================================================================
# CELERY SETTINGS
# =============================================================================

CELERY_BROKER_URL = config('CELERY_BROKER_URL')
CELERY_RESULT_BACKEND = config('CELERY_RESULT_BACKEND')
CELERY_TASK_ALWAYS_EAGER = config('CELERY_TASK_ALWAYS_EAGER', default=False, cast=bool)
CELERY_TASK_EAGER_PROPAGATES = config('CELERY_TASK_EAGER_PROPAGATES', default=True, cast=bool)

# Production-specific Celery settings
CELERY_WORKER_PREFETCH_MULTIPLIER = 1
CELERY_WORKER_MAX_TASKS_PER_CHILD = 1000
CELERY_TASK_REJECT_ON_WORKER_LOST = True
CELERY_TASK_ACKS_LATE = True

# =============================================================================
# LOGGING SETTINGS
# =============================================================================

LOG_LEVEL = config('LOG_LEVEL', default='INFO')

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '[{levelname}] {asctime} {name} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '[{levelname}] {asctime} {name} {message}',
            'style': '{',
            'datefmt': '%Y-%m-%d %H:%M:%S'
        },
        'json': {
            '()': 'pythonjsonlogger.jsonlogger.JsonFormatter',
            'format': '%(asctime)s %(name)s %(levelname)s %(message)s'
        },
    },
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse',
        },
        'require_debug_true': {
            '()': 'django.utils.log.RequireDebugTrue',
        },
    },
    'handlers': {
        'console': {
            'level': LOG_LEVEL,
            'class': 'logging.StreamHandler',
            'formatter': 'json',
        },
        'file': {
            'level': LOG_LEVEL,
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(BASE_DIR, 'logs', 'pasargad_prints.log'),
            'maxBytes': 1024 * 1024 * 50,  # 50MB
            'backupCount': 20,
            'formatter': 'json',
        },
        'error_file': {
            'level': 'ERROR',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(BASE_DIR, 'logs', 'errors.log'),
            'maxBytes': 1024 * 1024 * 50,  # 50MB
            'backupCount': 20,
            'formatter': 'json',
        },
        'security_file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(BASE_DIR, 'logs', 'security.log'),
            'maxBytes': 1024 * 1024 * 50,  # 50MB
            'backupCount': 20,
            'formatter': 'json',
        },
        'performance_file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(BASE_DIR, 'logs', 'performance.log'),
            'maxBytes': 1024 * 1024 * 50,  # 50MB
            'backupCount': 20,
            'formatter': 'json',
        },
        'syslog': {
            'level': LOG_LEVEL,
            'class': 'logging.handlers.SysLogHandler',
            'address': '/dev/log',
            'facility': 'local0',
            'formatter': 'json',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': LOG_LEVEL,
            'propagate': True,
        },
        'django.request': {
            'handlers': ['error_file', 'syslog'],
            'level': 'ERROR',
            'propagate': False,
        },
        'django.security': {
            'handlers': ['security_file', 'syslog'],
            'level': 'INFO',
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
        'performance': {
            'handlers': ['performance_file'],
            'level': 'INFO',
            'propagate': False,
        },
        'celery': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': True,
        },
    },
    'root': {
        'handlers': ['console', 'file'],
        'level': LOG_LEVEL,
    },
}

# =============================================================================
# SENTRY CONFIGURATION
# =============================================================================

SENTRY_DSN = config('SENTRY_DSN', default='')
if SENTRY_DSN:
    sentry_sdk.init(
        dsn=SENTRY_DSN,
        environment=config('SENTRY_ENVIRONMENT', default='production'),
        release=config('SENTRY_RELEASE', default='1.0.0'),
        integrations=[
            DjangoIntegration(transaction_style='url'),
            CeleryIntegration(monitor_beat_tasks=True),
            RedisIntegration(),
        ],
        traces_sample_rate=0.1,
        send_default_pii=False,
        attach_stacktrace=True,
        before_send=lambda event, hint: event if event.get('level') != 'info' else None,
    )

# =============================================================================
# PERFORMANCE SETTINGS
# =============================================================================

# Database connection pooling
DATABASES['default']['OPTIONS']['MAX_CONNS'] = config('DB_POOL_SIZE', default=20, cast=int)

# Template caching
TEMPLATES[0]['OPTIONS']['loaders'] = [
    ('django.template.loaders.cached.Loader', [
        'django.template.loaders.filesystem.Loader',
        'django.template.loaders.app_directories.Loader',
    ]),
]

# =============================================================================
# RATE LIMITING
# =============================================================================

REST_FRAMEWORK['DEFAULT_THROTTLE_RATES'] = {
    'anon': config('RATE_LIMIT_ANON', default='100/hour'),
    'user': config('RATE_LIMIT_USER', default='1000/hour'),
    'burst': config('RATE_LIMIT_BURST', default='20/minute'),
    'sustained': config('RATE_LIMIT_SUSTAINED', default='1000/day'),
}

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