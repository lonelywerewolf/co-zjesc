"""
Pobiera z Open Food Facts produkty spożywcze sprzedawane w Polsce
w wybranych sieciach i zapisuje je do data/off/<sklep>.json.

Uruchamiane automatycznie przez GitHub Actions (.github/workflows/import-products.yml).
Lokalnie: python scripts/import_off.py [lidl biedronka ...]

Open Food Facts limituje wyszukiwanie do ok. 10 zapytań na minutę,
dlatego między stronami jest przerwa.
"""

from __future__ import annotations

import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

API = "https://world.openfoodfacts.org/api/v2/search"
USER_AGENT = "co-zjesc/0.1 (projekt prywatny, github)"
PAGE_SIZE = 100
MAX_PAGES = 30
PAUSE_S = 7

FIELDS = ",".join([
    "code", "product_name", "product_name_pl", "brands", "quantity",
    "product_quantity", "categories_tags", "stores_tags", "nutriments",
])

STORES = {
    "lidl": "lidl",
    "biedronka": "biedronka",
    "dino": "dino",
    "zabka": "zabka",
    "intermarche": "intermarche",
}

OUT_DIR = Path(__file__).resolve().parent.parent / "data" / "off"


def _num(value) -> float | None:
    try:
        return round(float(value), 1)
    except (TypeError, ValueError):
        return None


def normalize(raw: dict) -> dict | None:
    """Zamienia surowy rekord OFF na nasz format. Zwraca None, jeśli rekord bezużyteczny."""
    name = (raw.get("product_name_pl") or raw.get("product_name") or "").strip()
    code = str(raw.get("code") or "").strip()
    n = raw.get("nutriments") or {}
    kcal = _num(n.get("energy-kcal_100g"))
    if not name or not code or kcal is None:
        return None
    return {
        "barcode": code,
        "name": name,
        "brand": (raw.get("brands") or "").split(",")[0].strip() or None,
        "quantity": raw.get("quantity") or None,
        "package_g": _num(raw.get("product_quantity")),
        "kcal": kcal,
        "protein_g": _num(n.get("proteins_100g")),
        "fat_g": _num(n.get("fat_100g")),
        "carbs_g": _num(n.get("carbohydrates_100g")),
        "fiber_g": _num(n.get("fiber_100g")),
        "salt_g": _num(n.get("salt_100g")),
        "categories": [c for c in raw.get("categories_tags") or [] if c.startswith("en:")][:8],
    }


RETRY_STATUSES = {429, 500, 502, 503, 504}
RETRY_DELAYS_S = [15, 30, 60, 120, 240]  # Open Food Facts bywa chwilowo przeciążony

_sleep = time.sleep  # podmieniane w testach


def _get_json(url: str) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.load(resp)


def fetch_page(store_tag: str, page: int, get_json=_get_json) -> dict:
    params = urllib.parse.urlencode({
        "countries_tags_en": "poland",
        "stores_tags": store_tag,
        "fields": FIELDS,
        "page_size": PAGE_SIZE,
        "page": page,
        "sort_by": "unique_scans_n",  # najpierw najczęściej skanowane = najpopularniejsze
    })
    url = f"{API}?{params}"
    for attempt, delay in enumerate([*RETRY_DELAYS_S, None], start=1):
        try:
            return get_json(url)
        except urllib.error.HTTPError as err:
            if err.code not in RETRY_STATUSES or delay is None:
                raise
            retry_after = err.headers.get("Retry-After") if err.headers else None
            wait = int(retry_after) if retry_after and retry_after.isdigit() else delay
            print(f"  HTTP {err.code}, próba {attempt}, czekam {wait} s")
        except (urllib.error.URLError, TimeoutError) as err:
            if delay is None:
                raise
            wait = delay
            print(f"  błąd sieci ({err}), próba {attempt}, czekam {wait} s")
        _sleep(wait)
    raise RuntimeError("nieosiągalne")


def load_existing(slug: str) -> dict[str, dict]:
    path = OUT_DIR / f"{slug}.json"
    if not path.exists():
        return {}
    return {p["barcode"]: p for p in json.loads(path.read_text(encoding="utf-8"))}


def import_store(slug: str, get_json=_get_json) -> tuple[int, bool]:
    """Zwraca (liczba produktów w pliku, czy pobrano wszystkie strony)."""
    tag = STORES[slug]
    # Startujemy od poprzednich danych: przerwany import niczego nie usuwa.
    products = load_existing(slug)
    complete = True
    for page in range(1, MAX_PAGES + 1):
        try:
            data = fetch_page(tag, page, get_json)
        except Exception as err:  # noqa: BLE001 - zapisujemy to, co już mamy
            print(f"! {slug}: przerwano na stronie {page}: {err}")
            complete = False
            break
        batch = data.get("products") or []
        for raw in batch:
            item = normalize(raw)
            if item:
                products[item["barcode"]] = item
        print(f"{slug}: strona {page}, razem {len(products)}")
        if len(batch) < PAGE_SIZE:
            break
        _sleep(PAUSE_S)

    if products:
        OUT_DIR.mkdir(parents=True, exist_ok=True)
        out = OUT_DIR / f"{slug}.json"
        ordered = sorted(products.values(), key=lambda p: p["name"].lower())
        out.write_text(json.dumps(ordered, ensure_ascii=False, indent=1), encoding="utf-8")
    return len(products), complete


def main(argv: list[str]) -> None:
    slugs = argv or list(STORES)
    for slug in slugs:
        if slug not in STORES:
            sys.exit(f"Nieznany sklep: {slug}. Dostępne: {', '.join(STORES)}")
    total = 0
    for i, slug in enumerate(slugs):
        count, complete = import_store(slug)
        total += count
        mark = "✓" if complete else "~"
        note = "" if complete else " (niepełny, dokończy się przy następnym uruchomieniu)"
        print(f"{mark} {slug}: zapisano {count} produktów{note}")
        if i < len(slugs) - 1:
            _sleep(PAUSE_S)
    if total == 0:
        sys.exit("Nie udało się pobrać żadnych produktów.")


if __name__ == "__main__":
    main(sys.argv[1:])
