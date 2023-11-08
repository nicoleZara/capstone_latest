from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),
    path('', include('home.urls', namespace='home')),

    path('supermarket/', include('supermarket.urls', namespace='supermarket')),
    path('charts/', include('charts.urls')),

    path('', include('auth_system.urls', namespace='auth_system')),



    # You can add more URL patterns as needed for other apps or features
]
