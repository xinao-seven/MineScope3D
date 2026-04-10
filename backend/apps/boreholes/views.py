from rest_framework.response import Response
from rest_framework.views import APIView
from .services.excel_import_service import get_borehole_detail, get_borehole_geojson, get_borehole_layers, get_borehole_list


class BoreholeListView(APIView):
    def get(self, request):
        """返回本地 Excel 解析得到的钻孔列表。"""
        return Response(get_borehole_list(keyword=request.query_params.get('keyword'), workface=request.query_params.get('workface')))


class BoreholeDetailView(APIView):
    def get(self, request, borehole_id: str):
        """返回单个钻孔详情。"""
        detail = get_borehole_detail(borehole_id)
        return Response(detail or {}, status=200 if detail else 404)


class BoreholeLayerView(APIView):
    def get(self, request, borehole_id: str):
        """返回单个钻孔分层列表。"""
        return Response(get_borehole_layers(borehole_id))


class BoreholeGeoJsonView(APIView):
    def get(self, request):
        """返回钻孔 GeoJSON 点集。"""
        return Response(get_borehole_geojson())
