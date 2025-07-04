from django.urls import path
from . import views

urlpatterns = [
    path('', views.CartRetrieveView.as_view(), name='cart_detail'),
    path('add/', views.add_to_cart, name='add_to_cart'),
    path('items/<int:item_id>/', views.update_cart_item, name='update_cart_item'),
    path('items/<int:item_id>/remove/', views.remove_from_cart, name='remove_from_cart'),
    path('clear/', views.clear_cart, name='clear_cart'),
    path('merge/', views.merge_guest_cart, name='merge_guest_cart'),
]