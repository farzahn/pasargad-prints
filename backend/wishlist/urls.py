from django.urls import path
from . import views

app_name = 'wishlist'

urlpatterns = [
    path('', views.get_wishlist, name='get_wishlist'),
    path('add/', views.add_to_wishlist, name='add_to_wishlist'),
    path('remove/<int:product_id>/', views.remove_from_wishlist, name='remove_from_wishlist'),
    path('clear/', views.clear_wishlist, name='clear_wishlist'),
    path('move-to-cart/<int:product_id>/', views.move_to_cart, name='move_to_cart'),
]