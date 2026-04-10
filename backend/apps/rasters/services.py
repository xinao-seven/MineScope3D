"""TIFF 栅格文件扫描与直连加载服务（不依赖数据库）。"""
from pathlib import Path
from typing import Any
import struct

from django.conf import settings
from django.http import FileResponse, Http404
from pyproj import CRS, Transformer

DATA_DIR = Path(settings.BASE_DIR) / 'data'
TIF_DIR = DATA_DIR / 'tif'
MINE_PRJ_FILE = DATA_DIR / 'shp' / '锦界矿边界.prj'
FALLBACK_SOURCE_CRS = ('EPSG:4326', 'EPSG:32649', 'EPSG:32648', 'EPSG:4547', 'EPSG:4548')


def is_lonlat(lon: float, lat: float) -> bool:
    """判断坐标是否已经是经纬度。"""
    return -180 <= lon <= 180 and -90 <= lat <= 90


def read_source_crs_candidates() -> list[tuple[str, Transformer]]:
    """读取 TIFF 可能使用的源坐标系候选。"""
    crs_candidates: list[CRS] = []
    if MINE_PRJ_FILE.exists():
        prj_text = MINE_PRJ_FILE.read_text(encoding='utf-8', errors='ignore').strip()
        if prj_text:
            crs_candidates.append(CRS.from_wkt(prj_text))
    for crs_text in FALLBACK_SOURCE_CRS:
        crs_candidates.append(CRS.from_string(crs_text))

    result: list[tuple[str, Transformer]] = []
    seen = set()
    for crs in crs_candidates:
        crs_text = crs.to_string()
        if crs_text in seen:
            continue
        seen.add(crs_text)
        result.append((crs_text, Transformer.from_crs(crs, CRS.from_epsg(4326), always_xy=True)))
    return result


def read_tfw(tfw_path: Path) -> tuple[float, float, float, float, float, float]:
    """读取 TFW 六参数。"""
    values = [float(line.strip()) for line in tfw_path.read_text(encoding='utf-8', errors='ignore').splitlines() if line.strip()]
    if len(values) != 6:
        raise ValueError(f'TFW 文件格式错误：{tfw_path.name}')
    return values[0], values[1], values[2], values[3], values[4], values[5]


def read_uint(data: bytes, endian: str) -> int:
    """按 TIFF 字节序读取无符号整数。"""
    if len(data) == 2:
        return struct.unpack(f'{endian}H', data)[0]
    if len(data) == 4:
        return struct.unpack(f'{endian}I', data)[0]
    if len(data) == 8:
        return struct.unpack(f'{endian}Q', data)[0]
    raise ValueError(f'不支持的整数长度：{len(data)}')


def extract_inline_value(value_bytes: bytes, byte_count: int, endian: str) -> bytes:
    """读取 TIFF IFD 内联值。"""
    if endian == '<':
        return value_bytes[:byte_count]
    return value_bytes[4 - byte_count:]


def read_tiff_size(tif_path: Path) -> tuple[int, int]:
    """读取 TIFF 宽高。"""
    type_sizes = {1: 1, 2: 1, 3: 2, 4: 4, 5: 8, 6: 1, 7: 1, 8: 2, 9: 4, 10: 8, 11: 4, 12: 8}
    width: int | None = None
    height: int | None = None
    with tif_path.open('rb') as file:
        header = file.read(8)
        endian = '<' if header[:2] == b'II' else '>'
        offset = struct.unpack(f'{endian}I', header[4:8])[0]
        file.seek(offset)
        entry_count = struct.unpack(f'{endian}H', file.read(2))[0]
        for _index in range(entry_count):
            entry = file.read(12)
            tag = struct.unpack(f'{endian}H', entry[0:2])[0]
            field_type = struct.unpack(f'{endian}H', entry[2:4])[0]
            count = struct.unpack(f'{endian}I', entry[4:8])[0]
            if tag not in (256, 257) or field_type not in type_sizes:
                continue
            unit = type_sizes[field_type]
            total_size = unit * count
            if total_size <= 4:
                value_bytes = extract_inline_value(entry[8:12], unit, endian)
            else:
                value_offset = struct.unpack(f'{endian}I', entry[8:12])[0]
                current = file.tell()
                file.seek(value_offset)
                value_bytes = file.read(unit)
                file.seek(current)
            value = read_uint(value_bytes, endian)
            if tag == 256:
                width = value
            if tag == 257:
                height = value
    if width is None or height is None:
        raise ValueError(f'无法读取 TIFF 宽高：{tif_path.name}')
    return width, height


def to_wgs84(x: float, y: float, transformer: Transformer) -> tuple[float, float] | None:
    """将 TIFF 坐标点转换为 WGS84。"""
    if is_lonlat(x, y):
        return x, y
    lon, lat = transformer.transform(x, y)
    if is_lonlat(lon, lat):
        return lon, lat
    lon_swapped, lat_swapped = transformer.transform(y, x)
    if is_lonlat(lon_swapped, lat_swapped):
        return lon_swapped, lat_swapped
    return None


def compute_bounds(width: int, height: int, tfw: tuple[float, float, float, float, float, float]) -> tuple[dict[str, float], str]:
    """根据 TFW 和影像尺寸计算 WGS84 范围。"""
    a, d, b, e, c, f = tfw
    edge_x = c - (a + b) / 2.0
    edge_y = f - (d + e) / 2.0
    corners = [(0, 0), (width, 0), (0, height), (width, height)]

    for crs_text, transformer in read_source_crs_candidates():
        points = []
        for col, row in corners:
            point = to_wgs84(edge_x + a * col + b * row, edge_y + d * col + e * row, transformer)
            if point is None:
                points = []
                break
            points.append(point)
        if points:
            lons = [point[0] for point in points]
            lats = [point[1] for point in points]
            return {
                'west': round(min(lons), 8),
                'south': round(min(lats), 8),
                'east': round(max(lons), 8),
                'north': round(max(lats), 8),
            }, crs_text
    raise ValueError('无法将 TIFF 范围转换为 WGS84')


def build_legend() -> list[dict[str, str]]:
    """返回第一版专题图默认图例。"""
    return [
        {'label': '稳定区', 'value': '0 - 12 mm', 'color': '#23d18b'},
        {'label': '轻微沉降', 'value': '12 - 28 mm', 'color': '#f2c94c'},
        {'label': '显著沉降', 'value': '28 - 45 mm', 'color': '#f2994a'},
        {'label': '重点预警', 'value': '> 45 mm', 'color': '#eb5757'},
    ]


def build_raster_item(tif_path: Path) -> dict[str, Any] | None:
    """将单个 TIFF 文件转换为 API 返回对象。"""
    tfw_path = tif_path.with_suffix('.tfw')
    if not tfw_path.exists():
        return None
    width, height = read_tiff_size(tif_path)
    bounds, source_crs = compute_bounds(width, height, read_tfw(tfw_path))
    raster_id = tif_path.stem
    return {
        'id': raster_id,
        'name': tif_path.stem,
        'type': 'subsidence',
        'url': f'/api/rasters/files/{raster_id}/',
        'bounds': bounds,
        'opacity': 0.62,
        'legend_config': build_legend(),
        'description': f'由本地 TIFF 文件 {tif_path.name} 解析生成，源坐标系 {source_crs}',
        'time_tag': tif_path.stem,
        'source_crs': source_crs,
        'source_file': tif_path.name,
    }


def list_tif_files() -> list[Path]:
    """扫描本地 TIFF 文件。"""
    if not TIF_DIR.exists():
        return []
    return sorted([*TIF_DIR.glob('*.tif'), *TIF_DIR.glob('*.tiff')])


def import_rasters_from_tif(remove_missing: bool = True) -> dict[str, int]:
    """兼容旧命令：当前仅执行本地 TIFF 扫描，不入库。"""
    del remove_missing
    return {'rasters': len(get_raster_list())}


def get_raster_list() -> list[dict[str, Any]]:
    """读取本地 TIFF 解析得到的专题图层。"""
    rows: list[dict[str, Any]] = []
    for tif_path in list_tif_files():
        item = build_raster_item(tif_path)
        if item:
            rows.append(item)
    return rows


def get_raster_detail(raster_id: str) -> dict[str, Any] | None:
    """按编号返回单个本地 TIFF 专题图层。"""
    for item in get_raster_list():
        if item['id'] == raster_id:
            return item
    return None


def build_tif_file_map() -> dict[str, Path]:
    """构造 raster_id 到本地 TIFF 文件路径的映射。"""
    result: dict[str, Path] = {}
    for tif_path in list_tif_files():
        result[tif_path.stem] = tif_path
    return result


def get_raster_file_response(raster_id: str) -> FileResponse:
    """返回可直接读取的 TIFF 文件流。"""
    tif_path = build_tif_file_map().get(raster_id)
    if not tif_path or not tif_path.exists():
        raise Http404('TIFF 文件不存在')

    response = FileResponse(tif_path.open('rb'), content_type='image/tiff')
    response['Content-Disposition'] = f'inline; filename="{tif_path.name}"'
    return response
