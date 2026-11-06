import json
import tempfile
import unittest
import urllib.error
from pathlib import Path

import import_off
from import_off import normalize


def http_error(code):
    return urllib.error.HTTPError("https://x", code, "err", {}, None)


def page(n_products, start=0):
    return {"products": [
        {"code": str(start + i), "product_name": f"P{start + i}",
         "nutriments": {"energy-kcal_100g": 100}}
        for i in range(n_products)
    ]}


class RetryAndPartialTest(unittest.TestCase):
    def setUp(self):
        self.sleeps = []
        self._orig_sleep, self._orig_dir = import_off._sleep, import_off.OUT_DIR
        import_off._sleep = self.sleeps.append
        self.tmp = tempfile.TemporaryDirectory()
        import_off.OUT_DIR = Path(self.tmp.name)

    def tearDown(self):
        import_off._sleep, import_off.OUT_DIR = self._orig_sleep, self._orig_dir
        self.tmp.cleanup()

    def test_retries_on_503_then_succeeds(self):
        calls = iter([http_error(503), http_error(503), page(3)])

        def get_json(_url):
            r = next(calls)
            if isinstance(r, Exception):
                raise r
            return r

        count, complete = import_off.import_store("lidl", get_json)
        self.assertEqual((count, complete), (3, True))
        self.assertEqual(self.sleeps[:2], import_off.RETRY_DELAYS_S[:2])

    def test_does_not_retry_on_404(self):
        def get_json(_url):
            raise http_error(404)

        count, complete = import_off.import_store("lidl", get_json)
        self.assertEqual((count, complete), (0, False))
        self.assertEqual(self.sleeps, [])

    def test_partial_import_keeps_previous_data(self):
        (import_off.OUT_DIR / "lidl.json").write_text(json.dumps(
            [{"barcode": "old", "name": "Stary produkt"}]), encoding="utf-8")
        pages = iter([page(import_off.PAGE_SIZE)])

        def get_json(_url):
            try:
                return next(pages)
            except StopIteration:
                raise http_error(503)

        count, complete = import_off.import_store("lidl", get_json)
        self.assertFalse(complete)
        self.assertEqual(count, import_off.PAGE_SIZE + 1)
        saved = json.loads((import_off.OUT_DIR / "lidl.json").read_text(encoding="utf-8"))
        self.assertIn("old", {p["barcode"] for p in saved})


class NormalizeTest(unittest.TestCase):
    def test_full_record(self):
        raw = {
            "code": "4056489000001",
            "product_name": "Skyr naturalny",
            "brands": "Milbona, Lidl",
            "quantity": "450 g",
            "product_quantity": "450",
            "categories_tags": ["en:dairies", "en:yogurts", "pl:skyr"],
            "nutriments": {
                "energy-kcal_100g": 63,
                "proteins_100g": 11,
                "fat_100g": 0.2,
                "carbohydrates_100g": 4,
                "salt_100g": 0.1,
            },
        }
        p = normalize(raw)
        self.assertEqual(p["brand"], "Milbona")
        self.assertEqual(p["package_g"], 450.0)
        self.assertEqual(p["protein_g"], 11.0)
        self.assertIsNone(p["fiber_g"])
        self.assertEqual(p["categories"], ["en:dairies", "en:yogurts"])

    def test_polish_name_preferred(self):
        raw = {"code": "1", "product_name": "Chicken", "product_name_pl": "Kurczak",
               "nutriments": {"energy-kcal_100g": 106}}
        self.assertEqual(normalize(raw)["name"], "Kurczak")

    def test_skips_without_kcal_or_name(self):
        self.assertIsNone(normalize({"code": "1", "product_name": "X", "nutriments": {}}))
        self.assertIsNone(normalize({"code": "1", "nutriments": {"energy-kcal_100g": 5}}))


if __name__ == "__main__":
    unittest.main()
