"""Material types CRUD with safe-delete enforcement."""
import os
import logging
from flask import current_app, jsonify, request

from modules.materials import materials_bp
from modules.db import get_db

logger = logging.getLogger(__name__)


def _data_dir():
    return current_app.config.get("DATA_DIR", os.path.join(os.path.dirname(__file__), "..", "..", "data"))


@materials_bp.route("", methods=["GET"])
def api_materials_list():
    data_dir = _data_dir()
    try:
        with get_db(data_dir) as conn:
            rows = conn.execute("SELECT * FROM materials ORDER BY id").fetchall()
            return jsonify([{"id": r["id"], "name": r["name"], "description": r["description"]} for r in rows])
    except Exception as e:
        logger.error("Materials list error: %s", e)
        return jsonify({"status": "error", "error": str(e)}), 500


@materials_bp.route("", methods=["POST"])
def api_materials_create():
    data_dir = _data_dir()
    try:
        data = request.get_json() or {}
        name = (data.get("name") or "").strip()
        if not name:
            return jsonify({"status": "error", "error": "材料名称不能为空"}), 400
        description = data.get("description", "")
        with get_db(data_dir) as conn:
            cursor = conn.execute(
                "INSERT INTO materials (name, description) VALUES (?, ?)",
                (name, description),
            )
            conn.commit()
            return jsonify({"status": "success", "id": cursor.lastrowid})
    except Exception as e:
        logger.error("Material create error: %s", e)
        msg = "材料名称已存在" if "UNIQUE" in str(e).upper() else str(e)
        return jsonify({"status": "error", "error": msg}), 400 if "UNIQUE" in str(e).upper() else 500


@materials_bp.route("/<int:material_id>", methods=["PUT"])
def api_materials_update(material_id):
    data_dir = _data_dir()
    try:
        data = request.get_json() or {}
        name = (data.get("name") or "").strip()
        description = data.get("description", "")
        with get_db(data_dir) as conn:
            existing = conn.execute("SELECT * FROM materials WHERE id = ?", (material_id,)).fetchone()
            if not existing:
                return jsonify({"status": "error", "error": "材料类型不存在"}), 404
            if name:
                conn.execute(
                    "UPDATE materials SET name = ?, description = ? WHERE id = ?",
                    (name, description, material_id),
                )
            else:
                conn.execute(
                    "UPDATE materials SET description = ? WHERE id = ?",
                    (description, material_id),
                )
            conn.commit()
            return jsonify({"status": "success"})
    except Exception as e:
        logger.error("Material update error: %s", e)
        msg = "材料名称已存在" if "UNIQUE" in str(e).upper() else str(e)
        return jsonify({"status": "error", "error": msg}), 400 if "UNIQUE" in str(e).upper() else 500


@materials_bp.route("/<int:material_id>", methods=["DELETE"])
def api_materials_delete(material_id):
    data_dir = _data_dir()
    try:
        with get_db(data_dir) as conn:
            material = conn.execute("SELECT * FROM materials WHERE id = ?", (material_id,)).fetchone()
            if not material:
                return jsonify({"status": "error", "error": "材料类型不存在"}), 404
            ref_count = conn.execute(
                "SELECT COUNT(*) AS cnt FROM filaments WHERE material_type = ?",
                (material["name"],),
            ).fetchone()["cnt"]
            if ref_count > 0:
                return jsonify({
                    "status": "error",
                    "error": f"该材料类型下仍有 {ref_count} 个耗材库存，无法删除",
                }), 400
            conn.execute("DELETE FROM materials WHERE id = ?", (material_id,))
            conn.commit()
            return jsonify({"status": "success"})
    except Exception as e:
        logger.error("Material delete error: %s", e)
        return jsonify({"status": "error", "error": str(e)}), 500
