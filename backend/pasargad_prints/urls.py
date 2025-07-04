"""
URL configuration for pasargad_prints project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import JsonResponse
from rest_framework.decorators import api_view

@api_view(['GET'])
def api_root(request):
    """API root endpoint providing navigation links."""
    return JsonResponse({
        'message': 'Welcome to Pasargad Prints API',
        'version': '1.0',
        'endpoints': {
            'users': '/api/users/',
            'products': '/api/products/',
            'cart': '/api/cart/',
            'orders': '/api/orders/',
            'payments': '/api/payments/',
            'wishlist': '/api/wishlist/',
            'recommendations': '/api/recommendations/',
            'promotions': '/api/promotions/',
            'analytics': '/api/analytics/',
            'admin': '/admin/',
            'health': '/health/',
        }
    })

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # API root
    path('api/', api_root, name='api-root'),
    
    # API endpoints
    path('api/users/', include('users.urls')),
    path('api/products/', include('products.urls')),
    path('api/cart/', include('cart.urls')),
    path('api/orders/', include('orders.urls')),
    path('api/payments/', include('payments.urls')),
    path('api/wishlist/', include('wishlist.urls')),
    path('api/recommendations/', include('recommendations.urls')),
    path('api/promotions/', include('promotions.urls')),
    path('api/analytics/', include('analytics.urls')),
    
    # Utility endpoints
    path('', include('utils.urls')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)