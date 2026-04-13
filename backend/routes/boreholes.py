from __future__ import annotations

from flask import Blueprint, jsonify, request

from services.boreholes import get_borehole_detail, get_borehole_geojson, get_borehole_layers, get_borehole_list

boreholes_bp = Blueprint('boreholes', __name__, url_prefix='/api/boreholes')


@boreholes_bp.get('/')
def borehole_list():
    data = get_borehole_list(keyword=request.args.get('keyword'), workface=request.args.get('workface'))
    return jsonify(data)


@boreholes_bp.get('/geojson/')
def borehole_geojson():
    return jsonify(get_borehole_geojson())


@boreholes_bp.get('/<string:borehole_id>/')
def borehole_detail(borehole_id: str):
    detail = get_borehole_detail(borehole_id)
    if detail is None:
        return jsonify({}), 404
    return jsonify(detail)


@boreholes_bp.get('/<string:borehole_id>/layers/')
def borehole_layers(borehole_id: str):
    return jsonify(get_borehole_layers(borehole_id))
