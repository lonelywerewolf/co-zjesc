import unittest

from import_off import normalize


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
