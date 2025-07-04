from django.urls import path
from . import views

app_name = 'promotions'

urlpatterns = [
    # Public endpoints
    path('validate/', views.validate_promotion_code, name='validate_code'),
    path('apply/', views.apply_promotion_code, name='apply_code'),
    path('active/', views.ActivePromotionsView.as_view(), name='active_promotions'),
    
    # Removed unused admin endpoints - frontend admin panel not implemented
]