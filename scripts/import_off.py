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


def fetch_page(store_tag: str, page: int) -> dict:
    params = urllib.parse.urlencode({
        "countries_tags_en": "poland",
        "stores_tags": store_tag,
        "fields": FIELDS,
        "page_size": PAGE_SIZE,
        "page": page,
        "sort_by": "unique_scans_n",  # najpierw najczęściej skanowane = najpopularniejsze
    })
    req = urllib.request.Request(f"{API}?{params}", headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.load(resp)


def import_store(slug: str) -> int:
    tag = STORES[slug]
    products: dict[str, dict] = {}
    for page in range(1, MAX_PAGES + 1):
        data = fetch_page(tag, page)
        batch = data.get("products") or []
        for raw in batch:
            item = normalize(raw)
            if item:
                products[item["barcode"]] = item
        print(f"{slug}: strona {page}, razem {len(products)}")
        if len(batch) < PAGE_SIZE:
            break
        time.sleep(PAUSE_S)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out = OUT_DIR / f"{slug}.json"
    ordered = sorted(products.values(), key=lambda p: p["name"].lower())
    out.write_text(json.dumps(ordered, ensure_ascii=False, indent=1), encoding="utf-8")
    return len(ordered)


def main(argv: list[str]) -> None:
    slugs = argv or list(STORES)
    for slug in slugs:
        if slug not in STORES:
            sys.exit(f"Nieznany sklep: {slug}. Dostępne: {', '.join(STORES)}")
    for i, slug in enumerate(slugs):
        count = import_store(slug)
        print(f"✓ {slug}: zapisano {count} produktów")
        if i < len(slugs) - 1:
            time.sleep(PAUSE_S)


if __name__ == "__main__":
    main(sys.argv[1:])
