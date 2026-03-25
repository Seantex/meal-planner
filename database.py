import sqlite3
import json
from datetime import datetime, date
from config import DB_PATH


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    conn = get_db()
    c = conn.cursor()

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

    # ── Schema-Migration (Single-User → Multi-User) ───────────────────────────
    _migrate_schema(c)

    conn.commit()
    conn.close()


def _migrate_schema(c):
    """Migriert alte Single-User-Tabellen auf das Multi-User-Schema."""
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
        # Bestehende User (admin) als verifiziert markieren
        c.execute("UPDATE users SET is_verified = 1")

    # week_plans: default_persons hinzufügen falls fehlt
    wp_cols = [r[1] for r in c.execute("PRAGMA table_info(week_plans)").fetchall()]
    if wp_cols and "default_persons" not in wp_cols:
        c.execute("ALTER TABLE week_plans ADD COLUMN default_persons INTEGER DEFAULT 2")

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


# ── Benutzer ───────────────────────────────────────────────────────────────────

def create_user(email: str, name: str, password_hash: str, is_admin: bool = False) -> int:
    conn = get_db()
    cur = conn.execute("""
        INSERT INTO users (email, name, password_hash, is_admin)
        VALUES (?, ?, ?, ?)
    """, (email.lower().strip(), name.strip(), password_hash, int(is_admin)))
    user_id = cur.lastrowid
    conn.commit()
    conn.close()
    return user_id


def get_user_by_email(email: str):
    conn = get_db()
    r = conn.execute("SELECT * FROM users WHERE email = ? COLLATE NOCASE", (email.strip(),)).fetchone()
    conn.close()
    return dict(r) if r else None


def get_user_by_id(user_id: int):
    conn = get_db()
    r = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    conn.close()
    return dict(r) if r else None


def email_exists(email: str) -> bool:
    conn = get_db()
    r = conn.execute("SELECT 1 FROM users WHERE email = ? COLLATE NOCASE", (email.strip(),)).fetchone()
    conn.close()
    return r is not None


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
    r = conn.execute("""
        SELECT count FROM ai_usage
        WHERE user_id = ? AND usage_type = ? AND week_start = ?
    """, (user_id, usage_type, _week_start_str())).fetchone()
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
    conn.execute("""
        INSERT INTO ai_usage (user_id, usage_type, week_start, count)
        VALUES (?, ?, ?, 1)
        ON CONFLICT(user_id, usage_type, week_start)
        DO UPDATE SET count = count + 1
    """, (user_id, usage_type, _week_start_str()))
    conn.commit()
    conn.close()


def can_use_ai(user_id: int, usage_type: str, is_admin: bool = False) -> bool:
    return get_ai_remaining(user_id, usage_type, is_admin) > 0


# ── Eigene Benutzer-Rezepte ───────────────────────────────────────────────────

def save_user_recipe(user_id: int, recipe: dict):
    conn = get_db()
    conn.execute("""
        INSERT OR REPLACE INTO user_recipes (user_id, recipe_id, recipe_json)
        VALUES (?, ?, ?)
    """, (user_id, recipe["id"], json.dumps(recipe, ensure_ascii=False)))
    conn.commit()
    conn.close()


def get_user_recipes(user_id: int) -> list:
    conn = get_db()
    rows = conn.execute("""
        SELECT recipe_json FROM user_recipes WHERE user_id = ?
        ORDER BY created_at DESC
    """, (user_id,)).fetchall()
    conn.close()
    return [json.loads(r["recipe_json"]) for r in rows]


def delete_user_recipe(user_id: int, recipe_id: str):
    conn = get_db()
    conn.execute("DELETE FROM user_recipes WHERE user_id = ? AND recipe_id = ?",
                 (user_id, recipe_id))
    conn.commit()
    conn.close()


def is_user_recipe(user_id: int, recipe_id: str) -> bool:
    conn = get_db()
    r = conn.execute("SELECT 1 FROM user_recipes WHERE user_id = ? AND recipe_id = ?",
                     (user_id, recipe_id)).fetchone()
    conn.close()
    return r is not None


# ── Favoriten ──────────────────────────────────────────────────────────────────

def add_favorite(recipe_id: str, user_id: int = 1):
    conn = get_db()
    conn.execute("""
        INSERT INTO favorites (user_id, recipe_id, cook_count, last_cooked)
        VALUES (?, ?, 1, date('now'))
        ON CONFLICT(user_id, recipe_id) DO UPDATE SET
            cook_count  = cook_count + 1,
            last_cooked = date('now')
    """, (user_id, recipe_id))
    conn.commit()
    conn.close()


def remove_favorite(recipe_id: str, user_id: int = 1):
    conn = get_db()
    conn.execute("DELETE FROM favorites WHERE user_id = ? AND recipe_id = ?", (user_id, recipe_id))
    conn.commit()
    conn.close()


def get_favorites(user_id: int = 1) -> list:
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM favorites WHERE user_id = ? ORDER BY cook_count DESC", (user_id,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def is_favorite(recipe_id: str, user_id: int = 1) -> bool:
    conn = get_db()
    r = conn.execute(
        "SELECT 1 FROM favorites WHERE user_id = ? AND recipe_id = ?", (user_id, recipe_id)
    ).fetchone()
    conn.close()
    return r is not None


# ── Nie-Wieder ─────────────────────────────────────────────────────────────────

def add_never_again(recipe_id: str, reason: str = "", user_id: int = 1):
    conn = get_db()
    conn.execute("""
        INSERT OR REPLACE INTO never_again (user_id, recipe_id, reason)
        VALUES (?, ?, ?)
    """, (user_id, recipe_id, reason))
    conn.commit()
    conn.close()


def remove_never_again(recipe_id: str, user_id: int = 1):
    conn = get_db()
    conn.execute("DELETE FROM never_again WHERE user_id = ? AND recipe_id = ?", (user_id, recipe_id))
    conn.commit()
    conn.close()


def get_never_again(user_id: int = 1) -> list:
    conn = get_db()
    rows = conn.execute("SELECT * FROM never_again WHERE user_id = ?", (user_id,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def is_never_again(recipe_id: str, user_id: int = 1) -> bool:
    conn = get_db()
    r = conn.execute(
        "SELECT 1 FROM never_again WHERE user_id = ? AND recipe_id = ?", (user_id, recipe_id)
    ).fetchone()
    conn.close()
    return r is not None


# ── Deals ──────────────────────────────────────────────────────────────────────

def save_deals(deals: list):
    conn = get_db()
    conn.execute("DELETE FROM deals")
    conn.executemany("""
        INSERT INTO deals
          (supermarket, product_name, description, price, original_price,
           discount_pct, discount_label, category, valid_from, valid_to)
        VALUES
          (:supermarket, :product_name, :description, :price, :original_price,
           :discount_pct, :discount_label, :category, :valid_from, :valid_to)
    """, deals)
    conn.commit()
    conn.close()


def get_deals() -> list:
    conn = get_db()
    rows = conn.execute("SELECT * FROM deals ORDER BY supermarket, discount_pct DESC").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def deals_are_fresh() -> bool:
    conn = get_db()
    r = conn.execute("""
        SELECT COUNT(*) as cnt FROM deals
        WHERE date(scraped_at) = date('now')
    """).fetchone()
    conn.close()
    return r["cnt"] > 0


# ── Wochenplan ─────────────────────────────────────────────────────────────────

def create_week_plan(week_start: str, cravings: str = "", user_id: int = 1, default_persons: int = 2) -> int:
    conn = get_db()
    cur = conn.execute("""
        INSERT INTO week_plans (user_id, week_start, cravings, default_persons) VALUES (?, ?, ?, ?)
    """, (user_id, week_start, cravings, default_persons))
    plan_id = cur.lastrowid
    conn.commit()
    conn.close()
    return plan_id


def get_active_plan(user_id: int = 1):
    conn = get_db()
    r = conn.execute("""
        SELECT * FROM week_plans WHERE user_id = ?
        ORDER BY created_at DESC LIMIT 1
    """, (user_id,)).fetchone()
    conn.close()
    return dict(r) if r else None


def get_plan(plan_id: int, user_id: int = None):
    conn = get_db()
    if user_id is not None:
        r = conn.execute(
            "SELECT * FROM week_plans WHERE id = ? AND user_id = ?", (plan_id, user_id)
        ).fetchone()
    else:
        r = conn.execute("SELECT * FROM week_plans WHERE id = ?", (plan_id,)).fetchone()
    conn.close()
    return dict(r) if r else None


def finish_plan(plan_id: int):
    conn = get_db()
    conn.execute("UPDATE week_plans SET status = 'done' WHERE id = ?", (plan_id,))
    conn.commit()
    conn.close()


def get_recent_recipe_ids(exclude_plan_id: int, limit_plans: int = 2, user_id: int = 1) -> list:
    conn = get_db()
    rows = conn.execute("""
        SELECT DISTINCT ms.recipe_id
        FROM meal_selections ms
        JOIN week_plans wp ON ms.plan_id = wp.id
        WHERE wp.status = 'done'
          AND wp.user_id = ?
          AND wp.id != ?
        ORDER BY wp.created_at DESC
        LIMIT ?
    """, (user_id, exclude_plan_id, limit_plans * 9)).fetchall()
    conn.close()
    return [r["recipe_id"] for r in rows]


# ── Mahlzeiten-Auswahl ─────────────────────────────────────────────────────────

def save_selection(plan_id: int, meal_slot: str, recipe_id: str):
    conn = get_db()
    conn.execute("""
        INSERT OR REPLACE INTO meal_selections (plan_id, meal_slot, recipe_id)
        VALUES (?, ?, ?)
    """, (plan_id, meal_slot, recipe_id))
    conn.commit()
    conn.close()


def get_selections(plan_id: int) -> dict:
    conn = get_db()
    rows = conn.execute("""
        SELECT meal_slot, recipe_id FROM meal_selections WHERE plan_id = ?
    """, (plan_id,)).fetchall()
    conn.close()
    return {r["meal_slot"]: r["recipe_id"] for r in rows}


# ── Einkaufsliste ──────────────────────────────────────────────────────────────

def save_shopping_list(plan_id: int, items: list):
    conn = get_db()
    conn.execute("DELETE FROM shopping_items WHERE plan_id = ?", (plan_id,))
    for item in items:
        conn.execute("""
            INSERT INTO shopping_items
              (plan_id, ingredient_name, amount, unit, category,
               is_deal, supermarket, deal_price)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
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
    rows = conn.execute("""
        SELECT * FROM shopping_items WHERE plan_id = ?
        ORDER BY category, ingredient_name
    """, (plan_id,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def toggle_shopping_item(item_id: int) -> bool:
    conn = get_db()
    r = conn.execute("SELECT checked FROM shopping_items WHERE id = ?", (item_id,)).fetchone()
    if not r:
        conn.close()
        return False
    new_state = 1 - r["checked"]
    conn.execute("UPDATE shopping_items SET checked = ? WHERE id = ?", (new_state, item_id))
    conn.commit()
    conn.close()
    return True


def update_shopping_note(item_id: int, note: str):
    conn = get_db()
    conn.execute("UPDATE shopping_items SET note = ? WHERE id = ?", (note, item_id))
    conn.commit()
    conn.close()


def get_shopping_item(item_id: int):
    conn = get_db()
    row = conn.execute("SELECT * FROM shopping_items WHERE id = ?", (item_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def delete_shopping_item(item_id: int):
    conn = get_db()
    conn.execute("DELETE FROM shopping_items WHERE id = ?", (item_id,))
    conn.commit()
    conn.close()


# ── Kochanweisungen ────────────────────────────────────────────────────────────

def get_instructions(recipe_id: str):
    conn = get_db()
    r = conn.execute(
        "SELECT instructions FROM recipe_instructions WHERE recipe_id = ?", (recipe_id,)
    ).fetchone()
    conn.close()
    return json.loads(r["instructions"]) if r else None


def save_instructions(recipe_id: str, instructions: list):
    conn = get_db()
    conn.execute("""
        INSERT OR REPLACE INTO recipe_instructions (recipe_id, instructions)
        VALUES (?, ?)
    """, (recipe_id, json.dumps(instructions, ensure_ascii=False)))
    conn.commit()
    conn.close()


# ── KI-Vorschläge ──────────────────────────────────────────────────────────────

def save_suggestions(plan_id: int, meal_slot: str, suggestions: list):
    conn = get_db()
    conn.execute("""
        INSERT OR REPLACE INTO ai_suggestions (plan_id, meal_slot, suggestions)
        VALUES (?, ?, ?)
    """, (plan_id, meal_slot, json.dumps(suggestions, ensure_ascii=False)))
    conn.commit()
    conn.close()


def get_suggestions(plan_id: int, meal_slot: str) -> list:
    conn = get_db()
    r = conn.execute("""
        SELECT suggestions FROM ai_suggestions
        WHERE plan_id = ? AND meal_slot = ?
    """, (plan_id, meal_slot)).fetchone()
    conn.close()
    return json.loads(r["suggestions"]) if r else []


def get_all_suggestions(plan_id: int) -> dict:
    conn = get_db()
    rows = conn.execute("""
        SELECT meal_slot, suggestions FROM ai_suggestions WHERE plan_id = ?
    """, (plan_id,)).fetchall()
    conn.close()
    return {r["meal_slot"]: json.loads(r["suggestions"]) for r in rows}


# ── Portionen ──────────────────────────────────────────────────────────────────

def get_default_persons(plan_id: int) -> int:
    conn = get_db()
    r = conn.execute("SELECT default_persons FROM week_plans WHERE id = ?", (plan_id,)).fetchone()
    conn.close()
    return (r["default_persons"] if r and r["default_persons"] else 2)


def set_default_persons(plan_id: int, persons: int):
    conn = get_db()
    conn.execute("UPDATE week_plans SET default_persons = ? WHERE id = ?", (persons, plan_id))
    conn.commit()
    conn.close()


def get_slot_portions(plan_id: int, meal_slot: str, default_persons: int = 2, leftovers: bool = False) -> int:
    """Gibt die Portionen für einen Slot zurück (Override oder Standard)."""
    conn = get_db()
    r = conn.execute(
        "SELECT portions FROM slot_settings WHERE plan_id = ? AND meal_slot = ?",
        (plan_id, meal_slot)
    ).fetchone()
    conn.close()
    if r:
        return r["portions"]
    # Standard: bei Leftovers-Slots = persons * 1.5 aufgerundet
    if leftovers:
        return max(2, round(default_persons * 1.5))
    return default_persons


def set_slot_portions(plan_id: int, meal_slot: str, portions: int):
    conn = get_db()
    conn.execute("""
        INSERT OR REPLACE INTO slot_settings (plan_id, meal_slot, portions)
        VALUES (?, ?, ?)
    """, (plan_id, meal_slot, portions))
    conn.commit()
    conn.close()


def get_all_slot_portions(plan_id: int) -> dict:
    """Gibt alle Slot-Overrides als Dict zurück."""
    conn = get_db()
    rows = conn.execute("SELECT meal_slot, portions FROM slot_settings WHERE plan_id = ?", (plan_id,)).fetchall()
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
    conn.execute("DELETE FROM email_tokens WHERE user_id = ? AND token_type = ?", (user_id, token_type))
    conn.execute("""
        INSERT INTO email_tokens (user_id, token, token_type, expires_at)
        VALUES (?, ?, ?, ?)
    """, (user_id, token, token_type, expires))
    conn.commit()
    conn.close()
    return token


def verify_email_token(token: str, token_type: str):
    """Gibt user_id zurück wenn Token gültig, sonst None."""
    from datetime import datetime
    conn = get_db()
    r = conn.execute("""
        SELECT user_id, expires_at FROM email_tokens
        WHERE token = ? AND token_type = ?
    """, (token, token_type)).fetchone()
    if not r:
        conn.close()
        return None
    if datetime.utcnow().isoformat() > r["expires_at"]:
        conn.execute("DELETE FROM email_tokens WHERE token = ?", (token,))
        conn.commit()
        conn.close()
        return None
    user_id = r["user_id"]
    conn.execute("DELETE FROM email_tokens WHERE token = ?", (token,))
    conn.commit()
    conn.close()
    return user_id


def set_user_verified(user_id: int):
    conn = get_db()
    conn.execute("UPDATE users SET is_verified = 1 WHERE id = ?", (user_id,))
    conn.commit()
    conn.close()


def update_user_password(user_id: int, password_hash: str):
    conn = get_db()
    conn.execute("UPDATE users SET password_hash = ? WHERE id = ?", (password_hash, user_id))
    conn.commit()
    conn.close()


# ── Abgehakte Slots (gekocht) ───────────────────────────────────────────────────

def get_cooked_slots(plan_id: int) -> set:
    conn = get_db()
    rows = conn.execute("SELECT meal_slot FROM slot_cooked WHERE plan_id = ?", (plan_id,)).fetchall()
    conn.close()
    return {r["meal_slot"] for r in rows}


def toggle_slot_cooked(plan_id: int, meal_slot: str) -> bool:
    """Toggelt den 'gekocht'-Status. Gibt True zurück wenn jetzt gekocht, False wenn zurückgesetzt."""
    conn = get_db()
    exists = conn.execute(
        "SELECT 1 FROM slot_cooked WHERE plan_id = ? AND meal_slot = ?", (plan_id, meal_slot)
    ).fetchone()
    if exists:
        conn.execute("DELETE FROM slot_cooked WHERE plan_id = ? AND meal_slot = ?", (plan_id, meal_slot))
        conn.commit()
        conn.close()
        return False
    else:
        conn.execute("INSERT INTO slot_cooked (plan_id, meal_slot) VALUES (?, ?)", (plan_id, meal_slot))
        conn.commit()
        conn.close()
        return True
