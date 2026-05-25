"""Data migration utilities for importing from legacy sources."""
import os
import sqlite3
import logging

logger = logging.getLogger(__name__)


def migrate_from_db(source_path, data_dir):
    """Import filaments, usage_records, settings from a legacy DB file.

    Returns (added_filaments, added_records, updated_settings, errors).
    """
    added_filaments = 0
    added_records = 0
    updated_settings = 0
    errors = []

    from modules.db import get_db_path, get_db

    if not os.path.isfile(source_path):
        return 0, 0, 0, ["源数据库文件不存在"]

    try:
        src_conn = sqlite3.connect(source_path)
        src_conn.row_factory = sqlite3.Row
    except sqlite3.Error as e:
        return 0, 0, 0, [f"无法打开源数据库: {e}"]

    try:
        # Check if source has the expected tables
        tables = src_conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()
        table_names = {r["name"] for r in tables}

        with get_db(data_dir) as dst_conn:
            # --- Migrate filaments ---
            if "filaments" in table_names:
                src_rows = src_conn.execute("SELECT * FROM filaments").fetchall()
                existing_names = {
                    r["name"] for r in dst_conn.execute("SELECT name FROM filaments").fetchall()
                }
                for row in src_rows:
                    name = row["name"]
                    if name in existing_names:
                        continue  # skip duplicates by name
                    try:
                        dst_conn.execute(
                            """INSERT INTO filaments
                               (name, manufacturer, material_type, color, location,
                                is_opened, initial_weight, current_weight, is_favorite,
                                created_at, purchase_date, purchase_price,
                                purchase_channel, opened_at)
                               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                            (
                                name,
                                row["manufacturer"] if "manufacturer" in row.keys() else "",
                                row["material_type"] if "material_type" in row.keys() else "",
                                row["color"] if "color" in row.keys() else "#000000",
                                row["location"] if "location" in row.keys() else "",
                                row["is_opened"] if "is_opened" in row.keys() else 0,
                                row["initial_weight"] if "initial_weight" in row.keys() else 1000.0,
                                row["current_weight"] if "current_weight" in row.keys() else 1000.0,
                                row["is_favorite"] if "is_favorite" in row.keys() else 0,
                                row["created_at"] if "created_at" in row.keys() else None,
                                row["purchase_date"] if "purchase_date" in row.keys() else None,
                                row["purchase_price"] if "purchase_price" in row.keys() else None,
                                row["purchase_channel"] if "purchase_channel" in row.keys() else None,
                                row["opened_at"] if "opened_at" in row.keys() else None,
                            ),
                        )
                        added_filaments += 1
                    except sqlite3.Error as e:
                        errors.append(f"导入耗材 {name} 失败: {e}")

            # --- Migrate usage_records ---
            if "usage_records" in table_names and added_filaments > 0:
                src_records = src_conn.execute("SELECT * FROM usage_records").fetchall()
                for row in src_records:
                    try:
                        dst_conn.execute(
                            """INSERT INTO usage_records
                               (filament_id, used_weight, note, used_at)
                               VALUES (?, ?, ?, ?)""",
                            (
                                row["filament_id"] if "filament_id" in row.keys() else None,
                                row["used_weight"] if "used_weight" in row.keys() else 0,
                                row["note"] if "note" in row.keys() else "",
                                row["used_at"] if "used_at" in row.keys() else None,
                            ),
                        )
                        added_records += 1
                    except sqlite3.Error as e:
                        errors.append(f"导入使用记录 {row['id']} 失败: {e}")

            # --- Migrate settings ---
            if "settings" in table_names:
                src_setting = src_conn.execute(
                    "SELECT * FROM settings WHERE id = 1"
                ).fetchone()
                if src_setting:
                    try:
                        dst_conn.execute(
                            "UPDATE settings SET threshold = ?, default_weight = ? WHERE id = 1",
                            (
                                src_setting["threshold"] if "threshold" in src_setting.keys() else 200,
                                src_setting["default_weight"] if "default_weight" in src_setting.keys() else 1000.0,
                            ),
                        )
                        updated_settings = 1
                    except sqlite3.Error as e:
                        errors.append(f"导入设置失败: {e}")

            dst_conn.commit()

    except Exception as e:
        errors.append(f"迁移过程异常: {e}")
    finally:
        src_conn.close()

    return added_filaments, added_records, updated_settings, errors


def migrate_from_txt(file_storage, table_name, data_dir):
    """Import lines from a txt file into the materials or manufacturers table.

    Returns (added, skipped, errors).
    """
    added = 0
    skipped = 0
    errors = []

    from modules.db import get_db_path, get_db

    try:
        content = file_storage.read().decode("utf-8-sig")
        lines = [line.strip() for line in content.splitlines() if line.strip()]
    except Exception as e:
        return 0, 0, [f"无法读取文件: {e}"]

    if not lines:
        return 0, 0, ["文件中没有有效数据"]

    try:
        with get_db(data_dir) as conn:
            existing = {
                r["name"]
                for r in conn.execute(f"SELECT name FROM {table_name}").fetchall()
            }
            for name in lines:
                if name in existing:
                    skipped += 1
                    continue
                try:
                    conn.execute(
                        f"INSERT INTO {table_name} (name) VALUES (?)", (name,)
                    )
                    added += 1
                except sqlite3.Error as e:
                    errors.append(f"导入 {name} 失败: {e}")
            conn.commit()
    except Exception as e:
        errors.append(f"数据库操作异常: {e}")

    return added, skipped, errors
