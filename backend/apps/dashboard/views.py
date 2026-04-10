from collections import Counter

from rest_framework.response import Response
from rest_framework.views import APIView
from apps.boreholes.services.excel_import_service import load_boreholes
from apps.boundaries.services import get_boundary_list
from apps.rasters.services import get_raster_list


class DashboardOverviewView(APIView):
    def get(self, request):
        """返回基于本地文件的总览统计。"""
        boreholes = load_boreholes()
        boundaries = get_boundary_list(boreholes=boreholes)
        rasters = get_raster_list()
        return Response({
            'boreholeTotal': len(boreholes),
            'workfaceTotal': len({item['workface_name'] for item in boreholes if item['workface_name']}),
            'boundaryTotal': len(boundaries),
            'rasterTotal': len(rasters),
        })


class LayerDistributionView(APIView):
    def get(self, request):
        """返回本地钻孔分层类型占比。"""
        counter: Counter[str] = Counter()
        for borehole in load_boreholes():
            for layer in borehole['layers']:
                if layer['thickness'] > 0:
                    counter[layer['layer_name']] += 1
        return Response([{'name': name, 'value': value} for name, value in counter.most_common()])


class WorkfaceBoreholesView(APIView):
    def get(self, request):
        """返回本地工作面边界内的钻孔数量统计。"""
        boreholes = load_boreholes()
        workfaces = [
            item
            for item in get_boundary_list(boundary_type='workface', boreholes=boreholes)
            if item['borehole_count'] > 0
        ]
        rows = sorted(workfaces, key=lambda item: item['borehole_count'], reverse=True)[:14]
        if rows:
            return Response([{'name': item['name'], 'value': item['borehole_count']} for item in rows])
        counter = Counter(item['workface_name'] or '本地钻孔数据' for item in boreholes)
        return Response([{'name': name, 'value': value} for name, value in counter.items()])


class BoreholeDepthDistributionView(APIView):
    def get(self, request):
        """返回本地钻孔动态深度区间分布。"""
        boreholes = load_boreholes()
        ranges = build_depth_ranges(boreholes)
        return Response([build_depth_range(row, boreholes) for row in ranges])


def build_depth_ranges(boreholes: list[dict]) -> list[tuple[str, int, int | None]]:
    """根据真实钻孔深度生成 20 米粒度分箱。"""
    depths = [item['depth_total'] for item in boreholes if item['depth_total'] > 0]
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


def build_depth_range(row: tuple[str, int, int | None], boreholes: list[dict]) -> dict:
    """统计单个深度区间的钻孔数量。"""
    name, min_depth, max_depth = row
    value = 0
    for borehole in boreholes:
        depth = borehole['depth_total']
        if depth >= min_depth and (max_depth is None or depth < max_depth):
            value += 1
    return {'name': name, 'value': value}
