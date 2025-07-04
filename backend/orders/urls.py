from django.urls import path
from . import views

app_name = 'orders'

urlpatterns = [
    # Order management endpoints
    path('', views.OrderListView.as_view(), name='order-list'),
    path('<int:pk>/', views.OrderDetailView.as_view(), name='order-detail'),
    path('<int:pk>/status/', views.OrderStatusUpdateView.as_view(), name='order-status-update'),
    
    # Goshippo shipping endpoints
    path('<int:pk>/shipping-rates/', views.OrderShippingRatesView.as_view(), name='order-shipping-rates'),
    path('<int:pk>/create-shipment/', views.OrderCreateShipmentView.as_view(), name='order-create-shipment'),
    path('<int:pk>/update-tracking/', views.OrderTrackingUpdateView.as_view(), name='order-update-tracking'),
    
    # Public tracking endpoints
    path('track/<str:tracking_number>/', views.OrderTrackingView.as_view(), name='order-tracking'),
    path('track/id/<int:id>/', views.OrderTrackingByIdView.as_view(), name='order-tracking-by-id'),
    path('track/guest/', views.GuestOrderTrackingView.as_view(), name='guest-order-tracking'),
    
    # Admin statistics endpoint
    path('statistics/', views.OrderStatisticsView.as_view(), name='order-statistics'),
]