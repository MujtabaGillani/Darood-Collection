from django.urls import path

from . import views

urlpatterns = [
    # Recording
    path('darood/add/', views.AddDaroodView.as_view(), name='add_darood'),
    path('darood/submit/', views.SubmitDaroodView.as_view(), name='submit_darood'),

    # Reserve (a manager's private stash)
    path('darood/reserve/add/', views.AddReserveView.as_view(), name='reserve_add'),
    path('darood/reserve/use/', views.UseReserveView.as_view(), name='reserve_use'),

    # Approvals
    path('darood/approvals/', views.ApprovalsView.as_view(), name='approvals'),
    path('darood/<int:pk>/review/', views.ReviewEntryView.as_view(), name='review_entry'),

    # Viewing
    path('fazail/', views.FazailView.as_view(), name='fazail'),
    path('darood/overview/', views.DaroodOverviewView.as_view(), name='darood_overview'),
    path('me/', views.MyProgressView.as_view(), name='my_progress'),
    path('users/<int:pk>/darood/', views.UserDetailView.as_view(), name='user_detail'),

    # JSON APIs
    path('api/users/search/', views.UserSearchAPI.as_view(), name='user_search_api'),
    path('api/chart/', views.ChartDataAPI.as_view(), name='chart_data_api'),
    path('api/chart/managers/', views.ManagerSeriesAPI.as_view(), name='manager_series_api'),
    path('api/chart/users/', views.UserSeriesAPI.as_view(), name='user_series_api'),
    path('api/stats/tops/', views.TopStatsAPI.as_view(), name='top_stats_api'),
]
