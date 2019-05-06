from sanic import Sanic
from sanic.response import json, text
from sanic_cors import CORS, cross_origin
import json as _json
from .client import ContractingClient
from multiprocessing import Queue

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
    return text(client.get_contract(contract))

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
