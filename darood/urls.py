from django.urls import path

from . import views

urlpatterns = [
    # Recording
    path('darood/add/', views.AddDaroodView.as_view(), name='add_darood'),
    path('darood/submit/', views.SubmitDaroodView.as_view(), name='submit_darood'),

    # Approvals
    path('darood/approvals/', views.ApprovalsView.as_view(), name='approvals'),
    path('darood/<int:pk>/review/', views.ReviewEntryView.as_view(), name='review_entry'),

    # Viewing
    path('darood/overview/', views.DaroodOverviewView.as_view(), name='darood_overview'),
    path('me/', views.MyProgressView.as_view(), name='my_progress'),
    path('users/<int:pk>/darood/', views.UserDetailView.as_view(), name='user_detail'),

    # JSON APIs
    path('api/users/search/', views.UserSearchAPI.as_view(), name='user_search_api'),
    path('api/chart/', views.ChartDataAPI.as_view(), name='chart_data_api'),
]
