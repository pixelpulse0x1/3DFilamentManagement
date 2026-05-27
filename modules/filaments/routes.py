"""Filament CRUD, usage records, statistics."""
import os
import logging
from flask import current_app, jsonify, request

from modules.filaments import filaments_bp
from modules.db import get_db

logger = logging.getLogger(__name__)


def _data_dir():
    return current_app.config.get("DATA_DIR", os.path.join(os.path.dirname(__file__), "..", "..", "data"))


def _filament_to_dict(row):
    keys = row.keys()
    result = {
        "id": row["id"],
        "name": row["name"],
        "manufacturer": row["manufacturer"],
        "material_type": row["material_type"],
        "color": row["color"],
        "location": row["location"],
        "is_opened": bool(row["is_opened"]),
        "status": row["status"] if "status" in keys else ("闲置" if row["is_opened"] else "全新"),
        "initial_weight": row["initial_weight"],
        "current_weight": row["current_weight"],
        "is_favorite": bool(row["is_favorite"]),
        "created_at": row["created_at"],
        "purchase_date": row["purchase_date"],
        "purchase_price": row["purchase_price"],
        "purchase_channel": row["purchase_channel"],
        "opened_at": row["opened_at"],
    }
    if "image_id" in keys:
        result["image_id"] = row["image_id"]
    if "remark" in keys:
        result["remark"] = row["remark"]
    return result


# ─── Filament CRUD ───

@filaments_bp.route("/api/filaments", methods=["GET", "POST"])
def api_filaments():
    data_dir = _data_dir()
    try:
        with get_db(data_dir) as conn:
            if request.method == "GET":
                rows = conn.execute("""
                    SELECT f.*, fi.file_name AS image_file, ch.name AS channel_name
                    FROM filaments f
                    LEFT JOIN filament_images fi ON f.image_id = fi.id
                    LEFT JOIN channels ch ON f.channel_id = ch.id
                    ORDER BY f.id DESC
                """).fetchall()
                result = []
                for r in rows:
                    d = _filament_to_dict(r)
                    d["image_file"] = r["image_file"] if "image_file" in r.keys() else None
                    d["channel_name"] = r["channel_name"] if "channel_name" in r.keys() else None
                    result.append(d)
                return jsonify(result)
            else:
                data = request.get_json()
                # Determine initial status from legacy is_opened or new status field
                status = data.get("status", "全新")
                if "is_opened" in data and "status" not in data:
                    status = "闲置" if data.get("is_opened") else "全新"
                cursor = conn.execute(
                    """INSERT INTO filaments
                       (name, manufacturer, material_type, color, location, is_opened,
                        initial_weight, current_weight, is_favorite, purchase_date,
                        purchase_price, purchase_channel, opened_at, status, image_id, remark, channel_id)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        data["name"], data.get("manufacturer", ""),
                        data["material_type"], data["color"],
                        data.get("location", ""),
                        1 if data.get("is_opened") or status in ("闲置", "上机", "用尽") else 0,
                        data.get("initial_weight", 1000.0),
                        data.get("current_weight", data.get("initial_weight", 1000.0)),
                        1 if data.get("is_favorite") else 0,
                        data.get("purchase_date"), data.get("purchase_price"),
                        data.get("purchase_channel"), data.get("opened_at"),
                        status,
                        data.get("image_id"),
                        data.get("remark"),
                        data.get("channel_id"),
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
                    "status", "image_id", "remark", "channel_id",
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
                filament = conn.execute(
                    "SELECT * FROM filaments WHERE id = ?", (filament_id,)
                ).fetchone()
                if not filament:
                    return jsonify({"status": "error", "error": "耗材不存在"}), 404
                if filament["status"] == "上机":
                    return jsonify({
                        "status": "error",
                        "error": "该耗材正处于上机状态，请先下机后再执行删除",
                    }), 400
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
                        purchase_price, purchase_channel, status, image_id, remark)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        data["name"], data.get("manufacturer", ""),
                        data["material_type"], data["color"],
                        data.get("location", ""),
                        0,
                        data.get("initial_weight", 1000.0),
                        data.get("current_weight", data.get("initial_weight", 1000.0)),
                        1 if data.get("is_favorite") else 0,
                        data.get("purchase_date"), data.get("purchase_price"),
                        data.get("purchase_channel"),
                        "全新",
                        data.get("image_id"),
                        data.get("remark"),
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
            # Block deletion of any 上机 filaments
            placeholders = ",".join("?" for _ in ids)
            active = conn.execute(
                f"SELECT id FROM filaments WHERE id IN ({placeholders}) AND status = '上机'", ids
            ).fetchall()
            if active:
                return jsonify({
                    "status": "error",
                    "error": "选中的耗材中有处于上机状态的，请先下机后再执行删除",
                }), 400
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

            new_weight = round(max(0, filament["current_weight"] - used_weight), 2)
            new_status = "用尽" if new_weight == 0 else filament["status"]
            conn.execute(
                "UPDATE filaments SET current_weight = ?, is_opened = 1, status = ? WHERE id = ?",
                (new_weight, new_status, filament_id),
            )
            conn.execute(
                "INSERT INTO usage_records (filament_id, used_weight, note) VALUES (?, ?, ?)",
                (filament_id, used_weight, note),
            )
            # Auto-unbind from printer slot when depleted
            if new_weight == 0:
                conn.execute(
                    "UPDATE printer_slots SET current_filament_id = NULL WHERE current_filament_id = ?",
                    (filament_id,),
                )
            conn.commit()
            return jsonify({
                "status": "success",
                "current_weight": round(new_weight, 2),
                "auto_unbound": new_weight == 0,
            })
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
                new_weight = round(filament["current_weight"] + record["used_weight"], 2)
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
    filter_status = request.args.get("filter", "all")  # all | remaining | used
    try:
        with get_db(data_dir) as conn:
            all_filaments = conn.execute("SELECT * FROM filaments").fetchall()
            settings_row = conn.execute("SELECT * FROM settings WHERE id = 1").fetchone()
            threshold = settings_row["threshold"] if settings_row else 200

            # Apply status filter
            if filter_status == "remaining":
                filaments = [f for f in all_filaments if f["status"] in ("全新", "闲置", "上机")]
            elif filter_status == "used":
                filaments = [f for f in all_filaments if f["status"] == "用尽"]
            else:
                filaments = all_filaments

            total_filaments = len(filaments)

            if filter_status == "used":
                total_value = sum(
                    (f["purchase_price"] or 0)
                    for f in filaments
                    if f["purchase_price"]
                )
            elif filter_status == "remaining":
                total_value = sum(
                    (f["purchase_price"] or 0) * (f["current_weight"] / f["initial_weight"])
                    if f["initial_weight"] and f["initial_weight"] > 0 and f["purchase_price"]
                    else 0
                    for f in filaments
                )
            else:
                # all = remaining value + used-up full purchase price
                total_value = 0.0
                for f in filaments:
                    price = f["purchase_price"] or 0
                    if not price:
                        continue
                    if f["current_weight"] > 0 and f["initial_weight"] and f["initial_weight"] > 0:
                        total_value += price * (f["current_weight"] / f["initial_weight"])
                    elif f["current_weight"] == 0:
                        total_value += price

            favorites = sum(1 for f in filaments if f["is_favorite"])
            low_stock = sum(
                1 for f in filaments
                if f["status"] != "用尽" and f["current_weight"] > 0 and f["current_weight"] < threshold
            )
            material_types = len(set(f["material_type"] for f in filaments))

            material_distribution = {}
            for f in filaments:
                mt = f["material_type"]
                material_distribution[mt] = material_distribution.get(mt, 0) + 1

            stock_status = {
                "unopened": sum(1 for f in filaments if f["status"] == "全新"),
                "sufficient": sum(
                    1 for f in filaments
                    if f["status"] in ("闲置", "上机") and f["current_weight"] >= threshold
                ),
                "insufficient": low_stock,
                "normal": sum(
                    1 for f in filaments
                    if f["status"] == "全新" and f["current_weight"] >= threshold
                ),
                "used_up": sum(1 for f in filaments if f["status"] == "用尽"),
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
                if f["purchase_price"]:
                    if filter_status == "used":
                        s["total_value"] += float(f["purchase_price"])
                    elif filter_status == "remaining":
                        if f["initial_weight"] and f["initial_weight"] > 0:
                            s["total_value"] += float(f["purchase_price"]) * (f["current_weight"] / float(f["initial_weight"]))
                    else:
                        # all: remaining value + used-up full price
                        if f["current_weight"] == 0:
                            s["total_value"] += float(f["purchase_price"])
                        elif f["initial_weight"] and f["initial_weight"] > 0:
                            s["total_value"] += float(f["purchase_price"]) * (f["current_weight"] / float(f["initial_weight"]))
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
                "filter_status": filter_status,
            })
    except Exception as e:
        logger.error("Statistics error: %s", e)
        return jsonify({"status": "error", "error": str(e)}), 500


