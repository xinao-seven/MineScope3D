"""后端 API 路由配置。"""
from django.conf import settings
from django.conf.urls.static import static
from django.urls import include, path

urlpatterns = [
    path('api/boreholes/', include('apps.boreholes.urls')),
    path('api/boundaries/', include('apps.boundaries.urls')),
    path('api/rasters/', include('apps.rasters.urls')),
    path('api/dashboard/', include('apps.dashboard.urls')),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
