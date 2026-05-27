"""Brand & spool weight CRUD API."""
import os
import logging
from flask import current_app, jsonify, request

from modules.brands import brands_bp
from modules.db import get_db

logger = logging.getLogger(__name__)


def _data_dir():
    return current_app.config.get("DATA_DIR", os.path.join(os.path.dirname(__file__), "..", "..", "data"))


@brands_bp.route("/api/brands", methods=["GET", "POST"])
def api_brands():
    data_dir = _data_dir()
    try:
        with get_db(data_dir) as conn:
            if request.method == "GET":
                rows = conn.execute(
                    "SELECT * FROM brands ORDER BY name, spool_type"
                ).fetchall()
                return jsonify([{
                    "id": r["id"], "name": r["name"],
                    "spool_type": r["spool_type"], "spool_weight": r["spool_weight"],
                    "remark": r["remark"],
                } for r in rows])
            else:
                data = request.get_json() or {}
                name = data.get("name", "").strip()
                spool_type = data.get("spool_type", "标准盘").strip()
                spool_weight = float(data.get("spool_weight", 0))
                if not name:
                    return jsonify({"status": "error", "error": "品牌名称不能为空"}), 400
                cursor = conn.execute(
                    "INSERT INTO brands (name, spool_type, spool_weight, remark) VALUES (?, ?, ?, ?)",
                    (name, spool_type, spool_weight, data.get("remark", "").strip()),
                )
                conn.commit()
                return jsonify({"status": "success", "id": cursor.lastrowid})
    except Exception as e:
        logger.error("Brands error: %s", e)
        return jsonify({"status": "error", "error": str(e)}), 500


@brands_bp.route("/api/brands/rename", methods=["POST"])
def api_brands_rename():
    """Rename all brand records with a given name to a new name."""
    data_dir = _data_dir()
    try:
        data = request.get_json() or {}
        old_name = data.get("old_name", "").strip()
        new_name = data.get("new_name", "").strip()
        if not old_name or not new_name:
            return jsonify({"status": "error", "error": "品牌名称不能为空"}), 400
        with get_db(data_dir) as conn:
            # Check if target name already exists (different from old_name)
            exists = conn.execute(
                "SELECT COUNT(*) FROM brands WHERE name = ? AND name != ?",
                (new_name, old_name),
            ).fetchone()
            if exists and exists[0] > 0:
                return jsonify({"status": "error", "error": "该品牌名称已存在，无法重命名！"}), 400
            conn.execute(
                "UPDATE brands SET name = ? WHERE name = ?",
                (new_name, old_name),
            )
            conn.commit()
            return jsonify({"status": "success", "updated_name": new_name})
    except Exception as e:
        logger.error("Brand rename error: %s", e)
        return jsonify({"status": "error", "error": str(e)}), 500


@brands_bp.route("/api/brands/<int:brand_id>", methods=["PUT", "DELETE"])
def api_brand_single(brand_id):
    data_dir = _data_dir()
    try:
        with get_db(data_dir) as conn:
            brand = conn.execute(
                "SELECT * FROM brands WHERE id = ?", (brand_id,)
            ).fetchone()
            if not brand:
                return jsonify({"status": "error", "error": "品牌不存在"}), 404

            if request.method == "PUT":
                data = request.get_json() or {}
                name = data.get("name", brand["name"]).strip()
                spool_type = data.get("spool_type", brand["spool_type"]).strip()
                spool_weight = float(data.get("spool_weight", brand["spool_weight"]))
                if not name:
                    return jsonify({"status": "error", "error": "品牌名称不能为空"}), 400
                conn.execute(
                    """UPDATE brands SET name=?, spool_type=?, spool_weight=?, remark=?
                       WHERE id=?""",
                    (name, spool_type, spool_weight, data.get("remark", "").strip(), brand_id),
                )
                conn.commit()
                return jsonify({"status": "success"})
            else:
                conn.execute("DELETE FROM brands WHERE id = ?", (brand_id,))
                conn.commit()
                return jsonify({"status": "success"})
    except Exception as e:
        logger.error("Brand single error: %s", e)
        return jsonify({"status": "error", "error": str(e)}), 500
