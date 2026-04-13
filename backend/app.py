from __future__ import annotations

from flask import Flask, send_from_directory
from flask_cors import CORS

from config import CORS_ALLOWED_ORIGINS, DEBUG, HOST, PORT, STATIC_DIR
from routes.boreholes import boreholes_bp
from routes.boundaries import boundaries_bp
from routes.dashboard import dashboard_bp
from routes.rasters import rasters_bp


def create_app() -> Flask:
    app = Flask(__name__)

    if '*' in CORS_ALLOWED_ORIGINS:
        CORS(app)
    else:
        CORS(app, origins=CORS_ALLOWED_ORIGINS)

    app.register_blueprint(boreholes_bp)
    app.register_blueprint(boundaries_bp)
    app.register_blueprint(rasters_bp)
    app.register_blueprint(dashboard_bp)

    @app.get('/static/<path:resource_path>')
    def static_files(resource_path: str):
        return send_from_directory(STATIC_DIR, resource_path)

    return app


app = create_app()


if __name__ == '__main__':
    app.run(host=HOST, port=PORT, debug=DEBUG)
