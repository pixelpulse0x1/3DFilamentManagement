"""Background image helpers for settings module."""
import os
import uuid
import logging

logger = logging.getLogger(__name__)

ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "webp"}


def get_background_dir(static_folder):
    return os.path.join(static_folder, "uploads", "backgrounds")


def get_active_background(data_dir, static_folder):
    """Get the active background filename from system_settings."""
    import sqlite3
    from modules.db import get_db_path

    db_path = get_db_path(data_dir)
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        row = conn.execute(
            "SELECT value FROM system_settings WHERE key = 'active_background'"
        ).fetchone()
        conn.close()
        filename = row["value"] if row else ""
        if filename:
            bg_path = os.path.join(get_background_dir(static_folder), filename)
            if not os.path.isfile(bg_path):
                return ""
        return filename
    except sqlite3.Error as e:
        logger.error("Failed to get active background: %s", e)
        return ""


def list_backgrounds(static_folder):
    """List all uploaded background filenames."""
    bg_dir = get_background_dir(static_folder)
    try:
        os.makedirs(bg_dir, exist_ok=True)
        return sorted(
            f for f in os.listdir(bg_dir)
            if os.path.isfile(os.path.join(bg_dir, f))
            and f.rsplit(".", 1)[-1].lower() in ALLOWED_EXTENSIONS
        )
    except OSError as e:
        logger.error("Failed to list backgrounds: %s", e)
        return []


def upload_background(file_storage, static_folder):
    """Validate and save a background image. Returns (success, message, filename)."""
    if not file_storage or not file_storage.filename:
        return False, "未选择文件", None

    ext = file_storage.filename.rsplit(".", 1)[-1].lower() if "." in file_storage.filename else ""
    if ext not in ALLOWED_EXTENSIONS:
        return False, "仅支持 jpg、jpeg、png、webp 格式的图片", None

    safe_name = f"{uuid.uuid4().hex}.{ext}"
    bg_dir = get_background_dir(static_folder)
    try:
        os.makedirs(bg_dir, exist_ok=True)
        file_storage.save(os.path.join(bg_dir, safe_name))
        return True, "上传成功", safe_name
    except OSError as e:
        logger.error("Failed to save background: %s", e)
        return False, "文件保存失败，请检查磁盘权限", None


def set_active_background(data_dir, filename):
    """Set the active background in system_settings."""
    import sqlite3
    from modules.db import get_db_path

    db_path = get_db_path(data_dir)
    try:
        conn = sqlite3.connect(db_path)
        conn.execute(
            "INSERT INTO system_settings (key, value) VALUES ('active_background', ?) "
            "ON CONFLICT(key) DO UPDATE SET value = ?",
            (filename, filename),
        )
        conn.commit()
        conn.close()
        return True
    except sqlite3.Error as e:
        logger.error("Failed to set active background: %s", e)
        return False
