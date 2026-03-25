import os
from dotenv import load_dotenv

# Absoluter Pfad zur .env – funktioniert auch wenn Flask den Reloader startet
_BASE = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(_BASE, ".env"), override=True)

# ── Anthropic API ──────────────────────────────────────────────────────────────
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
CLAUDE_MODEL = "claude-haiku-4-5-20251001"

# ── Flask ──────────────────────────────────────────────────────────────────────
SECRET_KEY = os.getenv("SECRET_KEY", "meal-planner-secret-2024")
DEBUG = os.getenv("DEBUG", "true").lower() == "true"

# ── Pfade ──────────────────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.getenv("DB_PATH", os.path.join(BASE_DIR, "data", "meal_planner.db"))
RECIPES_PATH = os.path.join(BASE_DIR, "data", "recipes.json")
UPLOADS_DIR = os.path.join(BASE_DIR, "uploads")

# ── Budget ─────────────────────────────────────────────────────────────────────
BUDGET_MIN = 75
BUDGET_MAX = 100
BUDGET_WARNING = 120   # ab hier Warnung anzeigen

# ── Mahlzeiten-Slots der Woche ─────────────────────────────────────────────────
# Jeder Slot = Abendessen (+ Mittagessen nächster Tag als Reste)
# Samstag und Sonntag: extra Mittag und Abend
MEAL_SLOTS = [
    {"id": "sa_mittag", "label": "Samstag Mittag",    "type": "weekend", "note": "Mittagessen · 2 Pers.",      "leftovers": False},
    {"id": "sa_abend",  "label": "Samstag Abend",     "type": "weekend", "note": "Reste → Sonntag Mittag",     "leftovers": True},
    {"id": "so_mittag", "label": "Sonntag Mittag",    "type": "weekend", "note": "Mittagessen · 2 Pers.",      "leftovers": False},
    {"id": "so_abend",  "label": "Sonntag Abend",     "type": "weekend", "note": "Reste → Montag Mittag",      "leftovers": True},
    {"id": "mo_abend",  "label": "Montag Abend",      "type": "weekday", "note": "Reste → Dienstag Mittag",    "leftovers": True},
    {"id": "di_abend",  "label": "Dienstag Abend",    "type": "weekday", "note": "Reste → Mittwoch Mittag",    "leftovers": True},
    {"id": "mi_abend",  "label": "Mittwoch Abend",    "type": "weekday", "note": "Reste → Donnerstag Mittag",  "leftovers": True},
    {"id": "do_abend",  "label": "Donnerstag Abend",  "type": "weekday", "note": "Reste → Freitag Mittag",     "leftovers": True},
    {"id": "fr_abend",  "label": "Freitag Abend",     "type": "weekend", "note": "Nur Abendessen · 2 Pers.",   "leftovers": False},
]

# ── Scraper Einstellungen ──────────────────────────────────────────────────────
SCRAPER_TIMEOUT = 15
SCRAPER_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "de-AT,de;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}
