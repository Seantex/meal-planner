"""
Scraper Manager – orchestriert alle Supermarkt-Scraper
und verwaltet den PDF-Upload-Fallback.
"""
import pdfplumber
import re
import os
import tempfile
import requests
from bs4 import BeautifulSoup
from datetime import date, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urljoin

from scraper.hofer import scrape_hofer
from scraper.lidl import scrape_lidl
from scraper.billa import scrape_billa
from scraper.spar import scrape_spar
from scraper.hofer import _categorize
from scraper.aggregator import scrape_via_aggregator
from scraper.playwright_scraper import scrape_with_playwright
from config import SCRAPER_HEADERS

# Bekannte Flugblatt-URLs der österreichischen Supermärkte
FLYER_URLS = {
    "Billa": "https://www.billa.at/unsere-aktionen/flugblatt",
    "Hofer": "https://www.hofer.at/de/angebote/aktuelle-flugblaetter-und-broschuren.html",
    "Spar":  "https://www.spar.at/aktionen/wien",
    "Lidl":  "https://www.lidl.at/c/flugblatt/s10012330",
}


def try_download_pdf_from_web(supermarket: str) -> list:
    """
    Versucht, das Flugblatt-PDF direkt von der Supermarkt-Website zu laden.
    Sucht nach PDF-Links auf der bekannten Flugblatt-Seite.
    """
    page_url = FLYER_URLS.get(supermarket)
    if not page_url:
        return []

    headers = {**SCRAPER_HEADERS, "Referer": page_url}

    pdf_url = None

    # Sonderfall Lidl: JSON-API versuchen
    if supermarket == "Lidl":
        pdf_url = _find_lidl_pdf_url()

    # Seite laden und nach PDF-Links suchen
    if not pdf_url:
        try:
            resp = requests.get(page_url, headers=headers, timeout=20)
            resp.raise_for_status()
            html = resp.text
            soup = BeautifulSoup(html, "lxml")

            # 1) Direkte PDF-Links in <a>, <iframe>, <embed>
            for tag in soup.find_all(["a", "iframe", "embed", "object"]):
                src = (tag.get("href") or tag.get("src") or tag.get("data") or "").strip()
                if ".pdf" in src.lower():
                    pdf_url = src if src.startswith("http") else urljoin(page_url, src)
                    break

            # 2) Script-Tags nach PDF-URLs durchsuchen
            if not pdf_url:
                for match in re.finditer(r'https?://[^"\'\\s]+\.pdf', html):
                    pdf_url = match.group(0)
                    break

            # 3) data-Attribute
            if not pdf_url:
                for tag in soup.find_all(attrs={"data-pdf": True}):
                    pdf_url = tag["data-pdf"]
                    if not pdf_url.startswith("http"):
                        pdf_url = urljoin(page_url, pdf_url)
                    break

        except Exception as e:
            print(f"[{supermarket}] Seite konnte nicht geladen werden: {e}")
            return []

    if not pdf_url:
        print(f"[{supermarket}] Keine PDF-URL auf der Flugblatt-Seite gefunden")
        return []

    # PDF herunterladen
    print(f"[{supermarket}] Lade PDF von: {pdf_url[:80]}…")
    try:
        pdf_resp = requests.get(pdf_url, headers=headers, timeout=60, stream=True)
        pdf_resp.raise_for_status()

        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            for chunk in pdf_resp.iter_content(chunk_size=8192):
                f.write(chunk)
            tmp_path = f.name

        deals = parse_pdf_deals(tmp_path, supermarket)
        os.unlink(tmp_path)
        print(f"[{supermarket}] {len(deals)} Angebote aus Web-PDF geladen")
        return deals

    except Exception as e:
        print(f"[{supermarket}] PDF-Download fehlgeschlagen: {e}")
        return []


def _find_lidl_pdf_url() -> str:
    """Lidl AT hat eine bekannte Publikations-API."""
    try:
        endpoints = [
            "https://www.lidl.at/api/publication/v2/publications?countryCode=AT",
            "https://www.lidl.at/api/flyer",
        ]
        for url in endpoints:
            resp = requests.get(url, headers=SCRAPER_HEADERS, timeout=10)
            if resp.status_code != 200:
                continue
            data = resp.json()
            pubs = data if isinstance(data, list) else data.get("publications", data.get("data", []))
            for pub in (pubs[:5] if isinstance(pubs, list) else []):
                for key in ("pdfUrl", "downloadUrl", "pdf", "fileUrl"):
                    if pub.get(key):
                        return pub[key]
    except Exception:
        pass
    return None


def scrape_all_deals() -> tuple:
    """
    Führt alle Scraper parallel aus.
    Fallback: PDF-Download von den bekannten Flugblatt-Seiten.
    Gibt (deals, failed_markets) zurück.
    """
    scrapers = {
        "Hofer": scrape_hofer,
        "Lidl":  scrape_lidl,
        "Billa": scrape_billa,
        "Spar":  scrape_spar,
    }

    all_deals = []
    html_failed = []

    # Runde 1: HTML-Scraping
    with ThreadPoolExecutor(max_workers=4) as ex:
        futures = {ex.submit(fn): name for name, fn in scrapers.items()}
        for future in as_completed(futures):
            name = futures[future]
            try:
                result = future.result()
                if result:
                    all_deals.extend(result)
                else:
                    html_failed.append(name)
            except Exception as e:
                print(f"[{name}] HTML-Scraping Fehler: {e}")
                html_failed.append(name)

    # Runde 2: Playwright (Headless-Browser für JS-Seiten)
    pw_failed = []
    if html_failed:
        print(f"[Scraper] HTML fehlgeschlagen für {html_failed}, versuche Playwright-Browser…")
        # Playwright sequenziell (jeder startet eigenen Browser)
        for name in html_failed:
            try:
                result = scrape_with_playwright(name)
                if result:
                    all_deals.extend(result)
                    print(f"[{name}] Playwright: {len(result)} Angebote geladen")
                else:
                    pw_failed.append(name)
            except Exception as e:
                print(f"[{name}] Playwright Fehler: {e}")
                pw_failed.append(name)

    # Runde 3: Aggregator-Websites (angebote.at, wogibtswas.at etc.)
    aggr_failed = []
    if pw_failed:
        print(f"[Scraper] Playwright fehlgeschlagen für {pw_failed}, versuche Aggregatoren…")
        with ThreadPoolExecutor(max_workers=4) as ex:
            futures = {ex.submit(scrape_via_aggregator, name): name for name in pw_failed}
            for future in as_completed(futures):
                name = futures[future]
                try:
                    result = future.result()
                    if result:
                        all_deals.extend(result)
                    else:
                        aggr_failed.append(name)
                except Exception as e:
                    print(f"[{name}] Aggregator Fehler: {e}")
                    aggr_failed.append(name)

    # Runde 4: Für restliche Märkte → PDF-Download von Website
    still_failed = []
    if aggr_failed:
        print(f"[Scraper] Aggregatoren fehlgeschlagen für {aggr_failed}, versuche Web-PDF…")
        with ThreadPoolExecutor(max_workers=4) as ex:
            futures = {ex.submit(try_download_pdf_from_web, name): name for name in aggr_failed}
            for future in as_completed(futures):
                name = futures[future]
                try:
                    result = future.result()
                    if result:
                        all_deals.extend(result)
                        print(f"[{name}] Web-PDF Fallback erfolgreich: {len(result)} Deals")
                    else:
                        still_failed.append(name)
                except Exception as e:
                    print(f"[{name}] Web-PDF Fehler: {e}")
                    still_failed.append(name)

    return all_deals, still_failed


def parse_pdf_deals(pdf_path: str, supermarket: str) -> list:
    """
    Liest ein Supermarkt-Prospekt-PDF aus und extrahiert Angebote.
    Nutzt pdfplumber für Textextraktion.
    """
    deals = []
    today = date.today()
    valid_from = (today - timedelta(days=today.weekday())).isoformat()
    valid_to = (today + timedelta(days=6 - today.weekday())).isoformat()

    try:
        with pdfplumber.open(pdf_path) as pdf:
            full_text = ""
            for page in pdf.pages:
                full_text += (page.extract_text() or "") + "\n"

        # Muster für Preise: "€ 2,99" oder "2.99" oder "statt 4,99"
        price_pattern = re.compile(r"(?:€\s*)?(\d+[,\.]\d{2})")
        discount_pattern = re.compile(r"(-?\d+)\s*%|statt\s+(\d+[,\.]\d{2})")

        lines = [l.strip() for l in full_text.split("\n") if l.strip()]

        i = 0
        while i < len(lines):
            line = lines[i]

            # Preis in dieser Zeile?
            prices = price_pattern.findall(line)
            if not prices:
                i += 1
                continue

            # Name ist typisch die Zeile vor dem Preis oder enthält Text vor dem Preis
            name_candidates = re.sub(r"€\s*\d+[,\.]\d{2}.*", "", line).strip()

            # Falls Zeile nur Preis enthält: Name ist vorherige Zeile
            if len(name_candidates) < 3 and i > 0:
                name_candidates = lines[i - 1]

            if len(name_candidates) < 3:
                i += 1
                continue

            # Produktname bereinigen
            name = re.sub(r"[•·\-–|]", "", name_candidates).strip()
            name = re.sub(r"\s+", " ", name).strip()

            if len(name) < 3 or re.match(r"^\d+", name):
                i += 1
                continue

            # Preis parsen
            price_str = prices[0].replace(",", ".")
            price = float(price_str)

            # Rabatt suchen
            disc_pct = None
            orig_price = None
            disc_match = discount_pattern.search(line)
            if not disc_match and i + 1 < len(lines):
                disc_match = discount_pattern.search(lines[i + 1])

            if disc_match:
                if disc_match.group(1):
                    disc_pct = abs(int(disc_match.group(1)))
                elif disc_match.group(2):
                    orig_str = disc_match.group(2).replace(",", ".")
                    orig_price = float(orig_str)
                    if orig_price > price:
                        disc_pct = round((1 - price / orig_price) * 100)

            deals.append({
                "supermarket": supermarket,
                "product_name": name[:100],
                "description": "",
                "price": price,
                "original_price": orig_price,
                "discount_pct": disc_pct,
                "discount_label": f"-{disc_pct}%" if disc_pct else "",
                "category": _categorize(name),
                "valid_from": valid_from,
                "valid_to": valid_to,
            })

            i += 1

    except Exception as e:
        print(f"[PDF] Fehler beim Lesen von {pdf_path}: {e}")

    # Deduplizieren
    seen = set()
    unique = []
    for d in deals:
        key = d["product_name"].lower()[:30]
        if key not in seen:
            seen.add(key)
            unique.append(d)

    return unique
