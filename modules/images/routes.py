"""Filament image assets CRUD API."""
import os
import uuid
import logging
from flask import current_app, jsonify, request

from modules.images import images_bp
from modules.db import get_db

logger = logging.getLogger(__name__)

ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "webp"}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB


def _data_dir():
    return current_app.config.get("DATA_DIR", os.path.join(os.path.dirname(__file__), "..", "..", "data"))


def _images_dir(data_dir):
    d = os.path.join(data_dir, "uploads", "filaments")
    os.makedirs(d, exist_ok=True)
    return d


def _allowed_file(filename):
    if "." not in filename:
        return False
    return filename.rsplit(".", 1)[-1].lower() in ALLOWED_EXTENSIONS


# ─── Image CRUD ───

@images_bp.route("/api/images", methods=["GET"])
def api_images_list():
    """List all images with ref_count (number of filaments referencing each)."""
    data_dir = _data_dir()
    try:
        with get_db(data_dir) as conn:
            rows = conn.execute("""
                SELECT fi.*, COUNT(f.id) AS ref_count
                FROM filament_images fi
                LEFT JOIN filaments f ON f.image_id = fi.id
                GROUP BY fi.id
                ORDER BY fi.id DESC
            """).fetchall()
            return jsonify([{
                "id": r["id"],
                "name": r["name"],
                "file_name": r["file_name"],
                "created_at": r["created_at"],
                "ref_count": r["ref_count"],
            } for r in rows])
    except Exception as e:
        logger.error("Image list error: %s", e)
        return jsonify({"status": "error", "error": str(e)}), 500


@images_bp.route("/api/images/upload", methods=["POST"])
def api_images_upload():
    """Upload a new filament image."""
    data_dir = _data_dir()
    try:
        name = (request.form.get("name") or "").strip()
        if not name:
            return jsonify({"status": "error", "error": "实物图名称不能为空"}), 400

        if "file" not in request.files:
            return jsonify({"status": "error", "error": "未选择文件"}), 400

        file = request.files["file"]
        if not file.filename:
            return jsonify({"status": "error", "error": "文件名为空"}), 400

        if not _allowed_file(file.filename):
            return jsonify({"status": "error", "error": "仅支持 jpg、jpeg、png、webp 格式"}), 400

        file.seek(0, 2)
        size = file.tell()
        file.seek(0)
        if size > MAX_FILE_SIZE:
            return jsonify({"status": "error", "error": "文件大小不能超过 5MB"}), 400

        ext = file.filename.rsplit(".", 1)[-1].lower()
        safe_name = f"{uuid.uuid4().hex}.{ext}"
        img_dir = _images_dir(data_dir)
        file.save(os.path.join(img_dir, safe_name))

        with get_db(data_dir) as conn:
            cursor = conn.execute(
                "INSERT INTO filament_images (name, file_name) VALUES (?, ?)",
                (name, safe_name),
            )
            conn.commit()
            return jsonify({"status": "success", "id": cursor.lastrowid, "file_name": safe_name})
    except Exception as e:
        logger.error("Image upload error: %s", e)
        return jsonify({"status": "error", "error": str(e)}), 500


@images_bp.route("/api/images/<int:image_id>", methods=["PUT", "DELETE"])
def api_image_single(image_id):
    data_dir = _data_dir()
    try:
        with get_db(data_dir) as conn:
            img = conn.execute(
                "SELECT * FROM filament_images WHERE id = ?", (image_id,)
            ).fetchone()
            if not img:
                return jsonify({"status": "error", "error": "实物图不存在"}), 404

            if request.method == "PUT":
                data = request.form or {}
                new_name = (data.get("name") or "").strip()

                if new_name:
                    conn.execute(
                        "UPDATE filament_images SET name = ? WHERE id = ?",
                        (new_name, image_id),
                    )

                # Optional: replace physical file
                if "file" in request.files and request.files["file"].filename:
                    file = request.files["file"]
                    if not _allowed_file(file.filename):
                        return jsonify({"status": "error", "error": "仅支持 jpg、jpeg、png、webp 格式"}), 400
                    file.seek(0, 2)
                    if file.tell() > MAX_FILE_SIZE:
                        return jsonify({"status": "error", "error": "文件大小不能超过 5MB"}), 400
                    file.seek(0)

                    # Remove old file if exists
                    old_path = os.path.join(_images_dir(data_dir), img["file_name"])
                    if os.path.isfile(old_path):
                        try:
                            os.remove(old_path)
                        except OSError as e:
                            logger.warning("Failed to remove old image: %s", e)

                    ext = file.filename.rsplit(".", 1)[-1].lower()
                    safe_name = f"{uuid.uuid4().hex}.{ext}"
                    file.save(os.path.join(_images_dir(data_dir), safe_name))
                    conn.execute(
                        "UPDATE filament_images SET file_name = ? WHERE id = ?",
                        (safe_name, image_id),
                    )

                conn.commit()
                return jsonify({"status": "success"})

            else:  # DELETE
                # Remove physical file if exists
                file_path = os.path.join(_images_dir(data_dir), img["file_name"])
                if os.path.isfile(file_path):
                    try:
                        os.remove(file_path)
                    except OSError as e:
                        logger.warning("Failed to remove image file: %s", e)

                conn.execute("DELETE FROM filament_images WHERE id = ?", (image_id,))
                conn.commit()
                return jsonify({"status": "success"})
    except Exception as e:
        logger.error("Image single error: %s", e)
        return jsonify({"status": "error", "error": str(e)}), 500
