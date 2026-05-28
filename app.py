"""3DFilamentManagement — Application entry point with multi-environment adaptive paths."""
import os
import sys
import logging

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

# ─── Multi-Environment Adaptive Paths ───

IS_FROZEN = getattr(sys, 'frozen', False)
IS_DOCKER = os.path.exists('/.dockerenv') or os.environ.get('IS_DOCKER') == 'true'

if IS_FROZEN:
    # A 轨道：PyInstaller Windows 便携版
    # server.exe 位于 backend/ 目录下，数据和静态资源在上一级总根目录
    EXE_DIR = os.path.dirname(os.path.abspath(sys.executable))
    BASE_DIR = os.path.dirname(EXE_DIR)

    STATIC_FOLDER = os.path.join(BASE_DIR, "static")
    TEMPLATE_FOLDER = os.path.join(BASE_DIR, "templates")
    BIND_HOST = "127.0.0.1"
    BIND_PORT = 9055
    _default_data_dir = os.path.join(BASE_DIR, "data")

elif IS_DOCKER:
    # B 轨道：Docker 容器环境
    # 严格保持原有容器根目录映射，确保原有数据卷挂载无缝兼容
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

    STATIC_FOLDER = os.path.join(BASE_DIR, "static")
    TEMPLATE_FOLDER = os.path.join(BASE_DIR, "templates")
    BIND_HOST = "0.0.0.0"
    BIND_PORT = 3155
    _default_data_dir = os.path.join(BASE_DIR, "data")

else:
    # C 轨道：本地 Python 脚本开发环境
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

    STATIC_FOLDER = os.path.join(BASE_DIR, "static")
    TEMPLATE_FOLDER = os.path.join(BASE_DIR, "templates")
    BIND_HOST = "127.0.0.1"
    BIND_PORT = 9055
    _default_data_dir = os.path.join(BASE_DIR, "data")

os.makedirs(_default_data_dir, exist_ok=True)

# ─── Debug Mode Logging ───
# When DEBUG_MODE is false (default), suppress werkzeug INFO logs
# to keep the console quiet during normal operation.
_is_debug_env = os.environ.get('DEBUG_MODE', 'false').lower() == 'true'
if not _is_debug_env:
    logging.getLogger('werkzeug').setLevel(logging.WARNING)


def create_app():
    app = Flask(__name__,
                static_folder=STATIC_FOLDER,
                template_folder=TEMPLATE_FOLDER)

    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "change-me-to-random-string")
    app.config["DATA_DIR"] = os.environ.get("DATA_DIR", _default_data_dir)
    app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024  # 5MB max upload

    init_db(app.config["DATA_DIR"])

    # Seed default background into data/ (needed on first run of Windows portable)
    from modules.base.bg_utils import seed_default_background
    seed_default_background(app.config["DATA_DIR"], STATIC_FOLDER)

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
        """每个请求结束后强制释放 DB 连接，防止连接池耗尽。"""
        db = g.pop('db', None)
        if db is not None:
            try:
                db.close()
            except Exception:
                pass

    @app.context_processor
    def inject_i18n():
        from modules.i18n import I18N
        try:
            import sqlite3
            db_path = os.path.join(app.config["DATA_DIR"], "database", "filament_inventory.db")
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                "SELECT value FROM system_settings WHERE key='system_language'"
            ).fetchone()
            conn.close()
            lang = row["value"] if row and row["value"] in I18N else "zh"
        except Exception:
            lang = "zh"
        return {'i18n': I18N.get(lang, I18N['zh']), 'current_lang': lang}

    return app


if __name__ == "__main__":
    app = create_app()
    port = int(os.environ.get("PORT", BIND_PORT))
    app.run(host=BIND_HOST, port=port, debug=False)
