"""
Migriert die DB vom Single-User- auf das Multi-User-Schema.
Bestehende Daten werden dem Admin-User (id=1) zugewiesen.
"""
import sqlite3
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import DB_PATH


def migrate():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = OFF")
    c = conn.cursor()

    # ── users Tabelle ──────────────────────────────────────────────────────────
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            email         TEXT    NOT NULL UNIQUE COLLATE NOCASE,
            name          TEXT    NOT NULL,
            password_hash TEXT    NOT NULL,
            is_admin      INTEGER DEFAULT 0,
            created_at    TEXT    DEFAULT (datetime('now'))
        )
    """)

    # ── favorites migrieren ────────────────────────────────────────────────────
    fav_cols = [r[1] for r in c.execute("PRAGMA table_info(favorites)").fetchall()]
    if "user_id" not in fav_cols:
        print("Migriere favorites…")
        old_favs = c.execute("SELECT recipe_id, cook_count, last_cooked, added_at FROM favorites").fetchall()
        c.execute("DROP TABLE favorites")
        c.execute("""
            CREATE TABLE favorites (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id     INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                recipe_id   TEXT    NOT NULL,
                cook_count  INTEGER DEFAULT 1,
                last_cooked TEXT,
                added_at    TEXT    DEFAULT (datetime('now')),
                UNIQUE(user_id, recipe_id)
            )
        """)
        for row in old_favs:
            c.execute("INSERT INTO favorites (user_id, recipe_id, cook_count, last_cooked, added_at) VALUES (1,?,?,?,?)",
                      (row[0], row[1], row[2], row[3]))
        print(f"  {len(old_favs)} Favoriten zu user_id=1 migriert.")

    # ── never_again migrieren ──────────────────────────────────────────────────
    na_cols = [r[1] for r in c.execute("PRAGMA table_info(never_again)").fetchall()]
    if "user_id" not in na_cols:
        print("Migriere never_again…")
        old_na = c.execute("SELECT recipe_id, reason, added_at FROM never_again").fetchall()
        c.execute("DROP TABLE never_again")
        c.execute("""
            CREATE TABLE never_again (
                id        INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id   INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                recipe_id TEXT    NOT NULL,
                reason    TEXT,
                added_at  TEXT    DEFAULT (datetime('now')),
                UNIQUE(user_id, recipe_id)
            )
        """)
        for row in old_na:
            c.execute("INSERT INTO never_again (user_id, recipe_id, reason, added_at) VALUES (1,?,?,?)",
                      (row[0], row[1], row[2]))
        print(f"  {len(old_na)} Never-again zu user_id=1 migriert.")

    # ── week_plans migrieren ───────────────────────────────────────────────────
    wp_cols = [r[1] for r in c.execute("PRAGMA table_info(week_plans)").fetchall()]
    if "user_id" not in wp_cols:
        print("Migriere week_plans…")
        old_plans = c.execute("SELECT id, week_start, cravings, status, created_at FROM week_plans").fetchall()
        c.execute("DROP TABLE week_plans")
        c.execute("""
            CREATE TABLE week_plans (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id     INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                week_start  TEXT NOT NULL,
                cravings    TEXT,
                status      TEXT DEFAULT 'in_progress',
                created_at  TEXT DEFAULT (datetime('now'))
            )
        """)
        for row in old_plans:
            c.execute("INSERT INTO week_plans (id, user_id, week_start, cravings, status, created_at) VALUES (?,1,?,?,?,?)",
                      (row[0], row[1], row[2], row[3], row[4]))
        print(f"  {len(old_plans)} Wochenpläne zu user_id=1 migriert.")

    # ── neue Tabellen anlegen (falls noch nicht vorhanden) ─────────────────────
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

    conn.commit()
    conn.execute("PRAGMA foreign_keys = ON")
    conn.close()
    print("Migration abgeschlossen.")


if __name__ == "__main__":
    migrate()
