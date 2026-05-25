"""3D Consumables Inventory Management System - Flask Backend."""
import os
import csv
import io
import re
import socket
from datetime import datetime

from flask import Flask, render_template, jsonify, request, Response

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "change-me-to-random-string")

DATA_DIR = os.environ.get("DATA_DIR", os.path.join(os.path.dirname(__file__), "data"))
DB_PATH = os.path.join(DATA_DIR, "database", "filament_inventory.db")
MATERIALS_PATH = os.path.join(DATA_DIR, "database", "materials.txt")
MANUFACTURERS_PATH = os.path.join(DATA_DIR, "database", "manufacturers.txt")

DEFAULT_MATERIALS = [
    "PLA Basic", "PLA +", "PLA Matte", "PLA Lite", "PLA Metal", "PLA Silk",
    "PLA Silk+", "PLA Marble", "PLA Sparkle", "PLA Tough", "PLA Wood",
    "PLA Glod", "PLA - CF", "PETG Basic", "PETG - HF", "PETG - CF",
    "PETG - Translucent", "ABS", "ABS - GF", "ASA", "ASA - Aero", "ASA - CF",
    "TPU 95A", "TPU 95A HF", "TPU For AMS", "Support For PLA",
    "Support For PLA/PERG", "PC", "PCFR", "PA6 - CF", "PA6 - GF",
    "PAHT - CF", "PPS - CF", "PET - CF", "HIPS",
]

DEFAULT_MANUFACTURERS = [
    "拓竹", "三绿", "三慈", "彩魔方", "科雷迪", "印未来", "普菲丝PRIFIL",
    "INKCLOUD", "JAYO", "CMYK", "巴斯夫", "P家", "易生", "K家", "F家",
    "爱丽兹", "爱三迪", "点维", "天瑞", "大简", "必应", "蓝极光", "瑞本",
    "优线", "彩格", "邦通诺", "兰度", "叁生万物", "彩多屋", "聚材", "方途",
    "锦胜", "海创", "丝工坊", "蓝小度", "元洋", "闪铸", "造物新材料",
    "爱乐酷", "创想三维", "纵维立方", "启庞", "余师兄",
]

import sqlite3


def get_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db():
    conn = get_db()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS filaments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            manufacturer TEXT,
            material_type TEXT NOT NULL,
            color TEXT NOT NULL,
            location TEXT,
            is_opened BOOLEAN NOT NULL DEFAULT 0,
            initial_weight REAL NOT NULL DEFAULT 1000.0,
            current_weight REAL NOT NULL,
            is_favorite BOOLEAN NOT NULL DEFAULT 0,
            created_at TEXT DEFAULT (datetime('now', 'localtime')),
            purchase_date TEXT,
            purchase_price REAL,
            purchase_channel TEXT,
            opened_at TEXT
        );

        CREATE TABLE IF NOT EXISTS usage_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filament_id INTEGER NOT NULL,
            used_weight REAL NOT NULL,
            note TEXT,
            used_at TEXT DEFAULT (datetime('now', 'localtime'))
        );

        CREATE TABLE IF NOT EXISTS settings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            threshold INTEGER DEFAULT 200,
            default_weight REAL DEFAULT 1000.0,
            auto_update BOOLEAN DEFAULT 1
        );
    """)
    cur = conn.execute("SELECT COUNT(*) FROM settings")
    if cur.fetchone()[0] == 0:
        conn.execute("INSERT INTO settings (threshold, default_weight) VALUES (200, 1000.0)")
    conn.commit()
    conn.close()

    # Write default materials/manufacturers files if they don't exist
    os.makedirs(os.path.dirname(MATERIALS_PATH), exist_ok=True)
    if not os.path.exists(MATERIALS_PATH):
        with open(MATERIALS_PATH, "w", encoding="utf-8") as f:
            f.write("\n".join(DEFAULT_MATERIALS))
    if not os.path.exists(MANUFACTURERS_PATH):
        with open(MANUFACTURERS_PATH, "w", encoding="utf-8") as f:
            f.write("\n".join(DEFAULT_MANUFACTURERS))


def load_text_list(path, defaults):
    try:
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                items = [line.strip() for line in f if line.strip()]
                return items if items else defaults
        return defaults
    except Exception:
        return defaults


def save_text_list(path, items):
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write("\n".join(items))
    except Exception:
        pass


def filament_to_dict(row):
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


# ─── Frontend Route ───

@app.route("/")
def index():
    return render_template("index.html")


# ─── API Routes ───

@app.route("/api/settings", methods=["GET", "PUT"])
def api_settings():
    conn = get_db()
    try:
        if request.method == "GET":
            row = conn.execute("SELECT * FROM settings WHERE id = 1").fetchone()
            return jsonify(dict(row))
        else:
            data = request.get_json()
            threshold = data.get("threshold", 200)
            default_weight = data.get("default_weight", 1000.0)
            conn.execute(
                "UPDATE settings SET threshold = ?, default_weight = ? WHERE id = 1",
                (threshold, default_weight),
            )
            conn.commit()
            row = conn.execute("SELECT * FROM settings WHERE id = 1").fetchone()
            return jsonify({"status": "success", "settings": dict(row)})
    except Exception as e:
        return jsonify({"status": "error", "error": str(e)}), 500
    finally:
        conn.close()


@app.route("/api/filaments", methods=["GET", "POST"])
def api_filaments():
    conn = get_db()
    try:
        if request.method == "GET":
            rows = conn.execute("SELECT * FROM filaments ORDER BY id DESC").fetchall()
            return jsonify([filament_to_dict(r) for r in rows])
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
        return jsonify({"status": "error", "error": str(e)}), 500
    finally:
        conn.close()


@app.route("/api/filaments/<int:filament_id>", methods=["PUT", "DELETE"])
def api_filament_single(filament_id):
    conn = get_db()
    try:
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
        return jsonify({"status": "error", "error": str(e)}), 500
    finally:
        conn.close()


@app.route("/api/filaments/batch", methods=["POST"])
def api_filaments_batch():
    conn = get_db()
    try:
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
        return jsonify({"status": "error", "error": str(e)}), 500
    finally:
        conn.close()


@app.route("/api/filaments/delete-multiple", methods=["POST"])
def api_filaments_delete_multiple():
    conn = get_db()
    try:
        data = request.get_json()
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
        return jsonify({"status": "error", "error": str(e)}), 500
    finally:
        conn.close()


@app.route("/api/filaments/<int:filament_id>/use", methods=["POST"])
def api_filament_use(filament_id):
    conn = get_db()
    try:
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
        return jsonify({"status": "error", "error": str(e)}), 500
    finally:
        conn.close()


@app.route("/api/usage_records", methods=["GET"])
def api_usage_records():
    conn = get_db()
    try:
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
        return jsonify({"status": "error", "error": str(e)}), 500
    finally:
        conn.close()


@app.route("/api/usage_records/<int:record_id>", methods=["DELETE"])
def api_usage_record_delete(record_id):
    conn = get_db()
    try:
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
        return jsonify({"status": "error", "error": str(e)}), 500
    finally:
        conn.close()


@app.route("/api/statistics", methods=["GET"])
def api_statistics():
    conn = get_db()
    try:
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

        # Manufacturer stats
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

        # Monthly usage stats
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
        return jsonify({"status": "error", "error": str(e)}), 500
    finally:
        conn.close()


@app.route("/api/materials", methods=["GET"])
def api_materials():
    items = load_text_list(MATERIALS_PATH, DEFAULT_MATERIALS)
    return jsonify(items)


@app.route("/api/materials", methods=["POST"])
def api_materials_update():
    items = request.get_json()
    if not isinstance(items, list):
        return jsonify({"status": "error", "error": "Expected a list"}), 400
    save_text_list(MATERIALS_PATH, items)
    return jsonify({"status": "success"})


@app.route("/api/manufacturers", methods=["GET"])
def api_manufacturers():
    items = load_text_list(MANUFACTURERS_PATH, DEFAULT_MANUFACTURERS)
    return jsonify(items)


@app.route("/api/manufacturers", methods=["POST"])
def api_manufacturers_update():
    items = request.get_json()
    if not isinstance(items, list):
        return jsonify({"status": "error", "error": "Expected a list"}), 400
    save_text_list(MANUFACTURERS_PATH, items)
    return jsonify({"status": "success"})


@app.route("/api/local-ip", methods=["GET"])
def api_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
    except Exception:
        ip = "127.0.0.1"
    return jsonify({"ip": ip})


@app.route("/api/export", methods=["GET"])
def api_export():
    conn = get_db()
    try:
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
        return jsonify({"status": "error", "error": str(e)}), 500
    finally:
        conn.close()


@app.route("/api/import", methods=["POST"])
def api_import():
    if "file" not in request.files:
        return jsonify({"status": "error", "error": "No file uploaded"}), 400
    file = request.files["file"]
    if not file.filename:
        return jsonify({"status": "error", "error": "Empty filename"}), 400
    conn = get_db()
    try:
        content = file.read().decode("utf-8-sig")
        reader = csv.DictReader(io.StringIO(content))
        added, updated, skipped = 0, 0, 0
        for row in reader:
            if not row.get("name"):
                skipped += 1
                continue
            # name matching is the key for updating
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
        return jsonify({"status": "error", "error": str(e)}), 500
    finally:
        conn.close()


if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=3155, debug=False)
