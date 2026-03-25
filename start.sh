#!/bin/bash
# ── Meal Planner Starter ────────────────────────────────────────

set -e
cd "$(dirname "$0")"

echo "🍽️  Meal Planner wird gestartet…"
echo ""

# Prüfen ob .env existiert
if [ ! -f ".env" ]; then
  echo "⚠️  Keine .env Datei gefunden!"
  echo "   Kopiere .env.example zu .env und trage deinen API Key ein:"
  echo ""
  echo "   cp .env.example .env"
  echo "   nano .env   (oder öffne die Datei in einem Editor)"
  echo ""
  cp .env.example .env 2>/dev/null || true
  echo "   .env wurde angelegt – bitte API Key eintragen und nochmal starten."
  exit 1
fi

# Prüfen ob Python 3 vorhanden
if ! command -v python3 &> /dev/null; then
  echo "❌ Python 3 nicht gefunden. Bitte installiere Python 3.10+"
  exit 1
fi

# Virtuelle Umgebung erstellen falls nicht vorhanden
if [ ! -d "venv" ]; then
  echo "📦 Erstelle virtuelle Python-Umgebung…"
  python3 -m venv venv
fi

# Abhängigkeiten installieren
echo "📦 Installiere Abhängigkeiten…"
source venv/bin/activate
pip install -q -r requirements.txt

# Datenbank initialisieren
echo "🗄️  Datenbank wird initialisiert…"
python3 -c "import database; database.init_db(); print('   ✓ Datenbank bereit')"

echo ""
echo "✅ Bereit! Die App öffnet sich unter:"
echo "   → http://localhost:5001"
echo ""
echo "   (Strg+C zum Beenden)"
echo ""

# App starten
python3 app.py
