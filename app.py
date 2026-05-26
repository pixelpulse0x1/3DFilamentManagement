"""3D Consumables Inventory Management System — Application entry point."""
import os

from flask import Flask, jsonify

from modules.db import init_db
from modules.base import base_bp
from modules.filaments import filaments_bp
from modules.materials import materials_bp
from modules.manufacturers import manufacturers_bp
from modules.printers import printers_bp


def create_app():
    app = Flask(__name__)
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "change-me-to-random-string")
    app.config["DATA_DIR"] = os.environ.get("DATA_DIR", os.path.join(os.path.dirname(__file__), "data"))

    init_db(app.config["DATA_DIR"])

    app.register_blueprint(base_bp)
    app.register_blueprint(filaments_bp)
    app.register_blueprint(materials_bp, url_prefix="/api/materials")
    app.register_blueprint(manufacturers_bp, url_prefix="/api/manufacturers")
    app.register_blueprint(printers_bp)

    @app.errorhandler(404)
    def not_found(error):
        return jsonify({"status": "error", "error": "接口不存在"}), 404

    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({"status": "error", "error": "服务器内部错误"}), 500

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=3155, debug=False)
