from collections import Counter

from django.db.models import Count
from rest_framework.response import Response
from rest_framework.views import APIView
from apps.boreholes.models import Borehole, BoreholeLayer
from apps.boundaries.models import BoundaryRegion
from apps.rasters.services import get_raster_list


class DashboardOverviewView(APIView):
    def get(self, request):
        """返回总览统计（TIFF 统计基于本地文件扫描）。"""
        return Response({
            'boreholeTotal': Borehole.objects.count(),
            'workfaceTotal': Borehole.objects.exclude(workface_name='').values('workface_name').distinct().count(),
            'boundaryTotal': BoundaryRegion.objects.count(),
            'rasterTotal': len(get_raster_list()),
        })


class LayerDistributionView(APIView):
    def get(self, request):
        """返回数据库中的钻孔分层类型占比。"""
        rows = (
            BoreholeLayer.objects
            .filter(thickness__gt=0)
            .values('layer_name')
            .annotate(value=Count('id'))
            .order_by('-value')
        )
        return Response([{'name': row['layer_name'], 'value': row['value']} for row in rows])


class WorkfaceBoreholesView(APIView):
    def get(self, request):
        """返回数据库中的工作面钻孔数量统计。"""
        rows = list(
            BoundaryRegion.objects
            .filter(type=BoundaryRegion.TYPE_WORKFACE, borehole_count__gt=0)
            .order_by('-borehole_count')[:14]
        )
        if rows:
            return Response([{'name': item.name, 'value': item.borehole_count} for item in rows])

        counter = Counter(
            value
            for value in Borehole.objects.values_list('workface_name', flat=True)
            if value
        )
        return Response([{'name': name, 'value': value} for name, value in counter.items()])


class BoreholeDepthDistributionView(APIView):
    def get(self, request):
        """返回数据库中的钻孔动态深度区间分布。"""
        depths = [depth for depth in Borehole.objects.values_list('depth_total', flat=True) if depth > 0]
        ranges = build_depth_ranges(depths)
        return Response([build_depth_range(row, depths) for row in ranges])


def build_depth_ranges(depths: list[float]) -> list[tuple[str, int, int | None]]:
    """根据真实钻孔深度生成 20 米粒度分箱。"""
    if not depths:
        return []
    min_depth = int(min(depths) // 20 * 20)
    max_depth = int(max(depths) // 20 * 20 + 20)
    ranges = []
    start = min_depth
    while start < max_depth:
        end = start + 20
        ranges.append((f'{start}-{end}m', start, end))
        start = end
    return ranges


def build_depth_range(row: tuple[str, int, int | None], depths: list[float]) -> dict:
    """统计单个深度区间的钻孔数量。"""
    name, min_depth, max_depth = row
    value = 0
    for depth in depths:
        if depth >= min_depth and (max_depth is None or depth < max_depth):
            value += 1
    return {'name': name, 'value': value}
