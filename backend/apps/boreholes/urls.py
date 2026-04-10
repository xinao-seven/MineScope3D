from django.urls import path
from .views import BoreholeDetailView, BoreholeGeoJsonView, BoreholeLayerView, BoreholeListView

urlpatterns = [
    path('', BoreholeListView.as_view()),
    path('geojson/', BoreholeGeoJsonView.as_view()),
    path('<str:borehole_id>/', BoreholeDetailView.as_view()),
    path('<str:borehole_id>/layers/', BoreholeLayerView.as_view()),
]
