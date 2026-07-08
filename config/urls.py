"""URL configuration for the Darood Collection project."""
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('darood.urls')),
    path('', include('accounts.urls')),
]
