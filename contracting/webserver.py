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
    return text('indeed')


@app.route('/contracts', methods=['GET'])
async def get_contracts(request):
    contracts = client.get_contracts()
    return json(contracts)


@app.route('/contracts/<contract>', methods=['GET'])
async def get_contract(request, contract):
    return text(client.raw_driver.get_contract(contract))


@app.route("/contracts/<contract>/methods", methods=["GET","OPTIONS",])
async def get_methods(request, contract):
    c = client.raw_driver.get_contract(contract)

    tree = ast.parse(c)

    function_defs = [n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]

    funcs = []
    for definition in function_defs:
        func_name = definition.name
        kwargs = [arg.arg for arg in definition.args.args]

        funcs.append((func_name, kwargs))

    return json(funcs)


@app.route('/contracts/<contract>/<variable>')
async def get_methods(request, contract, variable):
    key = request.args.get('key')
    if key is None:
        response = client.raw_driver.get('{}.{}'.format(contract, variable))
        print('response: {}'.format(response))
    else:
        response = client.raw_driver.get('{}.{}:{}'.format(contract, variable, key))
        print('response: {}'.format(response))
    if response is None:
        return json('null')
    else:
        return json(response)


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
        return json(violations)
    except Exception as e:
        return json({'error': str(e)})


@app.route('/compile', methods=['POST'])
async def compile_contract(request):
    try:
        compiled_code = client.compiler.parse_to_code(request.json.get('code'))
    except Exception as e:
        return text(str(e))

    return text(compiled_code)


@app.route('/submit', methods=['POST'])
async def submit_contract(request):
    try:
        client.submit(request.json.get('code'), name=request.json.get('name'))
    except AssertionError as e:
        return text(str(e))

    return text('success!')


@app.route('/exists', methods=['GET'])
async def contract_exists(request):
    c = client.get_contract(request.json.get('name'))
    if c is None:
        return text(False)
    else:
        return text(True)

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
