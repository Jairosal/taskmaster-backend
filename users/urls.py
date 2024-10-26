from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import (
    CustomTokenObtainPairView, 
    RegisterView, 
    UserProfileView, 
    ChangePasswordView, 
    PasswordResetRequestView, 
    PasswordResetConfirmView
)

urlpatterns = [
    path('token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('register/', RegisterView.as_view(), name='register'),
    path('profile/', UserProfileView.as_view(), name='user_profile'),
    path('change-password/', ChangePasswordView.as_view(), name='change-password'),
    path('password-reset/', PasswordResetRequestView.as_view(), name='password_reset'),
    path('password-reset-confirm/<str:uidb64>/<str:token>/', 
         PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
]