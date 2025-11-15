# carex/urls.py

from django.contrib import admin
from django.urls import path, include

# Imports for serving media files in development
from django.conf import settings
from django.conf.urls.static import static

# --- CORRECTED: Imports for Swagger/drf-yasg ---
from rest_framework import permissions
from drf_yasg.views import get_schema_view  # Corrected: drf_yasg
from drf_yasg import openapi               # Corrected: drf_yasg
from django.urls import re_path

# --- Schema view configuration ---
schema_view = get_schema_view(
   openapi.Info(
      title="CarEx API",
      default_version='v1',
      description="API documentation for the CarEx project. This provides endpoints for user authentication including registration, two-step login, profile management, and OTP verification.",
      terms_of_service="https://www.google.com/policies/terms/",
      contact=openapi.Contact(email="contact@carex.local"),
      license=openapi.License(name="BSD License"),
   ),
   public=True,
   permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Your API URLs
    path('api/accounts/', include('accounts.urls')),
    
    # --- Swagger and ReDoc Documentation URLs ---
    re_path(r'^swagger(?P<format>\.json|\.yaml)$', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
]

# Add this line to serve media files during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)