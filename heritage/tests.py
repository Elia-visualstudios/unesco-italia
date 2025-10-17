from django.test import TestCase
from heritage.models import Categoria, Accessibilita, Sito

class APITests(TestCase):
    def setUp(self):
        cat = Categoria.objects.create(nome="Culturale")
        acc = Accessibilita.objects.create(sedia_a_rotelle=True)
        Sito.objects.create(
            nome="Centro Storico",
            regione="Lazio", citta="Roma",
            latitudine=41.9, longitudine=12.49,
            categoria=cat, accessibilita=acc,
            unesco_id="TEST1"
        )
    def test_sites_geojson(self):
        r = self.client.get("/api/sites.geojson", {"accessibile": "1"})
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertEqual(data["type"], "FeatureCollection")
        self.assertTrue(data["features"])
        self.assertIn("count",data)

    def test_accessibility_any_mode(client, db, sito_factory, acc_factory):
     a1 = acc_factory(sedia_a_rotelle=True, ausili_visivi=None, supporto_uditivo=None)
     s1 = sito_factory(accessibilita=a1)
     res = client.get("/api/sites.geojson?wheelchair=1&acc_mode=any")
     assert res.status_code == 200
     data = res.json()
     assert data["count"] >= 1
