from django.urls import path
from . import views

urlpatterns = [
    # Categories
    path('categories/', views.CategoryListView.as_view(), name='category_list'),
    
    # Products
    path('', views.ProductListView.as_view(), name='product_list'),
    path('search/', views.search_products, name='product_search'),
    path('advanced-search/', views.advanced_search, name='advanced_search'),
    path('low-stock/', views.get_low_stock_products, name='low_stock_products'),
    path('<int:pk>/', views.ProductDetailView.as_view(), name='product_detail'),
    
    # Reviews
    path('<int:product_id>/reviews/', views.ProductReviewListCreateView.as_view(), name='product_review_list_create'),
    path('reviews/<int:pk>/', views.ProductReviewDetailView.as_view(), name='product_review_detail'),
]