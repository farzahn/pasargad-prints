from django.urls import path
from . import views

urlpatterns = [
    # Categories
    path('categories/', views.CategoryListView.as_view(), name='category_list'),
    
    # Products
    path('', views.ProductListView.as_view(), name='product_list'),
    path('featured/', views.FeaturedProductsView.as_view(), name='featured_products'),
    path('search/', views.search_products, name='product_search'),
    path('<int:pk>/', views.ProductDetailView.as_view(), name='product_detail'),
    
    # Reviews
    path('<int:product_id>/reviews/', views.ProductReviewListCreateView.as_view(), name='product_review_list_create'),
    path('reviews/<int:pk>/', views.ProductReviewDetailView.as_view(), name='product_review_detail'),
]