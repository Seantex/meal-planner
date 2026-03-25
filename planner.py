"""
Meal-Planner Kernlogik + Claude Haiku Integration
"""
import json
import re
from collections import defaultdict
from anthropic import Anthropic
from config import ANTHROPIC_API_KEY, CLAUDE_MODEL, MEAL_SLOTS, RECIPES_PATH
import database as db


_client = None

def _get_client():
    global _client
    if _client is None:
        _client = Anthropic(api_key=ANTHROPIC_API_KEY)
    return _client


# ── Rezepte laden ──────────────────────────────────────────────────────────────

_base_recipes_cache = None
_user_recipes_cache = {}   # user_id → list of recipes


def _load_base_recipes() -> list:
    global _base_recipes_cache
    if _base_recipes_cache is None:
        with open(RECIPES_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        _base_recipes_cache = data["recipes"]
    return _base_recipes_cache


def load_recipes(user_id: int = None) -> list:
    """Basis-Rezepte + eigene Benutzer-Rezepte (falls user_id angegeben)."""
    base = _load_base_recipes()
    if user_id is None:
        return base
    if user_id not in _user_recipes_cache:
        _user_recipes_cache[user_id] = db.get_user_recipes(user_id)
    user_recipes = _user_recipes_cache[user_id]
    # Benutzer-Rezepte haben Vorrang bei gleicher ID
    base_ids = {r["id"] for r in user_recipes}
    merged = [r for r in base if r["id"] not in base_ids] + user_recipes
    return merged


def invalidate_user_cache(user_id: int):
    """Leert den Rezept-Cache für einen Benutzer (nach Hinzufügen/Löschen)."""
    _user_recipes_cache.pop(user_id, None)


def reload_recipes():
    """Erzwingt Neuladen aller Rezepte."""
    global _base_recipes_cache
    _base_recipes_cache = None
    _user_recipes_cache.clear()


def get_recipe(recipe_id: str, user_id: int = None):
    for r in load_recipes(user_id=user_id):
        if r["id"] == recipe_id:
            return r
    return None


def get_recipes_by_ids(ids: list, user_id: int = None) -> list:
    lookup = {r["id"]: r for r in load_recipes(user_id=user_id)}
    return [lookup[i] for i in ids if i in lookup]


# ── Haupt-Planungs-Funktion ────────────────────────────────────────────────────

def generate_week_suggestions(plan_id: int, cravings: str = "", user_id: int = None) -> dict:
    """
    Generiert für alle 7 Meal-Slots je 3 Rezeptvorschläge via Claude Haiku.
    Wochenweite Deduplizierung: kein Rezept kommt zweimal vor.
    """
    import random
    deals = db.get_deals()
    recipes = load_recipes(user_id=user_id)
    favorites = [f["recipe_id"] for f in db.get_favorites(user_id or 1)]
    never_again = [n["recipe_id"] for n in db.get_never_again(user_id or 1)]
    recent_ids = db.get_recent_recipe_ids(exclude_plan_id=plan_id, limit_plans=2, user_id=user_id or 1)
    available = [r for r in recipes if r["id"] not in never_again]
    # Shuffle so fallback picks vary across plan generations
    random.shuffle(available)

    # Schneller Lookup: ID → Rezept, Name (lowercase) → Rezept
    by_id   = {r["id"]: r for r in available}
    by_name = {r["name"].lower(): r for r in available}

    suggestions_raw = _call_claude(deals=deals, recipes=available,
                                    favorites=favorites, cravings=cravings,
                                    recent_ids=recent_ids)

    result = {}
    # Global verwendete IDs über ALLE Slots tracken → keine Wiederholung
    all_used_ids: set = set()

    plan_slots = db.get_plan_slots(plan_id)
    for slot_row in plan_slots:
        slot = {"id": slot_row["slot_id"], "label": slot_row["label"],
                "type": slot_row["type"], "note": slot_row["note"],
                "leftovers": bool(slot_row["leftovers"])}
        slot_id = slot["id"]
        slot_suggestions = suggestions_raw.get(slot_id, [])

        valid = []
        for item in slot_suggestions:
            if len(valid) >= 3:
                break
            rid = item.get("recipe_id") if isinstance(item, dict) else item
            # Exakter Match
            recipe = by_id.get(rid)
            # Fuzzy: Claude schreibt manchmal "spaghetti_carbonara" statt "carbonara"
            if not recipe:
                rid_norm = rid.lower().replace("_", " ").replace("-", " ")
                recipe = by_name.get(rid_norm)
            if not recipe:
                for r in available:
                    if r["id"] in rid or rid in r["id"]:
                        recipe = r
                        break
            if recipe and recipe["id"] not in all_used_ids:
                all_used_ids.add(recipe["id"])
                valid.append({
                    "recipe": recipe,
                    "reason": item.get("reason", "") if isinstance(item, dict) else "",
                    "deal_matches": item.get("deal_matches", []) if isinstance(item, dict) else [],
                })

        # Fallback mit globalem already_suggested → keine Wiederholung
        if len(valid) < 3:
            fallback = _get_fallback_suggestions(
                slot=slot, recipes=available, deals=deals, favorites=favorites,
                already_suggested=list(all_used_ids),
                recent_ids=recent_ids,
                count=3 - len(valid),
            )
            for s in fallback:
                all_used_ids.add(s["recipe"]["id"])
            valid.extend(fallback)

        db.save_suggestions(plan_id, slot_id, [
            {"recipe_id": v["recipe"]["id"], "reason": v["reason"],
             "deal_matches": v["deal_matches"]}
            for v in valid
        ])
        result[slot_id] = valid

    return result


def _call_claude(deals: list, recipes: list, favorites: list, cravings: str, recent_ids: list = None) -> dict:
    """
    Ruft Claude Haiku auf und gibt strukturierte Vorschläge zurück.
    """
    # Kompaktes Deals-Format für den Prompt
    deals_text = _format_deals_for_prompt(deals)
    recipes_text = _format_recipes_for_prompt(recipes)
    favorites_text = ", ".join(favorites[:15]) if favorites else "keine"
    recent_names = []
    if recent_ids:
        id_to_name = {r["id"]: r["name"] for r in recipes}
        recent_names = [id_to_name[rid] for rid in recent_ids if rid in id_to_name]
    recent_text = ", ".join(recent_names[:14]) if recent_names else "keine"

    prompt = f"""Du bist ein österreichischer Meal-Planner Assistent. Erstelle für eine Woche (2 Personen, Studenten) Rezeptvorschläge.

AKTUELLE SUPERMARKT-ANGEBOTE (Hofer/Lidl/Billa/Spar):
{deals_text}

NUTZERWUNSCH: {cravings if cravings else "keine speziellen Wünsche"}

LETZTE WOCHE BEREITS GEGESSEN (diese Rezepte NICHT vorschlagen – Abwechslung!): {recent_text}

FAVORITEN DES NUTZERS (leicht bevorzugen, aber Vielfalt wahren): {favorites_text}

VERFÜGBARE REZEPTE (ID → Name → Typ → Aktivzeit):
{recipes_text}

AUFGABE: Wähle für jeden der 7 Mahlzeiten-Slots je 3 verschiedene Rezepte aus.

MAHLZEITEN-SYSTEM:
- so_abend, mo_abend, di_abend, mi_abend, do_abend: Abendessen + 1 Extra-Portion (= 3 Portionen kochen) → Reste = nächster Tag Mittagessen
- fr_abend, sa_abend: Nur Abendessen für 2 Personen (keine Reste nötig)

REGELN:
- Slots so_abend, mo_abend bis do_abend: NUR Rezepte mit type="weekday" oder type="both" (prep_time ≤ 45 min aktiv)
- Slots fr_abend, sa_abend: Rezepte mit type="weekend" oder type="both" erlaubt (bis 90 min gesamt)
- Bevorzuge Rezepte wo mindestens 1 Zutat im Angebot ist (deal_keywords prüfen)
- Keine Wiederholungen innerhalb der Woche (alle 21 Vorschläge sollen verschiedene Rezepte sein)
- Rezepte aus "LETZTE WOCHE" niemals vorschlagen – echte Abwechslung von Woche zu Woche!
- Vielfalt: nicht 5x Pasta, Mix aus Fleisch/Fisch/Vegetarisch
- Ernährung: mindestens 3-4 proteinreiche Gerichte pro Woche
- Gelegentlich darf auch etwas Leichteres dabei sein (Palatschinken, Omelette)
- Qualität über alles: keine faden, schlechten Gerichte

Antworte NUR mit einem JSON-Objekt in diesem Format (keine Erklärung davor/danach):
{{
  "so_abend": [
    {{"recipe_id": "pizza", "reason": "Wochenstart, Pizza ist ein Favorit", "deal_matches": ["Lidl: Mozzarella"]}},
    {{"recipe_id": "lasagne", "reason": "Klassiker fürs Wochenende", "deal_matches": []}},
    {{"recipe_id": "brathaehnchen", "reason": "Einfach und lecker", "deal_matches": ["Hofer: Hähnchen"]}}
  ],
  "mo_abend": [...],
  "di_abend": [...],
  "mi_abend": [...],
  "do_abend": [...],
  "fr_abend": [...],
  "sa_abend": [...]
}}"""

    try:
        client = _get_client()
        message = client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=3000,
            messages=[{"role": "user", "content": prompt}]
        )
        response_text = message.content[0].text.strip()
        print(f"[Claude] Antwort erhalten ({len(response_text)} Zeichen)")

        # JSON aus Antwort extrahieren
        json_match = re.search(r'\{[\s\S]*\}', response_text)
        if json_match:
            parsed = json.loads(json_match.group())
            slots_found = [k for k in parsed if parsed[k]]
            print(f"[Claude] Slots mit Vorschlägen: {slots_found}")
            return parsed
        else:
            print(f"[Claude] Kein JSON in Antwort gefunden. Antwort-Anfang: {response_text[:200]}")
    except Exception as e:
        print(f"[Claude] Fehler: {e}")

    return {}


def _format_deals_for_prompt(deals: list) -> str:
    if not deals:
        return "Keine Angebote verfügbar (bitte Prospekt hochladen)"
    lines = []
    for d in deals[:60]:  # max 60 Deals im Prompt
        price_info = ""
        if d.get("price"):
            price_info = f"€{d['price']:.2f}"
            if d.get("discount_pct"):
                price_info += f" (-{d['discount_pct']}%)"
            elif d.get("discount_label"):
                price_info += f" ({d['discount_label']})"
        lines.append(f"- {d['supermarket']}: {d['product_name']} {price_info}")
    return "\n".join(lines)


def _format_recipes_for_prompt(recipes: list) -> str:
    lines = []
    for r in recipes:
        lines.append(
            f"- {r['id']}: {r['name']} | {r['type']} | {r['prep_time']}min aktiv"
            f" | keywords: {','.join(r.get('deal_keywords', [])[:5])}"
        )
    return "\n".join(lines)


def _get_fallback_suggestions(slot: dict, recipes: list, deals: list,
                               favorites: list, already_suggested: list,
                               count: int, recent_ids: list = None,
                               cravings: str = "") -> list:
    """
    Regelbasierter Fallback: diverse Kategorien, kein Rezept doppelt (wochenweit).
    """
    import random
    slot_type = slot["type"]
    available = [
        r for r in recipes
        if r["id"] not in already_suggested
        and (r["type"] == slot_type or r["type"] == "both"
             or (slot_type == "weekend" and r["type"] in ("weekday", "both")))
    ]

    if not available:
        # Falls nach strenger Filterung nichts übrig: alle nicht-verwendeten nehmen
        available = [r for r in recipes if r["id"] not in already_suggested]

    deal_kws = {d["product_name"].lower() for d in deals}
    _recent = set(recent_ids or [])
    _craving_words = [w.lower().strip() for w in cravings.replace(",", " ").split() if len(w.strip()) > 2] if cravings else []

    def score(recipe):
        s = 0
        if recipe["id"] in favorites:
            s += 10
        for kw in recipe.get("deal_keywords", []):
            if any(kw in dk for dk in deal_kws):
                s += 4
                break
        # Wunsch-Boost: Rezept matcht den eingegebenen Wunsch
        if _craving_words:
            searchable = " ".join([
                recipe.get("name", ""),
                recipe.get("description", ""),
                recipe.get("category", ""),
                " ".join(recipe.get("tags", [])),
                " ".join(ing["name"] for ing in recipe.get("ingredients", [])),
            ]).lower()
            matches = sum(1 for w in _craving_words if w in searchable)
            s += matches * 15
        # Starke Zufallskomponente → echte Abwechslung bei Refresh
        s += random.uniform(0, 12)
        # Stark bestrafen wenn letzte Woche bereits gegessen
        if recipe["id"] in _recent:
            s -= 20
        return s

    # Kategorien die bereits in dieser Runde vergeben wurden
    used_categories = set()
    scored = sorted(available, key=score, reverse=True)

    result = []
    # 1. Durchgang: diverse Kategorien bevorzugen
    for r in scored:
        if len(result) >= count:
            break
        cat = r.get("category", "sonstiges")
        if cat not in used_categories:
            used_categories.add(cat)
            deal_m = [f"{d['supermarket']}: {d['product_name']}"
                      for d in deals
                      for kw in r.get("deal_keywords", [])
                      if kw in d["product_name"].lower()][:2]
            result.append({
                "recipe": r,
                "reason": f"Abwechslung für {slot['label']}",
                "deal_matches": deal_m,
            })

    # 2. Durchgang: Falls noch nicht genug, ohne Kategorie-Einschränkung auffüllen
    if len(result) < count:
        used_ids = {s["recipe"]["id"] for s in result}
        for r in scored:
            if len(result) >= count:
                break
            if r["id"] not in used_ids:
                deal_m = [f"{d['supermarket']}: {d['product_name']}"
                          for d in deals
                          for kw in r.get("deal_keywords", [])
                          if kw in d["product_name"].lower()][:2]
                result.append({
                    "recipe": r,
                    "reason": f"Passend für {slot['label']}",
                    "deal_matches": deal_m,
                })

    return result


# ── KI-Wunsch Rezept generieren ────────────────────────────────────────────────

def generate_wish_recipe(wish: str, slot_type: str = "weekday"):
    """
    Lässt Claude ein neues Rezept passend zum Wunsch des Nutzers generieren.
    Gibt ein recipe-dict zurück (kompatibel mit dem normalen Rezeptformat).
    """
    type_hint = "schnelles Alltagsgericht (≤45 Min aktive Kochzeit)" if slot_type == "weekday" else "Wochenend-Rezept (auch aufwendiger möglich)"
    prompt = f"""Der Nutzer wünscht sich heute: "{wish}"

Erstelle ein passendes Abendessen ({type_hint}) für 2 Personen.

Antworte NUR mit diesem JSON (kein Markdown, keine Erklärung):
{{
  "name": "Rezeptname",
  "description": "Kurze appetitliche Beschreibung (1 Satz)",
  "category": "pasta|fleisch|fisch|vegetarisch|eier|sonstiges",
  "difficulty": "einfach|mittel|schwer",
  "prep_time": 20,
  "total_time": 35,
  "servings": 2,
  "nutrition_per_portion": {{"calories": 550, "protein": 35, "carbs": 45, "fat": 18}},
  "ingredients": [
    {{"name": "Zutat", "amount": 200, "unit": "g", "category": "fleisch", "is_basic": false}}
  ],
  "tips": "Optionaler Tipp",
  "tags": ["tag1", "tag2"]
}}"""

    try:
        client = _get_client()
        msg = client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=1500,
            messages=[{"role": "user", "content": prompt}]
        )
        raw = msg.content[0].text.strip()
        # JSON aus Antwort extrahieren – erst Markdown-Block, dann freies JSON
        m = re.search(r'```(?:json)?\s*\n?(\{.*?\})\s*\n?```', raw, re.DOTALL)
        if m:
            json_str = m.group(1)
        else:
            m = re.search(r'\{.*\}', raw, re.DOTALL)
            if not m:
                print(f"[wish_recipe] Kein JSON in Antwort: {raw[:300]}")
                return None
            json_str = m.group()
        data = json.loads(json_str)

        # Rezept-ID generieren und ins Format bringen
        import re as _re
        recipe_id = "wish_" + _re.sub(r"[^a-z0-9]+", "_", data.get("name", "rezept").lower()).strip("_")
        data["id"] = recipe_id
        data["type"] = slot_type
        data["deal_keywords"] = list({w.lower() for ing in data.get("ingredients", [])
                                       for w in ing["name"].split() if len(w) > 3})[:10]
        return data
    except Exception as e:
        print(f"[wish_recipe] Fehler: {e}")
        return None


# ── KI: Vollständiges Rezept für Datenbank generieren ──────────────────────────

def generate_full_recipe(wish: str, slot_type: str = "weekday"):
    """
    Generiert ein vollständiges Rezept inkl. Schritt-für-Schritt Anleitung
    via Claude und gibt es als dict zurück (bereit für recipes.json).
    """
    type_hint = "schnelles Alltagsgericht (≤45 Min aktive Kochzeit, für 2 Personen + 1 Extra-Portion als Restessen)" \
                if slot_type == "weekday" else \
                "Wochenend-Rezept für 2 Personen (auch aufwendiger erlaubt)"
    prompt = f"""Der Nutzer möchte dieses Gericht als dauerhaftes Rezept in seine Datenbank aufnehmen: "{wish}"

Erstelle ein vollständiges, detailliertes Rezept ({type_hint}).

Antworte NUR mit diesem JSON (kein Markdown, keine Erklärung davor/danach):
{{
  "name": "Vollständiger Rezeptname",
  "description": "Appetitliche Kurzbeschreibung (1-2 Sätze)",
  "category": "pasta|fleisch|fisch|vegetarisch|eier|sonstiges",
  "difficulty": "einfach|mittel|schwer",
  "prep_time": 20,
  "total_time": 35,
  "servings": 2,
  "nutrition_per_portion": {{"calories": 600, "protein": 40, "carbs": 50, "fat": 20}},
  "ingredients": [
    {{"name": "Zutat", "amount": 300, "unit": "g", "category": "fleisch|fisch|gemuese|milchprodukte|getreide|sonstiges", "is_basic": false}},
    {{"name": "Salz", "amount": null, "unit": "nach Geschmack", "category": "gewuerze", "is_basic": true}}
  ],
  "instructions": [
    "Schritt 1: Detaillierte Beschreibung",
    "Schritt 2: Detaillierte Beschreibung",
    "Schritt 3: Detaillierte Beschreibung"
  ],
  "tips": "Praktischer Tipp zum Rezept",
  "tags": ["tag1", "tag2"]
}}

Wichtig:
- Mindestens 5 Schritte in instructions
- Alle Zutaten mit realistischen Mengen für 2 Personen (österreichische Preise beachten)
- is_basic=true nur für: Salz, Pfeffer, Öl, Butter, Mehl, Zucker
- Kalorien und Protein realistisch (Hauptgericht: 500-900 kcal, 30-60g Protein)"""

    try:
        client = _get_client()
        msg = client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=2000,
            messages=[{"role": "user", "content": prompt}]
        )
        raw = msg.content[0].text.strip()
        m = re.search(r'```(?:json)?\s*\n?(\{.*?\})\s*\n?```', raw, re.DOTALL)
        if m:
            json_str = m.group(1)
        else:
            m = re.search(r'\{.*\}', raw, re.DOTALL)
            if not m:
                print(f"[gen_full_recipe] Kein JSON: {raw[:300]}")
                return None
            json_str = m.group()
        data = json.loads(json_str)

        import re as _re
        recipe_id = _re.sub(r"[^a-z0-9]+", "_", data.get("name", "rezept").lower()).strip("_")
        data["id"] = recipe_id
        data["type"] = slot_type
        data.setdefault("instructions", [])
        data["deal_keywords"] = list({w.lower() for ing in data.get("ingredients", [])
                                       for w in ing["name"].split() if len(w) > 3})[:12]
        return data
    except Exception as e:
        print(f"[gen_full_recipe] Fehler: {e}")
        return None


# ── Einkaufsliste generieren ───────────────────────────────────────────────────

def generate_shopping_list(plan_id: int, user_id: int = None) -> list:
    """
    Erstellt eine konsolidierte Einkaufsliste aus allen ausgewählten Rezepten.
    Fasst gleiche Zutaten zusammen.
    """
    selections = db.get_selections(plan_id)
    if not selections:
        return []

    deals = db.get_deals()
    deal_lookup = _build_deal_lookup(deals)

    # Portionen pro Slot aus DB holen
    plan = db.get_plan(plan_id)
    default_persons = db.get_default_persons(plan_id) if plan else 2

    # Zutaten aggregieren
    aggregated: dict[str, dict] = {}

    # Slot-Lookup für leftovers-Flag (aus plan_slots oder MEAL_SLOTS als Fallback)
    _ps = db.get_plan_slots(plan_id)
    slot_map = {s["slot_id"]: {"id": s["slot_id"], "leftovers": bool(s["leftovers"]),
                                "label": s["label"]} for s in _ps}

    for slot_id, recipe_id in selections.items():
        if recipe_id == "SKIPPED":
            continue
        recipe = get_recipe(recipe_id, user_id=user_id)
        if not recipe:
            continue

        # Portionen aus DB holen (berücksichtigt default_persons und slot-spezifische Overrides)
        slot_info = slot_map.get(slot_id, {})
        slot_portions = db.get_slot_portions(plan_id, slot_id, default_persons, slot_info.get("leftovers", False))
        recipe_servings = recipe.get("servings", 2) or 2
        portion_factor = slot_portions / recipe_servings

        for ing in recipe.get("ingredients", []):
            if ing.get("is_basic"):
                continue  # Salz, Pfeffer etc. überspringen

            key = _normalize_ingredient_name(ing["name"])
            if key not in aggregated:
                aggregated[key] = {
                    "name": ing["name"],
                    "amounts": [],
                    "unit": ing.get("unit", ""),
                    "category": ing.get("category", "sonstiges"),
                    "is_deal": False,
                    "supermarket": None,
                    "deal_price": None,
                }

            if ing.get("amount"):
                raw_amt  = ing["amount"] * portion_factor
                raw_unit = str(ing.get("unit") or "").strip()
                # Alles in g/ml normalisieren damit Aggregation korrekt ist
                raw_unit_lc = raw_unit.lower()
                if raw_unit_lc == "kg":
                    raw_amt  = raw_amt * 1000
                    raw_unit = "g"
                    aggregated[key]["unit"] = "g"
                elif raw_unit_lc in ("l", "liter"):
                    raw_amt  = raw_amt * 1000
                    raw_unit = "ml"
                    aggregated[key]["unit"] = "ml"
                aggregated[key]["amounts"].append(raw_amt)

            # Deal-Matching
            if not aggregated[key]["is_deal"]:
                deal = _find_deal(key, ing["name"], deal_lookup)
                if deal:
                    aggregated[key]["is_deal"] = True
                    aggregated[key]["supermarket"] = deal["supermarket"]
                    aggregated[key]["deal_price"] = _format_deal_price(deal)

    # In Liste umwandeln und Mengen summieren
    items = []
    for key, data in aggregated.items():
        total_amount = sum(data["amounts"]) if data["amounts"] else None
        items.append({
            "name": data["name"],
            "amount": round(total_amount, 0) if total_amount else None,
            "unit": data["unit"],
            "category": data["category"],
            "is_deal": data["is_deal"],
            "supermarket": data["supermarket"],
            "deal_price": data["deal_price"],
        })

    # Sortieren: Deals zuerst, dann nach Kategorie
    category_order = {
        "fleisch": 0, "fisch": 1, "gemüse": 2, "milch": 3, "eier": 4,
        "käse": 5, "nudeln": 6, "reis": 7, "brot": 8,
        "konserven": 9, "gewürze": 10, "sonstiges": 11,
    }
    items.sort(key=lambda x: (
        0 if x["is_deal"] else 1,
        category_order.get(x["category"], 99),
        x["name"].lower(),
    ))

    db.save_shopping_list(plan_id, items)
    return items


def _normalize_ingredient_name(name: str) -> str:
    """Normalisiert Zutatennamen für Deduplizierung."""
    return re.sub(r"\s+", " ", name.lower()
                  .replace("oder", "/")
                  .split("/")[0]
                  .strip())


def _build_deal_lookup(deals: list) -> dict:
    """Erstellt einen schnellen Lookup für Deals."""
    lookup = {}
    for d in deals:
        key = d["product_name"].lower()
        lookup[key] = d
    return lookup


def _find_deal(normalized_name: str, original_name: str, deal_lookup: dict):
    """Findet einen passenden Deal für eine Zutat."""
    # Exakter Match
    if normalized_name in deal_lookup:
        return deal_lookup[normalized_name]
    # Teilstring-Match
    for dk, deal in deal_lookup.items():
        if normalized_name in dk or dk in normalized_name:
            return deal
        # Wort-Match
        words = normalized_name.split()
        if any(w in dk for w in words if len(w) > 3):
            return deal
    return None


def _format_deal_price(deal: dict) -> str:
    price = deal.get("price")
    orig = deal.get("original_price")
    if price:
        if orig and orig > price:
            savings = round(orig - price, 2)
            return f"€{price:.2f} statt €{orig:.2f} (spare €{savings:.2f})"
        elif deal.get("discount_pct"):
            return f"€{price:.2f} (-{deal['discount_pct']}%)"
        elif deal.get("discount_label"):
            return f"€{price:.2f} {deal['discount_label']}"
        return f"€{price:.2f}"
    return deal.get("discount_label", "im Angebot")


# ── Preisreferenz laden ────────────────────────────────────────────────────────

_price_ref: dict = {}

def _get_price_ref() -> dict:
    global _price_ref
    if not _price_ref:
        import os
        prices_path = os.path.join(os.path.dirname(RECIPES_PATH), "ingredient_prices.json")
        try:
            with open(prices_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            _price_ref = data.get("prices", {})
        except Exception as e:
            print(f"[prices] Konnte Preisreferenz nicht laden: {e}")
    return _price_ref


def _lookup_price(name: str, unit: str, amount, category: str) -> float:
    """
    Gibt den Preis für eine Zutat zurück.
    Sucht zuerst exakt, dann per Teilstring in der Preisreferenz.
    Gibt den absoluten Preis für die angegebene Menge zurück.
    """
    ref = _get_price_ref()
    # Name bereinigen: Klammerzusätze und "oder X"-Alternativen entfernen
    # z.B. "Spaghetti oder Trofie" → "spaghetti"
    #      "Pesto (Glas oder frisch)" → "pesto"
    #      "Koriander (frisch)" → "koriander"
    name_clean = re.sub(r'\s*\(.*?\)', '', name).strip()
    name_clean = re.sub(r'\s+oder\s+.*', '', name_clean, flags=re.IGNORECASE).strip()
    name_lc = name_clean.lower()

    # Normalisierung: Einheit auf Standard bringen
    UNIT_TO_G = {
        "g": 1, "kg": 1000, "ml": 1, "l": 1000, "liter": 1000,
        # Löffel: EL ≈ 15ml/g; TL ≈ 5ml/g
        "el": 15, "essl": 15, "tl": 5, "teel": 5,
        # Sonstiges
        "cm": 8,     # 1 cm Ingwer ≈ 8g
        "msp": 2,    # Messerspitze ≈ 2g
        "prise": 1,  # Prise ≈ 1g
    }
    PIECE_UNITS = {"stück", "stk", "stk.", "stueck", "stk,", "st"}
    BUND_UNITS  = {"bund", "bund.", "zweig", "zweige", "stängel"}
    ZEHE_UNITS  = {"zehe", "zehen"}

    raw_unit = str(unit or "g").lower().strip()

    # Sondereinheiten auflösen: "Dose (400g)" → unit="g", amount×=400
    # "Dose (400ml)" → unit="ml", amount×=400  etc.
    _dose_match = re.match(r'dose\s*\((\d+)\s*(g|ml)\)', raw_unit)
    _pkg_match  = re.match(r'packung\s*\((\d+)\s*(g|ml)\)', raw_unit)
    _can_match  = _dose_match or _pkg_match
    if _can_match:
        raw_unit = _can_match.group(2)   # "g" or "ml"
        amount   = float(amount or 1) * int(_can_match.group(1))
    elif raw_unit in ("dose", "pkg", "packung", "pck", "fl.", "flasche"):
        raw_unit = "stück"  # treat as piece unit

    # Leerzeichen/Sonderzeichen normalisieren
    unit_lc = raw_unit

    # Versuche Preisreferenz zu finden: exakt → Teilstring → Default nach Kategorie
    entry = ref.get(name_lc)
    if not entry and name_lc:  # nur suchen wenn Name nicht leer
        # Teilstring: prüfe ob ein bekannter Name im Zutatenname vorkommt
        for key, val in ref.items():
            if key.startswith("default_"):
                continue
            if key in name_lc or (len(name_lc) >= 4 and name_lc in key):
                entry = val
                break

    if not entry:
        # Fallback: Default nach Kategorie
        default_key = f"default_{category}"
        entry = ref.get(default_key, {"per_kg": 3.0})

    # Falls Grundzutat → 0
    if entry.get("is_basic"):
        return 0.0

    amt = float(amount) if amount else 1.0

    # Stückpreis
    if "per_stk" in entry:
        if unit_lc in PIECE_UNITS or unit_lc in ("", "stück", "stk"):
            return amt * entry["per_stk"]
        # Wenn Einheit g/kg: Stückpreis gilt als Durchschnitt pro Stück (~150g)
        if unit_lc in UNIT_TO_G:
            g = amt * UNIT_TO_G[unit_lc]
            return (g / 150.0) * entry["per_stk"]
        return entry["per_stk"]

    # Kräuter/Bund
    if "per_bund" in entry:
        if unit_lc == "bund":
            return amt * entry["per_bund"]
        elif unit_lc in ("zweig", "zweige", "stängel"):
            # Ein Zweig ist ~1/8 Bund
            return amt * entry["per_bund"] / 8
        return entry["per_bund"]  # einmalig für sonstige Einheiten

    # Preis per 100g
    if "per_100g" in entry:
        if unit_lc in UNIT_TO_G:
            g = amt * UNIT_TO_G[unit_lc]
        elif unit_lc in ZEHE_UNITS:
            g = amt * 5  # Knoblauchzehe ~5g
        elif unit_lc in BUND_UNITS:
            g = amt * 20  # Kräuterbund ~20g
        elif unit_lc in PIECE_UNITS:
            g = amt * 15
        else:
            g = amt * 15  # Löffel/unbekannt: kleiner Anteil
        return (g / 100.0) * entry["per_100g"]

    # Preis per kg
    if "per_kg" in entry:
        if unit_lc in UNIT_TO_G:
            g = amt * UNIT_TO_G[unit_lc]
        elif unit_lc in ZEHE_UNITS:
            g = amt * 5
        elif unit_lc in BUND_UNITS:
            g = amt * 25
        elif unit_lc in PIECE_UNITS:
            g = amt * 100  # ein "Stück" Gemüse/Sonstiges ca. 100g Durchschnitt
        else:
            g = amt * 15  # Löffel/unbekannt: ~15g
        return (g / 1000.0) * entry["per_kg"]

    # Preis per Liter
    if "per_l" in entry:
        if unit_lc in UNIT_TO_G:
            ml = amt * UNIT_TO_G[unit_lc]
        elif unit_lc in PIECE_UNITS:
            ml = amt * 200
        else:
            ml = amt * 15
        return (ml / 1000.0) * entry["per_l"]

    # Preis per Packung
    if "per_pck" in entry:
        return entry["per_pck"]

    return 0.0


# ── Kostenabschätzung ──────────────────────────────────────────────────────────

def estimate_recipe_cost(recipe: dict, deals: list, portions: int = 2) -> float:
    """
    Schätzt die Kosten für ein Gericht anhand der internen Preisreferenz
    (data/ingredient_prices.json). Deals werden NICHT für die Preis-
    berechnung verwendet – gescrapte Deal-Preise sind oft Hochrechnungen
    (z.B. €15.92/kg statt Packungspreis) und würden Ergebnisse verfälschen.
    """
    total = 0.0
    for ing in recipe.get("ingredients", []):
        if ing.get("is_basic"):
            continue
        total += _lookup_price(
            ing.get("name", ""),
            str(ing.get("unit") or "g"),
            ing.get("amount"),
            ing.get("category", "sonstiges"),
        )
    # Auf gewünschte Portionenzahl hochrechnen (Rezepte = 2 Personen)
    result = round(total * portions / 2, 2)
    return max(result, 0.50)


def estimate_cost(shopping_items: list) -> float:
    """
    Gesamtkosten der Einkaufsliste: Menge × Einzelpreis aus der internen
    Preisreferenz. Nur diese Methode liefert verlässliche Additions-Ergebnisse,
    weil gescrapte Deal-Preise oft unbrauchbare Werte enthalten.

    Hinweis: Items können entweder "name" (frisch generiert) oder
    "ingredient_name" (aus DB geladen) als Schlüssel haben.
    """
    total = 0.0
    for item in shopping_items:
        # DB-Items verwenden "ingredient_name", frisch generierte "name"
        name = item.get("name") or item.get("ingredient_name") or ""
        total += _lookup_price(
            name,
            str(item.get("unit") or "g"),
            item.get("amount"),
            item.get("category", "sonstiges"),
        )
    return round(total, 2)


# ── Kochanweisungen generieren ─────────────────────────────────────────────────

def _fetch_instructions_chefkoch(recipe_name: str) -> list:
    """
    Sucht auf Chefkoch.de nach dem Rezept und extrahiert die Kochschritte.
    Gibt eine Liste von Schritt-Strings zurück oder [] bei Misserfolg.
    """
    import requests
    from bs4 import BeautifulSoup
    from urllib.parse import quote_plus

    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept-Language": "de-DE,de;q=0.9",
        "Accept": "text/html,application/xhtml+xml",
    }

    def _extract_steps_from_instructions(raw) -> list:
        """Rekursiv Schritt-Texte aus recipeInstructions extrahieren (alle Formate)."""
        steps = []
        if isinstance(raw, str) and len(raw) > 20:
            steps.append(raw)
        elif isinstance(raw, list):
            for item in raw:
                if isinstance(item, str) and len(item) > 20:
                    steps.append(item)
                elif isinstance(item, dict):
                    t = item.get("text") or item.get("name") or ""
                    if len(t) > 20:
                        steps.append(t)
                    # HowToSection → itemListElement
                    sub = item.get("itemListElement")
                    if sub:
                        steps.extend(_extract_steps_from_instructions(sub))
        return steps

    try:
        # Suche das Rezept
        search_url = f"https://www.chefkoch.de/rs/s0/{quote_plus(recipe_name)}/Rezepte.html"
        resp = requests.get(search_url, headers=headers, timeout=12)
        if resp.status_code != 200:
            return []

        soup = BeautifulSoup(resp.text, "lxml")

        # Erstes passendes Suchergebnis finden – nur echte Rezept-URLs (numerische ID)
        recipe_url = None
        for link in soup.find_all("a", href=True):
            href = link["href"]
            if re.search(r"/rezepte/\d{8,}/", href):
                # Tracking-Fragment entfernen
                recipe_url = href.split("#")[0]
                if not recipe_url.startswith("http"):
                    recipe_url = "https://www.chefkoch.de" + recipe_url
                break

        if not recipe_url:
            return []

        # Rezeptseite laden
        r2 = requests.get(recipe_url, headers=headers, timeout=12)
        if r2.status_code != 200:
            return []

        soup2 = BeautifulSoup(r2.text, "lxml")
        steps = []

        # Methode 1: JSON-LD structured data (primär)
        for script in soup2.find_all("script", type="application/ld+json"):
            try:
                data = json.loads(script.string or "")
                items = data if isinstance(data, list) else [data]
                for item in items:
                    if item.get("@type") == "Recipe":
                        raw = item.get("recipeInstructions", [])
                        steps = _extract_steps_from_instructions(raw)
                        if steps:
                            break
            except Exception:
                continue
            if steps:
                break

        # Methode 2: Freitext-Zubereitung → Sätze aufteilen
        if not steps:
            prep = soup2.select_one(
                "#rezept-zubereitung, .ds-recipe-meta__body--preparation, "
                "[class*='preparation'], [class*='zubereitung'], .recipe-text"
            )
            if prep:
                full_text = prep.get_text(" ", strip=True)
                parts = re.split(r'\.\s+(?=[A-ZÄÖÜ])', full_text)
                steps = [p.strip() + ("." if not p.strip().endswith(".") else "")
                         for p in parts if len(p.strip()) > 20]

        return steps[:12] if steps else []

    except Exception as e:
        print(f"[Chefkoch] Fehler beim Laden für '{recipe_name}': {e}")
        return []


def generate_recipe_instructions(recipe: dict) -> list:
    """
    Holt Schritt-für-Schritt Kochanweisungen für ein Rezept.
    1. Versucht zuerst Chefkoch.de zu scrapen.
    2. Fallback: Claude API (falls Guthaben vorhanden).
    Gibt eine Liste von Schritt-Strings zurück.
    """
    # Primär: Chefkoch scrapen
    steps = _fetch_instructions_chefkoch(recipe["name"])
    if steps:
        print(f"[Chefkoch] {len(steps)} Schritte für '{recipe['name']}' geladen")
        return steps

    # Fallback 1: Claude API (falls Guthaben vorhanden)
    ings_text = "\n".join(
        f"- {i.get('amount','')} {i.get('unit','')} {i['name']}".strip()
        for i in recipe.get("ingredients", [])
        if not i.get("is_basic")
    )

    prompt = f"""Schreibe eine präzise Schritt-für-Schritt Kochanleitung auf Deutsch für das Rezept "{recipe['name']}".

Zutaten:
{ings_text}

Infos: {recipe.get('total_time', '30')} Minuten, {recipe.get('difficulty', 'mittel')}, 2 Personen

Erstelle 6-10 klare Kochschritte mit konkreten Temperaturen, Zeiten und Techniken.

Antworte NUR mit einem JSON-Array von Strings:
["Schritt 1...", "Schritt 2...", ...]"""

    try:
        client = _get_client()
        message = client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=1000,
            messages=[{"role": "user", "content": prompt}]
        )
        text = message.content[0].text.strip()
        json_match = re.search(r'\[[\s\S]*\]', text)
        if json_match:
            parsed = json.loads(json_match.group())
            if isinstance(parsed, list) and parsed:
                return parsed
    except Exception as e:
        print(f"[Claude] Fehler bei Kochanweisungen für {recipe['id']}: {e}")

    # Fallback 2: Offline-Vorlage aus den Rezept-Metadaten
    return _generate_template_instructions(recipe)


def _generate_template_instructions(recipe: dict) -> list:
    """
    Generiert eine einfache Schritt-für-Schritt Anleitung aus den Rezept-Metadaten
    ohne externe API – immer verfügbar als letzter Fallback.
    """
    name = recipe.get("name", "das Rezept")
    ings = [i for i in recipe.get("ingredients", []) if not i.get("is_basic")]
    cat = recipe.get("category", "sonstiges")
    prep = recipe.get("prep_time", 20)
    total = recipe.get("total_time", 30)
    passive = total - prep

    # Zutaten nach Kategorien gruppieren
    proteins = [i["name"] for i in ings if i.get("category") in ("fleisch", "fisch", "eier")]
    veggies  = [i["name"] for i in ings if i.get("category") == "gemüse"]
    bases    = [i["name"] for i in ings if i.get("category") in ("nudeln", "reis", "brot")]
    sauces   = [i["name"] for i in ings if i.get("category") in ("sonstiges", "konserven") and i not in proteins]

    steps = []

    # Schritt 1: Vorbereitung
    prep_items = [i["name"] for i in ings[:4]]
    steps.append(f"Alle Zutaten vorbereiten: {', '.join(prep_items[:4])} abwiegen, waschen und ggf. in mundgerechte Stücke schneiden.")

    # Schritt 2: Basis kochen (Pasta/Reis)
    if bases:
        if cat == "pasta" or any("nudel" in b.lower() or "spaghetti" in b.lower() or "pasta" in b.lower() for b in bases):
            steps.append(f"{bases[0]} in reichlich gesalzenem Wasser nach Packungsanweisung al dente kochen ({passive or 10} Minuten). Vor dem Abgießen etwas Kochwasser aufheben.")
        else:
            steps.append(f"{bases[0]} nach Packungsanweisung kochen ({passive or 15} Minuten).")

    # Schritt 3: Protein anbraten
    if proteins:
        steps.append(f"{proteins[0]} mit etwas Öl in einer Pfanne bei mittlerer bis hoher Hitze von allen Seiten {prep // 2 or 5} Minuten goldbraun anbraten. Mit Salz und Pfeffer würzen.")

    # Schritt 4: Gemüse
    if veggies:
        steps.append(f"{', '.join(veggies[:3])} in die Pfanne geben und weitere 3–5 Minuten unter gelegentlichem Rühren mitbraten, bis das Gemüse gar aber noch bissfest ist.")

    # Schritt 5: Sauce / Rest
    remaining = [i["name"] for i in ings if i["name"] not in proteins + veggies + bases]
    if remaining:
        steps.append(f"{', '.join(remaining[:4])} hinzufügen, alles gut vermischen und bei niedriger Hitze 2–3 Minuten köcheln lassen. Mit Salz, Pfeffer und ggf. Zitronensaft abschmecken.")
    else:
        steps.append(f"Alle weiteren Zutaten hinzufügen und gut vermengen. Mit Salz und Pfeffer abschmecken.")

    # Schritt 6: Zusammenführen
    if bases and (proteins or veggies):
        steps.append(f"Die gekochte{'n ' + bases[0] if bases else ''} zu den übrigen Zutaten geben und alles vorsichtig vermengen. Bei Bedarf etwas Kochwasser oder Brühe hinzufügen.")

    # Schritt 7: Servieren
    steps.append(f"{name} auf vorgewärmten Tellern anrichten und sofort servieren. Guten Appetit!")

    return [s for s in steps if s]


# ── Nährwert-Übersicht ─────────────────────────────────────────────────────────

def get_weekly_nutrition(plan_id: int, user_id: int = None) -> dict:
    """Berechnet Nährwerte für die gesamte Woche."""
    selections = db.get_selections(plan_id)
    totals = {"calories": 0, "protein": 0, "carbs": 0, "fat": 0}
    per_day = []

    plan_slots = db.get_plan_slots(plan_id)
    for slot_row in plan_slots:
        slot = {"id": slot_row["slot_id"], "label": slot_row["label"],
                "leftovers": bool(slot_row["leftovers"])}
        recipe_id = selections.get(slot["id"])
        if not recipe_id or recipe_id == "SKIPPED":
            continue
        recipe = get_recipe(recipe_id, user_id=user_id)
        if not recipe:
            continue
        n = recipe.get("nutrition_per_portion", {})
        # Gerichte mit leftovers=True werden 2x gegessen (Abend + Mittag nächsten Tag)
        meal_count = 2 if slot.get("leftovers") else 1
        day_n = {
            "slot": slot["label"],
            "recipe": recipe["name"],
            "calories": n.get("calories", 0),
            "protein": n.get("protein", 0),
            "carbs": n.get("carbs", 0),
            "fat": n.get("fat", 0),
            "leftovers": slot.get("leftovers", False),
        }
        per_day.append(day_n)
        for k in totals:
            totals[k] += n.get(k, 0) * meal_count

    return {
        "per_meal": per_day,
        "weekly_total": totals,
        "weekly_avg_per_day": {k: round(v / 7, 0) for k, v in totals.items()},
    }
