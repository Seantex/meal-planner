"""
Meal Planner – Flask Hauptanwendung (Multi-User)
"""
import os
import re
import json
from datetime import date, timedelta
from flask import (Flask, render_template, request, redirect,
                   url_for, jsonify, flash, make_response, g)
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import (LoginManager, UserMixin, login_user, logout_user,
                         login_required, current_user)

import database as db
import planner
from scraper.manager import scrape_all_deals, parse_pdf_deals, try_download_pdf_from_web, FLYER_URLS
from config import (SECRET_KEY, DEBUG, UPLOADS_DIR, MEAL_SLOTS, DB_PATH as _DB_PATH,
                    BUDGET_WARNING, ANTHROPIC_API_KEY, RECIPES_PATH,
                    MAIL_SERVER, MAIL_PORT, MAIL_USERNAME, MAIL_PASSWORD, MAIL_FROM, APP_URL)
from database import LIMITS as _LIMITS
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

app = Flask(__name__)
app.secret_key = SECRET_KEY


@app.after_request
def no_cache_html(response):
    """Prevent browsers/CDN from caching HTML pages so CSS/JS version bumps always take effect."""
    if 'text/html' in response.content_type:
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
    return response


# ── Flask-Login ────────────────────────────────────────────────────────────────

login_manager = LoginManager(app)
login_manager.login_view = "login"
login_manager.login_message = "Bitte melde dich an um fortzufahren."
login_manager.login_message_category = "warning"


class User(UserMixin):
    def __init__(self, data: dict):
        self.id = data["id"]
        self.email = data["email"]
        self.name = data["name"]
        self.is_admin = bool(data.get("is_admin", 0))

    def get_id(self):
        return str(self.id)


@login_manager.user_loader
def load_user(user_id):
    data = db.get_user_by_id(int(user_id))
    return User(data) if data else None


# ── Hilfsfunktionen ────────────────────────────────────────────────────────────

ALLOWED_EXTENSIONS = {"pdf"}


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def _current_week_start() -> str:
    """Nächsten oder aktuellen Samstag als Standard-Wochenstart."""
    today = date.today()
    # 5 = Samstag (weekday: Mon=0..Sun=6)
    days_until_saturday = (5 - today.weekday()) % 7
    if days_until_saturday == 0 and today.weekday() == 5:
        return today.isoformat()
    return (today + timedelta(days=days_until_saturday or 7)).isoformat()


_WEEKDAY_NAMES = ["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag", "Sonntag"]
_WEEKDAY_SHORT  = ["mo",    "di",       "mi",       "do",         "fr",      "sa",       "so"]


def _parse_slot_config(form, week_start: str):
    """
    Liest aus dem Formular die ausgewählten Tage + Mittag/Abend-Auswahl.
    Scannt alle day_YYYY-MM-DD Keys direkt — unabhängig von week_start,
    damit Browser-Caching des alten JS (UTC-Shift) keinen Einfluss hat.
    Gibt eine Liste von Slot-Dicts zurück oder None (→ Standard MEAL_SLOTS).
    """
    import re as _re
    # Alle eingereichten day_YYYY-MM-DD Schlüssel finden
    day_keys = sorted(
        m.group(1)
        for key in form.keys()
        for m in [_re.match(r'^day_(\d{4}-\d{2}-\d{2})$', key)]
        if m
    )
    if not day_keys:
        return None

    slots = []
    sort_idx = 0
    for day_key in day_keys:
        try:
            d = date.fromisoformat(day_key)
        except ValueError:
            continue
        day_name = _WEEKDAY_NAMES[d.weekday()]
        short    = _WEEKDAY_SHORT[d.weekday()]
        meal_types = form.getlist(f"meal_{day_key}")

        if "mittag" in meal_types:
            slots.append({
                "id":        f"{short}_mittag_{day_key}",
                "label":     f"{day_name} Mittag",
                "type":      "weekend" if d.weekday() >= 5 else "weekday",
                "note":      "Mittagessen",
                "leftovers": False,
                "sort_order": sort_idx,
            })
            sort_idx += 1
        if "abend" in meal_types:
            slots.append({
                "id":        f"{short}_abend_{day_key}",
                "label":     f"{day_name} Abend",
                "type":      "weekend" if d.weekday() >= 5 else "weekday",
                "note":      "",
                "leftovers": False,
                "sort_order": sort_idx,
            })
            sort_idx += 1

    return slots if slots else None


def _uid() -> int:
    """Gibt die aktuelle User-ID zurück."""
    return current_user.id


def _is_admin() -> bool:
    return getattr(current_user, "is_admin", False)


# Context-Processor: active_plan_id + user-Infos für alle Templates
@app.context_processor
def inject_globals():
    if current_user.is_authenticated:
        active = db.get_active_plan(_uid())
        recipe_remaining = db.get_ai_remaining(_uid(), "recipe", _is_admin())
        plan_remaining = db.get_ai_remaining(_uid(), "plan", _is_admin())
        return dict(
            active_plan_id=active["id"] if active else None,
            recipe_remaining=recipe_remaining,
            plan_remaining=plan_remaining,
        )
    return dict(active_plan_id=None, recipe_remaining=0, plan_remaining=0)


# ── Auth-Routen ────────────────────────────────────────────────────────────────

@app.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("index"))
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        name  = request.form.get("name", "").strip()
        pw    = request.form.get("password", "")
        pw2   = request.form.get("password2", "")

        if not email or not name or not pw:
            flash("Bitte alle Felder ausfüllen.", "error")
            return render_template("register.html")
        if len(pw) < 6:
            flash("Passwort muss mindestens 6 Zeichen haben.", "error")
            return render_template("register.html")
        if pw != pw2:
            flash("Passwörter stimmen nicht überein.", "error")
            return render_template("register.html")
        if db.email_exists(email):
            flash("Diese E-Mail-Adresse ist bereits registriert.", "error")
            return render_template("register.html")

        pw_hash = generate_password_hash(pw, method="pbkdf2:sha256")
        user_id = db.create_user(email, name, pw_hash)
        user_data = db.get_user_by_id(user_id)
        login_user(User(user_data), remember=True)
        # Verifikations-E-Mail senden
        token = db.create_email_token(user_id, "verify")
        verify_url = f"{APP_URL}/verify-email/{token}"
        _send_mail(
            email,
            "Meal Planner – E-Mail bestätigen",
            f"""<p>Hallo {name},</p>
<p>Bitte bestätige deine E-Mail-Adresse durch Klicken auf diesen Link:</p>
<p><a href="{verify_url}">{verify_url}</a></p>
<p>Der Link ist 24 Stunden gültig.</p>
<p>Meal Planner Team</p>"""
        )
        flash(f"Willkommen, {name}! Bitte bestätige deine E-Mail-Adresse (Link wurde gesendet an {email}).", "success")
        return redirect(url_for("onboarding"))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("index"))
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        pw    = request.form.get("password", "")
        remember = request.form.get("remember") == "on"

        user_data = db.get_user_by_email(email)
        if not user_data or not check_password_hash(user_data["password_hash"], pw):
            flash("E-Mail oder Passwort falsch.", "error")
            return render_template("login.html")

        login_user(User(user_data), remember=remember)
        flash(f"Willkommen zurück, {user_data['name']}!", "success")
        next_page = request.args.get("next")
        return redirect(next_page or url_for("index"))

    return render_template("login.html")


@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Du wurdest abgemeldet.", "info")
    return redirect(url_for("login"))


# ── Onboarding ─────────────────────────────────────────────────────────────────

def apply_dietary_filter(recipes, user_id):
    """Filtert Rezepte basierend auf Ernährungspräferenzen und Allergien des Nutzers."""
    profile = db.get_user_profile(user_id)
    dietary = set(json.loads(profile.get('dietary', '[]')))
    allergies = set(json.loads(profile.get('allergies', '[]')))

    if not dietary and not allergies:
        return recipes  # Kein Filter nötig

    filtered = []
    for r in recipes:
        r_allergens = set(r.get('allergens', []))
        r_dietary = set(r.get('dietary', []))

        # Hard exclude: Allergen-Übereinstimmung
        if r_allergens & allergies:
            continue

        # Ernährungsweise
        if 'vegan' in dietary:
            if 'vegan' not in r_dietary:
                continue
        elif 'vegetarisch' in dietary:
            if 'vegan' not in r_dietary and 'vegetarisch' not in r_dietary:
                continue

        if 'glutenfrei' in dietary and 'gluten' in r_allergens:
            continue
        if 'laktosefrei' in dietary and 'milch' in r_allergens:
            continue

        filtered.append(r)
    return filtered


@app.route("/onboarding", methods=["GET"])
@login_required
def onboarding():
    # Falls bereits abgeschlossen, zur Startseite weiterleiten
    if db.is_onboarding_done(current_user.id):
        return redirect(url_for("index"))
    return render_template("onboarding.html")


@app.route("/onboarding", methods=["POST"])
@login_required
def onboarding_post():
    goal = request.form.get("goal", "gesund_ernaehren")
    dietary = request.form.getlist("dietary")       # Multi-Select Checkboxen
    allergies = request.form.getlist("allergies")   # Multi-Select Checkboxen
    calorie_target = request.form.get("calorie_target", "")
    calorie_target = int(calorie_target) if calorie_target.strip().isdigit() else None

    db.save_user_profile(
        current_user.id,
        goal,
        json.dumps(dietary),
        json.dumps(allergies),
        calorie_target
    )
    flash("Dein Profil wurde gespeichert! Willkommen beim Meal Planner!", "success")
    return redirect(url_for("index"))


@app.route("/profile/preferences", methods=["GET", "POST"])
@login_required
def profile_preferences():
    if request.method == "POST":
        goal = request.form.get("goal", "gesund_ernaehren")
        dietary = request.form.getlist("dietary")
        allergies = request.form.getlist("allergies")
        calorie_target = request.form.get("calorie_target", "")
        calorie_target = int(calorie_target) if calorie_target.strip().isdigit() else None

        db.save_user_profile(
            current_user.id,
            goal,
            json.dumps(dietary),
            json.dumps(allergies),
            calorie_target
        )
        flash("Deine Präferenzen wurden gespeichert!", "success")
        return redirect(url_for("profile_preferences"))

    profile = db.get_user_profile(current_user.id)
    dietary_list = json.loads(profile.get('dietary', '[]'))
    allergies_list = json.loads(profile.get('allergies', '[]'))
    return render_template("profile_preferences.html", profile=profile,
                           dietary_list=dietary_list, allergies_list=allergies_list)


# ── Startseite ─────────────────────────────────────────────────────────────────

@app.route("/")
@login_required
def index():
    db.init_db()
    plan_limit = _LIMITS.get("plan", 1)
    recent_plans = db.get_recent_plans(_uid(), limit=50)
    active_plan = recent_plans[0] if recent_plans else None
    deals = db.get_deals()
    deals_fresh = db.deals_are_fresh()
    api_configured = bool(ANTHROPIC_API_KEY)

    from collections import Counter
    store_counts = dict(Counter(d["supermarket"] for d in deals))

    return render_template(
        "index.html",
        active_plan=active_plan,
        recent_plans=recent_plans,
        plan_limit=plan_limit,
        deals_count=len(deals),
        store_counts=store_counts,
        deals_fresh=deals_fresh,
        api_configured=api_configured,
        week_start=_current_week_start(),
        flyer_urls=FLYER_URLS,
    )


# ── Angebote laden ─────────────────────────────────────────────────────────────

@app.route("/deals/refresh", methods=["POST"])
@login_required
def refresh_deals():
    all_deals, failed = scrape_all_deals()
    if all_deals:
        db.save_deals(all_deals)
        flash(f"✓ {len(all_deals)} Angebote geladen von: "
              f"{', '.join(set(d['supermarket'] for d in all_deals))}", "success")
    if failed:
        flash(
            f"Für {', '.join(failed)}: Automatischer Download nicht möglich. "
            f"Klicke auf 'Einzeln laden' → PDF hochladen.", "info"
        )
    if not all_deals and not failed:
        flash("Keine Angebote gefunden.", "warning")
    return redirect(url_for("index"))


@app.route("/deals/fetch-web/<supermarket>", methods=["POST"])
@login_required
def fetch_deals_from_web(supermarket):
    if supermarket not in FLYER_URLS:
        flash("Unbekannter Supermarkt.", "error")
        return redirect(url_for("index"))
    deals = try_download_pdf_from_web(supermarket)
    if deals:
        existing = db.get_deals()
        other_deals = [d for d in existing if d["supermarket"] != supermarket]
        db.save_deals(other_deals + deals)
        flash(f"✓ {len(deals)} Angebote von {supermarket} geladen!", "success")
    else:
        flash(f"Automatischer Download für {supermarket} fehlgeschlagen. Bitte PDF manuell hochladen.", "warning")
    return redirect(url_for("index"))


@app.route("/deals/upload", methods=["POST"])
@login_required
def upload_pdf():
    supermarket = request.form.get("supermarket", "Unbekannt")
    if "pdf_file" not in request.files:
        flash("Keine Datei ausgewählt.", "error")
        return redirect(url_for("index"))
    file = request.files["pdf_file"]
    if file.filename == "" or not allowed_file(file.filename):
        flash("Bitte eine PDF-Datei hochladen.", "error")
        return redirect(url_for("index"))
    filename = secure_filename(f"{supermarket}_{file.filename}")
    save_path = os.path.join(UPLOADS_DIR, filename)
    file.save(save_path)
    deals = parse_pdf_deals(save_path, supermarket)
    if deals:
        existing = db.get_deals()
        other_deals = [d for d in existing if d["supermarket"] != supermarket]
        db.save_deals(other_deals + deals)
        flash(f"✓ {len(deals)} Angebote aus PDF extrahiert ({supermarket})", "success")
    else:
        flash("Konnte keine Angebote aus dem PDF lesen.", "warning")
    return redirect(url_for("index"))


# ── Wochenplan starten ─────────────────────────────────────────────────────────

@app.route("/plan/new", methods=["POST"])
@login_required
def new_plan():
    if not db.can_use_ai(_uid(), "plan", _is_admin()):
        flash("Du hast dein Limit für Wochenplan-Generierungen diese Woche erreicht (5/5). "
              "Nächste Woche kannst du wieder neue Pläne erstellen.", "warning")
        return redirect(url_for("index"))

    cravings = request.form.get("cravings", "").strip()
    # Wochenstart aus Formular, Fallback auf nächsten Samstag
    week_start_raw = request.form.get("week_start", "").strip()
    try:
        week_start = date.fromisoformat(week_start_raw).isoformat()
    except (ValueError, AttributeError):
        week_start = _current_week_start()
    default_persons = max(1, min(10, int(request.form.get("default_persons", 2) or 2)))
    plan_id = db.create_week_plan(week_start, cravings, _uid(),
                                  default_persons=default_persons,
                                  slot_config=_parse_slot_config(request.form, week_start))
    db.increment_ai_usage(_uid(), "plan")

    try:
        planner.generate_week_suggestions(plan_id, cravings, user_id=_uid())
        flash("✓ Wochenplan erstellt! Wähle jetzt deine Gerichte.", "success")
    except Exception as e:
        import traceback
        app.logger.error(f"generate_week_suggestions failed for plan {plan_id}: {traceback.format_exc()}")
        flash(f"Fehler bei KI-Vorschlägen: {e}", "error")

    return redirect(url_for("planning", plan_id=plan_id))


# ── Planungs-Wizard ────────────────────────────────────────────────────────────

@app.route("/plan/<int:plan_id>")
@login_required
def planning(plan_id):
    plan = db.get_plan(plan_id, _uid())
    if not plan:
        flash("Plan nicht gefunden.", "error")
        return redirect(url_for("index"))

    selections = db.get_selections(plan_id)
    all_suggestions = db.get_all_suggestions(plan_id)
    favorites = [f["recipe_id"] for f in db.get_favorites(_uid())]
    never_again = [n["recipe_id"] for n in db.get_never_again(_uid())]
    deals = db.get_deals()
    default_persons = db.get_default_persons(plan_id)
    slot_portions_map = db.get_all_slot_portions(plan_id)
    cooked_slots = db.get_cooked_slots(plan_id)
    plan_slots = db.get_plan_slots(plan_id)

    slots_data = []
    for slot_row in plan_slots:
        slot = {"id": slot_row["slot_id"], "label": slot_row["label"],
                "type": slot_row.get("type","weekday"), "note": slot_row.get("note",""),
                "leftovers": bool(slot_row["leftovers"])}
        sid = slot["id"]
        raw_suggestions = all_suggestions.get(sid, [])
        portions = db.get_slot_portions(plan_id, sid, default_persons, slot.get("leftovers", False))

        suggestions_with_recipes = []
        for s in raw_suggestions:
            rid = s["recipe_id"] if isinstance(s, dict) else s
            recipe = planner.get_recipe(rid, user_id=_uid())
            if recipe:
                suggestions_with_recipes.append({
                    "recipe": recipe,
                    "reason": s.get("reason", "") if isinstance(s, dict) else "",
                    "deal_matches": s.get("deal_matches", []) if isinstance(s, dict) else [],
                    "is_favorite": rid in favorites,
                    "is_never_again": rid in never_again,
                    "estimated_cost": planner.estimate_recipe_cost(recipe, deals, portions),
                    "ing_costs": {
                        ing["name"]: round(planner._lookup_price(
                            ing.get("name", ""), str(ing.get("unit") or "g"),
                            ing.get("amount"), ing.get("category", "sonstiges")
                        ) * (portions / 2), 2)
                        for ing in recipe.get("ingredients", []) if not ing.get("is_basic")
                    },
                })

        sel_id = selections.get(sid)
        slots_data.append({
            "slot": slot,
            "suggestions": suggestions_with_recipes,
            "selected_recipe_id": sel_id,
            "selected_recipe": planner.get_recipe(sel_id, user_id=_uid()) if sel_id and sel_id != "SKIPPED" else None,
            "skipped": sel_id == "SKIPPED",
            "portions": portions,
            "cooked": sid in cooked_slots,
        })

    completed = sum(1 for s in slots_data if s["selected_recipe_id"])
    total = len(slots_data)

    # Auto-fix status for plans whose shopping list was created before status tracking was added
    plan_done = plan["status"] == "done"
    if not plan_done and db.get_shopping_list(plan_id):
        db.finish_plan(plan_id)
        plan_done = True

    return render_template(
        "planning.html",
        plan=plan,
        slots_data=slots_data,
        completed=completed,
        total=total,
        progress_pct=int(completed / total * 100),
        default_persons=default_persons,
        slot_portions_map=slot_portions_map,
        plan_done=plan_done,
    )


@app.route("/plan/<int:plan_id>/select", methods=["POST"])
@login_required
def select_recipe(plan_id):
    plan = db.get_plan(plan_id, _uid())
    if not plan:
        return jsonify({"error": "Plan nicht gefunden"}), 404

    data = request.get_json(silent=True) or {}
    meal_slot = data.get("meal_slot") or request.form.get("meal_slot")
    recipe_id = data.get("recipe_id") or request.form.get("recipe_id")
    if not meal_slot or not recipe_id:
        return jsonify({"error": "Fehlende Parameter"}), 400

    # KI-Wunsch-Rezept permanent für diesen User speichern
    wish_recipe = data.get("wish_recipe")
    if wish_recipe and recipe_id.startswith("wish_"):
        if not db.is_user_recipe(_uid(), recipe_id):
            db.save_user_recipe(_uid(), wish_recipe)
            planner.invalidate_user_cache(_uid())

    db.save_selection(plan_id, meal_slot, recipe_id)
    recipe = planner.get_recipe(recipe_id, user_id=_uid()) or wish_recipe
    if not recipe:
        return jsonify({"error": "Rezept nicht gefunden"}), 404

    return jsonify({"success": True, "recipe_name": recipe["name"], "recipe_id": recipe_id})


@app.route("/plan/<int:plan_id>/wish/<meal_slot>", methods=["POST"])
@login_required
def wish_recipe(plan_id, meal_slot):
    plan = db.get_plan(plan_id, _uid())
    if not plan:
        return jsonify({"error": "Plan nicht gefunden"}), 404

    # Per-Slot-Limit: 1 KI-Wunschrezept pro Slot pro Woche
    if not db.can_use_ai(_uid(), f"wish_{meal_slot}", _is_admin()):
        return jsonify({"error": "Du hast für diesen Tag bereits ein KI-Wunschrezept erstellt. Das Limit ist 1 pro Slot pro Woche."}), 429

    data = request.get_json(silent=True) or {}
    wish = data.get("wish", "").strip()
    if not wish:
        return jsonify({"error": "Kein Wunsch angegeben"}), 400

    plan_slots = db.get_plan_slots(plan_id)
    slot_row = next((s for s in plan_slots if s["slot_id"] == meal_slot), None)
    slot_type = slot_row["type"] if slot_row else "weekday"
    leftovers = bool(slot_row["leftovers"]) if slot_row else False

    recipe = planner.generate_wish_recipe(wish, slot_type)
    if not recipe:
        return jsonify({"error": "KI konnte kein Rezept generieren. Bitte erneut versuchen."}), 500

    db.increment_ai_usage(_uid(), f"wish_{meal_slot}")
    portions = 3 if leftovers else 2
    cost = planner.estimate_recipe_cost(recipe, db.get_deals(), portions)

    return jsonify({"success": True, "recipe": recipe, "estimated_cost": round(cost, 2), "portions": portions})


@app.route("/plan/<int:plan_id>/skip/<meal_slot>", methods=["POST"])
@login_required
def skip_slot(plan_id, meal_slot):
    if not db.get_plan(plan_id, _uid()):
        return jsonify({"error": "Nicht gefunden"}), 404
    db.save_selection(plan_id, meal_slot, "SKIPPED")
    return jsonify({"success": True})


@app.route("/plan/<int:plan_id>/unskip/<meal_slot>", methods=["POST"])
@login_required
def unskip_slot(plan_id, meal_slot):
    if not db.get_plan(plan_id, _uid()):
        return jsonify({"error": "Nicht gefunden"}), 404
    conn = db.get_db()
    conn.execute("DELETE FROM meal_selections WHERE plan_id=? AND meal_slot=?", (plan_id, meal_slot))
    conn.commit()
    conn.close()
    return jsonify({"success": True})


@app.route("/plan/<int:plan_id>/persons", methods=["POST"])
@login_required
def set_plan_persons(plan_id):
    plan = db.get_plan(plan_id, _uid())
    if not plan:
        return jsonify({"error": "Nicht gefunden"}), 404
    persons = request.json.get("persons", 2)
    persons = max(1, min(10, int(persons)))
    db.set_default_persons(plan_id, persons)
    return jsonify({"success": True, "persons": persons})


@app.route("/plan/<int:plan_id>/slot-portions/<meal_slot>", methods=["POST"])
@login_required
def set_slot_portions(plan_id, meal_slot):
    plan = db.get_plan(plan_id, _uid())
    if not plan:
        return jsonify({"error": "Nicht gefunden"}), 404
    portions = request.json.get("portions", 2)
    portions = max(1, min(10, int(portions)))
    db.set_slot_portions(plan_id, meal_slot, portions)
    return jsonify({"success": True, "portions": portions})


@app.route("/plan/<int:plan_id>/cooked/<meal_slot>", methods=["POST"])
@login_required
def toggle_cooked(plan_id, meal_slot):
    plan = db.get_plan(plan_id, _uid())
    if not plan:
        return jsonify({"error": "Nicht gefunden"}), 404
    cooked = db.toggle_slot_cooked(plan_id, meal_slot)
    return jsonify({"success": True, "cooked": cooked})


@app.route("/plan/<int:plan_id>/slots", methods=["POST"])
@login_required
def add_plan_slot(plan_id):
    plan = db.get_plan(plan_id, _uid())
    if not plan:
        return jsonify({"error": "Nicht gefunden"}), 404
    data = request.get_json(silent=True) or {}
    label = (data.get("label") or "").strip()
    if not label:
        return jsonify({"error": "Label erforderlich"}), 400
    note = (data.get("note") or "").strip()
    leftovers = bool(data.get("leftovers", False))
    slot_id = db.add_plan_slot(plan_id, label, note=note, leftovers=leftovers)

    # Generate fallback suggestions for the new slot immediately
    deals = db.get_deals()
    never_again = [n["recipe_id"] for n in db.get_never_again(_uid())]
    recipes = planner.load_recipes(user_id=_uid())
    available = [r for r in recipes if r["id"] not in never_again]
    favorites = [f["recipe_id"] for f in db.get_favorites(_uid())]
    all_suggestions = db.get_all_suggestions(plan_id)
    selections = db.get_selections(plan_id)
    exclude_ids = set(selections.values())
    for slot_sugs in all_suggestions.values():
        for s in slot_sugs:
            rid = s["recipe_id"] if isinstance(s, dict) else s
            exclude_ids.add(rid)
    slot_obj = {"id": slot_id, "label": label, "type": "weekday",
                "note": note, "leftovers": leftovers}
    suggestions = planner._get_fallback_suggestions(
        slot=slot_obj, recipes=available, deals=deals, favorites=favorites,
        already_suggested=list(exclude_ids), count=3,
    )
    db.save_suggestions(plan_id, slot_id, [
        {"recipe_id": s["recipe"]["id"], "reason": s["reason"], "deal_matches": s["deal_matches"]}
        for s in suggestions
    ])

    return jsonify({"success": True, "slot_id": slot_id, "label": label,
                    "note": note, "leftovers": leftovers})


@app.route("/plan/<int:plan_id>/slots/<meal_slot>", methods=["DELETE"])
@login_required
def remove_plan_slot(plan_id, meal_slot):
    plan = db.get_plan(plan_id, _uid())
    if not plan:
        return jsonify({"error": "Nicht gefunden"}), 404
    db.remove_plan_slot(plan_id, meal_slot)
    return jsonify({"success": True})


@app.route("/plan/<int:plan_id>/slots/<meal_slot>", methods=["PATCH"])
@login_required
def update_plan_slot(plan_id, meal_slot):
    plan = db.get_plan(plan_id, _uid())
    if not plan:
        return jsonify({"error": "Nicht gefunden"}), 404
    data = request.get_json(silent=True) or {}
    label = (data.get("label") or "").strip()
    if not label:
        return jsonify({"error": "Label erforderlich"}), 400
    note = (data.get("note") or "").strip()
    leftovers = bool(data.get("leftovers", False))
    db.update_plan_slot(plan_id, meal_slot, label, note=note, leftovers=leftovers)
    return jsonify({"success": True, "label": label, "note": note, "leftovers": leftovers})


@app.route("/plan/<int:plan_id>/regenerate/<meal_slot>", methods=["POST"])
@login_required
def regenerate_slot(plan_id, meal_slot):
    plan = db.get_plan(plan_id, _uid())
    if not plan:
        return jsonify({"error": "Plan nicht gefunden"}), 404

    deals = db.get_deals()
    favorites = [f["recipe_id"] for f in db.get_favorites(_uid())]
    never_again = [n["recipe_id"] for n in db.get_never_again(_uid())]
    recipes = planner.load_recipes(user_id=_uid())
    available = [r for r in recipes if r["id"] not in never_again]

    # Look up slot from DB plan slots (supports dynamic date-specific slot IDs)
    plan_slots = db.get_plan_slots(plan_id)
    slot_row = next((s for s in plan_slots if s["slot_id"] == meal_slot), None)
    if not slot_row:
        # Fallback to static MEAL_SLOTS
        static = next((s for s in MEAL_SLOTS if s["id"] == meal_slot), None)
        if not static:
            return jsonify({"error": "Slot nicht gefunden"}), 404
        slot_obj = static
    else:
        slot_obj = {"id": slot_row["slot_id"], "label": slot_row["label"],
                    "type": slot_row["type"], "note": slot_row["note"],
                    "leftovers": bool(slot_row["leftovers"])}

    all_suggestions = db.get_all_suggestions(plan_id)
    selections = db.get_selections(plan_id)
    exclude_ids = set(selections.values())
    for slot_sugs in all_suggestions.values():
        for s in slot_sugs:
            rid = s["recipe_id"] if isinstance(s, dict) else s
            exclude_ids.add(rid)

    cravings = (request.json or {}).get("cravings", "") if request.is_json else request.form.get("cravings", "")
    suggestions = planner._get_fallback_suggestions(
        slot=slot_obj, recipes=available, deals=deals, favorites=favorites,
        already_suggested=list(exclude_ids), count=3, cravings=cravings,
    )

    db.save_suggestions(plan_id, meal_slot, [
        {"recipe_id": s["recipe"]["id"], "reason": s["reason"], "deal_matches": s["deal_matches"]}
        for s in suggestions
    ])

    portions = 3 if slot_obj.get("leftovers") else 2
    return jsonify({
        "success": True,
        "suggestions": [{
            "recipe_id": s["recipe"]["id"],
            "name": s["recipe"]["name"],
            "reason": s["reason"],
            "deal_matches": s["deal_matches"],
            "prep_time": s["recipe"]["prep_time"],
            "total_time": s["recipe"]["total_time"],
            "difficulty": s["recipe"]["difficulty"],
            "nutrition": s["recipe"].get("nutrition_per_portion", {}),
            "estimated_cost": planner.estimate_recipe_cost(s["recipe"], deals, portions),
            "ingredients": [ing for ing in s["recipe"].get("ingredients", []) if not ing.get("is_basic")],
            "ing_costs": {
                ing["name"]: round(planner._lookup_price(
                    ing.get("name", ""), str(ing.get("unit") or "g"),
                    ing.get("amount"), ing.get("category", "sonstiges")
                ) * (portions / 2), 2)
                for ing in s["recipe"].get("ingredients", []) if not ing.get("is_basic")
            },
        } for s in suggestions]
    })


@app.route("/api/recipe/<recipe_id>/modify", methods=["POST"])
@login_required
def modify_recipe(recipe_id):
    recipe = planner.get_recipe(recipe_id, user_id=_uid())
    if not recipe:
        return jsonify({"error": "Rezept nicht gefunden"}), 404

    data = request.get_json() or {}
    modification = data.get("modification", "").strip()
    if not modification:
        return jsonify({"error": "Keine Änderung angegeben"}), 400

    steps = db.get_instructions(recipe_id) or []
    if not steps:
        steps = planner.generate_recipe_instructions(recipe)

    ings_text = "\n".join(
        f"- {ing.get('amount','')} {ing.get('unit','')} {ing['name']}".strip()
        for ing in recipe.get("ingredients", [])
    )

    prompt = f"""Das Originalrezept ist "{recipe['name']}".

Zutaten:
{ings_text}

Kochschritte:
{chr(10).join(f'{i+1}. {s}' for i, s in enumerate(steps))}

Der Nutzer möchte folgende Änderung: "{modification}"

Passe das Rezept entsprechend an. Antworte mit einem JSON-Objekt:
{{
  "title": "Modifizierter Rezepttitel",
  "note": "Kurze Notiz zur Änderung (1 Satz)",
  "ingredients": ["- Menge Einheit Zutat", ...],
  "steps": ["Schritt 1...", "Schritt 2...", ...]
}}

Nur JSON, keine Erklärung."""

    try:
        from anthropic import Anthropic
        from config import ANTHROPIC_API_KEY, CLAUDE_MODEL
        client = Anthropic(api_key=ANTHROPIC_API_KEY)
        msg = client.messages.create(
            model=CLAUDE_MODEL, max_tokens=1500,
            messages=[{"role": "user", "content": prompt}]
        )
        text = msg.content[0].text.strip()
        match = re.search(r'\{[\s\S]*\}', text)
        if match:
            result = json.loads(match.group())

            # Zutaten aus KI-Antwort in Recipe-Format parsen
            def _parse_ai_ing(raw):
                t = raw.strip().lstrip("- ").strip()
                m = re.match(r'^([\d.,/]+)\s*([a-zA-ZäöüÄÖÜß]+\.?)?\s+(.+)$', t)
                if m:
                    try:
                        amt = float(m.group(1).replace(',', '.'))
                    except Exception:
                        amt = None
                    return {"name": m.group(3).strip(), "amount": amt,
                            "unit": m.group(2) or "", "is_basic": False}
                return {"name": t, "amount": None, "unit": "", "is_basic": False}

            # Modifiziertes Rezept aufbauen (original als Basis)
            import copy
            modified = copy.deepcopy(recipe)
            if result.get("title"):
                modified["name"] = result["title"]
            if result.get("ingredients"):
                modified["ingredients"] = [_parse_ai_ing(i) for i in result["ingredients"] if i.strip()]
            if result.get("note"):
                modified["tips"] = result["note"] + (" · " + modified.get("tips", "") if modified.get("tips") else "")

            # Als Benutzer-Rezept speichern (überschreibt Basis-Rezept für diesen User)
            db.save_user_recipe(_uid(), modified)
            planner.invalidate_user_cache(_uid())

            # Kochanleitung speichern falls vorhanden
            if result.get("steps"):
                db.save_instructions(recipe_id, result["steps"])

            return jsonify({"success": True,
                            "redirect": url_for("recipe_detail", recipe_id=recipe_id)})
    except Exception as e:
        print(f"[Claude] Modify error: {e}")

    return jsonify({"error": "KI-Modifikation fehlgeschlagen"}), 500


@app.route("/plan/<int:plan_id>/finish", methods=["POST"])
@login_required
def finish_plan(plan_id):
    plan = db.get_plan(plan_id, _uid())
    if not plan:
        flash("Plan nicht gefunden.", "error")
        return redirect(url_for("index"))

    selections = db.get_selections(plan_id)
    plan_slot_count = len(db.get_plan_slots(plan_id))
    if len(selections) < plan_slot_count:
        flash(f"Bitte noch {plan_slot_count - len(selections)} Gerichte auswählen oder überspringen.", "warning")
        return redirect(url_for("planning", plan_id=plan_id))

    for recipe_id in selections.values():
        if recipe_id and recipe_id != "SKIPPED":
            db.add_favorite(recipe_id, _uid())

    planner.generate_shopping_list(plan_id, user_id=_uid())
    db.finish_plan(plan_id)
    flash("✓ Wochenplan abgeschlossen! Deine Einkaufsliste ist bereit.", "success")
    return redirect(url_for("shopping", plan_id=plan_id))


@app.route("/plan/<int:plan_id>/rename", methods=["POST"])
@login_required
def rename_plan(plan_id):
    plan = db.get_plan(plan_id, _uid())
    if not plan:
        return jsonify({"error": "Nicht gefunden"}), 404
    name = (request.get_json(silent=True) or {}).get("name", "").strip()
    if not name:
        return jsonify({"error": "Name darf nicht leer sein"}), 400
    db.rename_plan(plan_id, name)
    return jsonify({"success": True})


@app.route("/plan/<int:plan_id>/reorder", methods=["POST"])
@login_required
def reorder_plan(plan_id):
    plan = db.get_plan(plan_id, _uid())
    if not plan:
        return jsonify({"error": "Nicht gefunden"}), 404
    direction = (request.get_json(silent=True) or {}).get("direction")
    if direction not in ("up", "down"):
        return jsonify({"error": "Ungültige Richtung"}), 400
    db.reorder_plan(plan_id, _uid(), direction)
    return jsonify({"success": True})


@app.route("/plan/<int:plan_id>/delete", methods=["POST"])
@login_required
def delete_plan(plan_id):
    plan = db.get_plan(plan_id, _uid())
    if not plan:
        return jsonify({"error": "Nicht gefunden"}), 404
    db.delete_plan(plan_id)
    flash("Plan gelöscht.", "success")
    return redirect(url_for("index"))


# ── Einkaufsliste ──────────────────────────────────────────────────────────────

@app.route("/shopping/<int:plan_id>")
@login_required
def shopping(plan_id):
    plan = db.get_plan(plan_id, _uid())
    if not plan:
        flash("Plan nicht gefunden.", "error")
        return redirect(url_for("index"))

    items = db.get_shopping_list(plan_id)
    selections = db.get_selections(plan_id)

    plan_slots = db.get_plan_slots(plan_id)
    selected_recipes = []
    for slot_row in plan_slots:
        slot = {"id": slot_row["slot_id"], "label": slot_row["label"],
                "leftovers": bool(slot_row["leftovers"])}
        rid = selections.get(slot["id"])
        if rid and rid != "SKIPPED":
            r = planner.get_recipe(rid, user_id=_uid())
            if r:
                portions = 3 if slot.get("leftovers") else 2
                selected_recipes.append({"slot": slot, "recipe": r,
                                         "cost": round(planner.estimate_recipe_cost(r, [], portions), 2)})

    for item in items:
        name = item.get("name") or item.get("ingredient_name") or ""
        item["estimated_item_cost"] = planner._lookup_price(
            name, str(item.get("unit") or "g"), item.get("amount"), item.get("category", "sonstiges")
        )
    estimated_cost = round(sum(i["estimated_item_cost"] for i in items), 2)
    budget_warning = estimated_cost > BUDGET_WARNING

    categories = {}
    for item in items:
        cat = item["category"]
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(item)

    CAT_LABELS = {
        "fleisch": "🥩 Fleisch & Wurst", "fisch": "🐟 Fisch & Meeresfrüchte",
        "gemüse": "🥦 Gemüse & Obst", "milch": "🥛 Milch & Molkerei",
        "eier": "🥚 Eier", "käse": "🧀 Käse", "nudeln": "🍝 Nudeln & Pasta",
        "reis": "🍚 Reis & Getreide", "brot": "🍞 Brot & Backwaren",
        "konserven": "🥫 Konserven & Fertigprodukte", "gewürze": "🌿 Gewürze & Kräuter",
        "sonstiges": "🛒 Sonstiges",
    }

    return render_template(
        "shopping.html", plan_id=plan_id, categories=categories, cat_labels=CAT_LABELS,
        items=items, total_items=len(items),
        checked_items=sum(1 for i in items if i["checked"]),
        estimated_cost=estimated_cost, budget_warning=budget_warning,
        selected_recipes=selected_recipes,
    )


@app.route("/shopping/toggle/<int:item_id>", methods=["POST"])
@login_required
def toggle_item(item_id):
    db.toggle_shopping_item(item_id)
    return jsonify({"success": True})


@app.route("/shopping/note/<int:item_id>", methods=["POST"])
@login_required
def update_note(item_id):
    note = request.json.get("note", "")
    db.update_shopping_note(item_id, note)
    return jsonify({"success": True})


@app.route("/shopping/amount/<int:item_id>", methods=["POST"])
@login_required
def update_amount(item_id):
    try:
        raw = request.json.get("amount", "")
        amount = float(str(raw).replace(",", ".").strip()) if raw != "" else None
    except (ValueError, TypeError):
        return jsonify({"success": False, "error": "Ungültige Menge"}), 400
    item = db.get_shopping_item(item_id)
    if not item:
        return jsonify({"success": False, "error": "Item nicht gefunden"}), 404
    db.update_shopping_amount(item_id, amount)
    # Format nicely for display
    if amount is None:
        display = ""
    elif amount == int(amount):
        display = str(int(amount))
    else:
        display = str(amount)
    return jsonify({"success": True, "display": display})


@app.route("/shopping/delete/<int:item_id>", methods=["POST"])
@login_required
def delete_item(item_id):
    item = db.get_shopping_item(item_id)
    item_cost = 0.0
    if item:
        name = item.get("name") or item.get("ingredient_name") or ""
        item_cost = planner._lookup_price(
            name, str(item.get("unit") or "g"), item.get("amount"), item.get("category", "sonstiges")
        )
    db.delete_shopping_item(item_id)
    return jsonify({"success": True, "item_cost": round(item_cost, 2)})


@app.route("/plan/<int:plan_id>/shopping/pdf")
@login_required
def shopping_pdf(plan_id):
    plan = db.get_plan(plan_id, _uid())
    if not plan:
        flash("Plan nicht gefunden.", "error")
        return redirect(url_for("index"))

    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import cm
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib import colors
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
    import io

    items = db.get_shopping_list(plan_id)
    CAT_LABELS = {
        "fleisch": "Fleisch & Wurst", "fisch": "Fisch & Meeresfrüchte",
        "gemüse": "Gemüse & Obst", "milch": "Milch & Molkerei",
        "eier": "Eier", "käse": "Käse", "nudeln": "Nudeln & Pasta",
        "reis": "Reis & Getreide", "brot": "Brot & Backwaren",
        "konserven": "Konserven & Fertigprodukte", "gewürze": "Gewürze & Kräuter",
        "sonstiges": "Sonstiges",
    }
    categories = {}
    for item in items:
        cat = item["category"]
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(item)

    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=2*cm, rightMargin=2*cm,
                            topMargin=2*cm, bottomMargin=2*cm)
    styles = getSampleStyleSheet()
    story = []

    title_style = ParagraphStyle("title", parent=styles["Title"], fontSize=20, spaceAfter=4)
    subtitle_style = ParagraphStyle("sub", parent=styles["Normal"], fontSize=10,
                                    textColor=colors.HexColor("#666666"), spaceAfter=12)
    story.append(Paragraph("Einkaufsliste", title_style))
    story.append(Paragraph(f"Meal Planner – {current_user.name}", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#dddddd"), spaceAfter=12))

    cat_style = ParagraphStyle("cat", parent=styles["Heading3"], fontSize=12,
                                textColor=colors.HexColor("#333333"), spaceBefore=10, spaceAfter=4)

    for cat_key, cat_items in categories.items():
        label = CAT_LABELS.get(cat_key, cat_key)
        story.append(Paragraph(label, cat_style))
        rows = []
        for it in cat_items:
            name = it.get("ingredient_name") or it.get("name") or ""
            amt = it.get("amount")
            unit = it.get("unit") or ""
            amt_str = ""
            if amt:
                try:
                    amt_str = str(int(amt)) if float(amt) == int(float(amt)) else str(amt)
                except Exception:
                    amt_str = str(amt)
                if unit:
                    amt_str += " " + unit
            deal_tag = f"  [Angebot: {it.get('supermarket', '')}]" if it.get("is_deal") else ""
            rows.append(["☐", name + deal_tag, amt_str])

        t = Table(rows, colWidths=[0.6*cm, None, 3*cm])
        t.setStyle(TableStyle([
            ("FONTSIZE", (0, 0), (-1, -1), 10),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("TOPPADDING", (0, 0), (-1, -1), 2),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
            ("TEXTCOLOR", (2, 0), (2, -1), colors.HexColor("#666666")),
        ]))
        story.append(t)

    story.append(Spacer(1, 0.5*cm))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#dddddd"), spaceAfter=6))
    total_cost = round(sum(
        planner._lookup_price(
            it.get("ingredient_name") or it.get("name") or "",
            str(it.get("unit") or "g"), it.get("amount"), it.get("category", "sonstiges")
        ) for it in items
    ), 2)
    story.append(Paragraph(f"Geschätzte Gesamtkosten: ~€{total_cost:.0f}", subtitle_style))

    doc.build(story)
    buf.seek(0)
    response = make_response(buf.read())
    response.headers["Content-Type"] = "application/pdf"
    response.headers["Content-Disposition"] = "attachment; filename=einkaufsliste.pdf"
    return response


# ── Rezept-Bibliothek ──────────────────────────────────────────────────────────

@app.route("/recipes")
@login_required
def recipes():
    all_recipes = planner.load_recipes(user_id=_uid())
    # Ernährungspräferenzen anwenden (nur wenn kein manueller Filter aktiv)
    all_recipes_filtered = apply_dietary_filter(all_recipes, _uid())
    favorites = [f["recipe_id"] for f in db.get_favorites(_uid())]
    never_again_ids = [n["recipe_id"] for n in db.get_never_again(_uid())]
    never_again_data = {n["recipe_id"]: n for n in db.get_never_again(_uid())}
    user_recipe_ids = {r["id"] for r in db.get_user_recipes(_uid())}

    search       = request.args.get("q", "").strip().lower()
    filter_cats  = request.args.getlist("cats")           # multi-category
    filter_type  = request.args.get("type", "").strip()
    min_protein  = request.args.get("min_protein", "").strip()
    max_cal      = request.args.get("max_cal", "").strip()
    min_cal      = request.args.get("min_cal", "").strip()

    filtered = all_recipes_filtered
    if search:
        filtered = [r for r in filtered
                    if search in r["name"].lower()
                    or search in r.get("description", "").lower()
                    or any(search in tag for tag in r.get("tags", []))]
    if filter_cats:
        filtered = [r for r in filtered if r.get("category") in filter_cats]
    if filter_type:
        filtered = [r for r in filtered if r.get("type") == filter_type or r.get("type") == "both"]
    if min_protein:
        try:
            mp = float(min_protein)
            filtered = [r for r in filtered
                        if (r.get("nutrition_per_portion") or {}).get("protein", 0) >= mp]
        except ValueError:
            pass
    if min_cal:
        try:
            mc = float(min_cal)
            filtered = [r for r in filtered
                        if (r.get("nutrition_per_portion") or {}).get("calories", 0) >= mc]
        except ValueError:
            pass
    if max_cal:
        try:
            mc = float(max_cal)
            filtered = [r for r in filtered
                        if (r.get("nutrition_per_portion") or {}).get("calories", 9999) <= mc]
        except ValueError:
            pass

    categories = sorted(set(r["category"] for r in all_recipes if r.get("category")))

    def sort_key(r):
        return (0 if r["id"] in favorites else 1, r["name"])
    filtered.sort(key=sort_key)

    return render_template(
        "recipes.html",
        recipes=filtered,
        all_count=len(all_recipes),
        favorites=favorites,
        never_again_ids=never_again_ids,
        never_again_data=never_again_data,
        user_recipe_ids=user_recipe_ids,
        search=search,
        selected_cats=filter_cats,
        selected_type=filter_type,
        categories=categories,
        min_protein=min_protein,
        max_cal=max_cal,
        min_cal=min_cal,
    )


@app.route("/recipes/ai-generate", methods=["POST"])
@login_required
def ai_generate_recipe():
    if not db.can_use_ai(_uid(), "recipe", _is_admin()):
        remaining = db.get_ai_remaining(_uid(), "recipe", _is_admin())
        return jsonify({
            "error": f"Du hast dein Limit für KI-Rezepte diese Woche erreicht (3/3). "
                     f"Nächste Woche kannst du wieder neue Rezepte erstellen."
        }), 429

    data = request.get_json() or {}
    wish = data.get("wish", "").strip()
    slot_type = data.get("slot_type", "weekday")
    if not wish:
        return jsonify({"error": "Kein Wunsch angegeben"}), 400

    recipe = planner.generate_full_recipe(wish, slot_type)
    if not recipe:
        return jsonify({"error": "KI konnte kein Rezept generieren. Bitte nochmal versuchen."}), 500

    # Unique ID sicherstellen (user-scope)
    all_recipes = planner.load_recipes(user_id=_uid())
    existing_ids = {r["id"] for r in all_recipes}
    base_id = recipe["id"]
    ctr = 2
    while recipe["id"] in existing_ids:
        recipe["id"] = f"{base_id}_{ctr}"
        ctr += 1

    # Als Benutzer-Rezept speichern (NICHT in recipes.json)
    recipe["created_by"] = _uid()
    db.save_user_recipe(_uid(), recipe)
    planner.invalidate_user_cache(_uid())
    db.increment_ai_usage(_uid(), "recipe")

    remaining = db.get_ai_remaining(_uid(), "recipe", _is_admin())
    return jsonify({
        "ok": True,
        "recipe_id": recipe["id"],
        "recipe_name": recipe["name"],
        "redirect": url_for("recipe_detail", recipe_id=recipe["id"]),
        "remaining": remaining,
    })


@app.route("/recipes/add", methods=["GET", "POST"])
@login_required
def add_recipe():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        if not name:
            flash("Name ist erforderlich.", "error")
            return redirect(url_for("add_recipe"))

        recipe_id = re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")
        existing_ids = {r["id"] for r in planner.load_recipes(user_id=_uid())}
        base_id = recipe_id
        counter = 2
        while recipe_id in existing_ids:
            recipe_id = f"{base_id}_{counter}"
            counter += 1

        ingredients = _parse_ingredients_from_form(request.form)
        deal_keywords = list({w.lower() for ing in ingredients
                               for w in ing["name"].split() if len(w) > 3})[:15]
        tags = [t.strip() for t in request.form.get("tags", "").split(",") if t.strip()]

        try:
            prep_time  = int(request.form.get("prep_time", 20))
            cook_time  = int(request.form.get("cook_time", 20))
            total_time = int(request.form.get("total_time") or prep_time + cook_time)
            servings   = int(request.form.get("servings", 2))
            calories   = int(request.form.get("calories", 500))
            protein    = int(request.form.get("protein", 30))
            carbs      = int(request.form.get("carbs", 50))
            fat        = int(request.form.get("fat", 15))
        except ValueError:
            flash("Ungültige Zahlenangaben.", "error")
            return redirect(url_for("add_recipe"))

        recipe = {
            "id": recipe_id, "name": name,
            "description": request.form.get("description", "").strip(),
            "category": request.form.get("category", "sonstiges"),
            "type": request.form.get("type", "weekday"),
            "difficulty": request.form.get("difficulty", "mittel"),
            "prep_time": prep_time, "cook_time": cook_time, "total_time": total_time,
            "servings": servings,
            "nutrition_per_portion": {"calories": calories, "protein": protein, "carbs": carbs, "fat": fat},
            "tags": tags, "deal_keywords": deal_keywords, "ingredients": ingredients,
            "tips": request.form.get("tips", "").strip(),
            "created_by": _uid(),
        }

        db.save_user_recipe(_uid(), recipe)
        planner.invalidate_user_cache(_uid())
        flash(f"✓ Rezept \"{name}\" wurde hinzugefügt!", "success")
        return redirect(url_for("recipe_detail", recipe_id=recipe_id))

    return render_template("add_recipe.html")


@app.route("/recipes/<recipe_id>/edit", methods=["GET", "POST"])
@login_required
def edit_recipe(recipe_id):
    recipe = planner.get_recipe(recipe_id, user_id=_uid())
    if not recipe:
        flash("Rezept nicht gefunden.", "error")
        return redirect(url_for("recipes"))

    # Basis-Rezepte dürfen nicht bearbeitet werden (nur eigene)
    is_own = db.is_user_recipe(_uid(), recipe_id)
    if not is_own and not _is_admin():
        flash("Du kannst nur deine eigenen Rezepte bearbeiten.", "warning")
        return redirect(url_for("recipe_detail", recipe_id=recipe_id))

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        if not name:
            flash("Name ist erforderlich.", "error")
            return redirect(url_for("edit_recipe", recipe_id=recipe_id))

        ingredients = _parse_ingredients_from_form(request.form)
        tags = [t.strip() for t in request.form.get("tags", "").split(",") if t.strip()]
        deal_keywords = list({w.lower() for ing in ingredients
                               for w in ing["name"].split() if len(w) > 3})[:15]
        try:
            prep_time  = int(request.form.get("prep_time", 20))
            cook_time  = int(request.form.get("cook_time", 20))
            total_time = int(request.form.get("total_time") or prep_time + cook_time)
            servings   = int(request.form.get("servings", 2))
            calories   = int(request.form.get("calories", 500))
            protein    = int(request.form.get("protein", 30))
            carbs      = int(request.form.get("carbs", 50))
            fat        = int(request.form.get("fat", 15))
        except ValueError:
            flash("Ungültige Zahlenangaben.", "error")
            return redirect(url_for("edit_recipe", recipe_id=recipe_id))

        updated = {
            "id": recipe_id, "name": name,
            "description": request.form.get("description", "").strip(),
            "category": request.form.get("category", "sonstiges"),
            "type": request.form.get("type", "weekday"),
            "difficulty": request.form.get("difficulty", "mittel"),
            "prep_time": prep_time, "cook_time": cook_time, "total_time": total_time,
            "servings": servings,
            "nutrition_per_portion": {"calories": calories, "protein": protein, "carbs": carbs, "fat": fat},
            "tags": tags, "deal_keywords": deal_keywords, "ingredients": ingredients,
            "tips": request.form.get("tips", "").strip(),
            "created_by": _uid(),
        }

        db.save_user_recipe(_uid(), updated)
        planner.invalidate_user_cache(_uid())
        flash(f"✓ Rezept \"{name}\" wurde aktualisiert!", "success")
        return redirect(url_for("recipe_detail", recipe_id=recipe_id))

    return render_template("edit_recipe.html", recipe=recipe)


@app.route("/recipes/<recipe_id>/delete", methods=["POST"])
@login_required
def delete_recipe(recipe_id):
    if not db.is_user_recipe(_uid(), recipe_id) and not _is_admin():
        flash("Du kannst nur deine eigenen Rezepte löschen.", "warning")
        return redirect(url_for("recipes"))
    recipe = planner.get_recipe(recipe_id, user_id=_uid())
    name = recipe["name"] if recipe else recipe_id
    db.delete_user_recipe(_uid(), recipe_id)
    planner.invalidate_user_cache(_uid())
    flash(f"Rezept \"{name}\" wurde gelöscht.", "success")
    return redirect(url_for("recipes"))


@app.route("/recipes/<recipe_id>")
@login_required
def recipe_detail(recipe_id):
    recipe = planner.get_recipe(recipe_id, user_id=_uid())
    if not recipe:
        flash("Rezept nicht gefunden.", "error")
        return redirect(url_for("recipes"))
    is_fav = db.is_favorite(recipe_id, _uid())
    is_never = db.is_never_again(recipe_id, _uid())
    is_own = db.is_user_recipe(_uid(), recipe_id)
    instructions = db.get_instructions(recipe_id)

    ing_costs = {}
    total_cost = 0.0
    for ing in recipe.get("ingredients", []):
        if ing.get("is_basic"):
            ing_costs[ing["name"]] = None
            continue
        cost = planner._lookup_price(
            ing.get("name", ""), str(ing.get("unit") or "g"),
            ing.get("amount"), ing.get("category", "sonstiges"),
        )
        ing_costs[ing["name"]] = round(cost, 2)
        total_cost += cost

    return render_template("recipe_detail.html",
                           recipe=recipe, is_fav=is_fav, is_never=is_never, is_own=is_own,
                           instructions=instructions, ing_costs=ing_costs,
                           total_cost=round(total_cost, 2))


@app.route("/recipes/favorite/<recipe_id>", methods=["POST"])
@login_required
def toggle_favorite(recipe_id):
    action = request.json.get("action", "add")
    if action == "add":
        db.add_favorite(recipe_id, _uid())
    else:
        db.remove_favorite(recipe_id, _uid())
    return jsonify({"success": True, "is_favorite": action == "add"})


@app.route("/recipes/never/<recipe_id>", methods=["POST"])
@login_required
def toggle_never(recipe_id):
    action = request.json.get("action", "add")
    reason = request.json.get("reason", "")
    if action == "add":
        db.add_never_again(recipe_id, reason, _uid())
        db.remove_favorite(recipe_id, _uid())
    else:
        db.remove_never_again(recipe_id, _uid())
    return jsonify({"success": True})


# ── Wochenübersicht ────────────────────────────────────────────────────────────

@app.route("/plan/<int:plan_id>/overview")
@login_required
def plan_overview(plan_id):
    plan = db.get_plan(plan_id, _uid())
    if not plan:
        flash("Plan nicht gefunden.", "error")
        return redirect(url_for("index"))

    selections = db.get_selections(plan_id)
    plan_slots = db.get_plan_slots(plan_id)
    slot_map = {s["slot_id"]: s for s in plan_slots}

    selected_recipes = []
    # Iterate selections directly — resilient regardless of slot ID format
    for slot_id, recipe_id in selections.items():
        if not recipe_id or recipe_id == "SKIPPED":
            continue
        r = planner.get_recipe(recipe_id, user_id=_uid())
        if not r:
            continue
        slot_row = slot_map.get(slot_id, {})
        slot = {
            "id": slot_id,
            "label": slot_row.get("label", slot_id),
            "note": slot_row.get("note", ""),
            "leftovers": bool(slot_row.get("leftovers", False)),
        }
        selected_recipes.append({"slot": slot, "recipe": r})

    # Sort by plan_slots order
    slot_order = {s["slot_id"]: i for i, s in enumerate(plan_slots)}
    selected_recipes.sort(key=lambda x: slot_order.get(x["slot"]["id"], 999))

    nutrition_data = planner.get_weekly_nutrition(plan_id, user_id=_uid())
    completed_count = sum(1 for s in plan_slots if selections.get(s["slot_id"]))

    # Auto-fix status for plans whose shopping list was created before status tracking was added
    if plan["status"] != "done" and db.get_shopping_list(plan_id):
        db.finish_plan(plan_id)
        plan = dict(plan)
        plan["status"] = "done"

    return render_template(
        "overview.html", plan=plan, selected_recipes=selected_recipes,
        nutrition=nutrition_data, total_slots=len(plan_slots),
        selected_count=len(selected_recipes),
        completed_count=completed_count,
    )


# ── Nährwerte API ──────────────────────────────────────────────────────────────

@app.route("/api/nutrition/<int:plan_id>")
@login_required
def api_nutrition(plan_id):
    data = planner.get_weekly_nutrition(plan_id, user_id=_uid())
    return jsonify(data)


@app.route("/api/recipe/<recipe_id>")
@login_required
def api_recipe(recipe_id):
    recipe = planner.get_recipe(recipe_id, user_id=_uid())
    if not recipe:
        return jsonify({"error": "Nicht gefunden"}), 404
    return jsonify(recipe)


@app.route("/api/recipe/<recipe_id>/instructions", methods=["POST"])
@login_required
def generate_instructions(recipe_id):
    recipe = planner.get_recipe(recipe_id, user_id=_uid())
    if not recipe:
        return jsonify({"error": "Rezept nicht gefunden"}), 404

    # ?refresh=1 löscht den Cache und generiert neu
    force_refresh = request.args.get("refresh") == "1"
    if not force_refresh:
        cached = db.get_instructions(recipe_id)
        if cached:
            return jsonify({"success": True, "instructions": cached, "cached": True})

    if force_refresh:
        conn = db.get_db()
        try:
            cur = db._cursor(conn)
            cur.execute(f"DELETE FROM recipe_instructions WHERE recipe_id = {db.PH}", (recipe_id,))
            conn.commit()
        finally:
            conn.close()

    steps = planner.generate_recipe_instructions(recipe)
    if steps:
        db.save_instructions(recipe_id, steps)
        return jsonify({"success": True, "instructions": steps, "cached": False})
    else:
        return jsonify({"error": "Konnte keine Kochanweisungen generieren"}), 500


# ── Hilfsfunktion: Zutaten aus Formular parsen ─────────────────────────────────

def _parse_ingredients_from_form(form):
    ingredients = []
    ing_names   = form.getlist("ing_name[]")
    ing_amounts = form.getlist("ing_amount[]")
    ing_units   = form.getlist("ing_unit[]")
    ing_cats    = form.getlist("ing_category[]")
    ing_basics  = form.getlist("ing_basic[]")
    basic_indices = set(ing_basics)
    for i, iname in enumerate(ing_names):
        iname = iname.strip()
        if not iname:
            continue
        try:
            amt = float(ing_amounts[i]) if ing_amounts[i].strip() else None
        except (ValueError, IndexError):
            amt = None
        ingredients.append({
            "name": iname,
            "amount": amt,
            "unit": ing_units[i].strip() if i < len(ing_units) else "g",
            "category": ing_cats[i].strip() if i < len(ing_cats) else "sonstiges",
            "is_basic": str(i) in basic_indices,
        })
    return ingredients


def _send_mail(to: str, subject: str, html_body: str):
    """Sendet eine E-Mail. Wenn SMTP nicht konfiguriert, wird der Link geloggt."""
    if not MAIL_USERNAME or not MAIL_PASSWORD:
        print(f"[Mail – kein SMTP konfiguriert] An: {to}\nBetreff: {subject}\n{html_body[:300]}")
        return
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = MAIL_FROM
        msg["To"] = to
        msg.attach(MIMEText(html_body, "html", "utf-8"))
        with smtplib.SMTP(MAIL_SERVER, MAIL_PORT, timeout=10) as srv:
            srv.starttls()
            srv.login(MAIL_USERNAME, MAIL_PASSWORD)
            srv.sendmail(MAIL_FROM, to, msg.as_string())
    except Exception as e:
        print(f"[Mail Fehler] {e}")


@app.route("/verify-email/<token>")
def verify_email(token):
    user_id = db.verify_email_token(token, "verify")
    if not user_id:
        flash("Der Link ist ungültig oder abgelaufen.", "error")
        return redirect(url_for("login"))
    db.set_user_verified(user_id)
    flash("E-Mail erfolgreich bestätigt! Du kannst dich jetzt anmelden.", "success")
    return redirect(url_for("login"))


@app.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        user_data = db.get_user_by_email(email)
        if user_data:
            token = db.create_email_token(user_data["id"], "reset")
            reset_url = f"{APP_URL}/reset-password/{token}"
            _send_mail(
                email,
                "Meal Planner – Passwort zurücksetzen",
                f"""<p>Hallo {user_data['name']},</p>
<p>Klicke auf diesen Link um dein Passwort zurückzusetzen:</p>
<p><a href="{reset_url}">{reset_url}</a></p>
<p>Der Link ist 24 Stunden gültig. Falls du kein Reset angefordert hast, ignoriere diese Mail.</p>
<p>Meal Planner Team</p>"""
            )
        # Immer gleiche Meldung (verhindert E-Mail-Enumeration)
        flash("Falls diese E-Mail registriert ist, wurde ein Link gesendet.", "info")
        return redirect(url_for("login"))
    return render_template("forgot_password.html")


@app.route("/reset-password/<token>", methods=["GET", "POST"])
def reset_password(token):
    if request.method == "POST":
        pw = request.form.get("password", "")
        pw2 = request.form.get("password2", "")
        if len(pw) < 6:
            flash("Passwort muss mindestens 6 Zeichen haben.", "error")
            return render_template("reset_password.html", token=token)
        if pw != pw2:
            flash("Passwörter stimmen nicht überein.", "error")
            return render_template("reset_password.html", token=token)
        user_id = db.verify_email_token(token, "reset")
        if not user_id:
            flash("Der Link ist ungültig oder abgelaufen. Bitte neu anfordern.", "error")
            return redirect(url_for("forgot_password"))
        db.update_user_password(user_id, generate_password_hash(pw, method="pbkdf2:sha256"))
        flash("Passwort erfolgreich geändert! Du kannst dich jetzt anmelden.", "success")
        return redirect(url_for("login"))
    return render_template("reset_password.html", token=token)


# ── Admin-Panel ────────────────────────────────────────────────────────────────

@app.route("/admin")
@login_required
def admin_panel():
    if not _is_admin():
        flash("Kein Zugriff.", "error")
        return redirect(url_for("index"))
    users = db.get_all_users()
    return render_template("admin.html", users=users, limits=_LIMITS)


@app.route("/admin/user/<int:user_id>", methods=["POST"])
@login_required
def admin_update_user(user_id):
    if not _is_admin():
        return jsonify({"error": "Forbidden"}), 403
    action = request.form.get("action", "update")

    if action == "delete":
        if user_id == _uid():
            return jsonify({"error": "Du kannst dich nicht selbst löschen."}), 400
        db.delete_user(user_id)
        flash("Benutzer gelöscht.", "success")
        return redirect(url_for("admin_panel"))

    if action == "update":
        name       = request.form.get("name", "").strip()
        email      = request.form.get("email", "").strip()
        is_admin   = 1 if request.form.get("is_admin") else 0
        is_verified = 1 if request.form.get("is_verified") else 0
        if not name or not email:
            flash("Name und E-Mail dürfen nicht leer sein.", "error")
            return redirect(url_for("admin_panel"))
        db.update_user_profile(user_id, name, email, is_admin, is_verified)
        # Optional: neues Passwort setzen
        new_pw = request.form.get("new_password", "").strip()
        if new_pw:
            if len(new_pw) < 6:
                flash("Passwort muss mindestens 6 Zeichen haben.", "error")
                return redirect(url_for("admin_panel"))
            db.update_user_password(user_id, generate_password_hash(new_pw, method="pbkdf2:sha256"))
        flash("Benutzer aktualisiert.", "success")
        return redirect(url_for("admin_panel"))

    if action == "reset_recipe":
        try:
            db.reset_user_ai_usage(user_id, "recipe")
            app.logger.info(f"Reset recipe usage for user {user_id}")
            return jsonify({"success": True, "msg": "KI-Rezept-Limit zurückgesetzt"})
        except Exception as e:
            app.logger.error(f"Reset recipe failed for user {user_id}: {e}")
            return jsonify({"error": str(e)}), 500

    if action == "reset_plan":
        try:
            db.reset_user_ai_usage(user_id, "plan")
            app.logger.info(f"Reset plan usage for user {user_id}")
            return jsonify({"success": True, "msg": "Plan-Limit zurückgesetzt"})
        except Exception as e:
            app.logger.error(f"Reset plan failed for user {user_id}: {e}")
            return jsonify({"error": str(e)}), 500

    return jsonify({"error": "Unbekannte Aktion"}), 400


@app.route("/admin/setup")
@login_required
def admin_setup():
    """Einmaliges Admin-Setup: Gibt dem ersten Nutzer Admin-Rechte,
    falls noch kein echter Admin vorhanden ist."""
    if _is_admin():
        return redirect(url_for("admin_panel"))
    admin_users = db.get_admin_users()
    # Nur auto-erstellter System-Admin oder kein Admin → aktuellen User zum Admin machen
    non_system = [u for u in admin_users if u.get("email") != "admin@mealplanner.at"]
    if not non_system:
        db.update_user_profile(current_user.id, current_user.name, current_user.email,
                               is_admin=1, is_verified=1)
        flash("✅ Admin-Rechte aktiviert! Du kannst jetzt das Admin-Panel nutzen.", "success")
        return redirect(url_for("admin_panel"))
    flash("Admin-Zugang existiert bereits. Bitte wende dich an einen bestehenden Admin.", "warning")
    return redirect(url_for("index"))


# ── Health-Check (für Uptime-Monitoring / Render Ping) ─────────────────────────
@app.route("/health")
def health():
    """Einfacher Health-Check – gibt 200 OK zurück. Wird von Uptime-Diensten gepingt."""
    return jsonify({"status": "ok", "service": "meal-planner"}), 200


# ── One-time data migration endpoint ────────────────────────────────────────────
@app.route("/admin/migrate-sqlite", methods=["POST"])
def migrate_sqlite():
    """One-time migration: imports SQLite data into the production database."""
    import os
    secret = request.headers.get("X-Migrate-Secret", "")
    if secret != os.environ.get("MIGRATE_SECRET", ""):
        return jsonify({"error": "unauthorized"}), 403

    data = request.get_json()
    if not data:
        return jsonify({"error": "no data"}), 400

    results = {}
    conn = db.get_db()
    try:
        cur = conn.cursor()
        is_pg = db.IS_POSTGRES

        def exec(sql_pg, sql_sq, params):
            cur.execute(sql_pg if is_pg else sql_sq, params)

        # Users
        count = 0
        for u in data.get("users", []):
            if is_pg:
                cur.execute("""
                    INSERT INTO users (id, email, name, password_hash, is_admin, created_at, is_verified)
                    VALUES (%s,%s,%s,%s,%s,%s,%s)
                    ON CONFLICT (id) DO UPDATE SET email=EXCLUDED.email, name=EXCLUDED.name,
                    password_hash=EXCLUDED.password_hash, is_admin=EXCLUDED.is_admin, is_verified=EXCLUDED.is_verified
                """, (u['id'], u['email'], u['name'], u['password_hash'], u['is_admin'], u['created_at'], u['is_verified']))
            else:
                cur.execute("INSERT OR REPLACE INTO users (id,email,name,password_hash,is_admin,created_at,is_verified) VALUES (?,?,?,?,?,?,?)",
                    (u['id'], u['email'], u['name'], u['password_hash'], u['is_admin'], u['created_at'], u['is_verified']))
            count += 1
        if is_pg and data.get("users"):
            cur.execute("SELECT setval('users_id_seq', (SELECT MAX(id) FROM users))")
        results["users"] = count

        # Week plans
        count = 0
        for p in data.get("week_plans", []):
            if is_pg:
                cur.execute("""
                    INSERT INTO week_plans (id, user_id, week_start, cravings, status, created_at, default_persons, name, sort_order)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s) ON CONFLICT (id) DO NOTHING
                """, (p['id'], p['user_id'], p['week_start'], p.get('cravings',''), p.get('status','in_progress'),
                      p['created_at'], p.get('default_persons',2), p.get('name',''), p.get('sort_order',0)))
            else:
                cur.execute("INSERT OR IGNORE INTO week_plans (id,user_id,week_start,cravings,status,created_at,default_persons,name,sort_order) VALUES (?,?,?,?,?,?,?,?,?)",
                    (p['id'], p['user_id'], p['week_start'], p.get('cravings',''), p.get('status','in_progress'),
                     p['created_at'], p.get('default_persons',2), p.get('name',''), p.get('sort_order',0)))
            count += 1
        if is_pg and data.get("week_plans"):
            cur.execute("SELECT setval('week_plans_id_seq', (SELECT MAX(id) FROM week_plans))")
        results["week_plans"] = count

        # Plan slots
        count = 0
        for s in data.get("plan_slots", []):
            if is_pg:
                cur.execute("""
                    INSERT INTO plan_slots (id, plan_id, slot_id, label, type, note, leftovers, sort_order)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s) ON CONFLICT (id) DO NOTHING
                """, (s['id'], s['plan_id'], s['slot_id'], s['label'], s['type'],
                      s.get('note',''), s.get('leftovers',0), s.get('sort_order',0)))
            else:
                cur.execute("INSERT OR IGNORE INTO plan_slots (id,plan_id,slot_id,label,type,note,leftovers,sort_order) VALUES (?,?,?,?,?,?,?,?)",
                    (s['id'], s['plan_id'], s['slot_id'], s['label'], s['type'],
                     s.get('note',''), s.get('leftovers',0), s.get('sort_order',0)))
            count += 1
        if is_pg and data.get("plan_slots"):
            cur.execute("SELECT setval('plan_slots_id_seq', (SELECT MAX(id) FROM plan_slots))")
        results["plan_slots"] = count

        # Meal selections
        count = 0
        for m in data.get("meal_selections", []):
            meal_slot = m.get('meal_slot') or m.get('slot_id', '')
            selected_at = m.get('selected_at') or m.get('created_at', '')
            if is_pg:
                cur.execute("""
                    INSERT INTO meal_selections (id, plan_id, meal_slot, recipe_id, selected_at)
                    VALUES (%s,%s,%s,%s,%s) ON CONFLICT (id) DO NOTHING
                """, (m['id'], m['plan_id'], meal_slot, m['recipe_id'], selected_at))
            else:
                cur.execute("INSERT OR IGNORE INTO meal_selections (id,plan_id,meal_slot,recipe_id,selected_at) VALUES (?,?,?,?,?)",
                    (m['id'], m['plan_id'], meal_slot, m['recipe_id'], selected_at))
            count += 1
        if is_pg and data.get("meal_selections"):
            cur.execute("SELECT setval('meal_selections_id_seq', (SELECT MAX(id) FROM meal_selections))")
        results["meal_selections"] = count

        # Shopping items
        count = 0
        for s in data.get("shopping_items", []):
            ingredient_name = s.get('ingredient_name') or s.get('ingredient', '')
            if is_pg:
                cur.execute("""
                    INSERT INTO shopping_items (id, plan_id, ingredient_name, amount, unit, category, checked)
                    VALUES (%s,%s,%s,%s,%s,%s,%s) ON CONFLICT (id) DO NOTHING
                """, (s['id'], s['plan_id'], ingredient_name, s.get('amount'),
                      s.get('unit', ''), s.get('category', ''), s.get('checked', 0)))
            else:
                cur.execute("INSERT OR IGNORE INTO shopping_items (id,plan_id,ingredient_name,amount,unit,category,checked) VALUES (?,?,?,?,?,?,?)",
                    (s['id'], s['plan_id'], ingredient_name, s.get('amount'),
                     s.get('unit', ''), s.get('category', ''), s.get('checked', 0)))
            count += 1
        if is_pg and data.get("shopping_items"):
            cur.execute("SELECT setval('shopping_items_id_seq', (SELECT MAX(id) FROM shopping_items))")
        results["shopping_items"] = count

        # Favorites
        count = 0
        for f in data.get("favorites", []):
            added_at = f.get('added_at') or f.get('created_at', '')
            if is_pg:
                cur.execute("INSERT INTO favorites (id, user_id, recipe_id, added_at) VALUES (%s,%s,%s,%s) ON CONFLICT (id) DO NOTHING",
                    (f['id'], f['user_id'], f['recipe_id'], added_at))
            else:
                cur.execute("INSERT OR IGNORE INTO favorites (id,user_id,recipe_id,added_at) VALUES (?,?,?,?)",
                    (f['id'], f['user_id'], f['recipe_id'], added_at))
            count += 1
        if is_pg and data.get("favorites"):
            cur.execute("SELECT setval('favorites_id_seq', (SELECT MAX(id) FROM favorites))")
        results["favorites"] = count

        # Never again
        count = 0
        for n in data.get("never_again", []):
            added_at = n.get('added_at') or n.get('created_at', '')
            if is_pg:
                cur.execute("INSERT INTO never_again (id, user_id, recipe_id, added_at) VALUES (%s,%s,%s,%s) ON CONFLICT (id) DO NOTHING",
                    (n['id'], n['user_id'], n['recipe_id'], added_at))
            else:
                cur.execute("INSERT OR IGNORE INTO never_again (id,user_id,recipe_id,added_at) VALUES (?,?,?,?)",
                    (n['id'], n['user_id'], n['recipe_id'], added_at))
            count += 1
        if is_pg and data.get("never_again"):
            cur.execute("SELECT setval('never_again_id_seq', (SELECT MAX(id) FROM never_again))")
        results["never_again"] = count

        # Deals
        count = 0
        for d in data.get("deals", []):
            if is_pg:
                cur.execute("""
                    INSERT INTO deals (id, supermarket, product_name, description, price, original_price,
                        discount_pct, discount_label, category, valid_from, valid_to, scraped_at)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) ON CONFLICT (id) DO NOTHING
                """, (d['id'], d['supermarket'], d['product_name'], d.get('description',''),
                      d.get('price'), d.get('original_price'), d.get('discount_pct'),
                      d.get('discount_label',''), d.get('category',''), d.get('valid_from'),
                      d.get('valid_to'), d.get('scraped_at','')))
            else:
                cur.execute("""INSERT OR IGNORE INTO deals
                    (id, supermarket, product_name, description, price, original_price,
                     discount_pct, discount_label, category, valid_from, valid_to, scraped_at)
                    VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
                    (d['id'], d['supermarket'], d['product_name'], d.get('description',''),
                     d.get('price'), d.get('original_price'), d.get('discount_pct'),
                     d.get('discount_label',''), d.get('category',''), d.get('valid_from'),
                     d.get('valid_to'), d.get('scraped_at','')))
            count += 1
        if is_pg and data.get("deals"):
            cur.execute("SELECT setval('deals_id_seq', (SELECT MAX(id) FROM deals))")
        results["deals"] = count

        # Clear instruction cache (so wrong cached instructions are removed)
        cur.execute("DELETE FROM recipe_instructions")
        results["instructions_cleared"] = True

        conn.commit()
        return jsonify({"success": True, "migrated": results}), 200

    except Exception as e:
        conn.rollback()
        import traceback
        return jsonify({"error": str(e), "trace": traceback.format_exc()}), 500


# Beim Start (auch via gunicorn): Verzeichnisse + DB initialisieren
os.makedirs(os.path.dirname(os.path.abspath(_DB_PATH)), exist_ok=True)
os.makedirs(UPLOADS_DIR, exist_ok=True)
db.init_db()

if __name__ == "__main__":
    app.run(debug=DEBUG, port=5001)
