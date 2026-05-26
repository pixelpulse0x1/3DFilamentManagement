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
    return {"id": row["id"], "name": row["name"], "model": row["model"]}


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
                printers = conn.execute("SELECT * FROM printers ORDER BY id").fetchall()
                result = []
                for p in printers:
                    pd = _printer_to_dict(p)
                    slots = conn.execute(
                        "SELECT ps.*, f.name AS f_name, f.manufacturer, f.material_type, "
                        "f.color, f.current_weight, f.initial_weight, f.status "
                        "FROM printer_slots ps "
                        "LEFT JOIN filaments f ON ps.current_filament_id = f.id "
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
                                "manufacturer": s["manufacturer"],
                                "material_type": s["material_type"],
                                "color": s["color"],
                                "current_weight": s["current_weight"],
                                "initial_weight": s["initial_weight"],
                                "status": s["status"],
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
                cursor = conn.execute(
                    "INSERT INTO printers (name, model) VALUES (?, ?)", (name, model)
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

            try:
                conn.execute(
                    "UPDATE printer_slots SET current_filament_id = ? WHERE id = ?",
                    (filament_id, slot_id),
                )
                conn.execute(
                    "UPDATE filaments SET status = '上机' WHERE id = ?", (filament_id,)
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


def _release_filament(conn, filament_id):
    """Release a filament from its slot: set status based on remaining weight."""
    filament = conn.execute(
        "SELECT * FROM filaments WHERE id = ?", (filament_id,)
    ).fetchone()
    if filament:
        new_status = "用尽" if filament["current_weight"] == 0 else "闲置"
        conn.execute(
            "UPDATE filaments SET status = ? WHERE id = ?",
            (new_status, filament_id),
        )
