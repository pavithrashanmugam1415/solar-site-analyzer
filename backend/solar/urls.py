from django.urls import path

from . import views

urlpatterns = [
    path("sites", views.SiteListView.as_view(), name="site-list"),
    path("sites/<int:site_id>", views.SiteDetailView.as_view(), name="site-detail"),
    path("analyze", views.AnalyzeView.as_view(), name="analyze"),
    path("statistics", views.StatisticsView.as_view(), name="statistics"),
    path("export", views.ExportView.as_view(), name="export"),
]