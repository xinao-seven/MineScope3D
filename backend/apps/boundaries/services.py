"""SHP 边界导入与数据库查询服务。"""
from pathlib import Path
from typing import Any
import json

import shapefile
from django.conf import settings
from django.contrib.gis.geos import GEOSGeometry
from django.db import transaction
from pyproj import CRS, Transformer

from apps.boreholes.models import Borehole
from apps.boundaries.models import BoundaryRegion
from apps.boundaries.serializers import BoundaryRegionSerializer

DATA_DIR = Path(settings.BASE_DIR) / 'data'
SHP_DIR = DATA_DIR / 'shp'
SHP_CONFIG = [
    {'path': SHP_DIR / '锦界矿边界.shp', 'type': 'mine', 'source': 'mine-area', 'fallback_name': '锦界矿边界'},
    {'path': SHP_DIR / '开采工作面.shp', 'type': 'workface', 'source': 'working-face', 'fallback_name': '开采工作面'},
]
ENCODING_CANDIDATES = ('utf-8', 'gbk', 'gb18030', 'latin1')


def to_json_value(value: Any) -> Any:
    """将 DBF 字段值转换为可 JSON 序列化的值。"""
    if hasattr(value, 'isoformat'):
        return value.isoformat()
    if isinstance(value, bytes):
        return value.decode('utf-8', errors='replace')
    return value


def read_source_crs(shp_path: Path) -> CRS:
    """读取 SHP 对应 PRJ 坐标系。"""
    prj_path = shp_path.with_suffix('.prj')
    if prj_path.exists():
        prj_text = prj_path.read_text(encoding='utf-8', errors='ignore').strip()
        if prj_text:
            return CRS.from_wkt(prj_text)
    return CRS.from_epsg(4326)


def build_transformer(source_crs: CRS) -> Transformer:
    """构造 SHP 坐标到 WGS84 的转换器。"""
    return Transformer.from_crs(source_crs, CRS.from_epsg(4326), always_xy=True)


def detect_encodings(shp_path: Path) -> list[str]:
    """读取 CPG 编码并补充常见兜底编码。"""
    candidates: list[str] = []
    cpg_path = shp_path.with_suffix('.cpg')
    if cpg_path.exists():
        cpg_encoding = cpg_path.read_text(encoding='utf-8', errors='ignore').strip()
        if cpg_encoding:
            candidates.append(cpg_encoding)
    for encoding in ENCODING_CANDIDATES:
        if encoding not in candidates:
            candidates.append(encoding)
    return candidates


def open_reader(shp_path: Path) -> shapefile.Reader:
    """按候选编码打开 SHP 文件。"""
    last_error: Exception | None = None
    for encoding in detect_encodings(shp_path):
        try:
            return shapefile.Reader(str(shp_path), encoding=encoding, encodingErrors='replace')
        except Exception as exc:
            last_error = exc
    raise RuntimeError(f'无法读取 SHP 文件：{last_error}')


def split_parts(points: list[Any], parts: list[int]) -> list[list[Any]]:
    """按 SHP parts 索引切分坐标串。"""
    boundaries = list(parts) + [len(points)]
    return [points[boundaries[index]:boundaries[index + 1]] for index in range(len(boundaries) - 1)]


def ensure_ring_closed(coords: list[list[float]]) -> list[list[float]]:
    """确保 Polygon 外环首尾闭合。"""
    if coords and coords[0] != coords[-1]:
        return coords + [coords[0]]
    return coords


def convert_point(point: Any, transformer: Transformer) -> list[float]:
    """将单个 SHP 坐标点转换为经纬度。"""
    lon, lat = transformer.transform(point[0], point[1])
    return [round(float(lon), 8), round(float(lat), 8)]


def shape_to_coordinate_parts(shape: shapefile.Shape, transformer: Transformer) -> list[list[list[float]]]:
    """将 SHP 几何转换为经纬度坐标分段。"""
    converted_parts = []
    for part in split_parts(shape.points, list(shape.parts)):
        converted = [convert_point(point, transformer) for point in part]
        if converted:
            converted_parts.append(converted)
    return converted_parts


def shape_to_geojson(shape: shapefile.Shape, transformer: Transformer) -> dict[str, Any] | None:
    """将 SHP 几何转换为 GeoJSON geometry。"""
    parts = shape_to_coordinate_parts(shape, transformer)
    if not parts:
        return None
    if shape.shapeType in (shapefile.POLYGON, shapefile.POLYGONZ, shapefile.POLYGONM):
        return {'type': 'Polygon', 'coordinates': [ensure_ring_closed(part) for part in parts]}
    if shape.shapeType in (shapefile.POLYLINE, shapefile.POLYLINEZ, shapefile.POLYLINEM):
        if len(parts) == 1:
            return {'type': 'LineString', 'coordinates': parts[0]}
        return {'type': 'MultiLineString', 'coordinates': parts}
    if shape.shapeType in (shapefile.POINT, shapefile.POINTZ, shapefile.POINTM):
        return {'type': 'Point', 'coordinates': parts[0][0]}
    return None


def pick_name(properties: dict[str, Any], fallback: str, index: int) -> str:
    """从属性字段中选择边界名称。"""
    for key in ('name', 'NAME', '名称', '工作面', '工作面名', '工作面名称'):
        value = properties.get(key)
        if value:
            return str(value)
    return f'{fallback}-{index}'


def read_outer_ring(geometry: dict[str, Any]) -> list[list[float]]:
    """读取前端第一版可绘制的外环坐标。"""
    if geometry['type'] == 'Polygon':
        return geometry['coordinates'][0]
    if geometry['type'] == 'LineString':
        return geometry['coordinates']
    if geometry['type'] == 'MultiLineString':
        return geometry['coordinates'][0]
    return []


def count_boreholes_by_geometry(geometry: GEOSGeometry) -> int:
    """基于边界几何统计边界内钻孔数量。"""
    if geometry.geom_type in ('Polygon', 'MultiPolygon'):
        return Borehole.objects.filter(geom__within=geometry).count()
    return 0


def parse_boundaries_from_shp() -> list[dict[str, Any]]:
    """读取 SHP 并转换为入库对象列表。"""
    result = []
    item_index = 1
    for config in SHP_CONFIG:
        shp_path = config['path']
        if not shp_path.exists():
            continue
        source_crs = read_source_crs(shp_path)
        transformer = build_transformer(source_crs)
        reader = open_reader(shp_path)
        field_names = [field[0] for field in reader.fields[1:]]

        for shape_record in reader.shapeRecords():
            geometry = shape_to_geojson(shape_record.shape, transformer)
            if not geometry:
                continue
            properties = {
                field_name: to_json_value(value)
                for field_name, value in zip(field_names, list(shape_record.record))
            }
            geos_geom = GEOSGeometry(json.dumps(geometry), srid=4326)
            borehole_count = count_boreholes_by_geometry(geos_geom)
            result.append({
                'name': pick_name(properties, config['fallback_name'], item_index),
                'type': config['type'],
                'area': round(abs(shape_record.shape.area) / 1_000_000, 3) if hasattr(shape_record.shape, 'area') else 0,
                'perimeter': round(float(geos_geom.length), 6),
                'borehole_count': borehole_count,
                'properties': {'source': config['source'], 'sourceCrs': source_crs.to_string(), **properties},
                'source': config['source'],
                'source_crs': source_crs.to_string(),
                'geom': geos_geom,
            })
            item_index += 1
    return result


@transaction.atomic
def import_boundaries_from_shp(replace_existing: bool = True) -> dict[str, int]:
    """将本地 SHP 边界数据导入数据库。"""
    rows = parse_boundaries_from_shp()
    if replace_existing:
        BoundaryRegion.objects.all().delete()
    for row in rows:
        BoundaryRegion.objects.create(**row)
    return {'boundaries': len(rows)}


def get_boundary_list(boundary_type: str | None = None, boreholes: list[dict[str, Any]] | None = None) -> list[dict[str, Any]]:
    """按类型返回边界对象列表。"""
    del boreholes
    queryset = BoundaryRegion.objects.all()
    if boundary_type:
        queryset = queryset.filter(type=boundary_type)
    return BoundaryRegionSerializer(queryset, many=True).data


def get_boundary_detail(boundary_id: str) -> dict[str, Any] | None:
    """按编号返回边界详情。"""
    boundary = BoundaryRegion.objects.filter(id=boundary_id).first()
    if not boundary:
        return None
    return BoundaryRegionSerializer(boundary).data


def get_boundary_geojson(boundary_type: str | None = None) -> dict[str, Any]:
    """返回边界 GeoJSON 集合。"""
    queryset = BoundaryRegion.objects.all()
    if boundary_type:
        queryset = queryset.filter(type=boundary_type)

    features = []
    for item in queryset:
        features.append({
            'type': 'Feature',
            'geometry': json.loads(item.geom.geojson),
            'properties': {
                'id': str(item.id),
                'name': item.name,
                'type': item.type,
                'area': item.area,
                'perimeter': item.perimeter,
                'borehole_count': item.borehole_count,
                'properties': item.properties,
            },
        })
    return {'type': 'FeatureCollection', 'features': features}
