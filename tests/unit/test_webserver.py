from unittest import TestCase
from contracting.webserver import app


class TestTimedelta(TestCase):
    def test_ping_api(self):
       _, response = app.test_client.get('/')
       self.assertEqual(response.status, 418)

    def test_get_all_contracts(self):
        _, response = app.test_client.get('/contracts')
        contracts = response.json.get('contracts')
        self.assertIn('submission', contracts)