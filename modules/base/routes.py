"""Base routes: pages, settings, background management, utilities."""
import os
import re
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


def _get_appearance_settings(conn):
    """Load card_opacity and card_color from system_settings with validation fallback."""
    rows = conn.execute(
        "SELECT key, value FROM system_settings WHERE key IN ('card_opacity', 'card_color', 'card_blur')"
    ).fetchall()
    sys = {r["key"]: r["value"] for r in rows}

    try:
        card_opacity = float(sys.get("card_opacity", "0.05"))
        if not (0.0 <= card_opacity <= 1.0):
            card_opacity = 0.05
    except (ValueError, TypeError):
        card_opacity = 0.05

    try:
        card_color = sys.get("card_color", "#ffffff")
        if not re.match(r'^#[0-9a-fA-F]{6}$', card_color):
            card_color = "#ffffff"
    except (ValueError, TypeError):
        card_color = "#ffffff"

    try:
        card_blur = int(sys.get("card_blur", "2"))
        if not (0 <= card_blur <= 30):
            card_blur = 2
    except (ValueError, TypeError):
        card_blur = 2

    return card_opacity, card_color, card_blur


def _bg_for_template():
    """Helper to get background for page renders."""
    return get_active_background(_data_dir(), current_app.static_folder)


# ─── Page Routes ───

@base_bp.route("/")
def index():
    return render_template("dashboard/overview.html",
                           active_background=_bg_for_template(),
                           active_nav="dashboard",
                           active_sub="overview")


@base_bp.route("/dashboard/overview")
def dashboard_overview():
    return render_template("dashboard/overview.html",
                           active_background=_bg_for_template(),
                           active_nav="dashboard",
                           active_sub="overview")


@base_bp.route("/dashboard/filaments")
def dashboard_filaments():
    return render_template("dashboard/filaments.html",
                           active_background=_bg_for_template(),
                           active_nav="dashboard",
                           active_sub="filaments")


@base_bp.route("/dashboard/logs")
def dashboard_logs():
    return render_template("dashboard/logs.html",
                           active_background=_bg_for_template(),
                           active_nav="dashboard",
                           active_sub="logs")


@base_bp.route("/dashboard/stats")
def dashboard_stats():
    return render_template("dashboard/stats.html",
                           active_background=_bg_for_template(),
                           active_nav="dashboard",
                           active_sub="stats")


@base_bp.route("/materials")
def materials_page():
    return render_template("materials.html",
                           active_background=_bg_for_template(),
                           active_nav="materials")


@base_bp.route("/manufacturers")
def manufacturers_page():
    return render_template("manufacturers.html",
                           active_background=_bg_for_template(),
                           active_nav="manufacturers")


@base_bp.route("/settings/general")
def settings_general():
    return render_template("settings/general.html",
                           active_background=_bg_for_template(),
                           active_nav="settings",
                           active_sub="general")


@base_bp.route("/settings/appearance")
def settings_appearance():
    return render_template("settings/appearance.html",
                           active_background=_bg_for_template(),
                           active_nav="settings",
                           active_sub="appearance")


@base_bp.route("/settings/advanced")
def settings_advanced():
    return render_template("settings/advanced.html",
                           active_background=_bg_for_template(),
                           active_nav="settings",
                           active_sub="advanced")


# ─── Settings API ───

@base_bp.route("/api/settings", methods=["GET", "PUT"])
def api_settings():
    data_dir = _data_dir()
    try:
        with get_db(data_dir) as conn:
            if request.method == "GET":
                row = conn.execute("SELECT * FROM settings WHERE id = 1").fetchone()
                result = dict(row)
                card_opacity, card_color, card_blur = _get_appearance_settings(conn)
                result["card_opacity"] = card_opacity
                result["card_color"] = card_color
                result["card_blur"] = card_blur
                return jsonify(result)
            else:
                data = request.get_json() or {}
                threshold = data.get("threshold", 200)
                default_weight = data.get("default_weight", 1000.0)
                conn.execute(
                    "UPDATE settings SET threshold = ?, default_weight = ? WHERE id = 1",
                    (threshold, default_weight),
                )

                if "card_opacity" in data:
                    try:
                        val = float(data["card_opacity"])
                        if 0.0 <= val <= 1.0:
                            conn.execute(
                                "INSERT OR REPLACE INTO system_settings (key, value) VALUES ('card_opacity', ?)",
                                (str(val),),
                            )
                    except (ValueError, TypeError):
                        pass

                if "card_color" in data:
                    color = str(data["card_color"])
                    if re.match(r'^#[0-9a-fA-F]{6}$', color):
                        conn.execute(
                            "INSERT OR REPLACE INTO system_settings (key, value) VALUES ('card_color', ?)",
                            (color,),
                        )

                if "card_blur" in data:
                    try:
                        val = int(data["card_blur"])
                        if 0 <= val <= 30:
                            conn.execute(
                                "INSERT OR REPLACE INTO system_settings (key, value) VALUES ('card_blur', ?)",
                                (str(val),),
                            )
                    except (ValueError, TypeError):
                        pass

                conn.commit()
                row = conn.execute("SELECT * FROM settings WHERE id = 1").fetchone()
                result = dict(row)
                card_opacity, card_color, card_blur = _get_appearance_settings(conn)
                result["card_opacity"] = card_opacity
                result["card_color"] = card_color
                result["card_blur"] = card_blur
                return jsonify({"status": "success", "settings": result})
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


# ─── Appearance API ───

@base_bp.route("/api/settings/appearance", methods=["GET"])
def api_appearance_get():
    data_dir = _data_dir()
    try:
        with get_db(data_dir) as conn:
            card_opacity, card_color, card_blur = _get_appearance_settings(conn)
            return jsonify({
                "card_opacity": card_opacity,
                "card_color": card_color,
                "card_blur": card_blur,
            })
    except Exception as e:
        logger.error("Appearance get error: %s", e)
        return jsonify({"card_opacity": 0.05, "card_color": "#ffffff", "card_blur": 2})


@base_bp.route("/api/settings/appearance", methods=["PUT"])
def api_appearance_update():
    data_dir = _data_dir()
    try:
        data = request.get_json() or {}
        with get_db(data_dir) as conn:
            if "card_opacity" in data:
                try:
                    val = float(data["card_opacity"])
                    if 0.0 <= val <= 1.0:
                        conn.execute(
                            "INSERT OR REPLACE INTO system_settings (key, value) VALUES ('card_opacity', ?)",
                            (str(val),),
                        )
                except (ValueError, TypeError):
                    pass

            if "card_color" in data:
                color = str(data["card_color"])
                if re.match(r'^#[0-9a-fA-F]{6}$', color):
                    conn.execute(
                        "INSERT OR REPLACE INTO system_settings (key, value) VALUES ('card_color', ?)",
                        (color,),
                    )

            if "card_blur" in data:
                try:
                    val = int(data["card_blur"])
                    if 0 <= val <= 30:
                        conn.execute(
                            "INSERT OR REPLACE INTO system_settings (key, value) VALUES ('card_blur', ?)",
                            (str(val),),
                        )
                except (ValueError, TypeError):
                    pass

            conn.commit()
            card_opacity, card_color, card_blur = _get_appearance_settings(conn)
            return jsonify({
                "status": "success",
                "card_opacity": card_opacity,
                "card_color": card_color,
                "card_blur": card_blur,
            })
    except Exception as e:
        logger.error("Appearance update error: %s", e)
        return jsonify({"status": "error", "error": str(e)}), 500


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
