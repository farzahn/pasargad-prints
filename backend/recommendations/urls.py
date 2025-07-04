from django.urls import path
from . import views

app_name = 'recommendations'

urlpatterns = [
    path('product/<int:product_id>/', views.get_product_recommendations, name='product_recommendations'),
    path('personalized/', views.get_personalized_recommendations, name='personalized_recommendations'),
    path('trending/', views.get_trending_products, name='trending_products'),
]