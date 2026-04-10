from django.urls import path
from .views import RasterDetailView, RasterListView

urlpatterns = [
    path('', RasterListView.as_view()),
    path('<str:raster_id>/', RasterDetailView.as_view()),
]
