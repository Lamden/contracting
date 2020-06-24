from unittest import TestCase
from contracting.webserver import app, client
import json
from http import HTTPStatus


class TestWebserver(TestCase):
    def tearDown(self):
        client.flush()

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
        kwargs = ['name', 'code', 'owner', 'constructor_args']

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
        with open('./test_sys_contracts/currency.s.py') as f:
            contract = f.read()

        payload = {'name': 'currency', 'code': contract}

        _, response = app.test_client.post('/submit', data=json.dumps(payload))

        self.assertEqual(response.status, 200)

        currency = client.raw_driver.get_contract('currency')

        self.assertIsNotNone(currency)

    def test_get_variable(self):
        with open('./test_sys_contracts/currency.s.py') as f:
            contract = f.read()

        payload = {'name': 'currency', 'code': contract}

        _, response = app.test_client.post('/submit', data=json.dumps(payload))

        _, response = app.test_client.get('/contracts/currency/seed_amount')

        self.assertEqual(response.status, 200)
        self.assertEqual(response.json.get('value'), 1000000)

    def test_get_variable_from_non_existent_contract(self):
        _, response = app.test_client.get('/contracts/currency/seed_amount')

        self.assertEqual(response.status, 404)

    def test_get_non_existent_variable_from_contract(self):
        with open('./test_sys_contracts/currency.s.py') as f:
            contract = f.read()

        payload = {'name': 'currency', 'code': contract}

        _, response = app.test_client.post('/submit', data=json.dumps(payload))

        _, response = app.test_client.get('/contracts/currency/hoooooooplah')

        self.assertEqual(response.status, 404)
        self.assertEqual(response.json.get('value'), None)

    def test_get_hash_value(self):
        with open('./test_sys_contracts/currency.s.py') as f:
            contract = f.read()

        payload = {'name': 'currency', 'code': contract}

        _, response = app.test_client.post('/submit', data=json.dumps(payload))

        _, response = app.test_client.get(
            '/contracts/currency/balances?key=324ee2e3544a8853a3c5a0ef0946b929aa488cbe7e7ee31a0fef9585ce398502'
        )

        self.assertEqual(response.status, 200)
        self.assertEqual(response.json.get('value'), 1000000)

    def test_get_hash_from_non_existent_contract(self):
        _, response = app.test_client.get(
            '/contracts/currency/balances?key=324ee2e3544a8853a3c5a0ef0946b929aa488cbe7e7ee31a0fef9585ce398502'
        )

        self.assertEqual(response.status, 404)
        self.assertEqual(response.json.get('value'), None)

    def test_get_non_existent_hash_from_contract(self):
        with open('./test_sys_contracts/currency.s.py') as f:
            contract = f.read()

        payload = {'name': 'currency', 'code': contract}

        _, response = app.test_client.post('/submit', data=json.dumps(payload))

        _, response = app.test_client.get(
            '/contracts/currency/balances?key=ZZZZZZZZZZZZZZZZZZZZZZ'
        )

        self.assertEqual(response.status, 404)
        self.assertEqual(response.json.get('value'), None)

    def test_lint_contract(self):
        with open('./test_sys_contracts/bad_lint.s.py') as f:
            contract = f.read()

        payload = {'code': contract}

        _, response = app.test_client.post('/lint', data=json.dumps(payload))

        violations = response.json.get('violations')

        self.assertEqual(len(violations), 1)
        self.assertEqual(response.status, 200)
        self.assertEqual(violations[0], 'Line 0: S13- No valid contracting decorator found')

    def test_lint_no_errors(self):
        with open('./test_sys_contracts/good_lint.s.py') as f:
            contract = f.read()

        payload = {'code': contract}

        _, response = app.test_client.post('/lint', data=json.dumps(payload))

        violations = response.json.get('violations')

        self.assertEqual(response.status, 200)
        self.assertEqual(violations, None)

    def test_lint_bad_params(self):
        payload = {'not_code': 'poo'}

        _, response = app.test_client.post('/lint', data=json.dumps(payload))

        self.assertEqual(response.status, 500)

    def test_compile_contract(self):
        with open('./test_sys_contracts/compile_this.s.py') as f:
            contract = f.read()

        payload = {'code': contract}

        _, response = app.test_client.post('/compile', data=json.dumps(payload))

        compiled_code = response.json.get('code')

        self.assertEqual(response.status, 200)

        code = client.compiler.parse_to_code(contract)

        self.assertEqual(code, compiled_code)

    def test_compile_bad_code(self):
        with open('./test_sys_contracts/bad_lint.s.py') as f:
            contract = f.read()

        payload = {'code': contract}

        _, response = app.test_client.post('/compile', data=json.dumps(payload))

        violations = response.json.get('violations')

        self.assertEqual(len(violations), 1)
        self.assertEqual(response.status, 500)
        self.assertEqual(violations[0], 'Line 0: S13- No valid contracting decorator found')

    def test_compile_no_code_param(self):
        payload = {'not_code': 'yo'}

        _, response = app.test_client.post('/compile', data=json.dumps(payload))

        self.assertEqual(response.status, 500)

    def test_submit_no_code_but_name(self):
        payload = {'no_code': 'poo', 'name': 'something'}

        _, response = app.test_client.post('/submit', data=json.dumps(payload))

        self.assertEqual(response.status, 500)

    def test_submit_code_but_no_name(self):
        with open('./test_sys_contracts/compile_this.s.py') as f:
            contract = f.read()

        payload = {'code': contract, 'no_name': 'something'}

        _, response = app.test_client.post('/submit', data=json.dumps(payload))

        self.assertEqual(response.status, 500)

    def test_submit_lint_errors(self):
        with open('./test_sys_contracts/bad_lint.s.py') as f:
            contract = f.read()

        payload = {'code': contract, 'name': 'something'}

        _, response = app.test_client.post('/submit', data=json.dumps(payload))

        self.assertEqual(response.status, 500)

