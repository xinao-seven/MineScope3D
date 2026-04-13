from __future__ import annotations

from collections import Counter
import mimetypes
from pathlib import Path
from typing import Any

from config import STATIC_DIR
from services.boreholes import get_borehole_list
from services.boundaries import get_boundary_list
from services.rasters import get_raster_list

TILESET_ROOT_DIR_CANDIDATES = (
    STATIC_DIR / '3dtiles',
    STATIC_DIR / 'tif-previews' / '3dtiles',
)


def get_dashboard_overview() -> dict[str, int]:
    boreholes = get_borehole_list()
    boundaries = get_boundary_list(boreholes=boreholes)
    workface_names = {item.get('workface_name', '') for item in boreholes if item.get('workface_name')}
    return {
        'boreholeTotal': len(boreholes),
        'workfaceTotal': len(workface_names),
        'boundaryTotal': len(boundaries),
        'rasterTotal': len(get_raster_list()),
    }


def get_layer_distribution() -> list[dict[str, Any]]:
    layer_counter: Counter[str] = Counter()
    for borehole in get_borehole_list():
        for layer in borehole.get('layers', []):
            thickness = float(layer.get('thickness', 0) or 0)
            if thickness <= 0:
                continue
            layer_name = str(layer.get('layer_name', '') or '').strip()
            if layer_name:
                layer_counter[layer_name] += 1

    return [
        {'name': name, 'value': value}
        for name, value in sorted(layer_counter.items(), key=lambda item: item[1], reverse=True)
    ]


def get_workface_boreholes() -> list[dict[str, Any]]:
    boreholes = get_borehole_list()
    rows = [
        {'name': item['name'], 'value': item['borehole_count']}
        for item in get_boundary_list(boundary_type='workface', boreholes=boreholes)
        if int(item.get('borehole_count', 0) or 0) > 0
    ]
    rows.sort(key=lambda item: item['value'], reverse=True)
    if rows:
        return rows[:14]

    counter = Counter(
        str(item.get('workface_name', '')).strip()
        for item in boreholes
        if str(item.get('workface_name', '')).strip()
    )
    return [{'name': name, 'value': value} for name, value in counter.items()]


def build_depth_ranges(depths: list[float]) -> list[tuple[str, int, int | None]]:
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


def build_depth_range(row: tuple[str, int, int | None], depths: list[float]) -> dict[str, Any]:
    name, min_depth, max_depth = row
    value = 0
    for depth in depths:
        if depth >= min_depth and (max_depth is None or depth < max_depth):
            value += 1
    return {'name': name, 'value': value}


def get_borehole_depth_distribution() -> list[dict[str, Any]]:
    depths = [float(item.get('depth_total', 0) or 0) for item in get_borehole_list()]
    valid_depths = [depth for depth in depths if depth > 0]
    ranges = build_depth_ranges(valid_depths)
    return [build_depth_range(row, valid_depths) for row in ranges]


def list_tileset_roots() -> list[Path]:
    roots: list[Path] = []
    for root in TILESET_ROOT_DIR_CANDIDATES:
        resolved_root = root.resolve()
        if resolved_root.exists() and resolved_root.is_dir() and resolved_root not in roots:
            roots.append(resolved_root)
    return roots


def list_tileset_dirs() -> list[Path]:
    roots = list_tileset_roots()
    if not roots:
        return []

    tileset_map: dict[str, Path] = {}
    for root in roots:
        for item in root.iterdir():
            if not item.is_dir() or not (item / 'tileset.json').exists():
                continue
            tileset_map.setdefault(item.name, item.resolve())

    return [tileset_map[name] for name in sorted(tileset_map.keys())]


def build_tileset_payload(tileset_dir: Path) -> dict[str, str]:
    return {
        'id': tileset_dir.name,
        'name': tileset_dir.name,
        'url': f'/api/dashboard/tilesets/{tileset_dir.name}/tileset.json',
    }


def get_tilesets() -> list[dict[str, str]]:
    return [build_tileset_payload(item) for item in list_tileset_dirs()]


def get_current_tileset() -> dict[str, str] | None:
    tilesets = get_tilesets()
    if not tilesets:
        return None
    return tilesets[0]


def find_tileset_dir(tileset_id: str) -> Path | None:
    for root in list_tileset_roots():
        candidate = (root / tileset_id).resolve()
        if candidate.exists() and candidate.is_dir():
            return candidate
    return None


def resolve_tileset_resource(tileset_id: str, resource_path: str) -> Path:
    if not tileset_id or '/' in tileset_id or '\\' in tileset_id:
        raise FileNotFoundError('Tileset does not exist')

    tileset_dir = find_tileset_dir(tileset_id)
    if tileset_dir is None:
        raise FileNotFoundError('Tileset does not exist')

    relative_path = Path(resource_path)
    if relative_path.is_absolute() or '..' in relative_path.parts:
        raise FileNotFoundError('Invalid resource path')

    target_file = (tileset_dir / relative_path).resolve()
    if not target_file.exists() or not target_file.is_file():
        raise FileNotFoundError('Tileset resource does not exist')

    if tileset_dir.resolve() not in target_file.parents and target_file != tileset_dir.resolve():
        raise FileNotFoundError('Invalid resource path')

    return target_file


def resolve_tileset_content_type(file_path: Path) -> str:
    if file_path.suffix.lower() == '.json':
        return 'application/json'
    if file_path.suffix.lower() in {'.b3dm', '.pnts', '.i3dm', '.cmpt'}:
        return 'application/octet-stream'
    return mimetypes.guess_type(file_path.name)[0] or 'application/octet-stream'
