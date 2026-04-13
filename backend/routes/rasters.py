from __future__ import annotations

from flask import Blueprint, abort, jsonify, send_file

from services.rasters import get_raster_detail, get_raster_file_path, get_raster_list

rasters_bp = Blueprint('rasters', __name__, url_prefix='/api/rasters')


@rasters_bp.get('/')
def raster_list():
    return jsonify(get_raster_list())


@rasters_bp.get('/<string:raster_id>/')
def raster_detail(raster_id: str):
    detail = get_raster_detail(raster_id)
    if detail is None:
        return jsonify({}), 404
    return jsonify(detail)


@rasters_bp.get('/files/<string:raster_id>/')
def raster_file(raster_id: str):
    tif_path = get_raster_file_path(raster_id)
    if tif_path is None:
        abort(404)

    response = send_file(tif_path, mimetype='image/tiff', as_attachment=False)
    response.headers['Content-Disposition'] = f'inline; filename="{tif_path.name}"'
    return response
