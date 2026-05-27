"""Cost calculator CRUD API."""
import os, json, logging
from flask import current_app, jsonify, request, render_template

from modules.tools import tools_bp
from modules.db import get_db

logger = logging.getLogger(__name__)

def _data_dir():
    return current_app.config.get("DATA_DIR", os.path.join(os.path.dirname(__file__), "..", "..", "data"))


@tools_bp.route("/tools/cost_calculator")
def cost_calculator_page():
    from modules.base.bg_utils import get_active_background
    bg = get_active_background(_data_dir())
    return render_template("tools/cost_calculator.html", active_background=bg, active_nav="tools", active_sub="calculator")


@tools_bp.route("/api/tools/calculator/history", methods=["GET"])
def api_calc_history_list():
    data_dir = _data_dir()
    try:
        with get_db(data_dir) as conn:
            rows = conn.execute("SELECT id, project_name, created_at, total_cost, suggested_price, pure_profit FROM calculation_history ORDER BY id DESC LIMIT 50").fetchall()
            return jsonify([{"id": r["id"], "project_name": r["project_name"], "created_at": r["created_at"], "total_cost": r["total_cost"], "suggested_price": r["suggested_price"], "pure_profit": r["pure_profit"]} for r in rows])
    except Exception as e:
        return jsonify({"status": "error", "error": str(e)}), 500


def _safe_float(val, default=0.0):
    try: return float(val)
    except (ValueError, TypeError): return default

@tools_bp.route("/api/tools/calculator/save", methods=["POST"])
def api_calc_save():
    data_dir = _data_dir()
    try:
        data = request.get_json() or {}
        if not data.get("project_name", "").strip():
            return jsonify({"status": "error", "error": "保存失败：项目/模型名称不能为空！"}), 400
        if not data.get("filaments") or data.get("filaments") == []:
            return jsonify({"status": "error", "error": "保存失败：请至少添加一种打印耗材！"}), 400
        if not data.get("printers") or data.get("printers") == []:
            return jsonify({"status": "error", "error": "保存失败：请至少关联一台打印设备！"}), 400

        record_id = data.get("id")
        profit_rate = _safe_float(data.get("profit_rate_expect", 0))
        commission_rate = _safe_float(data.get("platform_commission_rate", 0))
        tax_rate = _safe_float(data.get("tax_rate", 0))
        denominator = 1 - (profit_rate / 100.0) - (commission_rate / 100.0) - (tax_rate / 100.0)
        if denominator <= 0:
            return jsonify({"status": "error", "error": "期望利润率+平台抽成+税率之和不能大于或等于100%，请调整参数后重试"}), 400

        params = (
            data["project_name"],
            json.dumps(data.get("filaments", [])),
            json.dumps(data.get("printers", [])),
            json.dumps(data.get("post_processing", [])),
            _safe_float(data.get("design_fee")), _safe_float(data.get("packaging_fee")),
            _safe_float(data.get("shipping_fee")), _safe_float(data.get("other_fee")),
            tax_rate, commission_rate, profit_rate, _safe_float(data.get("labor_markup_fee")),
            _safe_float(data.get("total_cost")), _safe_float(data.get("suggested_price")), _safe_float(data.get("pure_profit")),
        )
        with get_db(data_dir) as conn:
            if record_id:
                conn.execute("""UPDATE calculation_history SET project_name=?, filaments_json=?, printers_json=?,
                    post_processing_json=?, design_fee=?, packaging_fee=?, shipping_fee=?, other_fee=?,
                    tax_rate=?, platform_commission_rate=?, profit_rate_expect=?, labor_markup_fee=?,
                    total_cost=?, suggested_price=?, pure_profit=? WHERE id=?""",
                    params + (record_id,))
                conn.commit()
                return jsonify({"status": "success", "id": record_id, "action": "updated"})
            else:
                cur = conn.execute("""INSERT INTO calculation_history
                    (project_name, filaments_json, printers_json, post_processing_json,
                     design_fee, packaging_fee, shipping_fee, other_fee,
                     tax_rate, platform_commission_rate, profit_rate_expect, labor_markup_fee,
                     total_cost, suggested_price, pure_profit)
                    VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""", params)
                conn.commit()
                return jsonify({"status": "success", "id": cur.lastrowid, "action": "created"})
    except Exception as e:
        logger.error("Calc save error: %s", e)
        return jsonify({"status": "error", "error": str(e)}), 500


@tools_bp.route("/api/tools/calculator/detail/<int:record_id>", methods=["GET"])
def api_calc_detail(record_id):
    data_dir = _data_dir()
    try:
        with get_db(data_dir) as conn:
            r = conn.execute("SELECT * FROM calculation_history WHERE id=?", (record_id,)).fetchone()
            if not r:
                return jsonify({"status": "error", "error": "记录不存在"}), 404
            return jsonify({
                "id": r["id"], "project_name": r["project_name"], "created_at": r["created_at"],
                "filaments": json.loads(r["filaments_json"]), "printers": json.loads(r["printers_json"]),
                "post_processing": json.loads(r["post_processing_json"]),
                "design_fee": r["design_fee"], "packaging_fee": r["packaging_fee"],
                "shipping_fee": r["shipping_fee"], "other_fee": r["other_fee"],
                "tax_rate": r["tax_rate"], "platform_commission_rate": r["platform_commission_rate"],
                "profit_rate_expect": r["profit_rate_expect"], "labor_markup_fee": r["labor_markup_fee"],
                "total_cost": r["total_cost"], "suggested_price": r["suggested_price"],
                "pure_profit": r["pure_profit"],
            })
    except Exception as e:
        return jsonify({"status": "error", "error": str(e)}), 500


@tools_bp.route("/api/tools/calculator/history/<int:record_id>", methods=["DELETE"])
def api_calc_delete(record_id):
    data_dir = _data_dir()
    try:
        with get_db(data_dir) as conn:
            conn.execute("DELETE FROM calculation_history WHERE id=?", (record_id,))
            conn.commit()
            return jsonify({"status": "success"})
    except Exception as e:
        return jsonify({"status": "error", "error": str(e)}), 500
