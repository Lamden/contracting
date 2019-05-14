from sanic import Sanic
from sanic.response import json, text
from sanic_cors import CORS, cross_origin
import json as _json
from contracting.client import ContractingClient
from multiprocessing import Queue
import ast

WEB_SERVER_PORT = 8080
SSL_WEB_SERVER_PORT = 443
NUM_WORKERS = 2

app = Sanic(__name__)

ssl = None
CORS(app, automatic_options=True)
client = ContractingClient()


@app.route("/", methods=["GET",])
async def submit_transaction(request):
    return text("I\'m a teapot", status=418)


# Returns {'contracts': JSON List of strings}
@app.route('/contracts', methods=['GET'])
async def get_contracts(request):
    contracts = client.get_contracts()
    return json({'contracts': contracts})


@app.route('/contracts/<contract>', methods=['GET'])
async def get_contract(request, contract):
    contract_code = client.raw_driver.get_contract(contract)

    if contract_code is None:
        return json({'error': '{} does not exist'.format(contract)}, status=404)
    return json({'name': contract, 'code': contract_code}, status=200)


@app.route("/contracts/<contract>/methods", methods=['GET'])
async def get_methods(request, contract):
    contract_code = client.raw_driver.get_contract(contract)

    if contract_code is None:
        return json({'error': '{} does not exist'.format(contract)}, status=404)

    tree = ast.parse(contract_code)

    function_defs = [n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]

    funcs = []
    for definition in function_defs:
        func_name = definition.name
        kwargs = [arg.arg for arg in definition.args.args]

        funcs.append({'name': func_name, 'arguments': kwargs})

    return json({'methods': funcs}, status=200)


@app.route('/contracts/<contract>/<variable>')
async def get_methods(request, contract, variable):
    contract_code = client.raw_driver.get_contract(contract)

    if contract_code is None:
        return json({'error': '{} does not exist'.format(contract)}, status=404)

    key = request.args.get('key')

    if key is None:
        response = client.raw_driver.get('{}.{}'.format(contract, variable))
    else:
        response = client.raw_driver.get('{}.{}:{}'.format(contract, variable, key))

    if response is None:
        return json({'value': None}, status=404)
    else:
        return json({'value': response}, status=200)


# Expects json object such that:
'''
{
    'name': 'string',
    'code': 'string'
}
'''
@app.route('/lint', methods=['POST'])
async def lint_contract(request):
    try:
        violations = client.lint(request.json.get('code'))
        return json({'violations': violations}, status=200)
    except Exception as e:
        return json({'error': str(e)}, status=500)


@app.route('/compile', methods=['POST'])
async def compile_contract(request):
    code = request.json.get('code')

    if code is None:
        json({'error': 'no code provided'}, status=500)

    violations = client.lint(request.json.get('code'))

    if violations is None:
        compiled_code = client.compiler.parse_to_code(code)
        return json({'code': compiled_code}, status=200)

    return json({'violations': violations}, status=500)


@app.route('/submit', methods=['POST'])
async def submit_contract(request):
    code = request.json.get('code')
    name = request.json.get('name')

    if code is None or name is None:
        return json({'error': 'malformed payload'}, status=500)

    violations = client.lint(request.json.get('code'))

    if violations is None:
        client.submit(request.json.get('code'), name=request.json.get('name'))

    else:
        return json({'violations': violations}, status=500)

    return json({'success': True}, status=200)


@app.route('/exists', methods=['GET'])
async def contract_exists(request):
    contract_code = client.get_contract(request.json.get('name'))

    if contract_code is None:
        return json({'exists': False}, status=404)
    else:
        return json({'exists': True}, status=200)


def start_webserver(q):
    app.queue = q
    if ssl:
        app.run(host='0.0.0.0', port=SSL_WEB_SERVER_PORT, workers=NUM_WORKERS, debug=False, access_log=False, ssl=ssl)
    else:
        app.run(host='0.0.0.0', port=WEB_SERVER_PORT, workers=NUM_WORKERS, debug=False, access_log=False)


if __name__ == '__main__':
    import pyximport; pyximport.install()
    if not app.config.REQUEST_MAX_SIZE:
        app.config.update({
            'REQUEST_MAX_SIZE': 5,
            'REQUEST_TIMEOUT': 5
        })
    start_webserver(Queue())
