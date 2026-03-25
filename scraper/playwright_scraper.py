"""
Playwright-basierter Scraper für Hofer, Spar und Lidl.
Nutzt einen echten Browser um JavaScript-Seiten zu laden.

Erkenntnisse aus HTML-Analyse:
- Hofer: PLP-Seite mit .plp_product tiles, GDPR via #onetrust-accept-btn-handler
- Spar:  Flugblatt-Seite mit .flyer-teaser__download-item, PDF via flugblatt.spar.at
- Lidl:  GDPR via button 'Akzeptieren', Angebote-Seite
"""
import asyncio
import re
import json
import os
import tempfile
import requests as _requests
from datetime import date, timedelta
from playwright.async_api import async_playwright, TimeoutError as PWTimeout

from scraper.hofer import _categorize, _parse_price


def _make_deal(supermarket, product_name, description="", price=None,
               original_price=None, discount_pct=None, discount_label="",
               category="sonstiges"):
    today = date.today()
    valid_from = (today - timedelta(days=today.weekday())).isoformat()
    valid_to = (today + timedelta(days=6 - today.weekday())).isoformat()
    return {
        "supermarket": supermarket,
        "product_name": str(product_name).strip()[:120],
        "description": str(description).strip()[:200],
        "price": price,
        "original_price": original_price,
        "discount_pct": discount_pct,
        "discount_label": str(discount_label),
        "category": category,
        "valid_from": valid_from,
        "valid_to": valid_to,
    }


async def _accept_gdpr(page):
    """Versucht GDPR-Banner zu schließen."""
    for selector in [
        "#onetrust-accept-btn-handler",
        "button:has-text(\"Alle bestätigen\")",
        "button:has-text(\"Akzeptieren\")",
        "button:has-text(\"Alle akzeptieren\")",
        ".ot-btn-container button:first-child",
        "[data-id='accept-recommended-btn-handler']",
    ]:
        try:
            btn = await page.query_selector(selector)
            if btn and await btn.is_visible():
                await btn.click()
                await asyncio.sleep(2)
                return True
        except Exception:
            pass
    return False


# ─── HOFER ────────────────────────────────────────────────────────────────────

async def _scrape_hofer_pw(page) -> list:
    """
    Nutzt die Hofer PLP-Seite (Angebote-Übersicht).
    Selektoren: .plp_product, .product-title, .at-product-price_lbl
    """
    deals = []
    url = "https://www.hofer.at/de/angebote/angebote-im-ueberblick.html?productState=In+der+Filiale+erh%C3%A4ltlich"
    await page.goto(url, wait_until="domcontentloaded", timeout=35000)
    await asyncio.sleep(3)
    await _accept_gdpr(page)
    await asyncio.sleep(3)

    # Scrollen für lazy-loaded Inhalte
    for _ in range(3):
        await page.evaluate("window.scrollBy(0, 1200)")
        await asyncio.sleep(1)

    from bs4 import BeautifulSoup
    html = await page.content()
    soup = BeautifulSoup(html, "lxml")

    items = soup.select(".plp_product")
    print(f"[Hofer PW] {len(items)} Produkte gefunden")

    for item in items:
        try:
            name_el = item.select_one(".product-title, h2[class*='product'], h3[class*='product']")
            price_el = item.select_one(".at-product-price_lbl, .price.at-product-price_lbl")
            orig_el = item.select_one("del, .price_before del, span.price_before del")

            if not name_el:
                continue
            name = name_el.get_text(strip=True)
            if len(name) < 3:
                continue

            price_text = price_el.get_text(strip=True) if price_el else ""
            orig_text = orig_el.get_text(strip=True) if orig_el else ""
            price = _parse_price(price_text)
            orig_price = _parse_price(orig_text)

            disc_pct = None
            if price and orig_price and orig_price > price:
                disc_pct = round((1 - price / orig_price) * 100)

            deals.append(_make_deal(
                supermarket="Hofer",
                product_name=name,
                price=price,
                original_price=orig_price,
                discount_pct=disc_pct,
                discount_label=f"-{disc_pct}%" if disc_pct else "",
                category=_categorize(name),
            ))
        except Exception:
            continue

    return _deduplicate(deals)


# ─── SPAR ─────────────────────────────────────────────────────────────────────

async def _scrape_spar_pw(page) -> list:
    """
    Spar: Lädt die Flugblatt-Seite, findet die aktuellen Flugblatt-IDs
    und parst die PDF-Seiten via flugblatt.spar.at.
    """
    deals = []

    # Lade Flyer-Liste für Wien
    await page.goto("https://www.spar.at/aktionen/wien", wait_until="networkidle", timeout=35000)
    await asyncio.sleep(3)
    await _accept_gdpr(page)
    await asyncio.sleep(2)

    from bs4 import BeautifulSoup
    html = await page.content()

    # Extrahiere Flyer-IDs aus flugblatt.spar.at URLs
    flyer_urls = re.findall(
        r'https://flugblatt\.spar\.at/(wien|niederoesterreich|oberoesterreich)/spar/([^/\"\']+)/',
        html
    )
    print(f"[Spar PW] {len(flyer_urls)} Flyer-URLs gefunden")

    if not flyer_urls:
        # Fallback: aus HTML-Seite nach aktuellstem KW-Flugblatt suchen
        flyer_urls_raw = re.findall(r'flugblatt\.spar\.at[^\s\"\'<>]+', html)
        print(f"[Spar PW] Fallback flyer URLs: {flyer_urls_raw[:3]}")
        return []

    # Nimm Wien-Flyer mit höchstem Datum (aktuellstes)
    wien_flyers = [(r, fid) for r, fid in flyer_urls if r == "wien" and "flugblatt" in fid.lower()]
    all_flyers = [(r, fid) for r, fid in flyer_urls]

    # Priorisiere "flugblatt-kw" über "obst-gemuse"
    main_flyers = [(r, fid) for r, fid in all_flyers if "flugblatt" in fid.lower() and "obst" not in fid.lower()]
    target = main_flyers[:1] or all_flyers[:1]

    seen_ids = set()
    for region, flyer_id in target[:2]:
        if flyer_id in seen_ids:
            continue
        seen_ids.add(flyer_id)

        # Versuche PDF-Download
        pdf_url = f"https://flugblatt.spar.at/{region}/spar/{flyer_id}/Flugblatt.pdf"
        try:
            r = _requests.get(pdf_url, headers={
                "User-Agent": "Mozilla/5.0",
                "Referer": "https://www.spar.at/",
            }, timeout=30, stream=True)

            if r.status_code == 200 and "pdf" in r.headers.get("content-type", "").lower():
                with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        f.write(chunk)
                    tmp_path = f.name
                from scraper.manager import parse_pdf_deals
                pdf_deals = parse_pdf_deals(tmp_path, "Spar")
                os.unlink(tmp_path)
                if pdf_deals:
                    deals.extend(pdf_deals)
                    print(f"[Spar PW] {len(pdf_deals)} Deals aus PDF {flyer_id}")
                    break
        except Exception as e:
            print(f"[Spar PW] PDF-Download fehlgeschlagen ({flyer_id}): {e}")

    if not deals:
        # Fallback: Spar Online-Shop Angebote-Seite
        deals = await _scrape_spar_shop(page)

    return _deduplicate(deals)


async def _scrape_spar_shop(page) -> list:
    """Fallback: Spar Online-Shop Angebote-Seite scrapen."""
    deals = []
    try:
        await page.goto("https://www.spar.at/angebote", wait_until="domcontentloaded", timeout=25000)
        await asyncio.sleep(3)
        await _accept_gdpr(page)
        await asyncio.sleep(3)
        await page.evaluate("window.scrollBy(0, 1500)")
        await asyncio.sleep(2)

        from bs4 import BeautifulSoup
        html = await page.content()
        soup = BeautifulSoup(html, "lxml")

        for sel in [".product-item", ".offer-item", "[class*='product']", "article"]:
            items = soup.select(sel)
            if len(items) < 3:
                continue
            for item in items[:60]:
                name_el = item.select_one("h2, h3, .name, [class*='name'], [class*='title']")
                price_el = item.select_one("[class*='price'], .preis")
                if not name_el:
                    continue
                name = name_el.get_text(strip=True)
                if len(name) < 3:
                    continue
                price = _parse_price(price_el.get_text() if price_el else "")
                deals.append(_make_deal("Spar", name, price=price, category=_categorize(name)))
            if deals:
                break
    except Exception as e:
        print(f"[Spar PW] Shop fallback fehlgeschlagen: {e}")
    return deals


# ─── LIDL ─────────────────────────────────────────────────────────────────────

async def _scrape_lidl_pw(page) -> list:
    """
    Lidl: Navigiert zur Angebote-Seite nach GDPR-Accept.
    """
    deals = []

    # Bekannte Lidl-API direkt versuchen
    api_url = "https://www.lidl.at/api/publication/v2/publications?countryCode=AT&locale=de_AT"
    try:
        r = _requests.get(api_url, headers={
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
            "Accept": "application/json",
        }, timeout=10)
        if r.status_code == 200 and "json" in r.headers.get("content-type", ""):
            data = r.json()
            pubs = data if isinstance(data, list) else data.get("publications", data.get("data", []))
            for pub in (pubs[:3] if isinstance(pubs, list) else []):
                pdf_url = pub.get("pdfUrl") or pub.get("downloadUrl") or pub.get("pdf")
                if pdf_url:
                    try:
                        pr = _requests.get(pdf_url, headers={"User-Agent": "Mozilla/5.0"}, timeout=30, stream=True)
                        if pr.status_code == 200:
                            with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
                                for chunk in pr.iter_content(chunk_size=8192):
                                    f.write(chunk)
                                tmp_path = f.name
                            from scraper.manager import parse_pdf_deals
                            pdf_deals = parse_pdf_deals(tmp_path, "Lidl")
                            os.unlink(tmp_path)
                            if pdf_deals:
                                deals.extend(pdf_deals)
                                print(f"[Lidl PW] {len(pdf_deals)} Deals aus API-PDF")
                                return _deduplicate(deals)
                    except Exception:
                        pass
    except Exception:
        pass

    # Playwright: Angebote-Seite laden
    await page.goto("https://www.lidl.at/c/lebensmittel-angebote/a10090330", wait_until="domcontentloaded", timeout=35000)
    await asyncio.sleep(3)

    # GDPR akzeptieren
    for selector in [
        "button:has-text(\"Akzeptieren\")",
        "button:has-text(\"Alle akzeptieren\")",
        "#onetrust-accept-btn-handler",
    ]:
        try:
            btn = await page.query_selector(selector)
            if btn and await btn.is_visible():
                await btn.click()
                await asyncio.sleep(3)
                break
        except Exception:
            pass

    # Scrollen
    for _ in range(4):
        await page.evaluate("window.scrollBy(0, 1500)")
        await asyncio.sleep(1)

    from bs4 import BeautifulSoup
    html = await page.content()
    soup = BeautifulSoup(html, "lxml")

    for sel in [
        ".n-product-card", ".product-grid-item", ".product-item",
        "[class*='product-card']", "[data-testid*='product']",
        ".ribbon-offer", "article.product",
    ]:
        items = soup.select(sel)
        if len(items) < 3:
            continue
        print(f"[Lidl PW] {len(items)} Produkte mit Selektor {sel!r}")
        for item in items[:60]:
            name_el = item.select_one(
                ".product-title, h3, h2, [class*='title'], [class*='name']"
            )
            price_el = item.select_one(
                ".m-price__price, .price-box, [class*='price']"
            )
            orig_el = item.select_one("[class*='rrp'], [class*='original'], del, s")
            if not name_el:
                continue
            name = name_el.get_text(strip=True)
            if len(name) < 3:
                continue
            price = _parse_price(price_el.get_text() if price_el else "")
            orig_price = _parse_price(orig_el.get_text() if orig_el else "")
            disc_pct = None
            if price and orig_price and orig_price > price:
                disc_pct = round((1 - price / orig_price) * 100)
            deals.append(_make_deal(
                "Lidl", name, price=price, original_price=orig_price,
                discount_pct=disc_pct,
                discount_label=f"-{disc_pct}%" if disc_pct else "",
                category=_categorize(name),
            ))
        if deals:
            break

    return _deduplicate(deals)


# ─── HILFSFUNKTIONEN ──────────────────────────────────────────────────────────

def _deduplicate(deals: list) -> list:
    seen = set()
    result = []
    for d in deals:
        key = d["product_name"].lower()[:30]
        if key not in seen:
            seen.add(key)
            result.append(d)
    return result


# ─── SYNC WRAPPER ─────────────────────────────────────────────────────────────

def scrape_with_playwright(market: str) -> list:
    """
    Synchroner Wrapper für Playwright-Scraping.
    Startet einen Headless-Browser und scrapt den angegebenen Markt.
    """
    async def _run():
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                viewport={"width": 1280, "height": 900},
                user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
                locale="de-AT",
                extra_http_headers={"Accept-Language": "de-AT,de;q=0.9"},
            )
            page = await context.new_page()

            try:
                if market == "Hofer":
                    return await _scrape_hofer_pw(page)
                elif market == "Spar":
                    return await _scrape_spar_pw(page)
                elif market == "Lidl":
                    return await _scrape_lidl_pw(page)
                else:
                    return []
            except PWTimeout:
                print(f"[{market}] Playwright Timeout")
                return []
            except Exception as e:
                print(f"[{market}] Playwright Fehler: {e}")
                return []
            finally:
                await browser.close()

    try:
        return asyncio.run(_run())
    except Exception as e:
        print(f"[{market}] asyncio.run Fehler: {e}")
        return []
