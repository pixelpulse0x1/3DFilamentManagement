"""Purchase channel CRUD API."""
import os
import logging
from flask import current_app, jsonify, request

from modules.channels import channels_bp
from modules.db import get_db

logger = logging.getLogger(__name__)


def _data_dir():
    return current_app.config.get("DATA_DIR", os.path.join(os.path.dirname(__file__), "..", "..", "data"))


@channels_bp.route("/api/channels", methods=["GET", "POST"])
def api_channels():
    data_dir = _data_dir()
    try:
        with get_db(data_dir) as conn:
            if request.method == "GET":
                rows = conn.execute("SELECT * FROM channels ORDER BY id").fetchall()
                return jsonify([{"id": r["id"], "name": r["name"], "description": r["description"]} for r in rows])
            else:
                data = request.get_json() or {}
                name = data.get("name", "").strip()
                if not name:
                    return jsonify({"status": "error", "error": "渠道名称不能为空"}), 400
                cursor = conn.execute(
                    "INSERT INTO channels (name, description) VALUES (?, ?)",
                    (name, data.get("description", "").strip()),
                )
                conn.commit()
                return jsonify({"status": "success", "id": cursor.lastrowid})
    except Exception as e:
        logger.error("Channels error: %s", e)
        return jsonify({"status": "error", "error": str(e)}), 500


@channels_bp.route("/api/channels/<int:channel_id>", methods=["PUT", "DELETE"])
def api_channel_single(channel_id):
    data_dir = _data_dir()
    try:
        with get_db(data_dir) as conn:
            ch = conn.execute("SELECT * FROM channels WHERE id = ?", (channel_id,)).fetchone()
            if not ch:
                return jsonify({"status": "error", "error": "渠道不存在"}), 404

            if request.method == "PUT":
                data = request.get_json() or {}
                name = data.get("name", "").strip()
                if not name:
                    return jsonify({"status": "error", "error": "渠道名称不能为空"}), 400
                conn.execute(
                    "UPDATE channels SET name = ?, description = ? WHERE id = ?",
                    (name, data.get("description", "").strip(), channel_id),
                )
                conn.commit()
                return jsonify({"status": "success"})
            else:
                used = conn.execute("SELECT COUNT(*) AS n FROM filaments WHERE channel_id = ?", (channel_id,)).fetchone()
                if used and used["n"] > 0:
                    return jsonify({
                        "status": "error",
                        "error": f"该渠道正被 {used['n']} 卷耗材使用，无法删除",
                    }), 400
                conn.execute("DELETE FROM channels WHERE id = ?", (channel_id,))
                conn.commit()
                return jsonify({"status": "success"})
    except Exception as e:
        logger.error("Channel single error: %s", e)
        return jsonify({"status": "error", "error": str(e)}), 500
