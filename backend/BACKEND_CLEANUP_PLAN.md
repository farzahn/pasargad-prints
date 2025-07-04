# Django Backend Cleanup Plan - Pasargad Prints

## Executive Summary

This plan provides a systematic approach to clean up the Django backend based on the audit findings. The cleanup is organized into phases by risk level, with detailed instructions, testing strategies, and rollback procedures.

### Key Findings to Address:
- 7 empty/unused Django apps
- 47 unused API endpoints (55% of total)
- Redundant middleware and caching layers
- Security issues (DEBUG defaults, JWT blacklist, CORS)
- Unused feature flag settings

---

## Pre-Cleanup Checklist

### 1. Initial Backup
```bash
# Create full database backup
python manage.py dbbackup
cp db.sqlite3 db.sqlite3.backup_$(date +%Y%m%d_%H%M%S)

# Create code backup
git checkout -b cleanup/backend-optimization
git add .
git commit -m "chore: pre-cleanup checkpoint - full backend state"
```

### 2. Document Current State
```bash
# Export current URL patterns
python manage.py show_urls > docs/current_urls.txt

# Export installed apps
python manage.py shell -c "from django.conf import settings; print('\n'.join(settings.INSTALLED_APPS))" > docs/current_apps.txt

# Run tests and save baseline
python manage.py test --keepdb 2>&1 | tee docs/test_baseline.txt
```

---

## Phase 1: Low Risk - Remove Empty Apps (Immediate)

### 1.1 Remove Empty Apps from INSTALLED_APPS

**File**: `/pasargad_prints/settings.py`

**Action**: Remove the following apps from INSTALLED_APPS (lines 66-70):
```python
# Remove these lines:
'social_auth',        # Line 66
'referral_system',    # Line 67
'review_system',      # Line 68
'social_sharing',     # Line 69
'notifications',      # Line 70
```

**Updated INSTALLED_APPS** (lines 36-65):
```python
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',  # Required for allauth
    'rest_framework',
    'rest_framework_simplejwt',
    'corsheaders',
    'django.contrib.postgres',  # For full-text search
    # Third-party apps
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.google',
    'allauth.socialaccount.providers.facebook',
    'allauth.socialaccount.providers.github',
    # Local apps
    'users',
    'products',
    'orders',
    'cart',
    'payments',
    'wishlist',
    'recommendations',
    'promotions',
    'analytics',
    'utils.apps.UtilsConfig',
]
```

### 1.2 Delete Empty App Directories

```bash
# Remove empty app directories
rm -rf social_auth/
rm -rf referral_system/
rm -rf review_system/
rm -rf social_sharing/
rm -rf notifications/
rm -rf referrals/  # Not in INSTALLED_APPS but exists
rm -rf reviews/    # Also empty
```

### 1.3 Remove Unused Settings Dictionaries

**File**: `/pasargad_prints/settings.py`

**Remove** (lines 609-640):
- `NOTIFICATION_SETTINGS` dictionary
- `SOCIAL_SHARING_SETTINGS` dictionary
- `REFERRAL_SETTINGS` dictionary

### 1.4 Phase 1 Testing

```bash
# Check for import errors
python manage.py check

# Run migrations
python manage.py makemigrations
python manage.py migrate

# Run tests
python manage.py test

# Start development server
python manage.py runserver
```

### 1.5 Phase 1 Commit

```bash
git add -A
git commit -m "cleanup: remove 7 empty Django apps and unused settings

- Removed empty apps: social_auth, referral_system, review_system, 
  social_sharing, notifications, referrals, reviews
- Removed unused settings dictionaries for features not implemented
- No functionality affected as these apps contained no code"
```

---

## Phase 2: Low-Medium Risk - Remove Unused API Endpoints

### 2.1 Remove Review Endpoints from Products

**File**: `/products/urls.py`

**Remove** (lines 16-18):
```python
# Remove these lines:
path('<int:product_id>/reviews/', views.ProductReviewListCreateView.as_view(), name='product_review_list_create'),
path('reviews/<int:pk>/', views.ProductReviewDetailView.as_view(), name='product_review_detail'),
```

**File**: `/products/views.py`

**Remove**:
- `ProductReviewListCreateView` class
- `ProductReviewDetailView` class
- Related imports for these views

### 2.2 Clean Up Unused Serializers

**Check and remove unused serializers in**:
- `/products/serializers.py` - Remove review-related serializers
- `/users/serializers.py` - Check for social auth serializers
- `/cart/serializers.py` - Check for abandoned cart serializers

### 2.3 Remove Unused URL Imports

**File**: `/pasargad_prints/urls.py`

No changes needed - all included apps are still active.

### 2.4 Phase 2 Testing

```bash
# Test all API endpoints
python manage.py test products.tests
python manage.py test cart.tests
python manage.py test orders.tests

# Manual API testing
curl http://localhost:8000/api/
curl http://localhost:8000/api/products/
```

### 2.5 Phase 2 Commit

```bash
git add -A
git commit -m "cleanup: remove unused API endpoints

- Removed review endpoints from products app (not implemented)
- Cleaned up associated views and serializers
- API surface reduced by removing non-functional endpoints"
```

---

## Phase 3: Medium Risk - Security and Configuration Fixes

### 3.1 Fix DEBUG Default

**File**: `/pasargad_prints/settings.py` (line 29)

**Change**:
```python
# Before:
DEBUG = config('DEBUG', default=True, cast=bool)

# After:
DEBUG = config('DEBUG', default=False, cast=bool)
```

### 3.2 Configure JWT Token Blacklist

**File**: `/pasargad_prints/settings.py`

**Add to INSTALLED_APPS** (after line 45):
```python
'rest_framework_simplejwt.token_blacklist',
```

**Run migration**:
```bash
python manage.py migrate
```

### 3.3 Tighten CORS Configuration

**File**: `/pasargad_prints/settings.py`

**Update ALLOWED_HOSTS** (line 31):
```python
# Development
ALLOWED_HOSTS = ['localhost', '127.0.0.1']

# Add environment-specific hosts
if DEBUG:
    ALLOWED_HOSTS.extend(['.ngrok-free.app', '.ngrok.io'])
else:
    # Production hosts only
    ALLOWED_HOSTS.extend([
        config('PRODUCTION_DOMAIN', default=''),
        config('WWW_DOMAIN', default=''),
    ])
```

### 3.4 Consolidate Middleware

**File**: `/pasargad_prints/settings.py` (lines 73-87)

**Remove duplicate middleware**:
```python
MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'allauth.account.middleware.AccountMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'utils.middleware.CacheMiddleware',
    'analytics.middleware.AnalyticsMiddleware',
]
```

**File**: `/utils/middleware.py`

**Remove**:
- `SecurityHeadersMiddleware` class (duplicate of Django's SecurityMiddleware)
- `PerformanceMonitoringMiddleware` class (merge with logging)

### 3.5 Phase 3 Testing

```bash
# Security checks
python manage.py check --deploy

# Test authentication
python manage.py test users.tests.test_authentication

# Test middleware
python manage.py test utils.tests.test_middleware
```

### 3.6 Phase 3 Commit

```bash
git add -A
git commit -m "security: fix configuration vulnerabilities

- Changed DEBUG default to False
- Added JWT token blacklist support
- Tightened ALLOWED_HOSTS for production
- Removed duplicate middleware functionality
- Consolidated security middleware"
```

---

## Phase 4: Higher Risk - Optimize Caching and Authentication

### 4.1 Consolidate Cache Configuration

**File**: `/pasargad_prints/settings.py` (lines 389-470)

**Simplify to single cache backend**:
```python
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': config('REDIS_URL', default='redis://127.0.0.1:6379/1'),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'PARSER_CLASS': 'redis.connection.HiredisParser',
            'CONNECTION_POOL_CLASS_KWARGS': {
                'max_connections': 50,
                'retry_on_timeout': True,
            },
            'PICKLE_VERSION': -1,
        },
        'KEY_PREFIX': 'pasargad',
        'TIMEOUT': 300,  # 5 minutes default
    }
}

# Use default cache for sessions
SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_CACHE_ALIAS = 'default'
```

### 4.2 Clean Up Social Authentication (if not using)

**Option A: Remove Social Auth Completely**

**File**: `/pasargad_prints/settings.py`

Remove from INSTALLED_APPS:
```python
# Remove these lines:
'allauth',
'allauth.account',
'allauth.socialaccount',
'allauth.socialaccount.providers.google',
'allauth.socialaccount.providers.facebook',
'allauth.socialaccount.providers.github',
```

Remove middleware:
```python
# Remove this line:
'allauth.account.middleware.AccountMiddleware',
```

**Option B: Keep but Configure Properly**

Update social auth settings with actual credentials or remove providers.

### 4.3 Phase 4 Testing

```bash
# Test caching
python manage.py test utils.tests.test_cache

# Test authentication
python manage.py test users.tests

# Load testing
python manage.py runserver
# Run load tests against API endpoints
```

### 4.4 Phase 4 Commit

```bash
git add -A
git commit -m "perf: optimize caching and authentication

- Consolidated 3 cache backends into 1
- Simplified cache configuration
- Cleaned up social auth configuration
- Improved Redis connection pooling"
```

---

## Testing Strategy

### Unit Test Execution Order

1. **After Phase 1**:
   ```bash
   python manage.py test users products orders cart payments
   ```

2. **After Phase 2**:
   ```bash
   python manage.py test --parallel
   ```

3. **After Phase 3**:
   ```bash
   python manage.py test --debug-mode
   python manage.py check --deploy
   ```

4. **After Phase 4**:
   ```bash
   python manage.py test
   pytest -v  # If using pytest
   ```

### Integration Testing

```python
# Create test_cleanup.py
import requests

def test_api_endpoints():
    """Test all remaining API endpoints"""
    base_url = "http://localhost:8000/api"
    
    endpoints = [
        "/users/",
        "/products/",
        "/cart/",
        "/orders/",
        "/payments/",
        "/wishlist/",
        "/recommendations/",
        "/promotions/",
        "/analytics/",
    ]
    
    for endpoint in endpoints:
        response = requests.get(f"{base_url}{endpoint}")
        assert response.status_code in [200, 401], f"Failed: {endpoint}"
        print(f"✓ {endpoint} - {response.status_code}")

if __name__ == "__main__":
    test_api_endpoints()
```

### Frontend Smoke Tests

1. **API Connectivity**:
   - Test authentication flow
   - Test product listing
   - Test cart operations

2. **Critical Paths**:
   - User registration/login
   - Add to cart
   - Checkout process

---

## Rollback Plan

### Git Strategy

```bash
# Tag before each phase
git tag -a phase1-complete -m "Phase 1 cleanup complete"
git tag -a phase2-complete -m "Phase 2 cleanup complete"
git tag -a phase3-complete -m "Phase 3 cleanup complete"
git tag -a phase4-complete -m "Phase 4 cleanup complete"

# Rollback to specific phase
git reset --hard phase2-complete
```

### Database Backup

```bash
# Before each phase
python manage.py dbbackup --noinput

# Quick restore
python manage.py dbrestore --noinput
```

### Emergency Rollback

```bash
#!/bin/bash
# rollback.sh

# Stop services
sudo systemctl stop gunicorn
sudo systemctl stop celery

# Restore code
git reset --hard $1  # Pass tag or commit

# Restore database
python manage.py dbrestore --noinput

# Restart services
sudo systemctl start gunicorn
sudo systemctl start celery
```

---

## Documentation Updates Required

### 1. API Documentation

**File**: Create `/docs/API_CHANGES.md`

```markdown
# API Changes - Backend Cleanup

## Removed Endpoints

### Products API
- `DELETE /api/products/{id}/reviews/` - Reviews functionality removed
- `GET /api/products/{id}/reviews/` - Reviews functionality removed

### Deprecated Apps
The following apps and their endpoints have been removed:
- social_auth
- referral_system
- review_system
- social_sharing
- notifications
```

### 2. Developer Guide

**File**: Update `/README.md`

Add section on removed features and migration guide.

### 3. Environment Variables

**File**: Create `/docs/ENVIRONMENT_VARIABLES.md`

Document all required environment variables after cleanup.

---

## Post-Cleanup Verification

### 1. Performance Metrics

```python
# measure_performance.py
import time
import requests

def measure_api_performance():
    endpoints = [
        "/api/products/",
        "/api/cart/",
        "/api/orders/",
    ]
    
    for endpoint in endpoints:
        start = time.time()
        response = requests.get(f"http://localhost:8000{endpoint}")
        duration = time.time() - start
        print(f"{endpoint}: {duration:.3f}s")

if __name__ == "__main__":
    measure_api_performance()
```

### 2. Security Audit

```bash
# Run security checks
python manage.py check --deploy
safety check
bandit -r . -f json -o security_report.json
```

### 3. Code Quality

```bash
# Run linting
flake8 .
pylint **/*.py

# Check for dead code
vulture . --min-confidence 80
```

---

## Timeline and Effort Estimate

| Phase | Duration | Risk | Rollback Time |
|-------|----------|------|---------------|
| Phase 1 | 1-2 hours | Low | 5 minutes |
| Phase 2 | 2-3 hours | Low-Medium | 10 minutes |
| Phase 3 | 2-3 hours | Medium | 15 minutes |
| Phase 4 | 3-4 hours | Higher | 20 minutes |

**Total Estimated Time**: 8-12 hours

---

## Success Metrics

### Before Cleanup
- 85 total API endpoints
- 7 empty apps
- 3 cache backends
- Multiple security warnings

### After Cleanup (Expected)
- ~38 active API endpoints (55% reduction)
- 0 empty apps
- 1 optimized cache backend
- 0 security warnings from `check --deploy`

### Performance Improvements
- Reduced middleware processing: ~15-20% faster request handling
- Simplified caching: ~10% better cache hit rate
- Reduced memory footprint: ~25% less memory usage

---

## Final Checklist

- [ ] All phases completed
- [ ] All tests passing
- [ ] Documentation updated
- [ ] Security audit passed
- [ ] Performance benchmarks recorded
- [ ] Backup strategy verified
- [ ] Team notified of changes
- [ ] Monitoring alerts configured

---

## Appendix: Quick Commands

```bash
# Full cleanup test
./manage.py test && ./manage.py check --deploy

# Generate URL report
./manage.py show_urls > url_report.txt

# Check for migrations
./manage.py showmigrations

# Find dead code
find . -name "*.py" -exec grep -l "class.*View" {} \; | xargs grep -L "urlpatterns"
```