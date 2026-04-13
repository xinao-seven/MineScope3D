from __future__ import annotations

from flask import Blueprint, abort, jsonify, send_file

from services.dashboard import (
    get_borehole_depth_distribution,
    get_current_tileset,
    get_dashboard_overview,
    get_layer_distribution,
    get_tilesets,
    get_workface_boreholes,
    resolve_tileset_content_type,
    resolve_tileset_resource,
)

dashboard_bp = Blueprint('dashboard', __name__, url_prefix='/api/dashboard')


@dashboard_bp.get('/overview/')
def dashboard_overview():
    return jsonify(get_dashboard_overview())


@dashboard_bp.get('/layer-distribution/')
def layer_distribution():
    return jsonify(get_layer_distribution())


@dashboard_bp.get('/workface-boreholes/')
def workface_boreholes():
    return jsonify(get_workface_boreholes())


@dashboard_bp.get('/borehole-depth-distribution/')
def borehole_depth_distribution():
    return jsonify(get_borehole_depth_distribution())


@dashboard_bp.get('/tilesets/')
def tilesets():
    return jsonify(get_tilesets())


@dashboard_bp.get('/tilesets/current/')
def current_tileset():
    current = get_current_tileset()
    if current is None:
        return jsonify({}), 404
    return jsonify(current)


@dashboard_bp.get('/tilesets/<string:tileset_id>/')
@dashboard_bp.get('/tilesets/<string:tileset_id>/<path:resource_path>')
def tileset_file(tileset_id: str, resource_path: str = 'tileset.json'):
    try:
        target_file = resolve_tileset_resource(tileset_id, resource_path)
    except FileNotFoundError:
        abort(404)

    content_type = resolve_tileset_content_type(target_file)
    response = send_file(target_file, mimetype=content_type, as_attachment=False)
    response.headers['Content-Disposition'] = f'inline; filename="{target_file.name}"'
    return response
