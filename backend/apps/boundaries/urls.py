from django.urls import path
from .views import BoundaryDetailView, BoundaryGeoJsonView, BoundaryListView

urlpatterns = [
    path('', BoundaryListView.as_view()),
    path('geojson/', BoundaryGeoJsonView.as_view()),
    path('<str:boundary_id>/', BoundaryDetailView.as_view()),
]
