from sanic import Sanic
from sanic.response import json, text
from contracting.client import ContractingClient
from multiprocessing import Queue
import ast
import ssl
import traceback

WEB_SERVER_PORT = 5757
SSL_WEB_SERVER_PORT = 443
NUM_WORKERS = 2

app = Sanic(__name__)

ssl_enabled = False
ssl_cert = '~/.ssh/server.csr'
ssl_key = '~/.ssh/server.key'

# CORS(app, automatic_options=True)
client = ContractingClient()


@app.route("/", methods=["GET",])
async def submit_transaction(request):
    return text('indeed')


# Expects json object such that:
'''
{
    'name': 'string',
    'code': 'string'
}
'''
@app.route('/lint', methods=['POST'])
async def lint_contract(request):
    code = request.json.get('code')

    if code is None:
        return json({'error': 'no code provided'}, status=500)

    try:
        violations = client.lint(request.json.get('code'))
        print("no errors")
    except Exception as err:
        args = err.args
        violations =  ["line " + str(args[1][1]) + ": " + args[0] + ", '" + args[1][3] + "'"]
        
    return json({'violations': violations}, status=200)


def start_webserver(q):
    app.queue = q
    if ssl_enabled:
        context = ssl.create_default_context(purpose=ssl.Purpose.CLIENT_AUTH)
        context.load_cert_chain(ssl_cert, keyfile=ssl_key)
        app.run(host='0.0.0.0', port=SSL_WEB_SERVER_PORT, workers=NUM_WORKERS, debug=False, access_log=False, ssl=context)
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
