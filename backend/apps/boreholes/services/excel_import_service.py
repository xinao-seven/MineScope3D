"""钻孔 Excel 本地文件解析服务。"""
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import openpyxl
from django.conf import settings
from pyproj import CRS, Transformer

FIELD_MAP = {
    'borehole_name': '钻孔名称',
    'layer_name': '地层名称',
    'depth': '深度',
    'thickness': '厚度',
}

LAYER_COLORS = {
    '煤': '#f2c94c',
    '砂': '#56ccf2',
    '泥': '#bb6bd9',
    '土': '#f2994a',
    '风积': '#6fcf97',
}

DATA_DIR = Path(settings.BASE_DIR) / 'data'
BOREHOLE_DIR = DATA_DIR / 'boreholes'
LOCATION_DIR = DATA_DIR / 'location'
MINE_PRJ_FILE = DATA_DIR / 'shp' / '锦界矿边界.prj'
DEFAULT_SOURCE_CRS = 'EPSG:2421'


@dataclass
class BoreholeLocation:
    name: str
    x: float
    y: float
    z: float


def normalize_name(name: str) -> str:
    """标准化钻孔名称以提升跨表匹配容错。"""
    return ''.join(char for char in str(name).strip().upper() if char.isalnum())


def read_cell_text(value: Any) -> str:
    """将 Excel 单元格内容转换为清理后的文本。"""
    if value is None:
        return ''
    return str(value).strip()


def read_float(value: Any, default: float = 0) -> float:
    """安全读取 Excel 数值单元格。"""
    try:
        if value is None or value == '':
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def discover_layer_files() -> list[Path]:
    """扫描本地钻孔分层 Excel 文件。"""
    if not BOREHOLE_DIR.exists():
        return []
    return sorted(path for path in BOREHOLE_DIR.glob('*.xlsx') if not path.name.startswith('~$'))


def discover_location_file() -> Path | None:
    """扫描本地钻孔位置 Excel 文件。"""
    if not LOCATION_DIR.exists():
        return None
    return next((path for path in sorted(LOCATION_DIR.glob('*.xlsx')) if not path.name.startswith('~$')), None)


def build_transformer() -> Transformer:
    """根据矿区 PRJ 或默认坐标系构造 WGS84 转换器。"""
    source_crs = CRS.from_string(DEFAULT_SOURCE_CRS)
    if MINE_PRJ_FILE.exists():
        prj_text = MINE_PRJ_FILE.read_text(encoding='utf-8', errors='ignore').strip()
        if prj_text:
            source_crs = CRS.from_wkt(prj_text)
    return Transformer.from_crs(source_crs, CRS.from_epsg(4326), always_xy=True)


def is_lonlat(lon: float, lat: float) -> bool:
    """判断坐标是否已经是经纬度。"""
    return -180 <= lon <= 180 and -90 <= lat <= 90


def convert_point_to_wgs84(x: float, y: float, transformer: Transformer) -> tuple[float, float] | None:
    """将钻孔平面坐标转换为 WGS84 坐标。"""
    if is_lonlat(x, y):
        return x, y
    lon, lat = transformer.transform(x, y)
    if is_lonlat(lon, lat):
        return lon, lat
    lon_swapped, lat_swapped = transformer.transform(y, x)
    if is_lonlat(lon_swapped, lat_swapped):
        return lon_swapped, lat_swapped
    return None


def load_location_index() -> dict[str, BoreholeLocation]:
    """读取钻孔位置表并返回按名称索引的位置字典。"""
    location_file = discover_location_file()
    if not location_file:
        return {}

    workbook = openpyxl.load_workbook(location_file, read_only=True, data_only=True)
    sheet = workbook.active
    header = [read_cell_text(value) for value in next(sheet.iter_rows(min_row=1, max_row=1, values_only=True))]
    column_index = {name: index for index, name in enumerate(header) if name}
    required = {'name', 'x', 'y', 'z'}
    missing = required - set(column_index)
    if missing:
        raise ValueError(f'钻孔位置表缺少列：{missing}')

    result: dict[str, BoreholeLocation] = {}
    for row in sheet.iter_rows(min_row=2, values_only=True):
        name = read_cell_text(row[column_index['name']])
        if not name:
            continue
        result[name] = BoreholeLocation(
            name=name,
            x=read_float(row[column_index['x']]),
            y=read_float(row[column_index['y']]),
            z=read_float(row[column_index['z']]),
        )
    return result


def match_location(name: str, locations: dict[str, BoreholeLocation]) -> BoreholeLocation | None:
    """按原始名称和标准化名称匹配钻孔位置。"""
    if name in locations:
        return locations[name]
    normalized = normalize_name(name)
    for location_name, location in locations.items():
        if normalize_name(location_name) == normalized:
            return location
    return None


def pick_layer_color(layer_name: str) -> str:
    """按地层名称给出分层默认颜色。"""
    for keyword, color in LAYER_COLORS.items():
        if keyword in layer_name:
            return color
    return '#23d18b'


def parse_layer_file(layer_file: Path) -> dict[str, list[dict[str, Any]]]:
    """解析单个钻孔分层 Excel 文件。"""
    workbook = openpyxl.load_workbook(layer_file, read_only=True, data_only=True)
    sheet = workbook.active
    header = [read_cell_text(value) for value in next(sheet.iter_rows(min_row=1, max_row=1, values_only=True))]
    column_index = {name: index for index, name in enumerate(header) if name}
    missing = [field for field in FIELD_MAP.values() if field not in column_index]
    if missing:
        raise ValueError(f'{layer_file.name} 缺少列：{missing}')

    result: dict[str, list[dict[str, Any]]] = {}
    for row in sheet.iter_rows(min_row=2, values_only=True):
        borehole_name = read_cell_text(row[column_index[FIELD_MAP['borehole_name']]])
        layer_name = read_cell_text(row[column_index[FIELD_MAP['layer_name']]])
        if not borehole_name or not layer_name:
            continue
        bottom_depth = read_float(row[column_index[FIELD_MAP['depth']]])
        thickness = read_float(row[column_index[FIELD_MAP['thickness']]])
        layer = {
            'layer_name': layer_name,
            'top_depth': round(max(bottom_depth - thickness, 0), 4),
            'thickness': round(thickness, 4),
            'bottom_depth': round(bottom_depth, 4),
            'color': pick_layer_color(layer_name),
        }
        result.setdefault(borehole_name, []).append(layer)
    return result


def load_layer_groups() -> dict[str, list[dict[str, Any]]]:
    """加载并合并全部钻孔分层文件。"""
    merged: dict[str, list[dict[str, Any]]] = {}
    for layer_file in discover_layer_files():
        parsed = parse_layer_file(layer_file)
        for borehole_name, layers in parsed.items():
            merged.setdefault(borehole_name, []).extend(layers)
    return merged


def build_borehole_item(index: int, name: str, layers: list[dict[str, Any]], location: BoreholeLocation | None, transformer: Transformer) -> dict[str, Any]:
    """组装前端使用的钻孔对象。"""
    sorted_layers = sorted(layers, key=lambda item: (item['top_depth'], item['bottom_depth']))
    for sort_order, layer in enumerate(sorted_layers, start=1):
        layer['id'] = f'{name}-{sort_order}'
        layer['sort_order'] = sort_order

    lon = 0.0
    lat = 0.0
    elevation = 0.0
    if location:
        converted = convert_point_to_wgs84(location.x, location.y, transformer)
        if converted:
            lon, lat = converted
            elevation = location.z

    return {
        'id': str(index),
        'borehole_code': name,
        'name': name,
        'longitude': round(lon, 8),
        'latitude': round(lat, 8),
        'elevation': round(elevation, 3),
        'depth_total': max((layer['bottom_depth'] for layer in sorted_layers), default=0),
        'workface_name': '本地钻孔数据',
        'remark': '由 backend/data/boreholes 与 backend/data/location 解析',
        'layers': sorted_layers,
    }


def load_boreholes() -> list[dict[str, Any]]:
    """加载全部本地钻孔数据。"""
    transformer = build_transformer()
    locations = load_location_index()
    layer_groups = load_layer_groups()
    result = []
    for index, (name, layers) in enumerate(sorted(layer_groups.items()), start=1):
        location = match_location(name, locations)
        result.append(build_borehole_item(index, name, layers, location, transformer))
    return result


def get_borehole_list(keyword: str | None = None, workface: str | None = None) -> list[dict[str, Any]]:
    """按条件返回钻孔列表。"""
    boreholes = load_boreholes()
    if keyword:
        boreholes = [item for item in boreholes if keyword.lower() in item['name'].lower()]
    if workface:
        boreholes = [item for item in boreholes if item['workface_name'] == workface]
    return boreholes


def get_borehole_detail(borehole_id: str) -> dict[str, Any] | None:
    """按编号返回单个钻孔详情。"""
    return next((item for item in load_boreholes() if item['id'] == str(borehole_id)), None)


def get_borehole_layers(borehole_id: str) -> list[dict[str, Any]]:
    """按编号返回单个钻孔分层。"""
    detail = get_borehole_detail(borehole_id)
    return detail['layers'] if detail else []


def get_borehole_geojson() -> dict[str, Any]:
    """返回钻孔 GeoJSON 点集。"""
    features = []
    for item in load_boreholes():
        if item['longitude'] == 0 and item['latitude'] == 0:
            continue
        features.append({
            'type': 'Feature',
            'geometry': {'type': 'Point', 'coordinates': [item['longitude'], item['latitude'], item['elevation']]},
            'properties': {
                'id': item['id'],
                'borehole_code': item['borehole_code'],
                'name': item['name'],
                'depth_total': item['depth_total'],
                'workface_name': item['workface_name'],
            },
        })
    return {'type': 'FeatureCollection', 'features': features}
