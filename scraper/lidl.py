"""
Lidl.at Angebots-Scraper
"""
import requests
from bs4 import BeautifulSoup
from datetime import date, timedelta
import re, json, sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from config import SCRAPER_HEADERS, SCRAPER_TIMEOUT
from scraper.hofer import _categorize, _parse_price, _scrape_wogibtswas

SUPERMARKET = "Lidl"


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


def scrape_lidl() -> list:
    deals = []

    # Versuch 1: Lidl API (Lidl nutzt eine interne REST-API)
    try:
        deals = _scrape_lidl_api()
        if deals:
            print(f"[Lidl] {len(deals)} Angebote via API geladen")
            return deals
    except Exception as e:
        print(f"[Lidl] API fehlgeschlagen: {e}")

    # Versuch 2: Lidl Website direkt
    try:
        deals = _scrape_lidl_direct()
        if deals:
            print(f"[Lidl] {len(deals)} Angebote von lidl.at geladen")
            return deals
    except Exception as e:
        print(f"[Lidl] Direktscraping fehlgeschlagen: {e}")

    # Versuch 3: Wogibtswas
    try:
        raw = _scrape_wogibtswas("lidl")
        deals = [{**d, "supermarket": SUPERMARKET} for d in raw]
        if deals:
            print(f"[Lidl] {len(deals)} Angebote von wogibtswas.at geladen")
            return deals
    except Exception as e:
        print(f"[Lidl] Wogibtswas fehlgeschlagen: {e}")

    print("[Lidl] Kein automatisches Scraping erfolgreich – PDF-Upload nötig")
    return []


def _scrape_lidl_api() -> list:
    """Lidl nutzt eine interne GraphQL/REST API."""
    headers = {**SCRAPER_HEADERS, "Accept": "application/json"}
    # Lidl AT API Endpunkte
    endpoints = [
        "https://www.lidl.at/api/offers",
        "https://www.lidl.at/api/v1/offers?country=AT",
        "https://www.lidl.at/de/angebote.htm",
    ]
    for url in endpoints:
        try:
            resp = requests.get(url, headers=headers, timeout=SCRAPER_TIMEOUT)
            if resp.status_code == 200 and "application/json" in resp.headers.get("content-type", ""):
                data = resp.json()
                return _parse_lidl_json(data)
        except Exception:
            continue
    return []


def _parse_lidl_json(data) -> list:
    deals = []
    items = []
    if isinstance(data, list):
        items = data
    elif isinstance(data, dict):
        for key in ("offers", "products", "items", "data"):
            if key in data:
                items = data[key]
                break
    for item in items[:60]:
        name = item.get("name") or item.get("title") or item.get("productName", "")
        price = item.get("price") or item.get("currentPrice") or item.get("offerPrice")
        orig = item.get("originalPrice") or item.get("normalPrice")
        desc = item.get("description") or item.get("subtitle", "")
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
            category=_categorize(str(name)),
        ))
    return deals


def _scrape_lidl_direct() -> list:
    url = "https://www.lidl.at/de/angebote.htm"
    resp = requests.get(url, headers=SCRAPER_HEADERS, timeout=SCRAPER_TIMEOUT)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "lxml")
    deals = []

    for selector in [
        ".offer-item", ".product-grid-item", ".n-product-card",
        "[data-testid='product']", ".ribbon-offer"
    ]:
        items = soup.select(selector)
        if not items:
            continue
        for item in items[:50]:
            name_el = item.select_one(
                ".offer-title, .product-title, h3, h2, [class*='title'], [class*='name']"
            )
            price_el = item.select_one("[class*='price'], .preis, .price")
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

    return deals
