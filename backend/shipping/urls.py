from django.urls import path
from . import views

app_name = 'shipping'

urlpatterns = [
    # Shipping rates
    path('rates/', views.ShippingRatesView.as_view(), name='shipping-rates'),
    
    # Shipping labels
    path('labels/', views.PurchaseShippingLabelView.as_view(), name='purchase-label'),
    
    # Tracking
    path('track/', views.TrackingInfoView.as_view(), name='tracking-info'),
    
    # Webhook
    path('webhook/', views.GoshippoWebhookView.as_view(), name='goshippo-webhook'),
    
    # Order-specific endpoints
    path('orders/<int:order_id>/rates/', views.OrderShippingRatesView.as_view(), name='order-shipping-rates'),
    path('orders/<int:order_id>/label/', views.OrderShippingLabelView.as_view(), name='order-shipping-label'),
    path('orders/<int:order_id>/tracking/events/', views.order_tracking_events, name='order-tracking-events'),
]