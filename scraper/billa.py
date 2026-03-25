"""
Billa.at Angebots-Scraper
Billa (Rewe Austria) hat eine gut dokumentierte API.
"""
import requests
from bs4 import BeautifulSoup
from datetime import date, timedelta
import re, json, sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from config import SCRAPER_HEADERS, SCRAPER_TIMEOUT
from scraper.hofer import _categorize, _parse_price, _scrape_wogibtswas

SUPERMARKET = "Billa"


def _make_deal(product_name, description="", price=None, original_price=None,
               discount_pct=None, discount_label="", category="sonstiges"):
    today = date.today()
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


def scrape_billa() -> list:
    deals = []

    # Versuch 1: Billa REWE API (bekannte Endpunkte)
    try:
        deals = _scrape_billa_api()
        if deals:
            print(f"[Billa] {len(deals)} Angebote via API geladen")
            return deals
    except Exception as e:
        print(f"[Billa] API fehlgeschlagen: {e}")

    # Versuch 2: Billa Website
    try:
        deals = _scrape_billa_direct()
        if deals:
            print(f"[Billa] {len(deals)} Angebote von billa.at geladen")
            return deals
    except Exception as e:
        print(f"[Billa] Direktscraping fehlgeschlagen: {e}")

    # Versuch 3: Wogibtswas
    try:
        raw = _scrape_wogibtswas("billa")
        deals = [{**d, "supermarket": SUPERMARKET} for d in raw]
        if deals:
            print(f"[Billa] {len(deals)} Angebote von wogibtswas.at geladen")
            return deals
    except Exception as e:
        print(f"[Billa] Wogibtswas fehlgeschlagen: {e}")

    print("[Billa] Kein automatisches Scraping erfolgreich – PDF-Upload nötig")
    return []


def _scrape_billa_api() -> list:
    """
    Billa/REWE nutzt eine GraphQL API.
    Bekannte Endpunkte für aktuelle Angebote:
    """
    headers = {
        **SCRAPER_HEADERS,
        "Accept": "application/json",
        "X-Requested-With": "XMLHttpRequest",
    }

    api_urls = [
        # REWE Austria Angebote API
        "https://www.billa.at/api/categories/aktuell-bei-billa",
        "https://www.billa.at/api/offers",
        # Alternativ über den REWE API Gateway
        "https://shop.billa.at/api/articles?category=aktionsartikel&pageSize=60",
        "https://shop.billa.at/api/search?category=aktionsartikel&limit=60",
    ]

    for url in api_urls:
        try:
            resp = requests.get(url, headers=headers, timeout=SCRAPER_TIMEOUT)
            if resp.status_code != 200:
                continue
            ct = resp.headers.get("content-type", "")
            if "json" not in ct:
                continue
            data = resp.json()
            deals = _parse_billa_json(data)
            if deals:
                return deals
        except Exception:
            continue

    return []


def _parse_billa_json(data) -> list:
    deals = []
    items = []

    # Verschiedene JSON-Strukturen durchsuchen
    if isinstance(data, list):
        items = data
    elif isinstance(data, dict):
        for key in ("results", "products", "articles", "items", "data", "elements"):
            val = data.get(key)
            if isinstance(val, list) and val:
                items = val
                break

    for item in items[:60]:
        # Verschiedene Feldnamen versuchen
        name = (item.get("name") or item.get("title") or
                item.get("articleTitle") or item.get("productName", ""))
        price_data = item.get("price") or {}
        if isinstance(price_data, dict):
            price = price_data.get("final") or price_data.get("current") or price_data.get("value")
            orig = price_data.get("normal") or price_data.get("original")
        else:
            price = price_data
            orig = item.get("normalPrice") or item.get("originalPrice")

        disc_label = item.get("badge") or item.get("promotion") or ""
        desc = item.get("description") or item.get("grammagePriceLabel", "")

        if not name:
            continue

        disc_pct = None
        if price and orig:
            try:
                disc_pct = round((1 - float(price) / float(orig)) * 100)
            except Exception:
                pass

        deals.append(_make_deal(
            product_name=str(name),
            description=str(desc),
            price=float(price) if price else None,
            original_price=float(orig) if orig else None,
            discount_pct=disc_pct,
            discount_label=str(disc_label),
            category=_categorize(str(name)),
        ))

    return deals


def _scrape_billa_direct() -> list:
    url = "https://www.billa.at/angebote"
    resp = requests.get(url, headers=SCRAPER_HEADERS, timeout=SCRAPER_TIMEOUT)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "lxml")
    deals = []

    # Verschiedene Selektoren versuchen
    for selector in [
        ".offer-tile", ".product-tile", ".article-tile",
        "[class*='offer']", "[class*='product-card']",
        ".cms-offer", ".bipa-offer"
    ]:
        items = soup.select(selector)
        if not items:
            continue
        for item in items[:50]:
            name_el = item.select_one(
                "h3, h2, .product-title, [class*='title'], [class*='name']"
            )
            price_el = item.select_one("[class*='price'], .preis")
            if not name_el:
                continue
            name = name_el.get_text(strip=True)
            if len(name) < 3:
                continue
            price = _parse_price(price_el.get_text() if price_el else "")
            deals.append(_make_deal(
                product_name=name,
                price=price,
                category=_categorize(name),
            ))
        if deals:
            break

    # JSON-LD Daten
    if not deals:
        for script in soup.find_all("script", type="application/ld+json"):
            try:
                data = json.loads(script.string or "")
                items = data if isinstance(data, list) else [data]
                for item in items:
                    if item.get("@type") in ("Product", "Offer"):
                        name = item.get("name", "")
                        if name:
                            offer = item.get("offers", {})
                            price = offer.get("price") if isinstance(offer, dict) else None
                            deals.append(_make_deal(
                                product_name=name,
                                price=float(price) if price else None,
                                category=_categorize(name),
                            ))
            except Exception:
                continue

    return deals
