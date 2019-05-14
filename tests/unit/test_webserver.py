from unittest import TestCase
from contracting.webserver import app, client
import json

class TestWebserver(TestCase):
    def tearDown(self):
        client.flush()

    def test_ping_api(self):
        _, response = app.test_client.get('/')
        self.assertEqual(response.status, 418)

    def test_get_all_contracts(self):
        _, response = app.test_client.get('/contracts')
        contracts = response.json.get('contracts')
        self.assertListEqual(['submission'], contracts)

    def test_get_submission_code(self):
        with open('../../contracting/contracts/submission.s.py') as f:
            contract = f.read()

        _, response = app.test_client.get('/contracts/submission')

        code = response.json.get('code')

        self.assertEqual(contract, code)
        self.assertEqual(response.status, 200)

    def test_get_non_existent_contract(self):
        _, response = app.test_client.get('/contracts/hoooooooopla')
        self.assertEqual(response.status, 404)

        error_message = response.json.get('error')

        self.assertEqual(error_message, 'hoooooooopla does not exist')

    def test_get_submission_methods(self):
        _, response = app.test_client.get('/contracts/submission/methods')

        method = 'submit_contract'
        kwargs = ['name', 'code']

        methods = response.json.get('methods')

        self.assertEqual(len(methods), 1)

        test_method = methods[0]

        self.assertEqual(method, test_method.get('name'))
        self.assertListEqual(kwargs, test_method.get('arguments'))
        self.assertEqual(response.status, 200)

    def test_get_non_existent_contract_methods(self):
        _, response = app.test_client.get('/contracts/huuuuuuuuupluh/methods')

        self.assertEqual(response.status, 404)

        error_message = response.json.get('error')

        self.assertEqual(error_message, 'huuuuuuuuupluh does not exist')

    def test_contract_submission_hits_raw_database(self):
        with open('../../contracting/contracts/currency.s.py') as f:
            contract = f.read()

        payload = {'name': 'currency', 'code': contract}

        _, response = app.test_client.post('/submit', data=json.dumps(payload))

        self.assertEqual(response.status, 200)

        currency = client.raw_driver.get_contract('currency')

        self.assertIsNotNone(currency)