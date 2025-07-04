from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# Create a router for viewsets
router = DefaultRouter()
router.register(r'admin/ab-experiments', views.ABTestExperimentViewSet, basename='ab-experiments')
router.register(r'admin/page-views', views.AdminPageViewViewSet, basename='admin-page-views')
router.register(r'admin/user-behavior', views.AdminUserBehaviorViewSet, basename='admin-user-behavior')
router.register(r'admin/product-views', views.AdminProductViewViewSet, basename='admin-product-views')
router.register(r'admin/cart-abandonment', views.AdminCartAbandonmentViewSet, basename='admin-cart-abandonment')
router.register(r'admin/conversions', views.AdminConversionViewSet, basename='admin-conversions')

app_name = 'analytics'

urlpatterns = [
    # Public analytics tracking endpoints
    path('track/page-view/', views.PageViewCreateView.as_view(), name='track-page-view'),
    path('track/user-behavior/', views.UserBehaviorCreateView.as_view(), name='track-user-behavior'),
    path('track/product-view/', views.ProductViewCreateView.as_view(), name='track-product-view'),
    path('track/cart-abandonment/', views.TrackCartAbandonmentView.as_view(), name='track-cart-abandonment'),
    path('track/conversion/', views.TrackConversionView.as_view(), name='track-conversion'),
    
    # A/B Testing endpoints
    path('ab-test/get-variant/', views.GetABTestVariantView.as_view(), name='get-ab-test-variant'),
    path('ab-test/record-conversion/', views.RecordABTestConversionView.as_view(), name='record-ab-test-conversion'),
    
    # Admin dashboard endpoints
    path('admin/dashboard/', views.AdminDashboardView.as_view(), name='admin-dashboard'),
    path('admin/product-performance/', views.AdminProductPerformanceView.as_view(), name='admin-product-performance'),
    path('admin/customer-analytics/', views.AdminCustomerAnalyticsView.as_view(), name='admin-customer-analytics'),
    
    # Report generation endpoints
    path('admin/reports/generate/', views.GenerateReportView.as_view(), name='generate-report'),
    path('admin/reports/', views.ReportListView.as_view(), name='list-reports'),
    
    # Include router URLs
    path('', include(router.urls)),
]