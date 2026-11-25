"""Card Nova - application factory."""
import os

from flask import Flask, jsonify, send_from_directory

from .config import BASE_DIR, Config
from .db import init_db

FRONTEND_DIR = os.path.join(BASE_DIR, "frontend")


def create_app(overrides=None, reseed=False):
    app = Flask(__name__, static_folder=FRONTEND_DIR, static_url_path="")
    app.config.from_object(Config)
    app.json.sort_keys = False  # keep category order as declared
    if overrides:
        app.config.update(overrides)
    init_db(app, reset=reseed)

    from .routes import auth, calculators, cards
    for module in (cards, calculators, auth):
        app.register_blueprint(module.bp)

    @app.get("/")
    def index():
        return send_from_directory(FRONTEND_DIR, "index.html")

    @app.errorhandler(404)
    def not_found(_e):
        from flask import request
        if request.path.startswith("/api/"):
            return jsonify({"error": "Not found"}), 404
        return send_from_directory(FRONTEND_DIR, "index.html")

    @app.errorhandler(405)
    def bad_method(_e):
        return jsonify({"error": "Method not allowed"}), 405

    @app.errorhandler(500)
    def server_error(_e):
        return jsonify({"error": "Internal server error"}), 500

    @app.after_request
    def headers(resp):
        resp.headers.setdefault("X-Content-Type-Options", "nosniff")
        resp.headers.setdefault("Referrer-Policy", "same-origin")
        return resp

    return app
