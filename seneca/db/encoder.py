import json
import decimal
from ..stdlib.bridge.time import Datetime


def encode(data: str):
    return json.dumps(data)


def decode(data):
    if data is None:
        return None

    if isinstance(data, bytes):
        data = data.decode()

    try:
        return json.loads(data, parse_float=decimal.Decimal)
    except json.decoder.JSONDecodeError:
        return None
