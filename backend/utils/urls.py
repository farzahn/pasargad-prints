from django.urls import path
from . import views
from . import monitoring

app_name = 'utils'

urlpatterns = [
    path('health/', views.health_check, name='health-check'),
    path('health/detailed/', views.detailed_health_check, name='detailed-health-check'),
    path('robots.txt', views.robots_txt, name='robots-txt'),
    
    # Monitoring endpoints
    path('monitoring/system/', monitoring.system_health_check, name='system-health'),
    path('monitoring/cache/', monitoring.cache_statistics, name='cache-stats'),
    path('monitoring/database/', monitoring.database_statistics, name='db-stats'),
    path('monitoring/cache/clear/', monitoring.clear_cache, name='clear-cache'),
]