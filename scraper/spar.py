"""
Spar.at Angebots-Scraper
"""
import requests
from bs4 import BeautifulSoup
from datetime import date, timedelta
import re, json, sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from config import SCRAPER_HEADERS, SCRAPER_TIMEOUT
from scraper.hofer import _categorize, _parse_price, _scrape_wogibtswas

SUPERMARKET = "Spar"


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


def scrape_spar() -> list:
    deals = []

    # Versuch 1: Spar API
    try:
        deals = _scrape_spar_api()
        if deals:
            print(f"[Spar] {len(deals)} Angebote via API geladen")
            return deals
    except Exception as e:
        print(f"[Spar] API fehlgeschlagen: {e}")

    # Versuch 2: Spar Website direkt
    try:
        deals = _scrape_spar_direct()
        if deals:
            print(f"[Spar] {len(deals)} Angebote von spar.at geladen")
            return deals
    except Exception as e:
        print(f"[Spar] Direktscraping fehlgeschlagen: {e}")

    # Versuch 3: Wogibtswas
    try:
        raw = _scrape_wogibtswas("spar")
        deals = [{**d, "supermarket": SUPERMARKET} for d in raw]
        if deals:
            print(f"[Spar] {len(deals)} Angebote von wogibtswas.at geladen")
            return deals
    except Exception as e:
        print(f"[Spar] Wogibtswas fehlgeschlagen: {e}")

    print("[Spar] Kein automatisches Scraping erfolgreich – PDF-Upload nötig")
    return []


def _scrape_spar_api() -> list:
    """Spar nutzt eine eigene API für ihre Online-Shop Aktionen."""
    headers = {
        **SCRAPER_HEADERS,
        "Accept": "application/json",
    }

    api_urls = [
        # Spar Online-Shop API
        "https://www.spar.at/api/offers",
        "https://www.spar.at/api/aktionen",
        "https://www.interspar.at/api/offers",
        # Spar verwendet manchmal einen ElasticSearch Endpunkt
        "https://www.spar.at/search-api/search/search?category=aktionen&pageSize=60",
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
            deals = _parse_spar_json(data)
            if deals:
                return deals
        except Exception:
            continue

    return []


def _parse_spar_json(data) -> list:
    deals = []
    items = []

    if isinstance(data, list):
        items = data
    elif isinstance(data, dict):
        for key in ("results", "products", "offers", "items", "data", "hits"):
            val = data.get(key)
            if isinstance(val, list) and val:
                items = val
                break
            elif isinstance(val, dict):
                inner = val.get("hits") or val.get("items", [])
                if inner:
                    items = inner
                    break

    for item in items[:60]:
        name = (item.get("name") or item.get("title") or
                item.get("productName") or item.get("articleName", ""))
        price_data = item.get("price") or {}
        if isinstance(price_data, dict):
            price = price_data.get("value") or price_data.get("final") or price_data.get("sales")
            orig = price_data.get("original") or price_data.get("regular")
        else:
            price = price_data
            orig = item.get("normalPrice") or item.get("regularPrice")

        desc = item.get("description") or item.get("subtitle", "")
        disc_label = item.get("badge") or item.get("promotionLabel", "")

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


def _scrape_spar_direct() -> list:
    urls_to_try = [
        "https://www.spar.at/angebote",
        "https://www.interspar.at/angebote",
        "https://www.spar.at/aktionen",
    ]

    for url in urls_to_try:
        try:
            resp = requests.get(url, headers=SCRAPER_HEADERS, timeout=SCRAPER_TIMEOUT)
            if resp.status_code != 200:
                continue
            soup = BeautifulSoup(resp.text, "lxml")
            deals = []

            for selector in [
                ".offer-item", ".product-item", ".article-item",
                "[class*='offer']", "[class*='product']", ".aktion"
            ]:
                items = soup.select(selector)
                if not items:
                    continue
                for item in items[:50]:
                    name_el = item.select_one(
                        "h3, h2, .name, .title, [class*='name'], [class*='title']"
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
                    return deals
        except Exception:
            continue

    return []
