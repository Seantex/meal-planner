#!/usr/bin/env python3
"""
Generiert 40+ neue hochwertige Rezepte via Claude API
und fügt sie zu data/recipes.json hinzu.
"""
import json, os, re, sys
from anthropic import Anthropic

BASE = os.path.dirname(os.path.abspath(__file__))
RECIPES_PATH = os.path.join(BASE, "data", "recipes.json")

# Load .env for API key
try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(BASE, ".env"), override=True)
except ImportError:
    pass

API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
if not API_KEY:
    print("FEHLER: ANTHROPIC_API_KEY nicht gesetzt!")
    sys.exit(1)

client = Anthropic(api_key=API_KEY)

with open(RECIPES_PATH, "r", encoding="utf-8") as f:
    data = json.load(f)

existing_ids   = {r["id"] for r in data["recipes"]}
existing_names = {r["name"] for r in data["recipes"]}
example        = json.dumps(data["recipes"][0], ensure_ascii=False, indent=2)

print(f"Aktuell: {len(data['recipes'])} Rezepte")
print("Generiere 40 neue Rezepte via Claude…")

BATCHES = [
    {
        "theme": "Schnelle Wochentags-Pasta & Nudeln",
        "recipes": [
            "Linguine alle Vongole (Muscheln)",
            "Spaghetti Aglio e Olio mit Petersilie",
            "Pasta Primavera mit Frühlingsgemüse",
            "Cacio e Pepe",
            "Pasta mit Zucchini und Garnelen",
            "Penne mit Ricotta und Spinat",
            "Orecchiette mit Brokkoli und Anchovis",
        ]
    },
    {
        "theme": "Fleisch & Geflügel (Wochentag, schnell)",
        "recipes": [
            "Teriyaki-Hähnchen mit gedämpftem Reis",
            "Hähnchenpfanne mit Paprika und Oliven",
            "Döner Bowl mit Joghurt-Knoblauch-Sauce",
            "Pulled Chicken Wraps",
            "Souvlaki mit Pitabrot und Tzatziki",
            "Schweinefilet in Senf-Sahne-Sauce",
            "Köttbullar (Schwedische Hackbällchen) mit Kartoffelpüree",
            "Chili con Carne mit Reis",
        ]
    },
    {
        "theme": "Fisch & Meeresfrüchte",
        "recipes": [
            "Garnelen in Knoblauch-Butter mit Baguette",
            "Thunfisch-Poke-Bowl mit Avocado",
            "Fish Tacos mit Coleslaw",
            "Lachsfilet mit Senf-Honig-Kruste",
            "Garnelen-Fried-Rice",
            "Forelle Müllerin Art mit Mandelbutter",
        ]
    },
    {
        "theme": "Vegetarisch & Vegan",
        "recipes": [
            "Kichererbsen-Curry mit Kokosmilch",
            "Cremige Tomatensuppe mit Croutons",
            "Linsensuppe mit geräuchertem Paprika",
            "Gemüse-Wok mit Erdnuss-Sauce",
            "Käse-Quesadillas mit Avocado-Dip",
            "Shakshuka (Pochierte Eier in Tomatensauce)",
            "Caprese-Gnocchi aus der Pfanne",
            "Süßkartoffel-Bowl mit Tahini",
        ]
    },
    {
        "theme": "Wochenend-Highlights (aufwendiger)",
        "recipes": [
            "Schweinsbraten mit Semmelknödeln und Sauerkraut",
            "Beef Bourguignon mit Baguette",
            "Pulled Pork Burger",
            "Lammkoteletts mit Rosmarinkartoffeln",
            "Paella Valenciana",
            "Moussaka nach griechischer Art",
            "Chicken Parmigiana mit Pasta",
            "Sushi Bowl mit Lachs und Mango",
        ]
    },
    {
        "theme": "Suppen, Eintöpfe & Comfort Food",
        "recipes": [
            "Zwiebelsuppe mit Käse-Croutons",
            "Minestrone",
            "Tom Kha Gai (Thai Kokossuppe)",
            "Tajine mit Hähnchen und Oliven",
        ]
    }
]

PROMPT_TEMPLATE = """Du bist ein professioneller Koch und Rezeptautor. Erstelle {count} hochwertige, wirklich leckere Rezepte auf Deutsch im exakten JSON-Format.

THEMA: {theme}
REZEPTE ZU ERSTELLEN: {recipe_list}

EXAKTES JSON-FORMAT (folge diesem Beispiel genau):
{example}

REGELN:
- id: snake_case, einzigartig (z.B. "linguine_vongole")
- name: Deutsch, appetitlich
- description: 1 Satz, macht Hunger
- category: pasta / fleisch / fisch / vegetarisch / geflügel / suppe / süß
- type: "weekday" (≤45min aktiv) / "weekend" (bis 90min) / "both"
- difficulty: einfach / mittel / schwer
- servings: immer 2
- nutrition_per_portion: realistische Werte (calories, protein, carbs, fat)
- deal_keywords: österreichische Supermarkt-relevante Begriffe auf Deutsch
- ingredients: für 2 Personen, mit amount (Zahl oder null), unit, category, is_basic
  - is_basic: true nur für Salz/Pfeffer/Öl/Zucker (Haushaltsgrundstoffe)
  - category: fleisch/fisch/gemüse/milch/eier/käse/nudeln/reis/brot/konserven/gewürze/sonstiges
- tips: optionaler Profi-Tipp (String)
- recipe_url: "" (leer lassen)

KEINE IDs aus dieser Liste verwenden: {existing_ids}

Antworte NUR mit einem JSON-Array [...] (keine Erklärung davor/danach):"""

all_new_recipes = []
errors = 0

for batch in BATCHES:
    recipe_list = "\n".join(f"- {r}" for r in batch["recipes"])
    existing_ids_sample = ", ".join(list(existing_ids)[:20])

    prompt = PROMPT_TEMPLATE.format(
        count=len(batch["recipes"]),
        theme=batch["theme"],
        recipe_list=recipe_list,
        example=example,
        existing_ids=existing_ids_sample,
    )

    print(f"\n[{batch['theme']}] Generiere {len(batch['recipes'])} Rezepte…")

    try:
        msg = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=6000,
            messages=[{"role": "user", "content": prompt}]
        )
        text = msg.content[0].text.strip()

        # JSON extrahieren
        json_match = re.search(r'\[[\s\S]*\]', text)
        if not json_match:
            print(f"  WARNUNG: Kein JSON gefunden in Antwort")
            errors += 1
            continue

        recipes = json.loads(json_match.group())
        new_count = 0
        for r in recipes:
            if not isinstance(r, dict):
                continue
            if r.get("id") in existing_ids:
                r["id"] = r["id"] + "_2"
            if r.get("id") and r.get("name"):
                # Sicherstellen dass recipe_url vorhanden
                r.setdefault("recipe_url", "")
                r.setdefault("tips", "")
                all_new_recipes.append(r)
                existing_ids.add(r["id"])
                new_count += 1

        print(f"  ✓ {new_count} Rezepte generiert")

    except Exception as e:
        print(f"  FEHLER: {e}")
        errors += 1

print(f"\n{'='*50}")
print(f"Gesamt neue Rezepte: {len(all_new_recipes)}")
print(f"Fehler: {errors}")

if all_new_recipes:
    data["recipes"].extend(all_new_recipes)

    # Backup
    backup_path = RECIPES_PATH + ".backup"
    import shutil
    shutil.copy2(RECIPES_PATH, backup_path)
    print(f"Backup erstellt: {backup_path}")

    with open(RECIPES_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"recipes.json aktualisiert: {len(data['recipes'])} Rezepte total")
    print("Starte die App neu um die neuen Rezepte zu sehen!")
else:
    print("Keine neuen Rezepte hinzugefügt.")
