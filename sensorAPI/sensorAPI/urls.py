from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/fingerprint/', include('fingerprint_app.urls')),  # Include fingerprint_app URLs
]

