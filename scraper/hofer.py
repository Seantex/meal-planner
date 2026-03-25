"""
Hofer.at Angebots-Scraper
Strategie: 1) Hofer-Website direkt  2) Wogibtswas.at  3) PDF-Fallback
"""
import requests
from bs4 import BeautifulSoup
from datetime import date, timedelta
import re
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from config import SCRAPER_HEADERS, SCRAPER_TIMEOUT


SUPERMARKET = "Hofer"


def _make_deal(product_name: str, description: str = "", price: float = None,
               original_price: float = None, discount_pct: int = None,
               discount_label: str = "", category: str = "sonstiges") -> dict:
    today = date.today()
    # Hofer-Prospekte laufen typisch Mo–So
    valid_from = (today - timedelta(days=today.weekday())).isoformat()
    valid_to = (today + timedelta(days=6 - today.weekday())).isoformat()
    return {
        "supermarket": SUPERMARKET,
        "product_name": product_name.strip(),
        "description": description.strip(),
        "price": price,
        "original_price": original_price,
        "discount_pct": discount_pct,
        "discount_label": discount_label,
        "category": category,
        "valid_from": valid_from,
        "valid_to": valid_to,
    }


def _categorize(name: str) -> str:
    name_lower = name.lower()
    if any(k in name_lower for k in ["fleisch", "schnitzel", "hack", "steak", "wurst", "speck",
                                      "schinken", "hähnchen", "hühn", "pute", "rind", "schwein",
                                      "lamm", "gulasch", "faschiertes"]):
        return "fleisch"
    if any(k in name_lower for k in ["fisch", "lachs", "thunfisch", "garnele", "shrimp",
                                      "forelle", "zander", "hecht", "makrele", "sardine"]):
        return "fisch"
    if any(k in name_lower for k in ["nudel", "pasta", "spaghetti", "penne", "rigatoni",
                                      "fusilli", "tortellini", "gnocchi", "lasagne"]):
        return "nudeln"
    if any(k in name_lower for k in ["käse", "parmesan", "mozzarella", "gouda", "emmental",
                                      "gorgonzola", "ricotta", "brie", "camembert"]):
        return "käse"
    if any(k in name_lower for k in ["milch", "joghurt", "sahne", "butter", "quark", "obers"]):
        return "milch"
    if any(k in name_lower for k in ["ei", "eier"]):
        return "eier"
    if any(k in name_lower for k in ["obst", "gemüse", "salat", "tomate", "zucchini",
                                      "paprika", "zwiebel", "karotte", "brokkoli", "spinat",
                                      "beere", "apfel", "banane", "orange", "zitrone"]):
        return "gemüse_obst"
    if any(k in name_lower for k in ["reis", "getreide", "quinoa", "couscous", "linsen", "bohnen"]):
        return "reis_hülsenfrüchte"
    if any(k in name_lower for k in ["gewürz", "oregano", "basilikum", "paprika", "curry",
                                      "pfeffer", "salz", "kräuter"]):
        return "gewürze"
    if any(k in name_lower for k in ["öl", "essig", "soße", "sauce", "ketchup", "mayo"]):
        return "saucen_öle"
    return "sonstiges"


def scrape_hofer() -> list:
    """Versucht Angebote von Hofer zu laden. Gibt Liste von Deal-Dicts zurück."""
    deals = []

    # Versuch 1: Hofer.at direkt
    try:
        deals = _scrape_hofer_direct()
        if deals:
            print(f"[Hofer] {len(deals)} Angebote von hofer.at geladen")
            return deals
    except Exception as e:
        print(f"[Hofer] Direktscraping fehlgeschlagen: {e}")

    # Versuch 2: Wogibtswas.at
    try:
        deals = _scrape_wogibtswas("hofer")
        if deals:
            print(f"[Hofer] {len(deals)} Angebote von wogibtswas.at geladen")
            return deals
    except Exception as e:
        print(f"[Hofer] Wogibtswas fehlgeschlagen: {e}")

    print(f"[Hofer] Kein automatisches Scraping erfolgreich – PDF-Upload nötig")
    return []


def _scrape_hofer_direct() -> list:
    url = "https://www.hofer.at/de/angebote.html"
    resp = requests.get(url, headers=SCRAPER_HEADERS, timeout=SCRAPER_TIMEOUT)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "lxml")
    deals = []

    # Hofer verwendet verschiedene Selektoren je nach Deployment
    # Wir versuchen mehrere gängige Muster
    for selector in [
        ".offer-item", ".product-item", ".angebot-item",
        "[data-testid='offer-card']", ".offer-card",
        ".js-offer", ".flyout-item"
    ]:
        items = soup.select(selector)
        if items:
            for item in items[:50]:
                name_el = item.select_one(
                    ".offer-title, .product-name, h3, h2, .title, [class*='name']"
                )
                price_el = item.select_one(
                    ".offer-price, .price, [class*='price'], .preis"
                )
                orig_el = item.select_one(
                    ".original-price, .old-price, [class*='original'], [class*='statt']"
                )
                desc_el = item.select_one(
                    ".offer-description, .description, p, .desc"
                )

                if not name_el:
                    continue

                name = name_el.get_text(strip=True)
                if len(name) < 3:
                    continue

                price = _parse_price(price_el.get_text() if price_el else "")
                orig_price = _parse_price(orig_el.get_text() if orig_el else "")
                desc = desc_el.get_text(strip=True) if desc_el else ""

                disc_pct = None
                if price and orig_price and orig_price > price:
                    disc_pct = round((1 - price / orig_price) * 100)

                deals.append(_make_deal(
                    product_name=name,
                    description=desc,
                    price=price,
                    original_price=orig_price,
                    discount_pct=disc_pct,
                    category=_categorize(name),
                ))
            break

    # Fallback: JSON-LD structured data
    if not deals:
        for script in soup.find_all("script", type="application/ld+json"):
            try:
                import json
                data = json.loads(script.string)
                if isinstance(data, list):
                    items = data
                elif isinstance(data, dict) and "@graph" in data:
                    items = data["@graph"]
                else:
                    items = [data]
                for item in items:
                    if item.get("@type") in ("Product", "Offer"):
                        name = item.get("name", "")
                        price = item.get("offers", {}).get("price") if isinstance(item.get("offers"), dict) else None
                        if name:
                            deals.append(_make_deal(
                                product_name=name,
                                price=float(price) if price else None,
                                category=_categorize(name),
                            ))
            except Exception:
                continue

    return deals


def _scrape_wogibtswas(market: str) -> list:
    """Scrape wogibtswas.at als Fallback."""
    url = f"https://www.wogibtswas.at/supermaerkte/{market}/angebote"
    resp = requests.get(url, headers=SCRAPER_HEADERS, timeout=SCRAPER_TIMEOUT)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "lxml")
    deals = []

    for item in soup.select(".offer, .angebot, [class*='offer'], [class*='product']")[:50]:
        name_el = item.select_one("h2, h3, .name, .title, [class*='name']")
        price_el = item.select_one(".price, .preis, [class*='price']")
        if not name_el:
            continue
        name = name_el.get_text(strip=True)
        price = _parse_price(price_el.get_text() if price_el else "")
        deals.append(_make_deal(
            product_name=name,
            price=price,
            category=_categorize(name),
        ))

    return deals


def _parse_price(text: str):
    if not text:
        return None
    match = re.search(r"(\d+[,.]?\d*)", text.replace(" ", ""))
    if match:
        return float(match.group(1).replace(",", "."))
    return None
