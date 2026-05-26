"""Database layer: connection management, initialization, and data migration."""
import os
import sqlite3
import logging
from contextlib import contextmanager

logger = logging.getLogger(__name__)

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


def get_db_path(data_dir: str) -> str:
    return os.path.join(data_dir, "database", "filament_inventory.db")


@contextmanager
def get_db(data_dir: str):
    """Context manager for SQLite connections with WAL mode and foreign keys."""
    db_path = get_db_path(data_dir)
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    try:
        yield conn
    finally:
        conn.close()


def init_db(data_dir: str):
    """Initialize database schema and run migrations.

    Creates all tables if they don't exist and migrates data from legacy
    materials.txt / manufacturers.txt into the new SQL tables.
    """
    db_path = get_db_path(data_dir)
    os.makedirs(os.path.dirname(db_path), exist_ok=True)

    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")

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

            CREATE TABLE IF NOT EXISTS materials (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                description TEXT DEFAULT ''
            );

            CREATE TABLE IF NOT EXISTS manufacturers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                website TEXT DEFAULT ''
            );

            CREATE TABLE IF NOT EXISTS system_settings (
                key TEXT UNIQUE NOT NULL,
                value TEXT DEFAULT ''
            );

            CREATE TABLE IF NOT EXISTS printers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                model TEXT DEFAULT '',
                created_at TEXT DEFAULT (datetime('now', 'localtime'))
            );

            CREATE TABLE IF NOT EXISTS printer_slots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                printer_id INTEGER NOT NULL,
                slot_name TEXT NOT NULL,
                current_filament_id INTEGER UNIQUE,
                FOREIGN KEY (printer_id) REFERENCES printers(id) ON DELETE CASCADE,
                FOREIGN KEY (current_filament_id) REFERENCES filaments(id) ON DELETE SET NULL
            );
        """)

        # --- Schema migration: add status column to filaments (v0.2.4.0) ---
        col_check = conn.execute("PRAGMA table_info(filaments)").fetchall()
        col_names = [c[1] for c in col_check]
        if "status" not in col_names:
            conn.execute("ALTER TABLE filaments ADD COLUMN status TEXT NOT NULL DEFAULT '全新'")
            # One-shot migration: map old is_opened to new 4-state model
            # Order matters: 用尽 first (catches weight=0 regardless of is_opened)
            conn.execute("""
                UPDATE filaments SET status = CASE
                    WHEN current_weight = 0 THEN '用尽'
                    WHEN is_opened = 1 THEN '闲置'
                    ELSE '全新'
                END
            """)
            logger.info("Migrated filaments to v0.2.4.0 4-state status model.")

        # Seed settings singleton
        cur = conn.execute("SELECT COUNT(*) FROM settings")
        if cur.fetchone()[0] == 0:
            conn.execute("INSERT INTO settings (threshold, default_weight) VALUES (200, 1000.0)")

        # Seed system_settings defaults
        conn.execute("INSERT OR IGNORE INTO system_settings (key, value) VALUES ('active_background', '')")
        conn.execute("INSERT OR IGNORE INTO system_settings (key, value) VALUES ('card_opacity', '0.05')")
        conn.execute("INSERT OR IGNORE INTO system_settings (key, value) VALUES ('card_color', '#ffffff')")
        conn.execute("INSERT OR IGNORE INTO system_settings (key, value) VALUES ('card_blur', '2')")

        # Migrate materials from txt to DB
        cur = conn.execute("SELECT COUNT(*) FROM materials")
        if cur.fetchone()[0] == 0:
            materials_path = os.path.join(data_dir, "database", "materials.txt")
            items = _read_txt_list(materials_path, DEFAULT_MATERIALS)
            for name in items:
                try:
                    conn.execute("INSERT OR IGNORE INTO materials (name) VALUES (?)", (name,))
                except sqlite3.Error:
                    pass

        # Migrate manufacturers from txt to DB
        cur = conn.execute("SELECT COUNT(*) FROM manufacturers")
        if cur.fetchone()[0] == 0:
            manufacturers_path = os.path.join(data_dir, "database", "manufacturers.txt")
            items = _read_txt_list(manufacturers_path, DEFAULT_MANUFACTURERS)
            for name in items:
                try:
                    conn.execute("INSERT OR IGNORE INTO manufacturers (name) VALUES (?)", (name,))
                except sqlite3.Error:
                    pass

        conn.commit()
        conn.close()
        logger.info("Database initialized and migrated successfully.")

    except sqlite3.Error as e:
        logger.error("Database initialization failed: %s", e)
        raise


def _read_txt_list(path, defaults):
    """Read a line-delimited text file, falling back to defaults."""
    try:
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                items = [line.strip() for line in f if line.strip()]
                return items if items else defaults
    except Exception:
        pass
    return defaults
