from rest_framework.response import Response
from rest_framework.views import APIView
from .services import get_raster_detail, get_raster_file_response, get_raster_list


class RasterListView(APIView):
    def get(self, request):
        """返回本地 TIFF 解析得到的专题图层列表。"""
        return Response(get_raster_list())


class RasterDetailView(APIView):
    def get(self, request, raster_id: str):
        """返回单个 TIFF 专题图层详情。"""
        detail = get_raster_detail(raster_id)
        return Response(detail or {}, status=200 if detail else 404)


class RasterFileView(APIView):
    def get(self, request, raster_id: str):
        """返回 TIFF 原始文件流。"""
        return get_raster_file_response(raster_id)
