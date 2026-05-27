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
        "material_type": row["material_type"],
        "color": row["color"],
        "location": row["location"],
        "status": row["status"] if "status" in keys else "全新",
        "initial_weight": row["initial_weight"],
        "current_weight": row["current_weight"],
        "is_favorite": bool(row["is_favorite"]),
        "created_at": row["created_at"],
        "purchase_date": row["purchase_date"],
        "purchase_price": row["purchase_price"],
        "opened_at": row["opened_at"],
        "image_id": row["image_id"] if "image_id" in keys else None,
        "remark": row["remark"] if "remark" in keys else None,
        "channel_id": row["channel_id"] if "channel_id" in keys else None,
        "brand_id": row["brand_id"] if "brand_id" in keys else None,
        "is_loaded": bool(row["is_loaded"]) if "is_loaded" in keys else False,
    }
    return result


# ─── Filament CRUD ───

@filaments_bp.route("/api/filaments", methods=["GET", "POST"])
def api_filaments():
    data_dir = _data_dir()
    try:
        with get_db(data_dir) as conn:
            if request.method == "GET":
                rows = conn.execute("""
                    SELECT f.*, fi.file_name AS image_file, ch.name AS channel_name,
                           b.name AS brand_name, b.spool_type, b.spool_weight
                    FROM filaments f
                    LEFT JOIN filament_images fi ON f.image_id = fi.id
                    LEFT JOIN channels ch ON f.channel_id = ch.id
                    LEFT JOIN brands b ON f.brand_id = b.id
                    ORDER BY f.is_favorite DESC, f.id DESC
                """).fetchall()
                result = []
                for r in rows:
                    d = _filament_to_dict(r)
                    d["image_file"] = r["image_file"] if "image_file" in r.keys() else None
                    d["channel_name"] = r["channel_name"] if "channel_name" in r.keys() else None
                    d["brand_name"] = r["brand_name"] if "brand_name" in r.keys() else None
                    d["spool_type"] = r["spool_type"] if "spool_type" in r.keys() else None
                    d["spool_weight"] = r["spool_weight"] if "spool_weight" in r.keys() else None
                    result.append(d)
                return jsonify(result)
            else:
                data = request.get_json()
                status = data.get("status", "全新")
                cursor = conn.execute(
                    """INSERT INTO filaments
                       (name, material_type, color, location,
                        initial_weight, current_weight, is_favorite, purchase_date,
                        purchase_price, opened_at, status, image_id, remark, channel_id, brand_id)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        data["name"],
                        data["material_type"], data["color"],
                        data.get("location", ""),
                        data.get("initial_weight", 1000.0),
                        data.get("current_weight", data.get("initial_weight", 1000.0)),
                        1 if data.get("is_favorite") else 0,
                        data.get("purchase_date"), data.get("purchase_price"),
                        data.get("opened_at"),
                        status,
                        data.get("image_id"),
                        data.get("remark"),
                        data.get("channel_id"),
                        data.get("brand_id"),
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
                    "name", "material_type", "color", "location",
                    "initial_weight", "current_weight", "is_favorite",
                    "purchase_date", "purchase_price", "opened_at",
                    "status", "image_id", "remark", "channel_id", "brand_id", "is_loaded",
                ]
                updates = {k: v for k, v in data.items() if k in allowed}
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
                       (name, material_type, color, location,
                        initial_weight, current_weight, is_favorite, purchase_date,
                        purchase_price, status, image_id, remark)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        data["name"],
                        data["material_type"], data["color"],
                        data.get("location", ""),
                        data.get("initial_weight", 1000.0),
                        data.get("current_weight", data.get("initial_weight", 1000.0)),
                        1 if data.get("is_favorite") else 0,
                        data.get("purchase_date"), data.get("purchase_price"),
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
                "UPDATE filaments SET current_weight = ?, status = ? WHERE id = ?",
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
                conn.execute(
                    "UPDATE filaments SET is_loaded = 0 WHERE id = ?",
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
                SELECT ur.*, f.name AS filament_name, f.material_type,
                       f.purchase_price, f.initial_weight
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
                    "material_type": r["material_type"],
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


@filaments_bp.route("/api/usage_records/<int:record_id>", methods=["PUT", "DELETE"])
def api_usage_record_modify(record_id):
    data_dir = _data_dir()
    try:
        with get_db(data_dir) as conn:
            record = conn.execute(
                "SELECT * FROM usage_records WHERE id = ?", (record_id,)
            ).fetchone()
            if not record:
                return jsonify({"status": "error", "error": "未找到对应的使用记录"}), 404

            if request.method == "PUT":
                data = request.get_json() or {}
                remark = data.get("remark")
                if remark is None:
                    return jsonify({"status": "error", "error": "缺少备注内容"}), 400
                conn.execute(
                    "UPDATE usage_records SET note = ? WHERE id = ?",
                    (str(remark) if remark else "", record_id),
                )
                conn.commit()
                return jsonify({"status": "success", "remark": remark})

            # DELETE
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
            all_filaments = conn.execute("""
                SELECT f.*, b.name AS brand_name
                FROM filaments f
                LEFT JOIN brands b ON f.brand_id = b.id
            """).fetchall()
            settings_row = conn.execute("SELECT * FROM settings WHERE id = 1").fetchone()
            threshold = settings_row["threshold"] if settings_row else 200

            # Apply status filter
            if filter_status == "remaining":
                filaments = [f for f in all_filaments if f["status"] != "用尽"]
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
                mfr = (f["brand_name"] if "brand_name" in f.keys() else "Unknown")
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

            # Remaining total weight (only active filaments)
            remaining_weight = round(sum(
                f["current_weight"] for f in all_filaments if f["status"] != "用尽"
            ), 2)

            # Total used weight (all time)
            total_used_weight = round(sum(
                r["total_used"] for r in usage_rows
            ), 2) if usage_rows else 0.0

            return jsonify({
                "total_filaments": total_filaments,
                "material_types": material_types,
                "favorites": favorites,
                "low_stock": low_stock,
                "threshold": threshold,
                "total_value": round(total_value, 2),
                "remaining_total_weight": remaining_weight,
                "total_used_weight": total_used_weight,
                "material_distribution": material_distribution,
                "stock_status": stock_status,
                "manufacturer_stats": mfr_stats_list,
                "usage_stats": usage_stats,
                "filter_status": filter_status,
            })
    except Exception as e:
        logger.error("Statistics error: %s", e)
        return jsonify({"status": "error", "error": str(e)}), 500


# ─── Cross Matrix Statistics ───

@filaments_bp.route("/api/stats/matrix", methods=["GET"])
def api_stats_matrix():
    """Return material_type × 5-state cross matrix with mutually exclusive statuses."""
    data_dir = _data_dir()
    matrix_filter = request.args.get("filter", "all")
    try:
        with get_db(data_dir) as conn:
            t_row = conn.execute(
                "SELECT CAST(value AS INTEGER) FROM system_settings WHERE key = 'low_weight_threshold'"
            ).fetchone()
            threshold = t_row[0] if t_row else 100

            rows = conn.execute("""
                SELECT
                    f.material_type,
                    SUM(CASE WHEN f.current_weight > :thresh AND f.status = '全新' THEN 1 ELSE 0 END) AS 全新,
                    SUM(CASE WHEN f.current_weight > :thresh AND f.status = '闲置' THEN 1 ELSE 0 END) AS 闲置,
                    SUM(CASE WHEN f.is_loaded = 1 THEN 1 ELSE 0 END) AS 上机,
                    SUM(CASE WHEN f.current_weight > 0 AND f.current_weight <= :thresh THEN 1 ELSE 0 END) AS 不足,
                    SUM(CASE WHEN f.current_weight = 0 THEN 1 ELSE 0 END) AS 用尽
                FROM filaments f
                GROUP BY f.material_type
                ORDER BY f.material_type
            """, {"thresh": threshold}).fetchall()

            matrix = []
            for r in rows:
                entry = {
                    "material_type": r["material_type"],
                    "全新": r["全新"], "闲置": r["闲置"], "上机": r["上机"],
                    "不足": r["不足"], "用尽": r["用尽"],
                }
                entry["total"] = entry["全新"] + entry["闲置"] + entry["上机"] + entry["不足"] + entry["用尽"]
                matrix.append(entry)

            # For pie chart: aggregate by filter
            statuses = ["全新", "闲置", "上机", "不足", "用尽"]
            if matrix_filter != "all" and matrix_filter in statuses:
                pie_data = [
                    {"material_type": m["material_type"], "count": m[matrix_filter]}
                    for m in matrix if m[matrix_filter] > 0
                ]
            else:
                pie_data = [
                    {"material_type": m["material_type"], "count": m["total"]}
                    for m in matrix if m["total"] > 0
                ]

            return jsonify({
                "matrix": matrix,
                "pie_data": pie_data,
                "threshold": threshold,
                "filter": matrix_filter,
            })
    except Exception as e:
        logger.error("Matrix stats error: %s", e)
        return jsonify({"status": "error", "error": str(e)}), 500


