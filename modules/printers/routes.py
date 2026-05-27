"""Printer and slot management REST API."""
import os
import logging
from flask import current_app, jsonify, request

from modules.printers import printers_bp
from modules.db import get_db

logger = logging.getLogger(__name__)


def _data_dir():
    return current_app.config.get("DATA_DIR", os.path.join(os.path.dirname(__file__), "..", "..", "data"))


def _printer_to_dict(row):
    return {
        "id": row["id"], "name": row["name"], "model": row["model"],
        "model_id": row["model_id"] if "model_id" in row.keys() else None,
        "pm_name": row["pm_name"] if "pm_name" in row.keys() else None,
        "pm_brand": row["pm_brand"] if "pm_brand" in row.keys() else None,
        "bed_size": row["bed_size"] if "bed_size" in row.keys() else None,
    }


def _slot_to_dict(row):
    return {
        "id": row["id"],
        "printer_id": row["printer_id"],
        "slot_name": row["slot_name"],
        "current_filament_id": row["current_filament_id"],
    }


# ─── Printer CRUD ───

@printers_bp.route("/api/printers", methods=["GET", "POST"])
def api_printers():
    data_dir = _data_dir()
    try:
        with get_db(data_dir) as conn:
            if request.method == "GET":
                printers = conn.execute("""
                    SELECT p.*, pm.model_name AS pm_name, pm.brand AS pm_brand, pm.bed_size
                    FROM printers p
                    LEFT JOIN printer_models pm ON p.model_id = pm.id
                    ORDER BY p.id
                """).fetchall()
                result = []
                for p in printers:
                    pd = _printer_to_dict(p)
                    slots = conn.execute(
                        "SELECT ps.*, f.name AS f_name, f.material_type, "
                        "f.color, f.current_weight, f.initial_weight, f.status, "
                        "f.image_id, fi.file_name AS image_file, "
                        "b.name AS brand_name, b.spool_type, b.spool_weight "
                        "FROM printer_slots ps "
                        "LEFT JOIN filaments f ON ps.current_filament_id = f.id "
                        "LEFT JOIN filament_images fi ON f.image_id = fi.id "
                        "LEFT JOIN brands b ON f.brand_id = b.id "
                        "WHERE ps.printer_id = ? "
                        "ORDER BY ps.id",
                        (p["id"],),
                    ).fetchall()
                    pd["slots"] = []
                    for s in slots:
                        sd = _slot_to_dict(s)
                        if s["current_filament_id"]:
                            sd["filament"] = {
                                "id": s["current_filament_id"],
                                "name": s["f_name"],
                                "material_type": s["material_type"],
                                "color": s["color"],
                                "current_weight": s["current_weight"],
                                "initial_weight": s["initial_weight"],
                                "status": s["status"],
                                "image_id": s["image_id"],
                                "image_file": s["image_file"],
                                "brand_name": s["brand_name"],
                                "spool_type": s["spool_type"],
                                "spool_weight": s["spool_weight"],
                            }
                        else:
                            sd["filament"] = None
                        pd["slots"].append(sd)
                    result.append(pd)
                return jsonify(result)

            else:
                data = request.get_json() or {}
                name = data.get("name", "").strip()
                if not name:
                    return jsonify({"status": "error", "error": "打印机名称不能为空"}), 400
                model = data.get("model", "").strip()
                model_id = data.get("model_id")
                cursor = conn.execute(
                    "INSERT INTO printers (name, model, model_id) VALUES (?, ?, ?)",
                    (name, model, model_id),
                )
                conn.commit()
                return jsonify({"status": "success", "id": cursor.lastrowid})
    except Exception as e:
        logger.error("Printers error: %s", e)
        return jsonify({"status": "error", "error": str(e)}), 500


@printers_bp.route("/api/printers/<int:printer_id>", methods=["DELETE"])
def api_printer_delete(printer_id):
    data_dir = _data_dir()
    try:
        with get_db(data_dir) as conn:
            printer = conn.execute(
                "SELECT * FROM printers WHERE id = ?", (printer_id,)
            ).fetchone()
            if not printer:
                return jsonify({"status": "error", "error": "打印机不存在"}), 404

            # Release all bound filaments before cascade delete
            slots = conn.execute(
                "SELECT * FROM printer_slots WHERE printer_id = ?", (printer_id,)
            ).fetchall()
            for s in slots:
                if s["current_filament_id"]:
                    _release_filament(conn, s["current_filament_id"])

            conn.execute("DELETE FROM printers WHERE id = ?", (printer_id,))
            conn.commit()
            return jsonify({"status": "success"})
    except Exception as e:
        logger.error("Printer delete error: %s", e)
        return jsonify({"status": "error", "error": str(e)}), 500


# ─── Slot CRUD ───

@printers_bp.route("/api/printers/<int:printer_id>/slots", methods=["POST"])
def api_slot_create(printer_id):
    data_dir = _data_dir()
    try:
        with get_db(data_dir) as conn:
            printer = conn.execute(
                "SELECT * FROM printers WHERE id = ?", (printer_id,)
            ).fetchone()
            if not printer:
                return jsonify({"status": "error", "error": "打印机不存在"}), 404

            data = request.get_json() or {}
            slot_name = data.get("slot_name", "").strip()
            if not slot_name:
                return jsonify({"status": "error", "error": "槽位名称不能为空"}), 400

            cursor = conn.execute(
                "INSERT INTO printer_slots (printer_id, slot_name) VALUES (?, ?)",
                (printer_id, slot_name),
            )
            conn.commit()
            return jsonify({"status": "success", "id": cursor.lastrowid})
    except Exception as e:
        logger.error("Slot create error: %s", e)
        return jsonify({"status": "error", "error": str(e)}), 500


@printers_bp.route("/api/slots/<int:slot_id>", methods=["DELETE"])
def api_slot_delete(slot_id):
    data_dir = _data_dir()
    try:
        with get_db(data_dir) as conn:
            slot = conn.execute(
                "SELECT * FROM printer_slots WHERE id = ?", (slot_id,)
            ).fetchone()
            if not slot:
                return jsonify({"status": "error", "error": "槽位不存在"}), 404

            if slot["current_filament_id"]:
                _release_filament(conn, slot["current_filament_id"])

            conn.execute("DELETE FROM printer_slots WHERE id = ?", (slot_id,))
            conn.commit()
            return jsonify({"status": "success"})
    except Exception as e:
        logger.error("Slot delete error: %s", e)
        return jsonify({"status": "error", "error": str(e)}), 500


# ─── Bind / Unbind ───

@printers_bp.route("/api/slots/<int:slot_id>/bind", methods=["PUT"])
def api_slot_bind(slot_id):
    data_dir = _data_dir()
    try:
        with get_db(data_dir) as conn:
            slot = conn.execute(
                "SELECT * FROM printer_slots WHERE id = ?", (slot_id,)
            ).fetchone()
            if not slot:
                return jsonify({"status": "error", "error": "槽位不存在"}), 404

            if slot["current_filament_id"] is not None:
                return jsonify({"status": "error", "error": "该槽位已被占用，请先下机解绑"}), 400

            data = request.get_json() or {}
            filament_id = data.get("filament_id")
            if not filament_id:
                return jsonify({"status": "error", "error": "请选择要绑定的耗材"}), 400

            filament = conn.execute(
                "SELECT * FROM filaments WHERE id = ?", (filament_id,)
            ).fetchone()
            if not filament:
                return jsonify({"status": "error", "error": "耗材不存在"}), 404

            if filament["status"] not in ("全新", "闲置"):
                return jsonify({
                    "status": "error",
                    "error": f"该耗材当前状态为「{filament['status']}」，仅「全新」或「闲置」的耗材可以上机",
                }), 400

            if filament["is_loaded"] if "is_loaded" in filament.keys() else False:
                return jsonify({"status": "error", "error": "该耗材已上机"}), 400

            try:
                conn.execute(
                    "UPDATE printer_slots SET current_filament_id = ? WHERE id = ?",
                    (filament_id, slot_id),
                )
                conn.execute(
                    "UPDATE filaments SET is_loaded = 1 WHERE id = ?", (filament_id,)
                )
                conn.commit()
            except sqlite3.IntegrityError:
                conn.rollback()
                return jsonify({
                    "status": "error",
                    "error": "该卷耗材已被其他机位绑定，请刷新页面",
                }), 400

            return jsonify({"status": "success"})
    except Exception as e:
        logger.error("Slot bind error: %s", e)
        return jsonify({"status": "error", "error": str(e)}), 500


@printers_bp.route("/api/slots/<int:slot_id>/unbind", methods=["PUT"])
def api_slot_unbind(slot_id):
    data_dir = _data_dir()
    try:
        with get_db(data_dir) as conn:
            slot = conn.execute(
                "SELECT * FROM printer_slots WHERE id = ?", (slot_id,)
            ).fetchone()
            if not slot:
                return jsonify({"status": "error", "error": "槽位不存在"}), 404

            if slot["current_filament_id"] is None:
                return jsonify({"status": "error", "error": "该槽位没有绑定的耗材"}), 400

            fid = slot["current_filament_id"]
            conn.execute(
                "UPDATE printer_slots SET current_filament_id = NULL WHERE id = ?",
                (slot_id,),
            )
            _release_filament(conn, fid)
            conn.commit()
            return jsonify({"status": "success"})
    except Exception as e:
        logger.error("Slot unbind error: %s", e)
        return jsonify({"status": "error", "error": str(e)}), 500


# ─── Quick Own (from model) ───

@printers_bp.route("/api/printers/from-model", methods=["POST"])
def api_printer_from_model():
    """Create a printer instance from a model_id with auto-naming."""
    data_dir = _data_dir()
    try:
        data = request.get_json() or {}
        model_id = data.get("model_id")
        if not model_id:
            return jsonify({"status": "error", "error": "缺少型号ID"}), 400

        with get_db(data_dir) as conn:
            model = conn.execute(
                "SELECT * FROM printer_models WHERE id = ?", (model_id,)
            ).fetchone()
            if not model:
                return jsonify({"status": "error", "error": "型号不存在"}), 404

            # Auto-name: count existing printers with same model_name prefix
            cnt = conn.execute(
                "SELECT COUNT(*) FROM printers WHERE name LIKE ?",
                (model["model_name"] + "-%",),
            ).fetchone()[0]
            auto_name = f"{model['model_name']}-{cnt + 1:02d}"

            cursor = conn.execute(
                "INSERT INTO printers (name, model, model_id) VALUES (?, ?, ?)",
                (auto_name, model["model_name"], model_id),
            )
            conn.commit()
            return jsonify({"status": "success", "id": cursor.lastrowid, "name": auto_name})
    except Exception as e:
        logger.error("Printer from-model error: %s", e)
        return jsonify({"status": "error", "error": str(e)}), 500


# ─── Printer Models CRUD ───

@printers_bp.route("/api/printer_models", methods=["GET", "POST", "PUT"])
def api_printer_models():
    data_dir = _data_dir()
    try:
        with get_db(data_dir) as conn:
            if request.method == "GET":
                rows = conn.execute(
                    "SELECT * FROM printer_models ORDER BY brand, model_name"
                ).fetchall()
                return jsonify([{
                    "id": r["id"], "brand": r["brand"], "model_name": r["model_name"],
                    "technology": r["technology"], "bed_size": r["bed_size"],
                    "power_w": r["power_w"] if "power_w" in r.keys() else 200,
                    "value_yuan": r["value_yuan"] if "value_yuan" in r.keys() else 0.0,
                    "lifespan_h": r["lifespan_h"] if "lifespan_h" in r.keys() else 20000,
                    "remark": r["remark"],
                } for r in rows])
            elif request.method == "POST":
                data = request.get_json() or {}
                name = (data.get("model_name") or "").strip()
                brand = (data.get("brand") or "").strip()
                if not name or not brand:
                    return jsonify({"status": "error", "error": "品牌和型号不能为空"}), 400
                cursor = conn.execute(
                    """INSERT INTO printer_models (brand, model_name, technology, bed_size, remark)
                       VALUES (?, ?, ?, ?, ?)""",
                    (brand, name, data.get("technology", "FDM"), data.get("bed_size", ""), data.get("remark", "")),
                )
                conn.commit()
                return jsonify({"status": "success", "id": cursor.lastrowid})
            else:  # PUT
                data = request.get_json() or {}
                mid = data.get("id")
                if not mid:
                    return jsonify({"status": "error", "error": "缺少型号ID"}), 400
                conn.execute(
                    """UPDATE printer_models SET brand=?, model_name=?, technology=?, bed_size=?,
                       power_w=?, value_yuan=?, lifespan_h=?, remark=? WHERE id=?""",
                    (data.get("brand", ""), data.get("model_name", ""), data.get("technology", "FDM"),
                     data.get("bed_size", ""), data.get("power_w", 200), data.get("value_yuan", 0.0),
                     data.get("lifespan_h", 20000), data.get("remark", ""), mid),
                )
                conn.commit()
                return jsonify({"status": "success"})
    except Exception as e:
        logger.error("Printer models error: %s", e)
        return jsonify({"status": "error", "error": str(e)}), 500


@printers_bp.route("/api/printer_models/<int:model_id>", methods=["DELETE"])
def api_printer_model_delete(model_id):
    data_dir = _data_dir()
    try:
        with get_db(data_dir) as conn:
            m = conn.execute(
                "SELECT * FROM printer_models WHERE id = ?", (model_id,)
            ).fetchone()
            if not m:
                return jsonify({"status": "error", "error": "型号不存在"}), 404
            refs = conn.execute(
                "SELECT COUNT(*) AS n FROM printers WHERE model_id = ?", (model_id,)
            ).fetchone()
            if refs and refs["n"] > 0:
                return jsonify({
                    "status": "error",
                    "error": "该型号下已有正在绑定的打印机设备，无法删除！",
                }), 400
            conn.execute("DELETE FROM printer_models WHERE id = ?", (model_id,))
            conn.commit()
            return jsonify({"status": "success"})
    except Exception as e:
        logger.error("Printer model delete error: %s", e)
        return jsonify({"status": "error", "error": str(e)}), 500


def _release_filament(conn, filament_id):
    """Release a filament from its slot: set is_loaded=0, update status if depleted."""
    filament = conn.execute(
        "SELECT * FROM filaments WHERE id = ?", (filament_id,)
    ).fetchone()
    if filament:
        new_status = "用尽" if filament["current_weight"] == 0 else filament["status"]
        conn.execute(
            "UPDATE filaments SET is_loaded = 0, status = ? WHERE id = ?",
            (new_status, filament_id),
        )
