"""Base routes: pages, settings, background management, utilities."""
import os
import socket
import logging
from datetime import datetime
from flask import current_app, render_template, jsonify, request

from modules.base import base_bp
from modules.db import get_db
from modules.base.bg_utils import (
    get_active_background, list_backgrounds, upload_background, set_active_background,
)
from modules.base.migrate_utils import migrate_from_db, migrate_from_txt

logger = logging.getLogger(__name__)


def _data_dir():
    return current_app.config.get("DATA_DIR", os.path.join(os.path.dirname(__file__), "..", "..", "data"))


# ─── Page Routes ───

@base_bp.route("/")
def index():
    static_folder = current_app.static_folder
    bg = get_active_background(_data_dir(), static_folder)
    return render_template("dashboard.html", active_background=bg)


@base_bp.route("/materials")
def materials_page():
    static_folder = current_app.static_folder
    bg = get_active_background(_data_dir(), static_folder)
    return render_template("materials.html", active_background=bg, active_nav="materials")


@base_bp.route("/manufacturers")
def manufacturers_page():
    static_folder = current_app.static_folder
    bg = get_active_background(_data_dir(), static_folder)
    return render_template("manufacturers.html", active_background=bg, active_nav="manufacturers")


@base_bp.route("/settings")
def settings_page():
    static_folder = current_app.static_folder
    bg = get_active_background(_data_dir(), static_folder)
    return render_template("settings.html", active_background=bg, active_nav="settings")


# ─── Settings API ───

@base_bp.route("/api/settings", methods=["GET", "PUT"])
def api_settings():
    data_dir = _data_dir()
    try:
        with get_db(data_dir) as conn:
            if request.method == "GET":
                row = conn.execute("SELECT * FROM settings WHERE id = 1").fetchone()
                return jsonify(dict(row))
            else:
                data = request.get_json() or {}
                threshold = data.get("threshold", 200)
                default_weight = data.get("default_weight", 1000.0)
                conn.execute(
                    "UPDATE settings SET threshold = ?, default_weight = ? WHERE id = 1",
                    (threshold, default_weight),
                )
                conn.commit()
                row = conn.execute("SELECT * FROM settings WHERE id = 1").fetchone()
                return jsonify({"status": "success", "settings": dict(row)})
    except Exception as e:
        logger.error("Settings error: %s", e)
        return jsonify({"status": "error", "error": str(e)}), 500


# ─── Background API ───

@base_bp.route("/api/settings/background", methods=["GET"])
def api_background_get():
    data_dir = _data_dir()
    static_folder = current_app.static_folder
    try:
        active = get_active_background(data_dir, static_folder)
        backgrounds = list_backgrounds(static_folder)
        return jsonify({
            "active": active,
            "backgrounds": backgrounds,
        })
    except Exception as e:
        logger.error("Get background error: %s", e)
        return jsonify({"status": "error", "error": str(e)}), 500


@base_bp.route("/api/settings/background/upload", methods=["POST"])
def api_background_upload():
    static_folder = current_app.static_folder
    try:
        if "file" not in request.files:
            return jsonify({"status": "error", "error": "未选择文件"}), 400
        ok, msg, filename = upload_background(request.files["file"], static_folder)
        if not ok:
            return jsonify({"status": "error", "error": msg}), 400
        return jsonify({"status": "success", "message": msg, "filename": filename})
    except Exception as e:
        logger.error("Background upload error: %s", e)
        return jsonify({"status": "error", "error": str(e)}), 500


@base_bp.route("/api/settings/background/set", methods=["POST"])
def api_background_set():
    data_dir = _data_dir()
    try:
        data = request.get_json() or {}
        filename = data.get("filename", "")
        set_active_background(data_dir, filename)
        return jsonify({"status": "success", "active": filename})
    except Exception as e:
        logger.error("Set background error: %s", e)
        return jsonify({"status": "error", "error": str(e)}), 500


# ─── Utility ───

@base_bp.route("/api/local-ip", methods=["GET"])
def api_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
    except Exception:
        ip = "127.0.0.1"
    return jsonify({"ip": ip})


# ─── Data Migration ───

@base_bp.route("/api/settings/migrate/db", methods=["POST"])
def api_migrate_db():
    """Import data from a legacy filament_inventory.db file."""
    data_dir = _data_dir()
    if "file" not in request.files:
        return jsonify({"status": "error", "error": "未选择文件"}), 400
    file = request.files["file"]
    if not file.filename:
        return jsonify({"status": "error", "error": "文件名为空"}), 400

    import tempfile
    tmp_path = None
    try:
        suffix = os.path.splitext(file.filename)[1] or ".db"
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
            file.save(tmp.name)
            tmp_path = tmp.name

        added_f, added_r, updated_s, errors = migrate_from_db(tmp_path, data_dir)
        return jsonify({
            "status": "success",
            "added_filaments": added_f,
            "added_records": added_r,
            "updated_settings": updated_s,
            "errors": errors,
        })
    except Exception as e:
        logger.error("DB migration error: %s", e)
        return jsonify({"status": "error", "error": str(e)}), 500
    finally:
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.unlink(tmp_path)
            except OSError:
                pass


@base_bp.route("/api/settings/migrate/materials", methods=["POST"])
def api_migrate_materials():
    """Import material types from a legacy materials.txt file."""
    data_dir = _data_dir()
    if "file" not in request.files:
        return jsonify({"status": "error", "error": "未选择文件"}), 400
    file = request.files["file"]
    if not file.filename:
        return jsonify({"status": "error", "error": "文件名为空"}), 400

    try:
        added, skipped, errors = migrate_from_txt(file, "materials", data_dir)
        return jsonify({
            "status": "success",
            "added": added,
            "skipped": skipped,
            "errors": errors,
        })
    except Exception as e:
        logger.error("Materials migration error: %s", e)
        return jsonify({"status": "error", "error": str(e)}), 500


@base_bp.route("/api/settings/migrate/manufacturers", methods=["POST"])
def api_migrate_manufacturers():
    """Import manufacturer brands from a legacy manufacturers.txt file."""
    data_dir = _data_dir()
    if "file" not in request.files:
        return jsonify({"status": "error", "error": "未选择文件"}), 400
    file = request.files["file"]
    if not file.filename:
        return jsonify({"status": "error", "error": "文件名为空"}), 400

    try:
        added, skipped, errors = migrate_from_txt(file, "manufacturers", data_dir)
        return jsonify({
            "status": "success",
            "added": added,
            "skipped": skipped,
            "errors": errors,
        })
    except Exception as e:
        logger.error("Manufacturers migration error: %s", e)
        return jsonify({"status": "error", "error": str(e)}), 500
