"""3DFilamentManagement — Application entry point."""
import os

from flask import Flask, jsonify, g

from modules.db import init_db
from modules.base import base_bp
from modules.filaments import filaments_bp
from modules.materials import materials_bp
from modules.printers import printers_bp
from modules.images import images_bp
from modules.channels import channels_bp
from modules.brands import brands_bp
from modules.tools import tools_bp


def create_app():
    app = Flask(__name__)
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "change-me-to-random-string")
    app.config["DATA_DIR"] = os.environ.get("DATA_DIR", os.path.join(os.path.dirname(__file__), "data"))
    app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024  # 5MB max upload

    init_db(app.config["DATA_DIR"])

    app.register_blueprint(base_bp)
    app.register_blueprint(filaments_bp)
    app.register_blueprint(materials_bp, url_prefix="/api/materials")
    app.register_blueprint(printers_bp)
    app.register_blueprint(images_bp)
    app.register_blueprint(channels_bp)
    app.register_blueprint(brands_bp)
    app.register_blueprint(tools_bp)

    @app.errorhandler(404)
    def not_found(error):
        return jsonify({"status": "error", "error": "Endpoint not found"}), 404

    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({"status": "error", "error": "Internal server error"}), 500

    @app.teardown_appcontext
    def close_db(error):
        """Force-close any lingering DB connection after each request."""
        db = g.pop('db', None)
        if db is not None:
            try: db.close()
            except Exception: pass

    @app.context_processor
    def inject_i18n():
        from modules.i18n import I18N
        try:
            import sqlite3, os
            db_path = os.path.join(app.config["DATA_DIR"], "database", "filament_inventory.db")
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row
            row = conn.execute("SELECT value FROM system_settings WHERE key='system_language'").fetchone()
            conn.close()
            lang = row["value"] if row and row["value"] in I18N else "zh"
        except Exception:
            lang = "zh"
        return {'i18n': I18N.get(lang, I18N['zh']), 'current_lang': lang}

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=3155, debug=False)
