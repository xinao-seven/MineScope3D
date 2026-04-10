from rest_framework.response import Response
from rest_framework.views import APIView
from .services import get_boundary_detail, get_boundary_geojson, get_boundary_list


class BoundaryListView(APIView):
    def get(self, request):
        """返回数据库中的边界列表。"""
        return Response(get_boundary_list(boundary_type=request.query_params.get('type')))


class BoundaryDetailView(APIView):
    def get(self, request, boundary_id: str):
        """返回单个边界详情。"""
        detail = get_boundary_detail(boundary_id)
        return Response(detail or {}, status=200 if detail else 404)


class BoundaryGeoJsonView(APIView):
    def get(self, request):
        """返回边界 GeoJSON 集合。"""
        return Response(get_boundary_geojson(boundary_type=request.query_params.get('type')))
