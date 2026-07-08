from django.urls import path

from . import views

urlpatterns = [
    path('darood/add/', views.AddDaroodView.as_view(), name='add_darood'),
    path('darood/overview/', views.DaroodOverviewView.as_view(), name='darood_overview'),
    path('me/', views.MyProgressView.as_view(), name='my_progress'),
    path('users/<int:pk>/darood/', views.UserDetailView.as_view(), name='user_detail'),

    # JSON APIs
    path('api/users/search/', views.UserSearchAPI.as_view(), name='user_search_api'),
    path('api/chart/', views.ChartDataAPI.as_view(), name='chart_data_api'),
]
