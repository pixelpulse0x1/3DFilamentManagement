"""Manufacturer brands CRUD with safe-delete enforcement."""
import os
import logging
from flask import current_app, jsonify, request

from modules.manufacturers import manufacturers_bp
from modules.db import get_db

logger = logging.getLogger(__name__)


def _data_dir():
    return current_app.config.get("DATA_DIR", os.path.join(os.path.dirname(__file__), "..", "..", "data"))


@manufacturers_bp.route("", methods=["GET"])
def api_manufacturers_list():
    data_dir = _data_dir()
    try:
        with get_db(data_dir) as conn:
            rows = conn.execute("SELECT * FROM manufacturers ORDER BY id").fetchall()
            return jsonify([{"id": r["id"], "name": r["name"], "website": r["website"]} for r in rows])
    except Exception as e:
        logger.error("Manufacturers list error: %s", e)
        return jsonify({"status": "error", "error": str(e)}), 500


@manufacturers_bp.route("", methods=["POST"])
def api_manufacturers_create():
    data_dir = _data_dir()
    try:
        data = request.get_json() or {}
        name = (data.get("name") or "").strip()
        if not name:
            return jsonify({"status": "error", "error": "品牌名称不能为空"}), 400
        website = data.get("website", "")
        with get_db(data_dir) as conn:
            cursor = conn.execute(
                "INSERT INTO manufacturers (name, website) VALUES (?, ?)",
                (name, website),
            )
            conn.commit()
            return jsonify({"status": "success", "id": cursor.lastrowid})
    except Exception as e:
        logger.error("Manufacturer create error: %s", e)
        msg = "品牌名称已存在" if "UNIQUE" in str(e).upper() else str(e)
        return jsonify({"status": "error", "error": msg}), 400 if "UNIQUE" in str(e).upper() else 500


@manufacturers_bp.route("/<int:manufacturer_id>", methods=["PUT"])
def api_manufacturers_update(manufacturer_id):
    data_dir = _data_dir()
    try:
        data = request.get_json() or {}
        name = (data.get("name") or "").strip()
        website = data.get("website", "")
        with get_db(data_dir) as conn:
            existing = conn.execute("SELECT * FROM manufacturers WHERE id = ?", (manufacturer_id,)).fetchone()
            if not existing:
                return jsonify({"status": "error", "error": "品牌不存在"}), 404
            if name:
                conn.execute(
                    "UPDATE manufacturers SET name = ?, website = ? WHERE id = ?",
                    (name, website, manufacturer_id),
                )
            else:
                conn.execute(
                    "UPDATE manufacturers SET website = ? WHERE id = ?",
                    (website, manufacturer_id),
                )
            conn.commit()
            return jsonify({"status": "success"})
    except Exception as e:
        logger.error("Manufacturer update error: %s", e)
        msg = "品牌名称已存在" if "UNIQUE" in str(e).upper() else str(e)
        return jsonify({"status": "error", "error": msg}), 400 if "UNIQUE" in str(e).upper() else 500


@manufacturers_bp.route("/<int:manufacturer_id>", methods=["DELETE"])
def api_manufacturers_delete(manufacturer_id):
    data_dir = _data_dir()
    try:
        with get_db(data_dir) as conn:
            mfr = conn.execute("SELECT * FROM manufacturers WHERE id = ?", (manufacturer_id,)).fetchone()
            if not mfr:
                return jsonify({"status": "error", "error": "品牌不存在"}), 404
            ref_count = conn.execute(
                "SELECT COUNT(*) AS cnt FROM filaments WHERE manufacturer = ?",
                (mfr["name"],),
            ).fetchone()["cnt"]
            if ref_count > 0:
                return jsonify({
                    "status": "error",
                    "error": f"该品牌下仍有 {ref_count} 个耗材库存，无法删除",
                }), 400
            conn.execute("DELETE FROM manufacturers WHERE id = ?", (manufacturer_id,))
            conn.commit()
            return jsonify({"status": "success"})
    except Exception as e:
        logger.error("Manufacturer delete error: %s", e)
        return jsonify({"status": "error", "error": str(e)}), 500
