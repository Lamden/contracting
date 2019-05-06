from sanic import Sanic
from sanic.response import json, text
from sanic_cors import CORS, cross_origin
import json as _json
from .client import ContractingClient
from multiprocessing import Queue

import ast

WEB_SERVER_PORT = 8080
SSL_WEB_SERVER_PORT = 443
NUM_WORKERS = 2

app = Sanic(__name__)


ssl = None
CORS(app, automatic_options=True)
client = ContractingClient()

@app.route("/", methods=["POST","OPTIONS",])
async def submit_transaction(request):
    return text('indeed')


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


# Expects a code string
@app.route('/lint', methods=['POST'])
async def lint_contract(request):
    violations = client.lint(request)
    return json(violations)


@app.route('/compile', methods=['POST'])
async def compile_contract(request):
    try:
        compiled_code = client.compiler.parse_to_code(request)
    except Exception as e:
        return text(str(e))

    return json(compiled_code)

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
