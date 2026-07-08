from django.urls import path

from . import views

urlpatterns = [
    path('login/', views.AppLoginView.as_view(), name='login'),
    path('logout/', views.AppLogoutView.as_view(), name='logout'),
    path('register/', views.RegisterView.as_view(), name='register'),
    path('', views.HomeRedirectView.as_view(), name='home'),
    path('dashboard/', views.DashboardView.as_view(), name='dashboard'),
    path('users/<int:pk>/update/', views.UpdateUserView.as_view(), name='update_user'),
]
