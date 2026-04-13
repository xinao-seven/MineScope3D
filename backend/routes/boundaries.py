from __future__ import annotations

from flask import Blueprint, jsonify, request

from services.boundaries import get_boundary_detail, get_boundary_geojson, get_boundary_list

boundaries_bp = Blueprint('boundaries', __name__, url_prefix='/api/boundaries')


@boundaries_bp.get('/')
def boundary_list():
    return jsonify(get_boundary_list(boundary_type=request.args.get('type')))


@boundaries_bp.get('/geojson/')
def boundary_geojson():
    return jsonify(get_boundary_geojson(boundary_type=request.args.get('type')))


@boundaries_bp.get('/<string:boundary_id>/')
def boundary_detail(boundary_id: str):
    detail = get_boundary_detail(boundary_id)
    if detail is None:
        return jsonify({}), 404
    return jsonify(detail)
