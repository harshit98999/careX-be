from django.urls import path
from .views import (
    RegisterView, 
    VerifyOTPView, 
    ResendOTPView,
    LoginView,
    ResendLoginOTPView,
    LoginVerifyOTPView,
    UserProfileView,
)
from rest_framework_simplejwt.views import TokenRefreshView

urlpatterns = [
    # --- Registration Flow ---
    path('register/', RegisterView.as_view(), name='register'),
    path('register-verify/', VerifyOTPView.as_view(), name='register-verify'),
    path('register-resend-otp/', ResendOTPView.as_view(), name='register-resend-otp'),
    
    # --- Login Flow (Two-Step Verification) ---
    path('login/', LoginView.as_view(), name='login'),
    path('login-resend-otp/', ResendLoginOTPView.as_view(), name='login-resend-otp'),
    path('login-verify/', LoginVerifyOTPView.as_view(), name='login-verify'),
    
    # --- Token Management ---
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # --- User Profile URL ---
    path('profile/', UserProfileView.as_view(), name='user-profile'),
]