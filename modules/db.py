"""Database layer: connection management, versioned migration engine, and data seeding."""
import os
import shutil
import sqlite3
import logging
from contextlib import contextmanager

logger = logging.getLogger(__name__)

LATEST_VERSION = 6

ALLOWED_IMAGE_EXTENSIONS = {"jpg", "jpeg", "png", "webp"}

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

DEFAULT_CHANNELS = [
    "拼多多", "京东", "淘宝", "小程序", "闲鱼", "实体店", "QQ", "微信", "拓竹官网", "其它",
]

BUILTIN_BRANDS = [
    ("天瑞", "标准盘", 188.4), ("R3D", "塑盘", 126.5), ("R3D", "纸盘", 191.0),
    ("Jayo", "标准盘", 126.0), ("Jayo", "新包装纸筒盘", 201.7),
    ("启庞", "标准盘", 138.1), ("三绿", "黑塑盘", 135.0), ("三绿", "透明盘", 140.0),
    ("三慈", "标准盘", 122.0), ("拓竹", "官方盘", 239.0),
    ("彩格", "标准盘", 181.0), ("彩多屋", "标准盘", 180.0),
    ("RMERME", "标准盘", 187.7), ("海螺号", "标准盘", 200.0),
    ("必应", "标准盘", 150.0), ("点维", "标准盘", 182.9),
    ("K家", "标准盘", 220.0), ("易生", "纸盘", 181.0),
    ("蓝极光", "标准盘", 165.0), ("兰博", "标准盘", 170.0),
    ("瑞本", "标准盘", 220.0), ("兰小度", "标准盘", 160.0),
    ("起迪", "标准盘", 246.0), ("双第", "标准盘", 200.0),
]

BUILTIN_MODELS = [
    ("Bambu Lab", "A1 mini", "FDM", "180x180x180", "入门首选，全自动校准，静音打印(≤48dB)，500mm/s，10000mm/s²"),
    ("Bambu Lab", "A1", "FDM", "256x256x256", "A1 mini放大版，全自动校准，500mm/s，兼容AMS Lite多色系统"),
    ("Bambu Lab", "P1P", "FDM", "256x256x256", "开放式CoreXY，500mm/s，20000mm/s²，支持16色打印"),
    ("Bambu Lab", "P1S", "FDM", "256x256x256", "封闭式CoreXY，全封闭箱体，可打印ABS/ASA，被广泛用于打印农场"),
    ("Bambu Lab", "P2S", "FDM", "256x256x256", "P1系列全面升级，2025年10月发布；5英寸触摸屏，1080P摄像头，AI检测，伺服挤出机"),
    ("Bambu Lab", "X1", "FDM", "256x256x256", "首款消费级产品(2022)，CoreXY，集成微激光雷达与AI检测"),
    ("Bambu Lab", "X1 Carbon", "FDM", "256x256x256", "铝+玻璃全封闭机身，300℃硬化钢喷嘴，AI激光雷达检测，16色(已停产)"),
    ("Bambu Lab", "X1E", "FDM", "256x256x256", "商用版(2024)，主动腔体加热60℃，喷嘴最高320℃，有线以太网接口"),
    ("Bambu Lab", "X2D", "FDM", "256x256x260", "2026年4月新旗舰，双喷嘴CoreXY，主动腔体加热60℃，最高1000mm/s"),
    ("Bambu Lab", "H2S", "FDM", "340x320x340", "消费级大尺寸旗舰，单喷嘴，1000mm/s，比X1C体积大120%"),
    ("Bambu Lab", "H2D", "FDM", "350x320x325", "个人制造中心，双喷嘴3D打印+激光雕刻切割+数字切割绘图，腔体65℃"),
    ("Bambu Lab", "H2C", "FDM", "300x320x325", "真旗舰，Vortek多喷嘴系统(最多7种材料)，多材料优化"),
    ("Creality", "K1C", "FDM", "220x220x250", ""),
    ("Creality", "K1 Max", "FDM", "300x300x300", ""),
    ("Creality", "K2", "FDM", "260x260x260", "CFS多色系统，16色打印，350°C喷嘴，CoreXY，2025年8月发布"),
    ("Creality", "K2 Pro", "FDM", "300x300x300", "CFS多色系统，350°C喷嘴+60°C主动腔体，压铸铝合金机身"),
    ("Creality", "K2 Plus", "FDM", "350x350x350", "CFS多色系统，准工业级旗舰，350°C喷嘴+60°C主动腔体"),
    ("Creality", "Ender-3 V3", "FDM", "220x220x250", ""),
    ("Creality", "Ender-3 V3 Plus", "FDM", "300x300x330", ""),
    ("Creality", "SPARKX i7", "FDM", "260x260x255", "桌面级多色，500mm/s，AI照片转3D，45dB静音，2026年1月CES首发"),
    ("Prusa", "i3 MK4", "FDM", "250x210x220", ""),
    ("Prusa", "XL", "FDM", "360x360x360", "多工具头快换系统，2026年新增液态硅胶打印工具头"),
    ("Prusa", "CORE One", "FDM", "250x220x220", "封闭式CoreXY，2025年发布"),
    ("Prusa", "CORE One L", "FDM", "300x300x330", "封闭式CoreXY，铸铝热床，打印体积增200%，60°C腔体"),
    ("Prusa", "Pro HT90", "FDM", "Φ300x400", "工业高温，Revo快拆喷嘴，支持PEEK/PEI，2026年发布"),
    ("Flashforge", "Adventurer 5M Pro", "FDM", "220x220x220", ""),
    ("Flashforge", "Creator 5", "FDM", "256x256x256", "4独立喷头FlashSwap，CoreXY，320°C喷嘴，2026年3月发布"),
    ("Flashforge", "Creator 5 Pro", "FDM", "256x256x256", "全封闭，65°C主动腔体加热，HEPA+活性炭过滤"),
    ("Flashforge", "CJ270", "Multi-jet+UV", "桌面级全彩", "7μm层厚，>1000万色，水溶性支撑，2026年3月TCT首展"),
    ("Raise3D", "Pro3", "FDM", "300x300x300", "双喷头IDEX，专业级"),
    ("Raise3D", "Pro3 Plus", "FDM", "300x300x605", "双喷头IDEX，大尺寸版"),
    ("Raise3D", "Pro3 HS", "FDM", "300x300x300", "Hyper FFF高速打印，碳化硅喷嘴，500mm/s"),
    ("Raise3D", "Pro3 HS Plus", "FDM", "300x300x605", "Hyper FFF高速打印大尺寸版，碳化硅喷嘴"),
    ("Raise3D", "E3", "FDM", "330x240x240", "IDEX独立双喷头，FlexFeed柔性材料套件，TPU 200mm/s"),
    ("Raise3D", "DF2", "DLP", "200x112x300", ""),
    ("Raise3D", "RMS220", "SLS", "220x220x350", "75W光纤激光，日产>5kg，重复精度±0.05mm"),
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


# ─── Database Initialization & Migration Engine ───

def init_db(data_dir: str):
    """Orchestrate database creation, cold backup, step-loop migration, and seeding."""
    db_path = get_db_path(data_dir)
    os.makedirs(os.path.dirname(db_path), exist_ok=True)

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")

    try:
        # Phase 1: Ensure all tables exist (idempotent CREATE IF NOT EXISTS)
        _create_all_tables(conn)

        # Phase 2: Cold backup
        _cold_backup(db_path)

        # Phase 3: Read current schema version
        conn.execute(
            "INSERT OR IGNORE INTO system_settings (key, value) VALUES ('database_version', '1')"
        )
        row = conn.execute(
            "SELECT value FROM system_settings WHERE key = 'database_version'"
        ).fetchone()
        current = int(row["value"]) if row else 1

        if current > LATEST_VERSION:
            logger.error(
                "Database version %d is newer than latest %d — cannot downgrade.",
                current, LATEST_VERSION,
            )
            conn.close()
            raise RuntimeError("Database version is ahead of software. Downgrade not supported.")

        # Phase 4: Step-loop migration
        while current < LATEST_VERSION:
            _run_migration(current, current + 1, data_dir, conn)
            current += 1
            conn.execute(
                "UPDATE system_settings SET value = ? WHERE key = 'database_version'",
                (str(current),),
            )
            conn.commit()
            logger.info("Database migrated to version %d.", current)

        # Phase 5: Seed default data
        _seed_data(conn, data_dir)

        conn.commit()
        logger.info("Database initialized and migrated successfully (version %d).", current)

    except Exception as e:
        logger.error("Database initialization failed: %s", e)
        conn.close()
        raise

    conn.close()


# ─── Phase 1: Table Creation ───

def _create_all_tables(conn):
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS filaments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            material_type TEXT NOT NULL,
            color TEXT NOT NULL,
            location TEXT,
            initial_weight REAL NOT NULL DEFAULT 1000.0,
            current_weight REAL NOT NULL,
            is_favorite BOOLEAN NOT NULL DEFAULT 0,
            created_at TEXT DEFAULT (datetime('now', 'localtime')),
            purchase_date TEXT,
            purchase_price REAL,
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

        CREATE TABLE IF NOT EXISTS filament_images (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            file_name TEXT NOT NULL,
            created_at TEXT DEFAULT (datetime('now', 'localtime'))
        );

        CREATE TABLE IF NOT EXISTS channels (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            description TEXT DEFAULT ''
        );

        CREATE TABLE IF NOT EXISTS brands (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            spool_type TEXT DEFAULT '标准盘',
            spool_weight REAL NOT NULL DEFAULT 0.0,
            remark TEXT DEFAULT '',
            UNIQUE(name, spool_type)
        );

        CREATE TABLE IF NOT EXISTS printer_models (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            brand TEXT NOT NULL,
            model_name TEXT NOT NULL UNIQUE,
            technology TEXT DEFAULT 'FDM',
            bed_size TEXT DEFAULT '',
            remark TEXT DEFAULT ''
        );
    """)


# ─── Phase 2: Cold Backup ───

def _cold_backup(db_path):
    if not os.path.isfile(db_path):
        return
    try:
        bak_path = db_path + ".v" + str(LATEST_VERSION) + ".bak"
        if not os.path.exists(bak_path):
            shutil.copy2(db_path, bak_path)
            logger.info("Cold backup created: %s", bak_path)
    except OSError as e:
        logger.warning("Cold backup skipped (non-fatal): %s", e)


# ─── Phase 4: Step Migrations ───

def _run_migration(from_ver, to_ver, data_dir, conn):
    logger.info("Migrating database v%d → v%d ...", from_ver, to_ver)
    if from_ver == 1 and to_ver == 2:
        _migrate_v1_to_v2(conn)
    elif from_ver == 2 and to_ver == 3:
        _migrate_v2_to_v3(data_dir, conn)
    elif from_ver == 3 and to_ver == 4:
        _migrate_v3_to_v4(conn)
    elif from_ver == 4 and to_ver == 5:
        _migrate_v4_to_v5(data_dir, conn)
    elif from_ver == 5 and to_ver == 6:
        _migrate_v5_to_v6(conn)
    else:
        logger.warning("Unknown migration step: %d → %d", from_ver, to_ver)


def _migrate_v1_to_v2(conn):
    """v0.2.4.0: printers, printer_slots, filaments.status 4-state model."""
    col_names = [c[1] for c in conn.execute("PRAGMA table_info(filaments)").fetchall()]
    if "status" not in col_names:
        conn.execute("ALTER TABLE filaments ADD COLUMN status TEXT NOT NULL DEFAULT '全新'")
        # Only run legacy mapping if is_opened column still exists
        if "is_opened" in col_names:
            conn.execute("""
                UPDATE filaments SET status = CASE
                    WHEN current_weight = 0 THEN '用尽'
                    WHEN is_opened = 1 THEN '闲置'
                    ELSE '全新'
                END
            """)
        logger.info("  ✓ filaments.status column added and migrated.")


def _migrate_v2_to_v3(data_dir, conn):
    """v0.3.0.0: filament_images table, filaments.image_id/remark, file reorganization."""
    col_names = [c[1] for c in conn.execute("PRAGMA table_info(filaments)").fetchall()]
    if "image_id" not in col_names:
        conn.execute("ALTER TABLE filaments ADD COLUMN image_id INTEGER REFERENCES filament_images(id) ON DELETE SET NULL")
    if "remark" not in col_names:
        conn.execute("ALTER TABLE filaments ADD COLUMN remark TEXT")
    conn.commit()

    # Physical file migration: scatter → subdirectories
    uploads = os.path.join(data_dir, "uploads")
    filaments_dir = os.path.join(uploads, "filaments")
    backgrounds_dir = os.path.join(uploads, "backgrounds")

    os.makedirs(filaments_dir, exist_ok=True)
    os.makedirs(backgrounds_dir, exist_ok=True)

    if not os.path.isdir(uploads):
        logger.info("  ✓ /data/uploads/ not found, skipping file migration.")
        return

    # Determine active background for routing
    bg_row = conn.execute(
        "SELECT value FROM system_settings WHERE key = 'active_background'"
    ).fetchone()
    active_bg = bg_row["value"] if bg_row else ""

    for filename in os.listdir(uploads):
        src = os.path.join(uploads, filename)
        if not os.path.isfile(src):
            continue
        ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
        if ext not in ALLOWED_IMAGE_EXTENSIONS:
            continue

        target = backgrounds_dir if filename == active_bg else filaments_dir
        dst = os.path.join(target, filename)

        if os.path.exists(dst):
            logger.debug("  ⏭ skip (exists): %s", filename)
            continue

        try:
            shutil.move(src, dst)
            logger.info("  ✓ migrated file: %s → %s/", filename,
                        "backgrounds" if target == backgrounds_dir else "filaments")
        except OSError as e:
            logger.error("  ✗ move failed (non-fatal): %s — %s", filename, e)

    logger.info("  ✓ V2→V3 file migration complete.")


def _migrate_v3_to_v4(conn):
    """v0.3.1.0: channels table, filaments.channel_id FK, data extraction."""
    col_names = [c[1] for c in conn.execute("PRAGMA table_info(filaments)").fetchall()]
    if "channel_id" not in col_names:
        if "purchase_channel" in col_names:
            conn.execute("""
                INSERT OR IGNORE INTO channels (name)
                SELECT DISTINCT purchase_channel FROM filaments
                WHERE purchase_channel IS NOT NULL AND purchase_channel != ''
            """)
        conn.execute("ALTER TABLE filaments ADD COLUMN channel_id INTEGER REFERENCES channels(id) ON DELETE SET NULL")
        if "purchase_channel" in col_names:
            conn.execute("""
                UPDATE filaments SET channel_id = (
                    SELECT c.id FROM channels c WHERE c.name = filaments.purchase_channel
                ) WHERE purchase_channel IS NOT NULL AND purchase_channel != ''
            """)
        logger.info("  ✓ filaments.channel_id FK added and data mapped.")


def _migrate_v4_to_v5(data_dir, conn):
    """v0.4.0.0: brands table with spool weights, filaments.brand_id FK, data extraction."""
    # 1. Seed built-in brand data
    for name, spool_type, weight in BUILTIN_BRANDS:
        conn.execute(
            "INSERT OR IGNORE INTO brands (name, spool_type, spool_weight) VALUES (?, ?, ?)",
            (name, spool_type, weight),
        )

    # 2. Scan old manufacturer texts only if column exists
    if "manufacturer" in col_names:
        old_mfrs = conn.execute(
            """SELECT DISTINCT manufacturer FROM filaments
               WHERE manufacturer IS NOT NULL AND manufacturer != ''
               AND manufacturer NOT IN (SELECT name FROM brands)"""
        ).fetchall()
        for r in old_mfrs:
            mfr = r[0]
            conn.execute(
                "INSERT OR IGNORE INTO brands (name, spool_type, spool_weight, remark) VALUES (?, '未知盘', 0.0, '旧数据自动迁移兜底')",
                (mfr,),
            )

    # 3. Add brand_id FK column to filaments
    col_names = [c[1] for c in conn.execute("PRAGMA table_info(filaments)").fetchall()]
    if "brand_id" not in col_names:
        conn.execute(
            "ALTER TABLE filaments ADD COLUMN brand_id INTEGER REFERENCES brands(id) ON DELETE SET NULL"
        )
        # 4. Map old manufacturer text → brand_id if column exists
        if "manufacturer" in col_names:
            conn.execute("""
                UPDATE filaments SET brand_id = (
                    SELECT b.id FROM brands b
                    WHERE b.name = filaments.manufacturer
                    ORDER BY b.spool_weight DESC LIMIT 1
                ) WHERE manufacturer IS NOT NULL AND manufacturer != ''
            """)
        logger.info("  ✓ filaments.brand_id FK added and old manufacturer data mapped.")


def _migrate_v5_to_v6(conn):
    """v0.4.1.0: printer_models table, seed built-in data, merge old printer model text."""
    # 1. Seed built-in models
    for brand, model_name, tech, bed, remark in BUILTIN_MODELS:
        conn.execute(
            "INSERT OR IGNORE INTO printer_models (brand, model_name, technology, bed_size, remark) VALUES (?, ?, ?, ?, ?)",
            (brand, model_name, tech, bed, remark),
        )

    # 2. Scan old printers.model text, create fallback records
    col_names = [c[1] for c in conn.execute("PRAGMA table_info(printers)").fetchall()]
    if "model" in col_names:
        old_models = conn.execute(
            """SELECT DISTINCT model FROM printers
               WHERE model IS NOT NULL AND model != ''
               AND model NOT IN (SELECT model_name FROM printer_models)"""
        ).fetchall()
        for r in old_models:
            m = r[0]
            conn.execute(
                "INSERT OR IGNORE INTO printer_models (brand, model_name, remark) VALUES ('自定义', ?, '历史数据迁移兜底')",
                (m,),
            )

    # 3. Add model_id FK to printers
    p_cols = [c[1] for c in conn.execute("PRAGMA table_info(printers)").fetchall()]
    if "model_id" not in p_cols:
        conn.execute(
            "ALTER TABLE printers ADD COLUMN model_id INTEGER REFERENCES printer_models(id) ON DELETE SET NULL"
        )
        if "model" in col_names:
            conn.execute("""
                UPDATE printers SET model_id = (
                    SELECT pm.id FROM printer_models pm
                    WHERE pm.model_name = printers.model
                    LIMIT 1
                ) WHERE model IS NOT NULL AND model != ''
            """)
        logger.info("  ✓ printers.model_id FK added and old model text mapped.")


# ─── Phase 5: Seed Data ───

def _seed_data(conn, data_dir):
    # Settings singleton
    cur = conn.execute("SELECT COUNT(*) FROM settings")
    if cur.fetchone()[0] == 0:
        conn.execute("INSERT INTO settings (threshold, default_weight) VALUES (200, 1000.0)")

    # System settings defaults
    for k, v in [
        ("active_background", ""),
        ("card_opacity", "0.05"),
        ("card_color", "#ffffff"),
        ("card_blur", "2"),
        ("low_weight_threshold", "100"),
    ]:
        conn.execute("INSERT OR IGNORE INTO system_settings (key, value) VALUES (?, ?)", (k, v))

    # Materials
    cur = conn.execute("SELECT COUNT(*) FROM materials")
    if cur.fetchone()[0] == 0:
        items = _read_txt_list(os.path.join(data_dir, "database", "materials.txt"), DEFAULT_MATERIALS)
        for name in items:
            try:
                conn.execute("INSERT OR IGNORE INTO materials (name) VALUES (?)", (name,))
            except sqlite3.Error:
                pass

    # Channels
    cur = conn.execute("SELECT COUNT(*) FROM channels")
    if cur.fetchone()[0] == 0:
        for name in DEFAULT_CHANNELS:
            conn.execute("INSERT OR IGNORE INTO channels (name) VALUES (?)", (name,))


# ─── Helpers ───

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
