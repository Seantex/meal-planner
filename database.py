import os
import json
from datetime import datetime, date
from config import DB_PATH, MEAL_SLOTS

# ── DB-Backend-Konfiguration ────────────────────────────────────────────────────

DATABASE_URL = os.getenv("DATABASE_URL", "")

# Render/Heroku liefern manchmal "postgres://" statt "postgresql://"
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = "postgresql://" + DATABASE_URL[len("postgres://"):]

if DATABASE_URL:
    import psycopg2
    import psycopg2.extras
    from psycopg2.pool import ThreadedConnectionPool
    import threading

    _pool = None
    _pool_lock = threading.Lock()

    def _get_pool():
        """Lazily initialise the connection pool. Never raises — returns None on failure."""
        global _pool
        with _pool_lock:
            if _pool is None or _pool.closed:
                try:
                    _pool = ThreadedConnectionPool(
                        minconn=1,
                        maxconn=8,
                        dsn=DATABASE_URL,
                        connect_timeout=10,
                    )
                except Exception as e:
                    print(f"[DB] Pool init failed, will use direct connections: {e}")
                    _pool = None
        return _pool

    class _PooledConn:
        """Wrapper: gibt Verbindung beim .close() zurück in den Pool."""
        def __init__(self, conn, pool):
            self._conn = conn
            self._pool = pool

        def __getattr__(self, name):
            return getattr(self._conn, name)

        def close(self):
            try:
                if not self._conn.closed:
                    try:
                        self._conn.rollback()
                    except Exception:
                        pass
                if self._pool is not None:
                    self._pool.putconn(self._conn)
                else:
                    self._conn.close()
            except Exception:
                try:
                    self._conn.close()
                except Exception:
                    pass

    def get_db():
        pool = _get_pool()
        try:
            if pool is not None:
                conn = pool.getconn()
                # Verbindung prüfen
                try:
                    cur = conn.cursor()
                    cur.execute("SELECT 1")
                    cur.close()
                except Exception:
                    try:
                        pool.putconn(conn, close=True)
                    except Exception:
                        pass
                    conn = pool.getconn()
                conn.autocommit = False
                return _PooledConn(conn, pool)
        except Exception as e:
            print(f"[DB] Pool getconn failed, falling back to direct: {e}")

        # Fallback: direkte Verbindung (kein Pool)
        conn = psycopg2.connect(DATABASE_URL, connect_timeout=15)
        conn.autocommit = False
        return _PooledConn(conn, None)

    def _cursor(conn):
        return conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    PH = "%s"           # Platzhalter
    NOW = "NOW()"       # aktuelle Zeit
    DATE_NOW = "CURRENT_DATE"
    SERIAL = "SERIAL"

    def get_lastrowid(cursor):
        row = cursor.fetchone()
        # RealDictCursor gibt dict zurück → key 'id'
        if isinstance(row, dict):
            return row.get("id") or list(row.values())[0]
        return row[0]

    IS_POSTGRES = True

else:
    import sqlite3

    def get_db():
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def _cursor(conn):
        return conn.cursor()

    PH = "?"
    NOW = "datetime('now')"
    DATE_NOW = "date('now')"
    SERIAL = "INTEGER"

    def get_lastrowid(cursor):
        return cursor.lastrowid

    IS_POSTGRES = False


def _exec(conn, sql, params=()):
    """Führt ein Statement aus und gibt den Cursor zurück."""
    cur = _cursor(conn)
    cur.execute(sql, params)
    return cur


def _fetchone(conn, sql, params=()):
    cur = _exec(conn, sql, params)
    row = cur.fetchone()
    if row is None:
        return None
    if IS_POSTGRES:
        return dict(row)
    return dict(row)   # sqlite3.Row unterstützt dict() direkt


def _fetchall(conn, sql, params=()):
    cur = _exec(conn, sql, params)
    rows = cur.fetchall()
    return [dict(r) for r in rows]


# ── Schema-Initialisierung ──────────────────────────────────────────────────────

def init_db():
    conn = get_db()

    if IS_POSTGRES:
        _init_postgres(conn)
        # PostgreSQL migrations
        cur = _cursor(conn)
        for ddl in [
            "ALTER TABLE week_plans ADD COLUMN IF NOT EXISTS name TEXT DEFAULT ''",
            "ALTER TABLE week_plans ADD COLUMN IF NOT EXISTS sort_order INTEGER DEFAULT 0",
        ]:
            try:
                cur.execute(ddl)
                conn.commit()
            except Exception:
                conn.rollback()
    else:
        c = conn.cursor()
        _init_sqlite(c)
        _migrate_schema(c)
        _ensure_admin(c)
        conn.commit()

    conn.close()


def _init_sqlite(c):
    # ── Benutzer ───────────────────────────────────────────────────────────────
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            email         TEXT    NOT NULL UNIQUE COLLATE NOCASE,
            name          TEXT    NOT NULL,
            password_hash TEXT    NOT NULL,
            is_admin      INTEGER DEFAULT 0,
            is_verified   INTEGER DEFAULT 0,
            created_at    TEXT    DEFAULT (datetime('now'))
        )
    """)

    # ── Favoriten ──────────────────────────────────────────────────────────────
    c.execute("""
        CREATE TABLE IF NOT EXISTS favorites (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id     INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            recipe_id   TEXT    NOT NULL,
            cook_count  INTEGER DEFAULT 1,
            last_cooked TEXT,
            added_at    TEXT    DEFAULT (datetime('now')),
            UNIQUE(user_id, recipe_id)
        )
    """)

    # ── Nie-Wieder-Liste ───────────────────────────────────────────────────────
    c.execute("""
        CREATE TABLE IF NOT EXISTS never_again (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id   INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            recipe_id TEXT    NOT NULL,
            reason    TEXT,
            added_at  TEXT    DEFAULT (datetime('now')),
            UNIQUE(user_id, recipe_id)
        )
    """)

    # ── Aktuelle Angebote (gecacht, global) ────────────────────────────────────
    c.execute("""
        CREATE TABLE IF NOT EXISTS deals (
            id               INTEGER PRIMARY KEY AUTOINCREMENT,
            supermarket      TEXT NOT NULL,
            product_name     TEXT NOT NULL,
            description      TEXT,
            price            REAL,
            original_price   REAL,
            discount_pct     INTEGER,
            discount_label   TEXT,
            category         TEXT,
            valid_from       TEXT,
            valid_to         TEXT,
            scraped_at       TEXT DEFAULT (datetime('now'))
        )
    """)

    # ── Wochenpläne ────────────────────────────────────────────────────────────
    c.execute("""
        CREATE TABLE IF NOT EXISTS week_plans (
            id             INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id        INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            week_start     TEXT NOT NULL,
            cravings       TEXT,
            status         TEXT DEFAULT 'in_progress',
            default_persons INTEGER DEFAULT 2,
            created_at     TEXT DEFAULT (datetime('now'))
        )
    """)

    # ── Ausgewählte Rezepte pro Slot ──────────────────────────────────────────
    c.execute("""
        CREATE TABLE IF NOT EXISTS meal_selections (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            plan_id     INTEGER NOT NULL REFERENCES week_plans(id) ON DELETE CASCADE,
            meal_slot   TEXT NOT NULL,
            recipe_id   TEXT NOT NULL,
            selected_at TEXT DEFAULT (datetime('now'))
        )
    """)

    # ── Einkaufsliste ──────────────────────────────────────────────────────────
    c.execute("""
        CREATE TABLE IF NOT EXISTS shopping_items (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            plan_id         INTEGER NOT NULL REFERENCES week_plans(id) ON DELETE CASCADE,
            ingredient_name TEXT NOT NULL,
            amount          REAL,
            unit            TEXT,
            category        TEXT,
            is_deal         INTEGER DEFAULT 0,
            supermarket     TEXT,
            deal_price      TEXT,
            checked         INTEGER DEFAULT 0,
            note            TEXT
        )
    """)

    # ── KI-Vorschläge (gecacht pro Plan + Slot) ───────────────────────────────
    c.execute("""
        CREATE TABLE IF NOT EXISTS ai_suggestions (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            plan_id     INTEGER NOT NULL REFERENCES week_plans(id) ON DELETE CASCADE,
            meal_slot   TEXT NOT NULL,
            suggestions TEXT NOT NULL,
            created_at  TEXT DEFAULT (datetime('now'))
        )
    """)

    # ── Kochanweisungen (gecacht, global) ─────────────────────────────────────
    c.execute("""
        CREATE TABLE IF NOT EXISTS recipe_instructions (
            recipe_id    TEXT PRIMARY KEY,
            instructions TEXT NOT NULL,
            generated_at TEXT DEFAULT (datetime('now'))
        )
    """)

    # ── Eigene Rezepte der Nutzer (KI-generiert oder manuell) ─────────────────
    c.execute("""
        CREATE TABLE IF NOT EXISTS user_recipes (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id     INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            recipe_id   TEXT    NOT NULL,
            recipe_json TEXT    NOT NULL,
            created_at  TEXT    DEFAULT (datetime('now')),
            UNIQUE(user_id, recipe_id)
        )
    """)

    # ── KI-Nutzungslimits ─────────────────────────────────────────────────────
    c.execute("""
        CREATE TABLE IF NOT EXISTS ai_usage (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id     INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            usage_type  TEXT    NOT NULL,
            week_start  TEXT    NOT NULL,
            count       INTEGER DEFAULT 0,
            UNIQUE(user_id, usage_type, week_start)
        )
    """)

    # ── Portionen pro Slot ─────────────────────────────────────────────────────
    c.execute("""
        CREATE TABLE IF NOT EXISTS slot_settings (
            plan_id   INTEGER NOT NULL REFERENCES week_plans(id) ON DELETE CASCADE,
            meal_slot TEXT    NOT NULL,
            portions  INTEGER NOT NULL DEFAULT 2,
            PRIMARY KEY (plan_id, meal_slot)
        )
    """)

    # ── Plan-spezifische Slots (anpassbar) ───────────────────────────────────
    c.execute("""
        CREATE TABLE IF NOT EXISTS plan_slots (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            plan_id    INTEGER NOT NULL REFERENCES week_plans(id) ON DELETE CASCADE,
            slot_id    TEXT    NOT NULL,
            label      TEXT    NOT NULL,
            type       TEXT    DEFAULT 'weekday',
            note       TEXT    DEFAULT '',
            leftovers  INTEGER DEFAULT 0,
            sort_order INTEGER DEFAULT 0,
            UNIQUE(plan_id, slot_id)
        )
    """)

    # ── Abgehakte Slots (gekocht) ─────────────────────────────────────────────
    c.execute("""
        CREATE TABLE IF NOT EXISTS slot_cooked (
            plan_id   INTEGER NOT NULL REFERENCES week_plans(id) ON DELETE CASCADE,
            meal_slot TEXT    NOT NULL,
            cooked_at TEXT    DEFAULT (datetime('now')),
            PRIMARY KEY (plan_id, meal_slot)
        )
    """)

    # ── E-Mail-Tokens (Verifikation & Passwort-Reset) ─────────────────────────
    c.execute("""
        CREATE TABLE IF NOT EXISTS email_tokens (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id    INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            token      TEXT    NOT NULL UNIQUE,
            token_type TEXT    NOT NULL,
            expires_at TEXT    NOT NULL,
            created_at TEXT    DEFAULT (datetime('now'))
        )
    """)

    # ── Benutzer-Profile (Onboarding) ─────────────────────────────────────────
    c.execute("""
        CREATE TABLE IF NOT EXISTS user_profiles (
            user_id        INTEGER PRIMARY KEY,
            goal           TEXT    DEFAULT 'gesund_ernaehren',
            dietary        TEXT    DEFAULT '[]',
            allergies      TEXT    DEFAULT '[]',
            calorie_target INTEGER DEFAULT NULL,
            onboarding_done INTEGER DEFAULT 0,
            updated_at     TEXT    DEFAULT (datetime('now')),
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    """)


def _init_postgres(conn):
    """Erstellt alle Tabellen für PostgreSQL (IF NOT EXISTS)."""
    stmts = [
        # users
        """CREATE TABLE IF NOT EXISTS users (
            id            SERIAL PRIMARY KEY,
            email         TEXT    NOT NULL UNIQUE,
            name          TEXT    NOT NULL,
            password_hash TEXT    NOT NULL,
            is_admin      INTEGER DEFAULT 0,
            is_verified   INTEGER DEFAULT 0,
            created_at    TEXT    DEFAULT NOW()
        )""",
        # favorites
        """CREATE TABLE IF NOT EXISTS favorites (
            id          SERIAL PRIMARY KEY,
            user_id     INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            recipe_id   TEXT    NOT NULL,
            cook_count  INTEGER DEFAULT 1,
            last_cooked TEXT,
            added_at    TEXT    DEFAULT NOW(),
            UNIQUE(user_id, recipe_id)
        )""",
        # never_again
        """CREATE TABLE IF NOT EXISTS never_again (
            id        SERIAL PRIMARY KEY,
            user_id   INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            recipe_id TEXT    NOT NULL,
            reason    TEXT,
            added_at  TEXT    DEFAULT NOW(),
            UNIQUE(user_id, recipe_id)
        )""",
        # deals
        """CREATE TABLE IF NOT EXISTS deals (
            id               SERIAL PRIMARY KEY,
            supermarket      TEXT NOT NULL,
            product_name     TEXT NOT NULL,
            description      TEXT,
            price            REAL,
            original_price   REAL,
            discount_pct     INTEGER,
            discount_label   TEXT,
            category         TEXT,
            valid_from       TEXT,
            valid_to         TEXT,
            scraped_at       TEXT DEFAULT NOW()
        )""",
        # week_plans
        """CREATE TABLE IF NOT EXISTS week_plans (
            id              SERIAL PRIMARY KEY,
            user_id         INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            week_start      TEXT NOT NULL,
            cravings        TEXT,
            status          TEXT DEFAULT 'in_progress',
            default_persons INTEGER DEFAULT 2,
            created_at      TEXT DEFAULT NOW()
        )""",
        # meal_selections
        """CREATE TABLE IF NOT EXISTS meal_selections (
            id          SERIAL PRIMARY KEY,
            plan_id     INTEGER NOT NULL REFERENCES week_plans(id) ON DELETE CASCADE,
            meal_slot   TEXT NOT NULL,
            recipe_id   TEXT NOT NULL,
            selected_at TEXT DEFAULT NOW()
        )""",
        # shopping_items
        """CREATE TABLE IF NOT EXISTS shopping_items (
            id              SERIAL PRIMARY KEY,
            plan_id         INTEGER NOT NULL REFERENCES week_plans(id) ON DELETE CASCADE,
            ingredient_name TEXT NOT NULL,
            amount          REAL,
            unit            TEXT,
            category        TEXT,
            is_deal         INTEGER DEFAULT 0,
            supermarket     TEXT,
            deal_price      TEXT,
            checked         INTEGER DEFAULT 0,
            note            TEXT
        )""",
        # ai_suggestions
        """CREATE TABLE IF NOT EXISTS ai_suggestions (
            id          SERIAL PRIMARY KEY,
            plan_id     INTEGER NOT NULL REFERENCES week_plans(id) ON DELETE CASCADE,
            meal_slot   TEXT    NOT NULL,
            suggestions TEXT    NOT NULL,
            created_at  TEXT    DEFAULT NOW()
        )""",
        # recipe_instructions
        """CREATE TABLE IF NOT EXISTS recipe_instructions (
            recipe_id    TEXT PRIMARY KEY,
            instructions TEXT NOT NULL,
            generated_at TEXT DEFAULT NOW()
        )""",
        # user_recipes
        """CREATE TABLE IF NOT EXISTS user_recipes (
            id          SERIAL PRIMARY KEY,
            user_id     INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            recipe_id   TEXT    NOT NULL,
            recipe_json TEXT    NOT NULL,
            created_at  TEXT    DEFAULT NOW(),
            UNIQUE(user_id, recipe_id)
        )""",
        # ai_usage
        """CREATE TABLE IF NOT EXISTS ai_usage (
            id          SERIAL PRIMARY KEY,
            user_id     INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            usage_type  TEXT    NOT NULL,
            week_start  TEXT    NOT NULL,
            count       INTEGER DEFAULT 0,
            UNIQUE(user_id, usage_type, week_start)
        )""",
        # slot_settings
        """CREATE TABLE IF NOT EXISTS slot_settings (
            plan_id   INTEGER NOT NULL REFERENCES week_plans(id) ON DELETE CASCADE,
            meal_slot TEXT    NOT NULL,
            portions  INTEGER NOT NULL DEFAULT 2,
            PRIMARY KEY (plan_id, meal_slot)
        )""",
        # plan_slots
        """CREATE TABLE IF NOT EXISTS plan_slots (
            id         SERIAL PRIMARY KEY,
            plan_id    INTEGER NOT NULL REFERENCES week_plans(id) ON DELETE CASCADE,
            slot_id    TEXT    NOT NULL,
            label      TEXT    NOT NULL,
            type       TEXT    DEFAULT 'weekday',
            note       TEXT    DEFAULT '',
            leftovers  INTEGER DEFAULT 0,
            sort_order INTEGER DEFAULT 0,
            UNIQUE(plan_id, slot_id)
        )""",
        # slot_cooked
        """CREATE TABLE IF NOT EXISTS slot_cooked (
            plan_id   INTEGER NOT NULL REFERENCES week_plans(id) ON DELETE CASCADE,
            meal_slot TEXT    NOT NULL,
            cooked_at TEXT    DEFAULT NOW(),
            PRIMARY KEY (plan_id, meal_slot)
        )""",
        # email_tokens
        """CREATE TABLE IF NOT EXISTS email_tokens (
            id         SERIAL PRIMARY KEY,
            user_id    INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            token      TEXT    NOT NULL UNIQUE,
            token_type TEXT    NOT NULL,
            expires_at TEXT    NOT NULL,
            created_at TEXT    DEFAULT NOW()
        )""",
        # user_profiles
        """CREATE TABLE IF NOT EXISTS user_profiles (
            user_id        INTEGER PRIMARY KEY,
            goal           TEXT    DEFAULT 'gesund_ernaehren',
            dietary        TEXT    DEFAULT '[]',
            allergies      TEXT    DEFAULT '[]',
            calorie_target INTEGER DEFAULT NULL,
            onboarding_done INTEGER DEFAULT 0,
            updated_at     TEXT    DEFAULT NOW(),
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )""",
    ]
    cur = _cursor(conn)
    for stmt in stmts:
        cur.execute(stmt)
    conn.commit()
    # Admin-Benutzer anlegen
    _ensure_admin_pg(conn)
    conn.commit()


def _migrate_schema(c):
    """Migriert alte Single-User-Tabellen auf das Multi-User-Schema (nur SQLite)."""
    # favorites
    fav_cols = [r[1] for r in c.execute("PRAGMA table_info(favorites)").fetchall()]
    if fav_cols and "user_id" not in fav_cols:
        old = c.execute("SELECT recipe_id, cook_count, last_cooked, added_at FROM favorites").fetchall()
        c.execute("DROP TABLE favorites")
        c.execute("""CREATE TABLE favorites (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            recipe_id TEXT NOT NULL, cook_count INTEGER DEFAULT 1,
            last_cooked TEXT, added_at TEXT DEFAULT (datetime('now')),
            UNIQUE(user_id, recipe_id))""")
        for r in old:
            c.execute("INSERT INTO favorites (user_id,recipe_id,cook_count,last_cooked,added_at) VALUES (1,?,?,?,?)",
                      (r[0], r[1], r[2], r[3]))

    # never_again
    na_cols = [r[1] for r in c.execute("PRAGMA table_info(never_again)").fetchall()]
    if na_cols and "user_id" not in na_cols:
        old = c.execute("SELECT recipe_id, reason, added_at FROM never_again").fetchall()
        c.execute("DROP TABLE never_again")
        c.execute("""CREATE TABLE never_again (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            recipe_id TEXT NOT NULL, reason TEXT, added_at TEXT DEFAULT (datetime('now')),
            UNIQUE(user_id, recipe_id))""")
        for r in old:
            c.execute("INSERT INTO never_again (user_id,recipe_id,reason,added_at) VALUES (1,?,?,?)",
                      (r[0], r[1], r[2]))

    # users: is_verified hinzufügen falls fehlt
    u_cols = [r[1] for r in c.execute("PRAGMA table_info(users)").fetchall()]
    if u_cols and "is_verified" not in u_cols:
        c.execute("ALTER TABLE users ADD COLUMN is_verified INTEGER DEFAULT 0")
        c.execute("UPDATE users SET is_verified = 1")

    # week_plans: default_persons hinzufügen falls fehlt
    wp_cols = [r[1] for r in c.execute("PRAGMA table_info(week_plans)").fetchall()]
    if wp_cols and "default_persons" not in wp_cols:
        c.execute("ALTER TABLE week_plans ADD COLUMN default_persons INTEGER DEFAULT 2")
    if wp_cols and "name" not in wp_cols:
        c.execute("ALTER TABLE week_plans ADD COLUMN name TEXT DEFAULT ''")
    if wp_cols and "sort_order" not in wp_cols:
        c.execute("ALTER TABLE week_plans ADD COLUMN sort_order INTEGER DEFAULT 0")

    # week_plans: user_id Migration
    if wp_cols and "user_id" not in wp_cols:
        old = c.execute("SELECT id, week_start, cravings, status, created_at FROM week_plans").fetchall()
        c.execute("DROP TABLE week_plans")
        c.execute("""CREATE TABLE week_plans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            week_start TEXT NOT NULL, cravings TEXT,
            status TEXT DEFAULT 'in_progress', created_at TEXT DEFAULT (datetime('now')))""")
        for r in old:
            c.execute("INSERT INTO week_plans (id,user_id,week_start,cravings,status,created_at) VALUES (?,1,?,?,?,?)",
                      (r[0], r[1], r[2], r[3], r[4]))


def _ensure_admin(c):
    """Legt den Standard-Admin an, falls noch kein Admin existiert (SQLite)."""
    from werkzeug.security import generate_password_hash
    existing = c.execute("SELECT id FROM users WHERE is_admin=1").fetchone()
    if not existing:
        pw_hash = generate_password_hash("MealAdmin2024!", method="pbkdf2:sha256")
        c.execute("""INSERT OR IGNORE INTO users (email, name, password_hash, is_admin, is_verified)
                     VALUES (?, ?, ?, 1, 1)""",
                  ("admin@mealplanner.at", "Admin", pw_hash))


def _ensure_admin_pg(conn):
    """Legt den Standard-Admin an, falls noch kein Admin existiert (PostgreSQL)."""
    from werkzeug.security import generate_password_hash
    cur = _cursor(conn)
    cur.execute("SELECT id FROM users WHERE is_admin=1")
    existing = cur.fetchone()
    if not existing:
        pw_hash = generate_password_hash("MealAdmin2024!", method="pbkdf2:sha256")
        cur.execute("""INSERT INTO users (email, name, password_hash, is_admin, is_verified)
                       VALUES (%s, %s, %s, 1, 1)
                       ON CONFLICT DO NOTHING""",
                    ("admin@mealplanner.at", "Admin", pw_hash))


# ── Benutzer ───────────────────────────────────────────────────────────────────

def create_user(email: str, name: str, password_hash: str, is_admin: bool = False) -> int:
    conn = get_db()
    if IS_POSTGRES:
        cur = _cursor(conn)
        cur.execute(f"""
            INSERT INTO users (email, name, password_hash, is_admin)
            VALUES ({PH}, {PH}, {PH}, {PH})
            RETURNING id
        """, (email.lower().strip(), name.strip(), password_hash, int(is_admin)))
        user_id = get_lastrowid(cur)
    else:
        cur = conn.execute(f"""
            INSERT INTO users (email, name, password_hash, is_admin)
            VALUES ({PH}, {PH}, {PH}, {PH})
        """, (email.lower().strip(), name.strip(), password_hash, int(is_admin)))
        user_id = get_lastrowid(cur)
    conn.commit()
    conn.close()
    return user_id


def get_user_by_email(email: str):
    conn = get_db()
    if IS_POSTGRES:
        r = _fetchone(conn, f"SELECT * FROM users WHERE LOWER(email) = LOWER({PH})", (email.strip(),))
    else:
        r = _fetchone(conn, f"SELECT * FROM users WHERE email = {PH} COLLATE NOCASE", (email.strip(),))
    conn.close()
    return r


def get_user_by_id(user_id: int):
    conn = get_db()
    r = _fetchone(conn, f"SELECT * FROM users WHERE id = {PH}", (user_id,))
    conn.close()
    return r


def get_all_users() -> list:
    """Gibt alle Benutzer mit Nutzungsstatistiken zurück (für Admin)."""
    conn = get_db()
    users = _fetchall(conn, "SELECT * FROM users ORDER BY created_at DESC")
    week = _week_start_str()
    for u in users:
        uid = u["id"]
        recipe_used = (_fetchone(conn, f"SELECT count FROM ai_usage WHERE user_id={PH} AND usage_type={PH} AND week_start={PH}",
                                  (uid, "recipe", week)) or {}).get("count", 0)
        plan_used   = (_fetchone(conn, f"SELECT count FROM ai_usage WHERE user_id={PH} AND usage_type={PH} AND week_start={PH}",
                                  (uid, "plan",   week)) or {}).get("count", 0)
        plan_count  = (_fetchone(conn, f"SELECT COUNT(*) AS c FROM week_plans WHERE user_id={PH}", (uid,)) or {}).get("c", 0)
        u["recipe_used"] = recipe_used
        u["plan_used"]   = plan_used
        u["total_plans"] = plan_count
    conn.close()
    return users


def get_admin_users() -> list:
    """Gibt alle Nutzer mit Admin-Rechten zurück."""
    conn = get_db()
    users = _fetchall(conn, "SELECT id, email, name FROM users WHERE is_admin = 1")
    conn.close()
    return users


def update_user_profile(user_id: int, name: str, email: str, is_admin: int, is_verified: int):
    conn = get_db()
    _exec(conn, f"""UPDATE users SET name={PH}, email={PH}, is_admin={PH}, is_verified={PH}
                    WHERE id={PH}""",
          (name.strip(), email.strip().lower(), int(is_admin), int(is_verified), user_id))
    conn.commit()
    conn.close()


def delete_user(user_id: int):
    conn = get_db()
    _exec(conn, f"DELETE FROM users WHERE id={PH}", (user_id,))
    conn.commit()
    conn.close()


def reset_user_ai_usage(user_id: int, usage_type: str):
    """Löscht alle KI-Nutzungseinträge eines Nutzers für diesen Typ (gibt vollen Kontingent zurück)."""
    conn = get_db()
    _exec(conn, f"DELETE FROM ai_usage WHERE user_id={PH} AND usage_type={PH}",
          (user_id, usage_type))
    conn.commit()
    conn.close()


def email_exists(email: str) -> bool:
    conn = get_db()
    if IS_POSTGRES:
        r = _fetchone(conn, f"SELECT 1 FROM users WHERE LOWER(email) = LOWER({PH})", (email.strip(),))
    else:
        r = _fetchone(conn, f"SELECT 1 FROM users WHERE email = {PH} COLLATE NOCASE", (email.strip(),))
    conn.close()
    return r is not None


# ── Benutzer-Profile (Onboarding) ─────────────────────────────────────────────

_DEFAULT_PROFILE = {
    'goal': 'gesund_ernaehren',
    'dietary': '[]',
    'allergies': '[]',
    'calorie_target': None,
    'onboarding_done': 0,
}


def get_user_profile(user_id: int) -> dict:
    """Gibt das Profil des Nutzers zurück. Falls nicht vorhanden, sensible Defaults."""
    conn = get_db()
    row = _fetchone(conn, f"SELECT * FROM user_profiles WHERE user_id = {PH}", (user_id,))
    conn.close()
    if row is None:
        result = dict(_DEFAULT_PROFILE)
        result['user_id'] = user_id
        return result
    return dict(row)


def save_user_profile(user_id: int, goal: str, dietary_json: str, allergies_json: str,
                      calorie_target) -> None:
    """Upsert Nutzerprofil, setzt onboarding_done=1."""
    conn = get_db()
    if IS_POSTGRES:
        _exec(conn, f"""
            INSERT INTO user_profiles (user_id, goal, dietary, allergies, calorie_target, onboarding_done, updated_at)
            VALUES ({PH}, {PH}, {PH}, {PH}, {PH}, 1, NOW())
            ON CONFLICT (user_id) DO UPDATE SET
                goal = EXCLUDED.goal,
                dietary = EXCLUDED.dietary,
                allergies = EXCLUDED.allergies,
                calorie_target = EXCLUDED.calorie_target,
                onboarding_done = 1,
                updated_at = NOW()
        """, (user_id, goal, dietary_json, allergies_json, calorie_target))
    else:
        _exec(conn, f"""
            INSERT INTO user_profiles (user_id, goal, dietary, allergies, calorie_target, onboarding_done, updated_at)
            VALUES ({PH}, {PH}, {PH}, {PH}, {PH}, 1, datetime('now'))
            ON CONFLICT(user_id) DO UPDATE SET
                goal = excluded.goal,
                dietary = excluded.dietary,
                allergies = excluded.allergies,
                calorie_target = excluded.calorie_target,
                onboarding_done = 1,
                updated_at = datetime('now')
        """, (user_id, goal, dietary_json, allergies_json, calorie_target))
    conn.commit()
    conn.close()


def is_onboarding_done(user_id: int) -> bool:
    """Gibt True zurück wenn Onboarding abgeschlossen wurde."""
    conn = get_db()
    row = _fetchone(conn, f"SELECT onboarding_done FROM user_profiles WHERE user_id = {PH}", (user_id,))
    conn.close()
    if row is None:
        return False
    return bool(row.get('onboarding_done', 0))


# ── KI-Limits ─────────────────────────────────────────────────────────────────

LIMITS = {
    "recipe": 3,   # 3 KI-Rezepte pro Woche
    "plan":   1,   # 1 Wochenplan pro Woche
    # wish_<slot_id>: 1 pro Slot pro Woche (dynamisch vergeben)
}


def _week_start_str() -> str:
    today = date.today()
    monday = today - __import__("datetime").timedelta(days=today.weekday())
    return monday.isoformat()


def get_ai_usage(user_id: int, usage_type: str) -> int:
    """Gibt den aktuellen Zähler zurück."""
    conn = get_db()
    r = _fetchone(conn, f"""
        SELECT count FROM ai_usage
        WHERE user_id = {PH} AND usage_type = {PH} AND week_start = {PH}
    """, (user_id, usage_type, _week_start_str()))
    conn.close()
    return r["count"] if r else 0


def get_ai_remaining(user_id: int, usage_type: str, is_admin: bool = False) -> int:
    """Gibt die verbleibenden Nutzungen zurück. Admins haben unbegrenzt."""
    if is_admin:
        return 999
    # wish_<slot> hat ein Limit von 1
    if usage_type.startswith("wish_"):
        limit = 1
    else:
        limit = LIMITS.get(usage_type, 0)
    used = get_ai_usage(user_id, usage_type)
    return max(0, limit - used)


def increment_ai_usage(user_id: int, usage_type: str):
    conn = get_db()
    _exec(conn, f"""
        INSERT INTO ai_usage (user_id, usage_type, week_start, count)
        VALUES ({PH}, {PH}, {PH}, 1)
        ON CONFLICT(user_id, usage_type, week_start)
        DO UPDATE SET count = ai_usage.count + 1
    """, (user_id, usage_type, _week_start_str()))
    conn.commit()
    conn.close()


def can_use_ai(user_id: int, usage_type: str, is_admin: bool = False) -> bool:
    return get_ai_remaining(user_id, usage_type, is_admin) > 0


# ── Eigene Benutzer-Rezepte ───────────────────────────────────────────────────

def save_user_recipe(user_id: int, recipe: dict):
    conn = get_db()
    _exec(conn, f"""
        INSERT INTO user_recipes (user_id, recipe_id, recipe_json)
        VALUES ({PH}, {PH}, {PH})
        ON CONFLICT(user_id, recipe_id)
        DO UPDATE SET recipe_json = EXCLUDED.recipe_json
    """, (user_id, recipe["id"], json.dumps(recipe, ensure_ascii=False)))
    conn.commit()
    conn.close()


def get_user_recipes(user_id: int) -> list:
    conn = get_db()
    rows = _fetchall(conn, f"""
        SELECT recipe_json FROM user_recipes WHERE user_id = {PH}
        ORDER BY created_at DESC
    """, (user_id,))
    conn.close()
    return [json.loads(r["recipe_json"]) for r in rows]


def delete_user_recipe(user_id: int, recipe_id: str):
    conn = get_db()
    _exec(conn, f"DELETE FROM user_recipes WHERE user_id = {PH} AND recipe_id = {PH}",
          (user_id, recipe_id))
    conn.commit()
    conn.close()


def is_user_recipe(user_id: int, recipe_id: str) -> bool:
    conn = get_db()
    r = _fetchone(conn, f"SELECT 1 FROM user_recipes WHERE user_id = {PH} AND recipe_id = {PH}",
                  (user_id, recipe_id))
    conn.close()
    return r is not None


# ── Favoriten ──────────────────────────────────────────────────────────────────

def add_favorite(recipe_id: str, user_id: int = 1):
    conn = get_db()
    _exec(conn, f"""
        INSERT INTO favorites (user_id, recipe_id, cook_count, last_cooked)
        VALUES ({PH}, {PH}, 1, {DATE_NOW})
        ON CONFLICT(user_id, recipe_id) DO UPDATE SET
            cook_count  = favorites.cook_count + 1,
            last_cooked = {DATE_NOW}
    """, (user_id, recipe_id))
    conn.commit()
    conn.close()


def remove_favorite(recipe_id: str, user_id: int = 1):
    conn = get_db()
    _exec(conn, f"DELETE FROM favorites WHERE user_id = {PH} AND recipe_id = {PH}", (user_id, recipe_id))
    conn.commit()
    conn.close()


def get_favorites(user_id: int = 1) -> list:
    conn = get_db()
    rows = _fetchall(conn,
        f"SELECT * FROM favorites WHERE user_id = {PH} ORDER BY cook_count DESC", (user_id,)
    )
    conn.close()
    return rows


def is_favorite(recipe_id: str, user_id: int = 1) -> bool:
    conn = get_db()
    r = _fetchone(conn,
        f"SELECT 1 FROM favorites WHERE user_id = {PH} AND recipe_id = {PH}", (user_id, recipe_id)
    )
    conn.close()
    return r is not None


# ── Nie-Wieder ─────────────────────────────────────────────────────────────────

def add_never_again(recipe_id: str, reason: str = "", user_id: int = 1):
    conn = get_db()
    _exec(conn, f"""
        INSERT INTO never_again (user_id, recipe_id, reason)
        VALUES ({PH}, {PH}, {PH})
        ON CONFLICT(user_id, recipe_id)
        DO UPDATE SET reason = EXCLUDED.reason
    """, (user_id, recipe_id, reason))
    conn.commit()
    conn.close()


def remove_never_again(recipe_id: str, user_id: int = 1):
    conn = get_db()
    _exec(conn, f"DELETE FROM never_again WHERE user_id = {PH} AND recipe_id = {PH}", (user_id, recipe_id))
    conn.commit()
    conn.close()


def get_never_again(user_id: int = 1) -> list:
    conn = get_db()
    rows = _fetchall(conn, f"SELECT * FROM never_again WHERE user_id = {PH}", (user_id,))
    conn.close()
    return rows


def is_never_again(recipe_id: str, user_id: int = 1) -> bool:
    conn = get_db()
    r = _fetchone(conn,
        f"SELECT 1 FROM never_again WHERE user_id = {PH} AND recipe_id = {PH}", (user_id, recipe_id)
    )
    conn.close()
    return r is not None


# ── Deals ──────────────────────────────────────────────────────────────────────

def save_deals(deals: list):
    conn = get_db()
    _exec(conn, "DELETE FROM deals")
    for deal in deals:
        _exec(conn, f"""
            INSERT INTO deals
              (supermarket, product_name, description, price, original_price,
               discount_pct, discount_label, category, valid_from, valid_to)
            VALUES
              ({PH}, {PH}, {PH}, {PH}, {PH}, {PH}, {PH}, {PH}, {PH}, {PH})
        """, (
            deal.get("supermarket"),
            deal.get("product_name"),
            deal.get("description"),
            deal.get("price"),
            deal.get("original_price"),
            deal.get("discount_pct"),
            deal.get("discount_label"),
            deal.get("category"),
            deal.get("valid_from"),
            deal.get("valid_to"),
        ))
    conn.commit()
    conn.close()


def get_deals() -> list:
    conn = get_db()
    rows = _fetchall(conn, "SELECT * FROM deals ORDER BY supermarket, discount_pct DESC")
    conn.close()
    return rows


def deals_are_fresh() -> bool:
    conn = get_db()
    if IS_POSTGRES:
        r = _fetchone(conn, """
            SELECT COUNT(*) as cnt FROM deals
            WHERE DATE(scraped_at::text) = CURRENT_DATE
        """)
    else:
        r = _fetchone(conn, """
            SELECT COUNT(*) as cnt FROM deals
            WHERE date(scraped_at) = date('now')
        """)
    conn.close()
    return r["cnt"] > 0


# ── Wochenplan ─────────────────────────────────────────────────────────────────

def create_week_plan(week_start: str, cravings: str = "", user_id: int = 1,
                     default_persons: int = 2, slot_config: list = None) -> int:
    conn = get_db()
    if IS_POSTGRES:
        cur = _cursor(conn)
        cur.execute(f"""
            INSERT INTO week_plans (user_id, week_start, cravings, default_persons)
            VALUES ({PH}, {PH}, {PH}, {PH})
            RETURNING id
        """, (user_id, week_start, cravings, default_persons))
        plan_id = get_lastrowid(cur)
    else:
        cur = conn.execute(f"""
            INSERT INTO week_plans (user_id, week_start, cravings, default_persons)
            VALUES ({PH}, {PH}, {PH}, {PH})
        """, (user_id, week_start, cravings, default_persons))
        plan_id = get_lastrowid(cur)

    # Slots: benutzerdefiniert oder Standard aus config.py
    slots_source = slot_config if slot_config else [
        {"id": s["id"], "label": s["label"], "type": s.get("type", "weekday"),
         "note": s.get("note", ""), "leftovers": s.get("leftovers", False)}
        for s in MEAL_SLOTS
    ]
    for i, slot in enumerate(slots_source):
        _exec(conn, f"""
            INSERT INTO plan_slots
                (plan_id, slot_id, label, type, note, leftovers, sort_order)
            VALUES ({PH}, {PH}, {PH}, {PH}, {PH}, {PH}, {PH})
            ON CONFLICT (plan_id, slot_id) DO NOTHING
        """, (plan_id, slot["id"], slot["label"], slot.get("type", "weekday"),
              slot.get("note", ""), int(slot.get("leftovers", False)),
              slot.get("sort_order", i)))
    conn.commit()
    conn.close()
    return plan_id


def get_active_plan(user_id: int = 1):
    conn = get_db()
    r = _fetchone(conn, f"""
        SELECT * FROM week_plans WHERE user_id = {PH}
        ORDER BY created_at DESC LIMIT 1
    """, (user_id,))
    conn.close()
    return r


def get_plan(plan_id: int, user_id: int = None):
    conn = get_db()
    if user_id is not None:
        r = _fetchone(conn,
            f"SELECT * FROM week_plans WHERE id = {PH} AND user_id = {PH}", (plan_id, user_id)
        )
    else:
        r = _fetchone(conn, f"SELECT * FROM week_plans WHERE id = {PH}", (plan_id,))
    conn.close()
    return r


def get_recent_plans(user_id: int, limit: int = 8) -> list:
    """Gibt die letzten Pläne eines Users zurück."""
    conn = get_db()
    rows = _fetchall(conn, f"""
        SELECT * FROM week_plans WHERE user_id = {PH}
        ORDER BY sort_order DESC, created_at DESC LIMIT {PH}
    """, (user_id, limit))
    conn.close()
    return rows


def finish_plan(plan_id: int):
    conn = get_db()
    _exec(conn, f"UPDATE week_plans SET status = 'done' WHERE id = {PH}", (plan_id,))
    conn.commit()
    conn.close()


def rename_plan(plan_id: int, name: str):
    conn = get_db()
    _exec(conn, f"UPDATE week_plans SET name = {PH} WHERE id = {PH}", (name.strip(), plan_id))
    conn.commit()
    conn.close()


def reorder_plan(plan_id: int, user_id: int, direction: str):
    """Swap sort_order with the adjacent plan (direction: 'up' or 'down')."""
    conn = get_db()
    plans = _fetchall(conn, f"""
        SELECT id, sort_order FROM week_plans WHERE user_id = {PH}
        ORDER BY sort_order DESC, created_at DESC
    """, (user_id,))
    idx = next((i for i, p in enumerate(plans) if p['id'] == plan_id), None)
    if idx is None:
        conn.close()
        return
    if direction == 'up' and idx > 0:
        neighbor = plans[idx - 1]
    elif direction == 'down' and idx < len(plans) - 1:
        neighbor = plans[idx + 1]
    else:
        conn.close()
        return
    my_order = plans[idx]['sort_order']
    nb_order = neighbor['sort_order']
    if my_order == nb_order:
        my_order = nb_order + 1 if direction == 'up' else nb_order - 1
    else:
        my_order, nb_order = nb_order, my_order
    _exec(conn, f"UPDATE week_plans SET sort_order = {PH} WHERE id = {PH}", (my_order, plan_id))
    _exec(conn, f"UPDATE week_plans SET sort_order = {PH} WHERE id = {PH}", (nb_order, neighbor['id']))
    conn.commit()
    conn.close()


def delete_plan(plan_id: int):
    conn = get_db()
    # Cascade-Löschen aller abhängigen Daten
    for table in ["meal_selections", "meal_suggestions", "plan_slots",
                  "slot_settings", "slot_cooked", "shopping_items"]:
        _exec(conn, f"DELETE FROM {table} WHERE plan_id = {PH}", (plan_id,))
    _exec(conn, f"DELETE FROM week_plans WHERE id = {PH}", (plan_id,))
    conn.commit()
    conn.close()


def get_recent_recipe_ids(exclude_plan_id: int, limit_plans: int = 2, user_id: int = 1) -> list:
    conn = get_db()
    rows = _fetchall(conn, f"""
        SELECT ms.recipe_id
        FROM meal_selections ms
        JOIN week_plans wp ON ms.plan_id = wp.id
        WHERE wp.status = 'done'
          AND wp.user_id = {PH}
          AND wp.id != {PH}
        GROUP BY ms.recipe_id, wp.created_at
        ORDER BY wp.created_at DESC
        LIMIT {PH}
    """, (user_id, exclude_plan_id, limit_plans * 9))
    conn.close()
    return [r["recipe_id"] for r in rows]


# ── Mahlzeiten-Auswahl ─────────────────────────────────────────────────────────

def save_selection(plan_id: int, meal_slot: str, recipe_id: str):
    conn = get_db()
    _exec(conn, f"DELETE FROM meal_selections WHERE plan_id = {PH} AND meal_slot = {PH}",
          (plan_id, meal_slot))
    _exec(conn, f"""
        INSERT INTO meal_selections (plan_id, meal_slot, recipe_id)
        VALUES ({PH}, {PH}, {PH})
    """, (plan_id, meal_slot, recipe_id))
    conn.commit()
    conn.close()


def get_selections(plan_id: int) -> dict:
    conn = get_db()
    rows = _fetchall(conn, f"""
        SELECT meal_slot, recipe_id FROM meal_selections WHERE plan_id = {PH}
    """, (plan_id,))
    conn.close()
    return {r["meal_slot"]: r["recipe_id"] for r in rows}


# ── Einkaufsliste ──────────────────────────────────────────────────────────────

def save_shopping_list(plan_id: int, items: list):
    conn = get_db()
    _exec(conn, f"DELETE FROM shopping_items WHERE plan_id = {PH}", (plan_id,))
    for item in items:
        _exec(conn, f"""
            INSERT INTO shopping_items
              (plan_id, ingredient_name, amount, unit, category,
               is_deal, supermarket, deal_price)
            VALUES ({PH}, {PH}, {PH}, {PH}, {PH}, {PH}, {PH}, {PH})
        """, (
            plan_id,
            item.get("name"),
            item.get("amount"),
            item.get("unit"),
            item.get("category"),
            int(item.get("is_deal", False)),
            item.get("supermarket"),
            item.get("deal_price"),
        ))
    conn.commit()
    conn.close()


def get_shopping_list(plan_id: int) -> list:
    conn = get_db()
    rows = _fetchall(conn, f"""
        SELECT * FROM shopping_items WHERE plan_id = {PH}
        ORDER BY category, ingredient_name
    """, (plan_id,))
    conn.close()
    return rows


def toggle_shopping_item(item_id: int) -> bool:
    conn = get_db()
    r = _fetchone(conn, f"SELECT checked FROM shopping_items WHERE id = {PH}", (item_id,))
    if not r:
        conn.close()
        return False
    new_state = 1 - r["checked"]
    _exec(conn, f"UPDATE shopping_items SET checked = {PH} WHERE id = {PH}", (new_state, item_id))
    conn.commit()
    conn.close()
    return True


def update_shopping_note(item_id: int, note: str):
    conn = get_db()
    _exec(conn, f"UPDATE shopping_items SET note = {PH} WHERE id = {PH}", (note, item_id))
    conn.commit()
    conn.close()


def update_shopping_amount(item_id: int, amount):
    conn = get_db()
    _exec(conn, f"UPDATE shopping_items SET amount = {PH} WHERE id = {PH}", (amount, item_id))
    conn.commit()
    conn.close()


def get_shopping_item(item_id: int):
    conn = get_db()
    row = _fetchone(conn, f"SELECT * FROM shopping_items WHERE id = {PH}", (item_id,))
    conn.close()
    return row


def delete_shopping_item(item_id: int):
    conn = get_db()
    _exec(conn, f"DELETE FROM shopping_items WHERE id = {PH}", (item_id,))
    conn.commit()
    conn.close()


# ── Kochanweisungen ────────────────────────────────────────────────────────────

def get_instructions(recipe_id: str):
    conn = get_db()
    r = _fetchone(conn,
        f"SELECT instructions FROM recipe_instructions WHERE recipe_id = {PH}", (recipe_id,)
    )
    conn.close()
    return json.loads(r["instructions"]) if r else None


def save_instructions(recipe_id: str, instructions: list):
    conn = get_db()
    _exec(conn, f"""
        INSERT INTO recipe_instructions (recipe_id, instructions)
        VALUES ({PH}, {PH})
        ON CONFLICT (recipe_id)
        DO UPDATE SET instructions = EXCLUDED.instructions
    """, (recipe_id, json.dumps(instructions, ensure_ascii=False)))
    conn.commit()
    conn.close()


# ── KI-Vorschläge ──────────────────────────────────────────────────────────────

def save_suggestions(plan_id: int, meal_slot: str, suggestions: list):
    conn = get_db()
    _exec(conn, f"DELETE FROM ai_suggestions WHERE plan_id = {PH} AND meal_slot = {PH}",
          (plan_id, meal_slot))
    _exec(conn, f"""
        INSERT INTO ai_suggestions (plan_id, meal_slot, suggestions)
        VALUES ({PH}, {PH}, {PH})
    """, (plan_id, meal_slot, json.dumps(suggestions, ensure_ascii=False)))
    conn.commit()
    conn.close()


def get_suggestions(plan_id: int, meal_slot: str) -> list:
    conn = get_db()
    r = _fetchone(conn, f"""
        SELECT suggestions FROM ai_suggestions
        WHERE plan_id = {PH} AND meal_slot = {PH}
    """, (plan_id, meal_slot))
    conn.close()
    return json.loads(r["suggestions"]) if r else []


def get_all_suggestions(plan_id: int) -> dict:
    conn = get_db()
    rows = _fetchall(conn, f"""
        SELECT meal_slot, suggestions FROM ai_suggestions WHERE plan_id = {PH}
    """, (plan_id,))
    conn.close()
    return {r["meal_slot"]: json.loads(r["suggestions"]) for r in rows}


# ── Portionen ──────────────────────────────────────────────────────────────────

def get_default_persons(plan_id: int) -> int:
    conn = get_db()
    r = _fetchone(conn, f"SELECT default_persons FROM week_plans WHERE id = {PH}", (plan_id,))
    conn.close()
    return (r["default_persons"] if r and r["default_persons"] else 2)


def set_default_persons(plan_id: int, persons: int):
    conn = get_db()
    _exec(conn, f"UPDATE week_plans SET default_persons = {PH} WHERE id = {PH}", (persons, plan_id))
    conn.commit()
    conn.close()


def get_slot_portions(plan_id: int, meal_slot: str, default_persons: int = 2, leftovers: bool = False) -> int:
    """Gibt die Portionen für einen Slot zurück (Override oder Standard)."""
    conn = get_db()
    r = _fetchone(conn,
        f"SELECT portions FROM slot_settings WHERE plan_id = {PH} AND meal_slot = {PH}",
        (plan_id, meal_slot)
    )
    conn.close()
    if r:
        return r["portions"]
    # Standard: bei Leftovers-Slots = persons * 1.5 aufgerundet
    if leftovers:
        return max(2, round(default_persons * 1.5))
    return default_persons


def set_slot_portions(plan_id: int, meal_slot: str, portions: int):
    conn = get_db()
    _exec(conn, f"""
        INSERT INTO slot_settings (plan_id, meal_slot, portions)
        VALUES ({PH}, {PH}, {PH})
        ON CONFLICT (plan_id, meal_slot)
        DO UPDATE SET portions = EXCLUDED.portions
    """, (plan_id, meal_slot, portions))
    conn.commit()
    conn.close()


def get_all_slot_portions(plan_id: int) -> dict:
    """Gibt alle Slot-Overrides als Dict zurück."""
    conn = get_db()
    rows = _fetchall(conn, f"SELECT meal_slot, portions FROM slot_settings WHERE plan_id = {PH}", (plan_id,))
    conn.close()
    return {r["meal_slot"]: r["portions"] for r in rows}


# ── E-Mail-Tokens ──────────────────────────────────────────────────────────────

def create_email_token(user_id: int, token_type: str) -> str:
    import secrets
    from datetime import datetime, timedelta
    token = secrets.token_urlsafe(32)
    expires = (datetime.utcnow() + timedelta(hours=24)).isoformat()
    conn = get_db()
    # Alte Tokens desselben Typs löschen
    _exec(conn, f"DELETE FROM email_tokens WHERE user_id = {PH} AND token_type = {PH}", (user_id, token_type))
    _exec(conn, f"""
        INSERT INTO email_tokens (user_id, token, token_type, expires_at)
        VALUES ({PH}, {PH}, {PH}, {PH})
    """, (user_id, token, token_type, expires))
    conn.commit()
    conn.close()
    return token


def verify_email_token(token: str, token_type: str):
    """Gibt user_id zurück wenn Token gültig, sonst None."""
    from datetime import datetime
    conn = get_db()
    r = _fetchone(conn, f"""
        SELECT user_id, expires_at FROM email_tokens
        WHERE token = {PH} AND token_type = {PH}
    """, (token, token_type))
    if not r:
        conn.close()
        return None
    if datetime.utcnow().isoformat() > r["expires_at"]:
        _exec(conn, f"DELETE FROM email_tokens WHERE token = {PH}", (token,))
        conn.commit()
        conn.close()
        return None
    user_id = r["user_id"]
    _exec(conn, f"DELETE FROM email_tokens WHERE token = {PH}", (token,))
    conn.commit()
    conn.close()
    return user_id


def set_user_verified(user_id: int):
    conn = get_db()
    _exec(conn, f"UPDATE users SET is_verified = 1 WHERE id = {PH}", (user_id,))
    conn.commit()
    conn.close()


def update_user_password(user_id: int, password_hash: str):
    conn = get_db()
    _exec(conn, f"UPDATE users SET password_hash = {PH} WHERE id = {PH}", (password_hash, user_id))
    conn.commit()
    conn.close()


# ── Abgehakte Slots (gekocht) ───────────────────────────────────────────────────

def get_cooked_slots(plan_id: int) -> set:
    conn = get_db()
    rows = _fetchall(conn, f"SELECT meal_slot FROM slot_cooked WHERE plan_id = {PH}", (plan_id,))
    conn.close()
    return {r["meal_slot"] for r in rows}


# ── Plan-Slots (anpassbar) ──────────────────────────────────────────────────────

def get_plan_slots(plan_id: int) -> list:
    """Gibt die Slots eines Plans zurück, sortiert nach sort_order."""
    conn = get_db()
    rows = _fetchall(conn, f"""
        SELECT slot_id, label, type, note, leftovers, sort_order
        FROM plan_slots WHERE plan_id = {PH}
        ORDER BY sort_order ASC, id ASC
    """, (plan_id,))
    conn.close()
    if rows:
        return rows
    # Fallback: falls noch keine plan_slots (alter Plan), Standard-Slots zurückgeben
    return [{"slot_id": s["id"], "label": s["label"], "type": s.get("type", "weekday"),
             "note": s.get("note", ""), "leftovers": int(s.get("leftovers", False)),
             "sort_order": i}
            for i, s in enumerate(MEAL_SLOTS)]


def add_plan_slot(plan_id: int, label: str, note: str = "", leftovers: bool = False) -> str:
    """Fügt einen neuen Slot hinzu. Gibt die neue slot_id zurück."""
    import re, time
    # Eindeutige ID aus dem Label generieren
    base = re.sub(r"[^a-z0-9]+", "_", label.lower().strip())[:20]
    slot_id = f"{base}_{int(time.time()) % 10000}"
    conn = get_db()
    r = _fetchone(conn, f"SELECT COALESCE(MAX(sort_order),0) AS mx FROM plan_slots WHERE plan_id = {PH}", (plan_id,))
    max_order = r["mx"] if r else 0
    _exec(conn, f"""
        INSERT INTO plan_slots (plan_id, slot_id, label, type, note, leftovers, sort_order)
        VALUES ({PH}, {PH}, {PH}, 'weekday', {PH}, {PH}, {PH})
    """, (plan_id, slot_id, label.strip(), note.strip(), int(leftovers), max_order + 1))
    conn.commit()
    conn.close()
    return slot_id


def remove_plan_slot(plan_id: int, slot_id: str):
    conn = get_db()
    _exec(conn, f"DELETE FROM plan_slots WHERE plan_id = {PH} AND slot_id = {PH}", (plan_id, slot_id))
    # Zugehörige Auswahl und Einstellungen ebenfalls löschen
    _exec(conn, f"DELETE FROM meal_selections WHERE plan_id = {PH} AND meal_slot = {PH}", (plan_id, slot_id))
    _exec(conn, f"DELETE FROM slot_settings WHERE plan_id = {PH} AND meal_slot = {PH}", (plan_id, slot_id))
    _exec(conn, f"DELETE FROM slot_cooked WHERE plan_id = {PH} AND meal_slot = {PH}", (plan_id, slot_id))
    conn.commit()
    conn.close()


def update_plan_slot(plan_id: int, slot_id: str, label: str, note: str = "", leftovers: bool = False):
    conn = get_db()
    _exec(conn, f"""
        UPDATE plan_slots SET label = {PH}, note = {PH}, leftovers = {PH}
        WHERE plan_id = {PH} AND slot_id = {PH}
    """, (label.strip(), note.strip(), int(leftovers), plan_id, slot_id))
    conn.commit()
    conn.close()


def toggle_slot_cooked(plan_id: int, meal_slot: str) -> bool:
    """Toggelt den 'gekocht'-Status. Gibt True zurück wenn jetzt gekocht, False wenn zurückgesetzt."""
    conn = get_db()
    exists = _fetchone(conn,
        f"SELECT 1 FROM slot_cooked WHERE plan_id = {PH} AND meal_slot = {PH}", (plan_id, meal_slot)
    )
    if exists:
        _exec(conn, f"DELETE FROM slot_cooked WHERE plan_id = {PH} AND meal_slot = {PH}", (plan_id, meal_slot))
        conn.commit()
        conn.close()
        return False
    else:
        _exec(conn, f"INSERT INTO slot_cooked (plan_id, meal_slot) VALUES ({PH}, {PH})", (plan_id, meal_slot))
        conn.commit()
        conn.close()
        return True
