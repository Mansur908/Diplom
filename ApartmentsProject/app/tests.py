from django.test import TestCase

from app.utils import get_avito_data, get_yandex_data, get_house_info, get_price_history, get_price


class TestUtils(TestCase):

    def test_avito(self):
        data = get_avito_data(address="Вишневского 49", area="47", rooms="2", floor="7", floorAtHouse="10")
        self.assertEqual(list(data.keys()), ["min_price", "price", "max_price"])

    def test_yandex(self):
        data = get_yandex_data(address="Вишневского 49", area="47", rooms="2")
        self.assertIsNotNone(data.get("price"))

    def test_domclick_house_info(self):
        data = get_house_info(address="Вишневского 49")
        self.assertIsNotNone(data)

    def test_domclick_price_history(self):
        data = get_price_history(address="Вишневского 49")
        self.assertIsNotNone(data)

    def test_domclick_price(self):
        data = get_price(address="Вишневского 49", area="47", rooms="2")
        self.assertIsNotNone(data.get("market_price"))

