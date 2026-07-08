"""URL configuration for the Darood Collection project."""
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('admin/', admin.site.urls),
    path('i18n/', include('django.conf.urls.i18n')),   # set_language endpoint
    path('api/v1/', include('api.urls')),              # mobile / JSON API (JWT)
    path('', include('darood.urls')),
    path('', include('accounts.urls')),
]
