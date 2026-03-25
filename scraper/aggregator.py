"""
Aggregator-Scraper für österreichische Supermarkt-Angebote.
Nutzt angebote.at und wogibtswas.at als Fallback-Quellen.
"""
import requests
import re
import json
from bs4 import BeautifulSoup
from datetime import date, timedelta
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from config import SCRAPER_HEADERS, SCRAPER_TIMEOUT
from scraper.hofer import _categorize, _parse_price

# Markt-Slugs für verschiedene Aggregatoren
MARKET_SLUGS = {
    "Hofer": {
        "angebote_at":  "hofer",
        "wogibtswas":   "hofer-oesterreich",
        "meinprospekt": "hofer",
        "marktjagd":    "hofer",
    },
    "Spar": {
        "angebote_at":  "spar",
        "wogibtswas":   "spar",
        "meinprospekt": "spar",
        "marktjagd":    "spar",
    },
    "Lidl": {
        "angebote_at":  "lidl",
        "wogibtswas":   "lidl",
        "meinprospekt": "lidl",
        "marktjagd":    "lidl",
    },
    "Billa": {
        "angebote_at":  "billa",
        "wogibtswas":   "billa",
        "meinprospekt": "billa",
        "marktjagd":    "billa",
    },
}


def _make_deal(supermarket, product_name, description="", price=None,
               original_price=None, discount_pct=None, discount_label="",
               category="sonstiges"):
    today = date.today()
    valid_from = (today - timedelta(days=today.weekday())).isoformat()
    valid_to = (today + timedelta(days=6 - today.weekday())).isoformat()
    return {
        "supermarket": supermarket,
        "product_name": product_name.strip()[:120],
        "description": description.strip()[:200],
        "price": price,
        "original_price": original_price,
        "discount_pct": discount_pct,
        "discount_label": discount_label,
        "category": category,
        "valid_from": valid_from,
        "valid_to": valid_to,
    }


def scrape_via_aggregator(supermarket: str) -> list:
    """
    Versucht Angebote über verschiedene Aggregator-Websites zu laden.
    Gibt eine Liste von Deal-Dicts zurück.
    """
    slugs = MARKET_SLUGS.get(supermarket, {})

    # Strategie 1: angebote.at
    slug = slugs.get("angebote_at", supermarket.lower())
    deals = _try_angebote_at(supermarket, slug)
    if deals:
        print(f"[{supermarket}] {len(deals)} Angebote von angebote.at geladen")
        return deals

    # Strategie 2: wogibtswas.at (korrekte Slug-Namen)
    slug = slugs.get("wogibtswas", supermarket.lower())
    deals = _try_wogibtswas_at(supermarket, slug)
    if deals:
        print(f"[{supermarket}] {len(deals)} Angebote von wogibtswas.at geladen")
        return deals

    # Strategie 3: marktjagd.at
    slug = slugs.get("marktjagd", supermarket.lower())
    deals = _try_marktjagd_at(supermarket, slug)
    if deals:
        print(f"[{supermarket}] {len(deals)} Angebote von marktjagd.at geladen")
        return deals

    # Strategie 4: Direkte JSON-LD in Supermarkt-Seite
    deals = _try_json_ld(supermarket)
    if deals:
        print(f"[{supermarket}] {len(deals)} Angebote via JSON-LD geladen")
        return deals

    print(f"[{supermarket}] Alle Aggregator-Quellen gescheitert")
    return []


def _try_angebote_at(supermarket: str, slug: str) -> list:
    """angebote.at – österreichischer Angebots-Aggregator"""
    urls = [
        f"https://www.angebote.at/supermarkt/{slug}/",
        f"https://www.angebote.at/{slug}/",
    ]
    headers = {
        **SCRAPER_HEADERS,
        "Referer": "https://www.angebote.at/",
        "Accept-Language": "de-AT,de;q=0.9",
    }
    for url in urls:
        try:
            resp = requests.get(url, headers=headers, timeout=SCRAPER_TIMEOUT)
            if resp.status_code != 200:
                continue
            soup = BeautifulSoup(resp.text, "lxml")
            deals = _extract_deals_generic(soup, supermarket)
            if deals:
                return deals
        except Exception as e:
            print(f"[{supermarket}] angebote.at Fehler: {e}")
    return []


def _try_wogibtswas_at(supermarket: str, slug: str) -> list:
    """wogibtswas.at – österreichischer Angebots-Aggregator mit korrekten Slugs"""
    urls = [
        f"https://www.wogibtswas.at/supermaerkte/{slug}/angebote",
        f"https://www.wogibtswas.at/supermaerkte/{slug}",
        f"https://www.wogibtswas.at/markt/{slug}/angebote",
    ]
    headers = {
        **SCRAPER_HEADERS,
        "Referer": "https://www.wogibtswas.at/",
        "Accept-Language": "de-AT,de;q=0.9",
    }
    for url in urls:
        try:
            resp = requests.get(url, headers=headers, timeout=SCRAPER_TIMEOUT)
            if resp.status_code != 200:
                continue
            soup = BeautifulSoup(resp.text, "lxml")
            deals = []

            # wogibtswas.at spezifische Selektoren
            for selector in [
                "article.product", ".product-card", ".offer-card",
                ".deal-item", "[class*='ProductItem']", "[class*='product-item']",
                ".angebot", "li.item",
            ]:
                items = soup.select(selector)
                if not items:
                    continue
                for item in items[:60]:
                    name_el = item.select_one(
                        "h2, h3, .name, .title, [class*='name'], [class*='title'], [class*='product']"
                    )
                    price_el = item.select_one(
                        ".price, .preis, [class*='price'], [class*='preis']"
                    )
                    if not name_el:
                        continue
                    name = name_el.get_text(strip=True)
                    if len(name) < 3:
                        continue
                    price = _parse_price(price_el.get_text() if price_el else "")
                    deals.append(_make_deal(
                        supermarket=supermarket,
                        product_name=name,
                        price=price,
                        category=_categorize(name),
                    ))
                if deals:
                    return deals
        except Exception as e:
            print(f"[{supermarket}] wogibtswas.at Fehler ({url}): {e}")
    return []


def _try_marktjagd_at(supermarket: str, slug: str) -> list:
    """marktjagd.at – weiterer österreichischer Aggregator"""
    urls = [
        f"https://www.marktjagd.at/haendler/{slug}/",
        f"https://www.marktjagd.at/{slug}/",
    ]
    headers = {**SCRAPER_HEADERS, "Accept-Language": "de-AT,de;q=0.9"}
    for url in urls:
        try:
            resp = requests.get(url, headers=headers, timeout=SCRAPER_TIMEOUT)
            if resp.status_code != 200:
                continue
            soup = BeautifulSoup(resp.text, "lxml")
            deals = _extract_deals_generic(soup, supermarket)
            if deals:
                return deals
        except Exception:
            pass
    return []


def _try_json_ld(supermarket: str) -> list:
    """Sucht JSON-LD structured data auf der Supermarkt-Startseite."""
    site_urls = {
        "Hofer": "https://www.hofer.at/de/angebote.html",
        "Spar":  "https://www.spar.at/angebote",
        "Lidl":  "https://www.lidl.at/de/angebote.htm",
        "Billa": "https://www.billa.at/angebote",
    }
    url = site_urls.get(supermarket)
    if not url:
        return []

    try:
        resp = requests.get(url, headers=SCRAPER_HEADERS, timeout=SCRAPER_TIMEOUT)
        if resp.status_code != 200:
            return []
        soup = BeautifulSoup(resp.text, "lxml")
        deals = []

        for script in soup.find_all("script", type="application/ld+json"):
            try:
                data = json.loads(script.string or "")
                items = []
                if isinstance(data, list):
                    items = data
                elif isinstance(data, dict):
                    items = data.get("@graph", [data])

                for item in items:
                    t = item.get("@type", "")
                    if t not in ("Product", "Offer", "ItemList"):
                        continue
                    if t == "ItemList":
                        for el in item.get("itemListElement", []):
                            inner = el.get("item", el)
                            name = inner.get("name", "")
                            if name:
                                deals.append(_make_deal(
                                    supermarket=supermarket,
                                    product_name=name,
                                    category=_categorize(name),
                                ))
                    else:
                        name = item.get("name", "")
                        price_info = item.get("offers", {})
                        price = None
                        if isinstance(price_info, dict):
                            price = price_info.get("price")
                        if name:
                            deals.append(_make_deal(
                                supermarket=supermarket,
                                product_name=name,
                                price=float(price) if price else None,
                                category=_categorize(name),
                            ))
            except Exception:
                continue

        return deals[:60]
    except Exception:
        return []


def _extract_deals_generic(soup: BeautifulSoup, supermarket: str) -> list:
    """Generischer Deal-Extraktor mit vielen möglichen Selektoren."""
    deals = []
    selectors_to_try = [
        ".offer-item", ".product-item", ".angebot-item", ".deal-item",
        "[class*='offer']", "[class*='product']", "[class*='angebot']",
        "article", ".card",
    ]
    for selector in selectors_to_try:
        items = soup.select(selector)
        if not items or len(items) < 3:
            continue
        for item in items[:60]:
            name_el = item.select_one(
                "h2, h3, h4, .name, .title, [class*='name'], [class*='title']"
            )
            price_el = item.select_one(".price, .preis, [class*='price']")
            orig_el = item.select_one(
                ".original-price, .old-price, [class*='original'], [class*='statt'], del"
            )
            if not name_el:
                continue
            name = name_el.get_text(strip=True)
            if len(name) < 3 or len(name) > 150:
                continue
            price = _parse_price(price_el.get_text() if price_el else "")
            orig_price = _parse_price(orig_el.get_text() if orig_el else "")
            disc_pct = None
            if price and orig_price and orig_price > price:
                disc_pct = round((1 - price / orig_price) * 100)
            deals.append(_make_deal(
                supermarket=supermarket,
                product_name=name,
                price=price,
                original_price=orig_price,
                discount_pct=disc_pct,
                category=_categorize(name),
            ))
        if deals:
            return deals
    return []
