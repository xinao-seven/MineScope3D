from django.urls import path
from .views import RasterDetailView, RasterFileView, RasterListView

urlpatterns = [
    path('files/<str:raster_id>/', RasterFileView.as_view()),
    path('', RasterListView.as_view()),
    path('<str:raster_id>/', RasterDetailView.as_view()),
]
