from __future__ import annotations

from pathlib import Path
from typing import Any
from uuid import NAMESPACE_URL, uuid5

import shapefile
from pyproj import CRS, Geod, Transformer

from config import DATA_DIR

SHP_DIR = DATA_DIR / 'shp'
SHP_CONFIG = [
    {
        'path': SHP_DIR / '锦界矿边界.shp',
        'type': 'mine',
        'source': 'mine-area',
        'fallback_name': '锦界矿边界',
    },
    {
        'path': SHP_DIR / '开采工作面.shp',
        'type': 'workface',
        'source': 'working-face',
        'fallback_name': '开采工作面',
    },
]
ENCODING_CANDIDATES = ('utf-8', 'gbk', 'gb18030', 'latin1')
GEOD = Geod(ellps='WGS84')


def to_json_value(value: Any) -> Any:
    if hasattr(value, 'isoformat'):
        return value.isoformat()
    if isinstance(value, bytes):
        return value.decode('utf-8', errors='replace')
    return value


def read_source_crs(shp_path: Path) -> CRS:
    prj_path = shp_path.with_suffix('.prj')
    if prj_path.exists():
        prj_text = prj_path.read_text(encoding='utf-8', errors='ignore').strip()
        if prj_text:
            return CRS.from_wkt(prj_text)
    return CRS.from_epsg(4326)


def build_transformer(source_crs: CRS) -> Transformer:
    return Transformer.from_crs(source_crs, CRS.from_epsg(4326), always_xy=True)


def detect_encodings(shp_path: Path) -> list[str]:
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
    last_error: Exception | None = None
    for encoding in detect_encodings(shp_path):
        try:
            return shapefile.Reader(str(shp_path), encoding=encoding, encodingErrors='replace')
        except Exception as exc:
            last_error = exc
    raise RuntimeError(f'Failed to read SHP: {last_error}')


def split_parts(points: list[Any], parts: list[int]) -> list[list[Any]]:
    boundaries = list(parts) + [len(points)]
    return [points[boundaries[index] : boundaries[index + 1]] for index in range(len(boundaries) - 1)]


def ensure_ring_closed(coords: list[list[float]]) -> list[list[float]]:
    if coords and coords[0] != coords[-1]:
        return coords + [coords[0]]
    return coords


def convert_point(point: Any, transformer: Transformer) -> list[float]:
    lon, lat = transformer.transform(point[0], point[1])
    return [round(float(lon), 8), round(float(lat), 8)]


def shape_to_coordinate_parts(shape: shapefile.Shape, transformer: Transformer) -> list[list[list[float]]]:
    converted_parts = []
    for part in split_parts(shape.points, list(shape.parts)):
        converted = [convert_point(point, transformer) for point in part]
        if converted:
            converted_parts.append(converted)
    return converted_parts


def shape_to_geojson(shape: shapefile.Shape, transformer: Transformer) -> dict[str, Any] | None:
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
    for key in ('name', 'NAME', '名称', '工作面', '工作面名', '工作面名称'):
        value = properties.get(key)
        if value:
            return str(value)
    return f'{fallback}-{index}'


def build_boundary_id(boundary_type: str, name: str, index: int) -> str:
    return str(uuid5(NAMESPACE_URL, f'minescope3d:boundary:{boundary_type}:{name}:{index}'))


def read_outer_ring(geometry: dict[str, Any]) -> list[list[float]]:
    if geometry['type'] == 'Polygon':
        return geometry['coordinates'][0]
    if geometry['type'] == 'LineString':
        return geometry['coordinates']
    if geometry['type'] == 'MultiLineString':
        return geometry['coordinates'][0]
    return []


def point_in_polygon(lon: float, lat: float, polygon: list[list[float]]) -> bool:
    if len(polygon) < 3:
        return False

    inside = False
    for index in range(len(polygon)):
        x1, y1 = polygon[index]
        x2, y2 = polygon[(index + 1) % len(polygon)]
        if (y1 > lat) == (y2 > lat):
            continue
        x_intersection = (x2 - x1) * (lat - y1) / ((y2 - y1) or 1e-12) + x1
        if lon < x_intersection:
            inside = not inside
    return inside


def count_boreholes_in_polygon(polygon: list[list[float]], boreholes: list[dict[str, Any]]) -> int:
    total = 0
    for borehole in boreholes:
        lon = float(borehole.get('longitude', 0) or 0)
        lat = float(borehole.get('latitude', 0) or 0)
        if lon == 0 and lat == 0:
            continue
        if point_in_polygon(lon, lat, polygon):
            total += 1
    return total


def compute_area_perimeter(geometry: dict[str, Any]) -> tuple[float, float]:
    if geometry['type'] == 'Polygon':
        ring = geometry['coordinates'][0]
        if len(ring) < 3:
            return 0.0, 0.0
        lons = [point[0] for point in ring]
        lats = [point[1] for point in ring]
        area, perimeter = GEOD.polygon_area_perimeter(lons, lats)
        return round(abs(area) / 1_000_000, 3), round(abs(perimeter), 3)

    if geometry['type'] == 'LineString':
        line = geometry['coordinates']
        if len(line) < 2:
            return 0.0, 0.0
        lons = [point[0] for point in line]
        lats = [point[1] for point in line]
        return 0.0, round(abs(GEOD.line_length(lons, lats)), 3)

    if geometry['type'] == 'MultiLineString':
        total = 0.0
        for line in geometry['coordinates']:
            if len(line) < 2:
                continue
            lons = [point[0] for point in line]
            lats = [point[1] for point in line]
            total += abs(GEOD.line_length(lons, lats))
        return 0.0, round(total, 3)

    return 0.0, 0.0


def parse_boundaries_from_shp(boreholes: list[dict[str, Any]] | None = None) -> list[dict[str, Any]]:
    if boreholes is None:
        from services.boreholes import get_borehole_list

        boreholes = get_borehole_list()

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
            name = pick_name(properties, config['fallback_name'], item_index)
            coordinates = read_outer_ring(geometry)
            area, perimeter = compute_area_perimeter(geometry)
            borehole_count = 0
            if geometry['type'] == 'Polygon' and config['type'] in {'mine', 'workface'}:
                borehole_count = count_boreholes_in_polygon(coordinates, boreholes)

            result.append(
                {
                    'id': build_boundary_id(config['type'], name, item_index),
                    'name': name,
                    'type': config['type'],
                    'area': area,
                    'perimeter': perimeter,
                    'borehole_count': borehole_count,
                    'properties': {'source': config['source'], 'sourceCrs': source_crs.to_string(), **properties},
                    'coordinates': coordinates,
                    'geometry': geometry,
                }
            )
            item_index += 1
    return result


def import_boundaries_from_shp(replace_existing: bool = True) -> dict[str, int]:
    del replace_existing
    return {'boundaries': len(parse_boundaries_from_shp())}


def get_boundary_list(
    boundary_type: str | None = None,
    boreholes: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    rows = parse_boundaries_from_shp(boreholes=boreholes)
    if boundary_type:
        rows = [row for row in rows if row['type'] == boundary_type]

    return [
        {
            'id': row['id'],
            'name': row['name'],
            'type': row['type'],
            'area': row['area'],
            'perimeter': row['perimeter'],
            'borehole_count': row['borehole_count'],
            'properties': row['properties'],
            'coordinates': row['coordinates'],
        }
        for row in rows
    ]


def get_boundary_detail(boundary_id: str) -> dict[str, Any] | None:
    for row in parse_boundaries_from_shp():
        if row['id'] == boundary_id:
            return {
                'id': row['id'],
                'name': row['name'],
                'type': row['type'],
                'area': row['area'],
                'perimeter': row['perimeter'],
                'borehole_count': row['borehole_count'],
                'properties': row['properties'],
                'coordinates': row['coordinates'],
            }
    return None


def get_boundary_geojson(boundary_type: str | None = None) -> dict[str, Any]:
    rows = parse_boundaries_from_shp()
    if boundary_type:
        rows = [row for row in rows if row['type'] == boundary_type]

    features = []
    for row in rows:
        features.append(
            {
                'type': 'Feature',
                'geometry': row['geometry'],
                'properties': {
                    'id': row['id'],
                    'name': row['name'],
                    'type': row['type'],
                    'area': row['area'],
                    'perimeter': row['perimeter'],
                    'borehole_count': row['borehole_count'],
                    'properties': row['properties'],
                },
            }
        )
    return {'type': 'FeatureCollection', 'features': features}
