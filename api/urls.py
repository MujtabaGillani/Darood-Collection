"""Versioned mobile/JSON API routes, all under /api/v1/."""

from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from . import views

app_name = 'api'

urlpatterns = [
    # Auth
    path('auth/register/', views.RegisterView.as_view(), name='register'),
    path('auth/login/', views.LoginView.as_view(), name='login'),
    path('auth/logout/', views.LogoutView.as_view(), name='logout'),
    path('auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('auth/me/', views.MeView.as_view(), name='me'),
    path('auth/change-password/', views.ChangePasswordView.as_view(), name='change_password'),

    # Users
    path('users/', views.UserListView.as_view(), name='user_list'),
    path('users/search/', views.UserSearchView.as_view(), name='user_search'),
    path('users/managers/', views.ManagerListView.as_view(), name='manager_list'),
    path('users/quick-add/', views.QuickAddUserView.as_view(), name='quick_add_user'),
    path('users/<int:pk>/', views.UserDetailView.as_view(), name='user_detail'),
    path('users/<int:pk>/update/', views.UserUpdateView.as_view(), name='user_update'),

    # Darood
    path('darood/record/', views.RecordDaroodView.as_view(), name='darood_record'),
    path('darood/submit/', views.SubmitDaroodView.as_view(), name='darood_submit'),
    path('darood/mine/', views.MyProgressView.as_view(), name='darood_mine'),
    path('darood/overview/', views.OverviewView.as_view(), name='darood_overview'),
    path('darood/approvals/', views.ApprovalsView.as_view(), name='darood_approvals'),
    path('darood/<int:pk>/review/', views.ReviewEntryView.as_view(), name='darood_review'),

    # Charts & stats
    path('charts/trend/', views.TrendChartView.as_view(), name='chart_trend'),
    path('charts/managers/', views.ManagerSeriesView.as_view(), name='chart_managers'),
    path('charts/users/', views.UserSeriesView.as_view(), name='chart_users'),
    path('stats/tops/', views.TopStatsView.as_view(), name='stats_tops'),
    path('stats/dashboard/', views.DashboardStatsView.as_view(), name='stats_dashboard'),
]
