from __future__ import annotations

from pathlib import Path
from typing import Any
import struct

from pyproj import CRS, Transformer

from config import DATA_DIR

TIF_DIR = DATA_DIR / 'tif'
MINE_PRJ_FILE = DATA_DIR / 'shp' / '锦界矿边界.prj'
FALLBACK_SOURCE_CRS = ('EPSG:4326', 'EPSG:32649', 'EPSG:32648', 'EPSG:4547', 'EPSG:4548')


def is_lonlat(lon: float, lat: float) -> bool:
    return -180 <= lon <= 180 and -90 <= lat <= 90


def read_source_crs_candidates() -> list[tuple[str, Transformer]]:
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
    values = [float(line.strip()) for line in tfw_path.read_text(encoding='utf-8', errors='ignore').splitlines() if line.strip()]
    if len(values) != 6:
        raise ValueError(f'Invalid TFW format: {tfw_path.name}')
    return values[0], values[1], values[2], values[3], values[4], values[5]


def read_uint(data: bytes, endian: str) -> int:
    if len(data) == 2:
        return struct.unpack(f'{endian}H', data)[0]
    if len(data) == 4:
        return struct.unpack(f'{endian}I', data)[0]
    if len(data) == 8:
        return struct.unpack(f'{endian}Q', data)[0]
    raise ValueError(f'Unsupported integer length: {len(data)}')


def extract_inline_value(value_bytes: bytes, byte_count: int, endian: str) -> bytes:
    if endian == '<':
        return value_bytes[:byte_count]
    return value_bytes[4 - byte_count :]


def read_tiff_size(tif_path: Path) -> tuple[int, int]:
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
        raise ValueError(f'Cannot read TIFF size: {tif_path.name}')
    return width, height


def to_wgs84(x: float, y: float, transformer: Transformer) -> tuple[float, float] | None:
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

    raise ValueError('Cannot convert TIFF bounds to WGS84')


def build_legend() -> list[dict[str, str]]:
    return [
        {'label': '稳定区', 'value': '0 - 12 mm', 'color': '#23d18b'},
        {'label': '轻微沉降', 'value': '12 - 28 mm', 'color': '#f2c94c'},
        {'label': '显著沉降', 'value': '28 - 45 mm', 'color': '#f2994a'},
        {'label': '重点预警', 'value': '> 45 mm', 'color': '#eb5757'},
    ]


def build_raster_item(tif_path: Path) -> dict[str, Any] | None:
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
        'description': f'Generated from local TIFF file {tif_path.name}; source CRS {source_crs}',
        'time_tag': tif_path.stem,
        'source_crs': source_crs,
        'source_file': tif_path.name,
    }


def list_tif_files() -> list[Path]:
    if not TIF_DIR.exists():
        return []
    return sorted([*TIF_DIR.glob('*.tif'), *TIF_DIR.glob('*.tiff')])


def import_rasters_from_tif(remove_missing: bool = True) -> dict[str, int]:
    del remove_missing
    return {'rasters': len(get_raster_list())}


def get_raster_list() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for tif_path in list_tif_files():
        item = build_raster_item(tif_path)
        if item:
            rows.append(item)
    return rows


def get_raster_detail(raster_id: str) -> dict[str, Any] | None:
    for item in get_raster_list():
        if item['id'] == raster_id:
            return item
    return None


def build_tif_file_map() -> dict[str, Path]:
    result: dict[str, Path] = {}
    for tif_path in list_tif_files():
        result[tif_path.stem] = tif_path
    return result


def get_raster_file_path(raster_id: str) -> Path | None:
    tif_path = build_tif_file_map().get(raster_id)
    if not tif_path or not tif_path.exists():
        return None
    return tif_path
