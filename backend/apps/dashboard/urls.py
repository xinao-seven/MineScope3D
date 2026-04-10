from django.urls import path
from .views import (
    BoreholeDepthDistributionView,
    DashboardOverviewView,
    LayerDistributionView,
    WorkfaceBoreholesView,
)

urlpatterns = [
    path('overview/', DashboardOverviewView.as_view()),
    path('layer-distribution/', LayerDistributionView.as_view()),
    path('workface-boreholes/', WorkfaceBoreholesView.as_view()),
    path('borehole-depth-distribution/', BoreholeDepthDistributionView.as_view()),
]
