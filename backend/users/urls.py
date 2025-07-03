from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from . import views

urlpatterns = [
    # Authentication
    path('auth/login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('auth/register/', views.UserRegistrationView.as_view(), name='user_registration'),
    
    # User profile
    path('profile/', views.UserProfileView.as_view(), name='user_profile'),
    path('password/change/', views.PasswordChangeView.as_view(), name='password_change'),
    
    # Addresses
    path('addresses/', views.AddressListCreateView.as_view(), name='address_list_create'),
    path('addresses/<int:pk>/', views.AddressRetrieveUpdateDestroyView.as_view(), name='address_detail'),
    
    # Newsletter
    path('newsletter/subscribe/', views.newsletter_subscribe, name='newsletter_subscribe'),
    path('newsletter/unsubscribe/', views.newsletter_unsubscribe, name='newsletter_unsubscribe'),
]