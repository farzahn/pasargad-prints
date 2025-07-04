from django.urls import path
from . import views

urlpatterns = [
    
    path('create-checkout-session/', views.create_checkout_session, name='create_checkout_session'),
    path('verify-checkout-session/', views.verify_checkout_session, name='verify_checkout_session'),
    path('stripe-webhook/', views.stripe_webhook, name='stripe_webhook'),
]