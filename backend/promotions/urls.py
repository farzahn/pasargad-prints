from django.urls import path
from . import views

app_name = 'promotions'

urlpatterns = [
    # Public endpoints
    path('validate/', views.validate_promotion_code, name='validate_code'),
    path('apply/', views.apply_promotion_code, name='apply_code'),
    path('active/', views.ActivePromotionsView.as_view(), name='active_promotions'),
    
    # Admin endpoints
    path('codes/', views.PromotionCodeListView.as_view(), name='code_list'),
    path('codes/<int:pk>/', views.PromotionCodeDetailView.as_view(), name='code_detail'),
    path('campaigns/', views.CampaignListView.as_view(), name='campaign_list'),
    path('campaigns/<int:pk>/', views.CampaignDetailView.as_view(), name='campaign_detail'),
    path('analytics/', views.promotion_analytics, name='analytics'),
]