"""Filament CRUD, usage records, statistics, import/export."""
import os
import csv
import io
import logging
from flask import current_app, jsonify, request, Response

from modules.filaments import filaments_bp
from modules.db import get_db

logger = logging.getLogger(__name__)


def _data_dir():
    return current_app.config.get("DATA_DIR", os.path.join(os.path.dirname(__file__), "..", "..", "data"))


def _filament_to_dict(row):
    return {
        "id": row["id"],
        "name": row["name"],
        "manufacturer": row["manufacturer"],
        "material_type": row["material_type"],
        "color": row["color"],
        "location": row["location"],
        "is_opened": bool(row["is_opened"]),
        "initial_weight": row["initial_weight"],
        "current_weight": row["current_weight"],
        "is_favorite": bool(row["is_favorite"]),
        "created_at": row["created_at"],
        "purchase_date": row["purchase_date"],
        "purchase_price": row["purchase_price"],
        "purchase_channel": row["purchase_channel"],
        "opened_at": row["opened_at"],
    }


# ─── Filament CRUD ───

@filaments_bp.route("/api/filaments", methods=["GET", "POST"])
def api_filaments():
    data_dir = _data_dir()
    try:
        with get_db(data_dir) as conn:
            if request.method == "GET":
                rows = conn.execute("SELECT * FROM filaments ORDER BY id DESC").fetchall()
                return jsonify([_filament_to_dict(r) for r in rows])
            else:
                data = request.get_json()
                cursor = conn.execute(
                    """INSERT INTO filaments
                       (name, manufacturer, material_type, color, location, is_opened,
                        initial_weight, current_weight, is_favorite, purchase_date,
                        purchase_price, purchase_channel, opened_at)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        data["name"], data.get("manufacturer", ""),
                        data["material_type"], data["color"],
                        data.get("location", ""),
                        1 if data.get("is_opened") else 0,
                        data.get("initial_weight", 1000.0),
                        data.get("current_weight", data.get("initial_weight", 1000.0)),
                        1 if data.get("is_favorite") else 0,
                        data.get("purchase_date"), data.get("purchase_price"),
                        data.get("purchase_channel"), data.get("opened_at"),
                    ),
                )
                conn.commit()
                return jsonify({"status": "success", "id": cursor.lastrowid})
    except Exception as e:
        logger.error("Filaments error: %s", e)
        return jsonify({"status": "error", "error": str(e)}), 500


@filaments_bp.route("/api/filaments/<int:filament_id>", methods=["PUT", "DELETE"])
def api_filament_single(filament_id):
    data_dir = _data_dir()
    try:
        with get_db(data_dir) as conn:
            if request.method == "PUT":
                data = request.get_json()
                allowed = [
                    "name", "manufacturer", "material_type", "color", "location",
                    "is_opened", "initial_weight", "current_weight", "is_favorite",
                    "purchase_date", "purchase_price", "purchase_channel", "opened_at",
                ]
                updates = {k: v for k, v in data.items() if k in allowed}
                if "is_opened" in updates:
                    updates["is_opened"] = 1 if updates["is_opened"] else 0
                if "is_favorite" in updates:
                    updates["is_favorite"] = 1 if updates["is_favorite"] else 0
                if updates:
                    sets = ", ".join(f"{k} = ?" for k in updates)
                    values = list(updates.values()) + [filament_id]
                    conn.execute(
                        f"UPDATE filaments SET {sets} WHERE id = ?", values
                    )
                    conn.commit()
                return jsonify({"status": "success"})
            else:
                conn.execute("DELETE FROM usage_records WHERE filament_id = ?", (filament_id,))
                conn.execute("DELETE FROM filaments WHERE id = ?", (filament_id,))
                conn.commit()
                return jsonify({"status": "success"})
    except Exception as e:
        logger.error("Filament single error: %s", e)
        return jsonify({"status": "error", "error": str(e)}), 500


@filaments_bp.route("/api/filaments/batch", methods=["POST"])
def api_filaments_batch():
    data_dir = _data_dir()
    try:
        with get_db(data_dir) as conn:
            items = request.get_json()
            for data in items:
                conn.execute(
                    """INSERT INTO filaments
                       (name, manufacturer, material_type, color, location, is_opened,
                        initial_weight, current_weight, is_favorite, purchase_date,
                        purchase_price, purchase_channel)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        data["name"], data.get("manufacturer", ""),
                        data["material_type"], data["color"],
                        data.get("location", ""),
                        1 if data.get("is_opened") else 0,
                        data.get("initial_weight", 1000.0),
                        data.get("current_weight", data.get("initial_weight", 1000.0)),
                        1 if data.get("is_favorite") else 0,
                        data.get("purchase_date"), data.get("purchase_price"),
                        data.get("purchase_channel"),
                    ),
                )
            conn.commit()
            return jsonify({"status": "success", "count": len(items)})
    except Exception as e:
        logger.error("Batch create error: %s", e)
        return jsonify({"status": "error", "error": str(e)}), 500


@filaments_bp.route("/api/filaments/delete-multiple", methods=["POST"])
def api_filaments_delete_multiple():
    data_dir = _data_dir()
    try:
        with get_db(data_dir) as conn:
            data = request.get_json() or {}
            ids = data.get("ids", [])
            if not ids:
                return jsonify({"status": "error", "error": "No IDs provided"}), 400
            placeholders = ",".join("?" for _ in ids)
            conn.execute(
                f"DELETE FROM usage_records WHERE filament_id IN ({placeholders})", ids
            )
            conn.execute(
                f"DELETE FROM filaments WHERE id IN ({placeholders})", ids
            )
            conn.commit()
            return jsonify({"status": "success", "count": len(ids)})
    except Exception as e:
        logger.error("Batch delete error: %s", e)
        return jsonify({"status": "error", "error": str(e)}), 500


@filaments_bp.route("/api/filaments/<int:filament_id>/use", methods=["POST"])
def api_filament_use(filament_id):
    data_dir = _data_dir()
    try:
        with get_db(data_dir) as conn:
            data = request.get_json()
            used_weight = float(data["used_weight"])
            note = data.get("note", "")

            filament = conn.execute(
                "SELECT * FROM filaments WHERE id = ?", (filament_id,)
            ).fetchone()
            if not filament:
                return jsonify({"status": "error", "error": "Filament not found"}), 404

            new_weight = max(0, filament["current_weight"] - used_weight)
            conn.execute(
                "UPDATE filaments SET current_weight = ?, is_opened = 1 WHERE id = ?",
                (new_weight, filament_id),
            )
            conn.execute(
                "INSERT INTO usage_records (filament_id, used_weight, note) VALUES (?, ?, ?)",
                (filament_id, used_weight, note),
            )
            conn.commit()
            return jsonify({"status": "success", "current_weight": new_weight})
    except Exception as e:
        logger.error("Filament use error: %s", e)
        return jsonify({"status": "error", "error": str(e)}), 500


# ─── Usage Records ───

@filaments_bp.route("/api/usage_records", methods=["GET"])
def api_usage_records():
    data_dir = _data_dir()
    try:
        with get_db(data_dir) as conn:
            rows = conn.execute("""
                SELECT ur.*, f.name AS filament_name, f.purchase_price, f.initial_weight
                FROM usage_records ur
                JOIN filaments f ON ur.filament_id = f.id
                ORDER BY ur.id DESC
            """).fetchall()
            result = []
            for r in rows:
                used_cost = 0.0
                if r["purchase_price"] and r["initial_weight"] and r["initial_weight"] > 0:
                    used_cost = round(
                        (float(r["purchase_price"]) / float(r["initial_weight"])) * float(r["used_weight"]), 2
                    )
                result.append({
                    "id": r["id"],
                    "filament_id": r["filament_id"],
                    "filament_name": r["filament_name"],
                    "used_weight": r["used_weight"],
                    "note": r["note"],
                    "used_at": r["used_at"],
                    "purchase_price": r["purchase_price"],
                    "initial_weight": r["initial_weight"],
                    "used_cost": used_cost,
                })
            return jsonify(result)
    except Exception as e:
        logger.error("Usage records error: %s", e)
        return jsonify({"status": "error", "error": str(e)}), 500


@filaments_bp.route("/api/usage_records/<int:record_id>", methods=["DELETE"])
def api_usage_record_delete(record_id):
    data_dir = _data_dir()
    try:
        with get_db(data_dir) as conn:
            record = conn.execute(
                "SELECT * FROM usage_records WHERE id = ?", (record_id,)
            ).fetchone()
            if not record:
                return jsonify({"status": "error", "error": "Record not found"}), 404

            filament = conn.execute(
                "SELECT * FROM filaments WHERE id = ?", (record["filament_id"],)
            ).fetchone()
            if filament:
                new_weight = filament["current_weight"] + record["used_weight"]
                conn.execute(
                    "UPDATE filaments SET current_weight = ? WHERE id = ?",
                    (new_weight, filament["id"]),
                )
            conn.execute("DELETE FROM usage_records WHERE id = ?", (record_id,))
            conn.commit()
            return jsonify({"status": "success"})
    except Exception as e:
        logger.error("Usage record delete error: %s", e)
        return jsonify({"status": "error", "error": str(e)}), 500


# ─── Statistics ───

@filaments_bp.route("/api/statistics", methods=["GET"])
def api_statistics():
    data_dir = _data_dir()
    try:
        with get_db(data_dir) as conn:
            filaments = conn.execute("SELECT * FROM filaments").fetchall()
            settings_row = conn.execute("SELECT * FROM settings WHERE id = 1").fetchone()
            threshold = settings_row["threshold"] if settings_row else 200

            total_filaments = len(filaments)
            total_value = sum(
                (f["purchase_price"] or 0) * (f["current_weight"] / f["initial_weight"])
                if f["initial_weight"] and f["initial_weight"] > 0 and f["purchase_price"]
                else 0
                for f in filaments
            )
            favorites = sum(1 for f in filaments if f["is_favorite"])
            low_stock = sum(
                1 for f in filaments
                if f["current_weight"] > 0 and f["current_weight"] < threshold
            )
            material_types = len(set(f["material_type"] for f in filaments))

            material_distribution = {}
            for f in filaments:
                mt = f["material_type"]
                material_distribution[mt] = material_distribution.get(mt, 0) + 1

            stock_status = {
                "unopened": sum(1 for f in filaments if not f["is_opened"]),
                "sufficient": sum(
                    1 for f in filaments
                    if f["is_opened"] and f["current_weight"] >= threshold
                ),
                "insufficient": low_stock,
                "normal": sum(
                    1 for f in filaments
                    if f["current_weight"] >= threshold and not f["is_opened"]
                ),
                "used_up": sum(1 for f in filaments if f["current_weight"] == 0),
            }

            manufacturer_stats = {}
            for f in filaments:
                mfr = f["manufacturer"] or "Unknown"
                if mfr not in manufacturer_stats:
                    manufacturer_stats[mfr] = {
                        "manufacturer": mfr,
                        "total_filaments": 0,
                        "total_weight": 0,
                        "total_value": 0,
                        "low_stock_count": 0,
                        "used_up_count": 0,
                        "distinct_colors": set(),
                        "distinct_materials": set(),
                    }
                s = manufacturer_stats[mfr]
                s["total_filaments"] += 1
                s["total_weight"] += f["current_weight"]
                val = 0.0
                if f["purchase_price"] and f["initial_weight"] and f["initial_weight"] > 0:
                    val = float(f["purchase_price"]) * (f["current_weight"] / float(f["initial_weight"]))
                s["total_value"] += val
                if 0 < f["current_weight"] < threshold:
                    s["low_stock_count"] += 1
                if f["current_weight"] == 0:
                    s["used_up_count"] += 1
                s["distinct_colors"].add(f["color"])
                s["distinct_materials"].add(f["material_type"])

            mfr_stats_list = []
            for mfr, s in manufacturer_stats.items():
                s["distinct_colors"] = len(s["distinct_colors"])
                s["distinct_materials"] = len(s["distinct_materials"])
                s["total_value"] = round(s["total_value"], 2)
                s["total_weight"] = round(s["total_weight"], 2)
                mfr_stats_list.append(s)

            usage_rows = conn.execute("""
                SELECT strftime('%Y-%m', used_at) AS month, SUM(used_weight) AS total_used
                FROM usage_records
                GROUP BY month
                ORDER BY month DESC
                LIMIT 12
            """).fetchall()
            usage_stats = [{"month": r["month"], "total_used": r["total_used"]} for r in usage_rows]

            return jsonify({
                "total_filaments": total_filaments,
                "material_types": material_types,
                "favorites": favorites,
                "low_stock": low_stock,
                "threshold": threshold,
                "total_value": round(total_value, 2),
                "material_distribution": material_distribution,
                "stock_status": stock_status,
                "manufacturer_stats": mfr_stats_list,
                "usage_stats": usage_stats,
            })
    except Exception as e:
        logger.error("Statistics error: %s", e)
        return jsonify({"status": "error", "error": str(e)}), 500


# ─── Export / Import ───

@filaments_bp.route("/api/export", methods=["GET"])
def api_export():
    data_dir = _data_dir()
    try:
        with get_db(data_dir) as conn:
            rows = conn.execute("SELECT * FROM filaments ORDER BY id").fetchall()
            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerow([
                "id", "name", "manufacturer", "material_type", "color", "location",
                "is_opened", "initial_weight", "current_weight", "is_favorite",
                "created_at", "purchase_date", "purchase_price", "purchase_channel",
                "opened_at",
            ])
            for r in rows:
                writer.writerow([r[c] for c in r.keys()])
            csv_content = output.getvalue()
            output.close()
            return Response(
                csv_content,
                mimetype="text/csv",
                headers={"Content-Disposition": "attachment; filename=filament_inventory.csv"},
            )
    except Exception as e:
        logger.error("Export error: %s", e)
        return jsonify({"status": "error", "error": str(e)}), 500


@filaments_bp.route("/api/import", methods=["POST"])
def api_import():
    data_dir = _data_dir()
    if "file" not in request.files:
        return jsonify({"status": "error", "error": "No file uploaded"}), 400
    file = request.files["file"]
    if not file.filename:
        return jsonify({"status": "error", "error": "Empty filename"}), 400
    try:
        with get_db(data_dir) as conn:
            content = file.read().decode("utf-8-sig")
            reader = csv.DictReader(io.StringIO(content))
            added, updated, skipped = 0, 0, 0
            for row in reader:
                if not row.get("name"):
                    skipped += 1
                    continue
                existing = conn.execute(
                    "SELECT id FROM filaments WHERE name = ?", (row["name"],)
                ).fetchone()
                if existing:
                    conn.execute(
                        """UPDATE filaments SET manufacturer=?, material_type=?, color=?,
                           location=?, is_opened=?, initial_weight=?, current_weight=?,
                           is_favorite=?, purchase_date=?, purchase_price=?,
                           purchase_channel=?, opened_at=? WHERE id=?""",
                        (
                            row.get("manufacturer", ""), row.get("material_type", ""),
                            row.get("color", ""), row.get("location", ""),
                            int(row.get("is_opened", 0)),
                            float(row.get("initial_weight", 1000)),
                            float(row.get("current_weight", 1000)),
                            int(row.get("is_favorite", 0)),
                            row.get("purchase_date"), row.get("purchase_price", ""),
                            row.get("purchase_channel", ""), row.get("opened_at"),
                            existing["id"],
                        ),
                    )
                    updated += 1
                else:
                    conn.execute(
                        """INSERT INTO filaments
                           (name, manufacturer, material_type, color, location,
                            is_opened, initial_weight, current_weight, is_favorite,
                            purchase_date, purchase_price, purchase_channel, opened_at)
                           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                        (
                            row["name"], row.get("manufacturer", ""),
                            row.get("material_type", ""), row.get("color", ""),
                            row.get("location", ""), int(row.get("is_opened", 0)),
                            float(row.get("initial_weight", 1000)),
                            float(row.get("current_weight", 1000)),
                            int(row.get("is_favorite", 0)),
                            row.get("purchase_date"), row.get("purchase_price", ""),
                            row.get("purchase_channel", ""), row.get("opened_at"),
                        ),
                    )
                    added += 1
            conn.commit()
            return jsonify({
                "status": "success",
                "added": added,
                "updated": updated,
                "skipped": skipped,
            })
    except Exception as e:
        logger.error("Import error: %s", e)
        return jsonify({"status": "error", "error": str(e)}), 500
